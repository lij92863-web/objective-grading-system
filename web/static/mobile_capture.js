(() => {
  "use strict";

  const DB_NAME = "objective-grading-mobile-capture";
  const DB_VERSION = 1;
  const STORE_NAME = "captures";
  const MAX_ATTEMPTS = 6;
  const CAPTURE_COOLDOWN_MS = 800;
  const FOREGROUND_POLL_MS = 1500;
  const BACKGROUND_POLL_MS = 10000;
  const SESSION_ID = document.body.dataset.sessionId;
  const STATES = Object.freeze({
    LOCAL_PENDING: "LOCAL_PENDING",
    UPLOADING: "UPLOADING",
    ACKNOWLEDGED: "ACKNOWLEDGED",
    RETRY_WAIT: "RETRY_WAIT",
    FAILED_MANUAL: "FAILED_MANUAL",
  });

  const elements = {
    video: document.querySelector("#mobile-video"),
    cameraSelect: document.querySelector("#camera-select"),
    start: document.querySelector("#start-camera"),
    capture: document.querySelector("#capture-button"),
    stop: document.querySelector("#stop-camera"),
    retry: document.querySelector("#retry-button"),
    cameraMessage: document.querySelector("#camera-message"),
    captureMessage: document.querySelector("#capture-message"),
    flash: document.querySelector("#capture-flash"),
    thumbnail: document.querySelector("#last-thumbnail"),
    serviceState: document.querySelector("#service-state"),
    recentJobs: document.querySelector("#recent-jobs"),
  };

  let database;
  let stream;
  let uploadWorkerActive = false;
  let captureLocked = false;
  let storageBlocked = false;
  let thumbnailUrl = "";
  let pollTimer;

  function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        const store = db.createObjectStore(STORE_NAME, { keyPath: "client_capture_id" });
        store.createIndex("session_id", "session_id", { unique: false });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("无法打开手机本地采集队列"));
      request.onblocked = () => reject(new Error("手机本地采集队列被其他页面占用"));
    });
  }

  function requestResult(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("IndexedDB 操作失败"));
    });
  }

  function transactionDone(transaction) {
    return new Promise((resolve, reject) => {
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error || new Error("IndexedDB 事务失败"));
      transaction.onabort = () => reject(transaction.error || new Error("IndexedDB 事务中止"));
    });
  }

  async function putQueueItem(item) {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    transaction.objectStore(STORE_NAME).put(item);
    await transactionDone(transaction);
  }

  async function queueItems() {
    const transaction = database.transaction(STORE_NAME, "readonly");
    const done = transactionDone(transaction);
    const request = transaction.objectStore(STORE_NAME).index("session_id").getAll(SESSION_ID);
    const items = await requestResult(request);
    await done;
    return items.sort((left, right) => left.captured_at.localeCompare(right.captured_at));
  }

  async function recoverInterruptedUploads() {
    const items = await queueItems();
    for (const item of items) {
      if (item.state === STATES.UPLOADING) {
        item.state = STATES.RETRY_WAIT;
        item.last_error = "页面重新打开，等待安全重试";
        item.next_retry_at = Date.now();
        await putQueueItem(item);
      }
    }
  }

  function stopCamera(message = "摄像头已停止") {
    if (stream) {
      for (const track of stream.getTracks()) track.stop();
      stream = undefined;
    }
    elements.video.srcObject = null;
    elements.capture.disabled = true;
    elements.stop.disabled = true;
    elements.cameraMessage.textContent = message;
  }

  async function startCamera(deviceId = "") {
    stopCamera("正在请求摄像头权限…");
    const video = deviceId
      ? { deviceId: { exact: deviceId }, width: { ideal: 3840 }, height: { ideal: 2160 } }
      : { facingMode: { ideal: "environment" }, width: { ideal: 3840 }, height: { ideal: 2160 } };
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: false, video });
      elements.video.srcObject = stream;
      await elements.video.play();
      await refreshCameraChoices();
      const settings = stream.getVideoTracks()[0].getSettings();
      if (settings.deviceId) elements.cameraSelect.value = settings.deviceId;
      elements.cameraMessage.textContent = "摄像头已启动，请把答题卡放入参考框";
      elements.capture.disabled = storageBlocked;
      elements.stop.disabled = false;
    } catch (error) {
      stopCamera("无法使用摄像头，请检查 Chrome 权限后重试");
      showCaptureMessage("摄像头未授权或不可用。", true);
    }
  }

  async function refreshCameraChoices() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const cameras = devices.filter((device) => device.kind === "videoinput");
    elements.cameraSelect.replaceChildren();
    cameras.forEach((camera, index) => {
      const option = document.createElement("option");
      option.value = camera.deviceId;
      option.textContent = camera.label || `摄像头 ${index + 1}`;
      elements.cameraSelect.append(option);
    });
    elements.cameraSelect.disabled = cameras.length < 2;
  }

  function canvasBlob() {
    const canvas = document.createElement("canvas");
    canvas.width = elements.video.videoWidth;
    canvas.height = elements.video.videoHeight;
    if (!canvas.width || !canvas.height) throw new Error("摄像头画面尚未准备好");
    canvas.getContext("2d", { alpha: false }).drawImage(elements.video, 0, 0);
    return new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => blob ? resolve(blob) : reject(new Error("无法生成照片")),
        "image/jpeg",
        0.95,
      );
    });
  }

  async function takePhoto() {
    const track = stream?.getVideoTracks()[0];
    if (!track) throw new Error("摄像头尚未启动");
    if ("ImageCapture" in window) {
      try {
        const blob = await new ImageCapture(track).takePhoto();
        if (["image/jpeg", "image/png"].includes(blob.type)) {
          return { blob, method: "IMAGE_CAPTURE" };
        }
      } catch (error) {
        // Progressive enhancement: canvas remains the safe fallback.
      }
    }
    return { blob: await canvasBlob(), method: "CANVAS" };
  }

  async function deviceIdSummary(deviceId) {
    if (!deviceId || !crypto.subtle) return "";
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(deviceId));
    return Array.from(new Uint8Array(digest).slice(0, 8), (value) => value.toString(16).padStart(2, "0")).join("");
  }

  function newCaptureId() {
    if (crypto.randomUUID) return crypto.randomUUID();
    return `capture-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  }

  function flash() {
    elements.flash.classList.remove("is-active");
    void elements.flash.offsetWidth;
    elements.flash.classList.add("is-active");
  }

  async function capture() {
    if (captureLocked || storageBlocked || !stream) return;
    captureLocked = true;
    elements.capture.disabled = true;
    let persistenceStarted = false;
    try {
      const { blob, method } = await takePhoto();
      const track = stream.getVideoTracks()[0];
      const settings = track.getSettings();
      const mimeType = blob.type === "image/png" ? "image/png" : "image/jpeg";
      const extension = mimeType === "image/png" ? "png" : "jpg";
      const clientCaptureId = newCaptureId();
      const item = {
        client_capture_id: clientCaptureId,
        session_id: SESSION_ID,
        blob,
        filename: `${clientCaptureId}.${extension}`,
        captured_at: new Date().toISOString(),
        capture_method: method,
        device_label: track.label || "",
        device_id: await deviceIdSummary(settings.deviceId || ""),
        facing_mode: settings.facingMode || "unknown",
        width: settings.width || elements.video.videoWidth,
        height: settings.height || elements.video.videoHeight,
        mime_type: mimeType,
        size_bytes: blob.size,
        state: STATES.LOCAL_PENDING,
        attempt_count: 0,
        last_error: "",
        next_retry_at: 0,
        server_capture_job_id: "",
      };
      persistenceStarted = true;
      await putQueueItem(item);
      persistenceStarted = false;
      flash();
      if (thumbnailUrl) URL.revokeObjectURL(thumbnailUrl);
      thumbnailUrl = URL.createObjectURL(blob);
      elements.thumbnail.src = thumbnailUrl;
      elements.thumbnail.hidden = false;
      showCaptureMessage("照片已安全保存到手机，正在排队上传。", false);
      await refreshLocalCounts();
      void runUploadWorker();
    } catch (error) {
      if (persistenceStarted) {
        storageBlocked = true;
        showCaptureMessage(`照片未保存：${error.message || "手机存储不可用"}。请释放空间后重试。`, true);
      } else {
        showCaptureMessage(`本次拍照失败：${error.message || "摄像头画面不可用"}。`, true);
      }
    } finally {
      window.setTimeout(() => {
        captureLocked = false;
        elements.capture.disabled = storageBlocked || !stream;
      }, CAPTURE_COOLDOWN_MS);
    }
  }

  function formFor(item) {
    const form = new FormData();
    form.append("image", item.blob, item.filename);
    for (const name of [
      "client_capture_id", "captured_at", "capture_method", "device_label",
      "device_id", "facing_mode", "width", "height", "mime_type",
    ]) {
      form.append(name, String(item[name]));
    }
    return form;
  }

  function retryDelay(attemptCount) {
    return Math.min(60000, 1000 * (2 ** Math.max(0, attemptCount - 1)));
  }

  async function nextUpload() {
    const now = Date.now();
    const items = await queueItems();
    return items.find((item) =>
      item.blob && (
        item.state === STATES.LOCAL_PENDING ||
        (item.state === STATES.RETRY_WAIT && item.next_retry_at <= now)
      )
    );
  }

  async function recordUploadFailure(item, message, manual) {
    item.attempt_count += 1;
    item.last_error = String(message || "上传失败").slice(0, 300);
    if (manual || item.attempt_count >= MAX_ATTEMPTS) {
      item.state = STATES.FAILED_MANUAL;
      item.next_retry_at = 0;
    } else {
      item.state = STATES.RETRY_WAIT;
      item.next_retry_at = Date.now() + retryDelay(item.attempt_count);
    }
    await putQueueItem(item);
  }

  async function uploadOne(item) {
    item.state = STATES.UPLOADING;
    await putQueueItem(item);
    await refreshLocalCounts();
    try {
      const response = await fetch(`/sessions/${encodeURIComponent(SESSION_ID)}/capture/mobile-web`, {
        method: "POST",
        body: formFor(item),
        cache: "no-store",
      });
      let payload;
      try {
        payload = await response.json();
      } catch (error) {
        throw new Error(`服务返回了非 JSON 响应（HTTP ${response.status}）`);
      }
      if (!response.ok || !payload.ok || !payload.capture_job_id) {
        const message = payload.message || `上传失败（HTTP ${response.status}）`;
        await recordUploadFailure(item, message, response.status >= 400 && response.status < 500);
        return;
      }
      item.state = STATES.ACKNOWLEDGED;
      item.server_capture_job_id = payload.capture_job_id;
      item.last_error = payload.warning || "";
      item.next_retry_at = 0;
      item.blob = null;
      await putQueueItem(item);
      showCaptureMessage(payload.warning || "服务器已确认入队，可继续拍摄。", false);
    } catch (error) {
      await recordUploadFailure(item, error.message, false);
    }
  }

  async function runUploadWorker() {
    if (uploadWorkerActive || !database) return;
    uploadWorkerActive = true;
    try {
      while (true) {
        const item = await nextUpload();
        if (!item) break;
        await uploadOne(item);
        await refreshLocalCounts();
      }
    } finally {
      uploadWorkerActive = false;
      const pending = await queueItems();
      const nextRetry = pending
        .filter((item) => item.state === STATES.RETRY_WAIT)
        .reduce((earliest, item) => Math.min(earliest, item.next_retry_at), Infinity);
      if (Number.isFinite(nextRetry)) {
        window.setTimeout(() => void runUploadWorker(), Math.max(250, nextRetry - Date.now()));
      }
    }
  }

  async function retryFailed() {
    const items = await queueItems();
    for (const item of items) {
      if (item.blob && [STATES.FAILED_MANUAL, STATES.RETRY_WAIT].includes(item.state)) {
        item.state = STATES.LOCAL_PENDING;
        item.attempt_count = 0;
        item.last_error = "";
        item.next_retry_at = 0;
        await putQueueItem(item);
      }
    }
    storageBlocked = false;
    elements.capture.disabled = !stream;
    await refreshLocalCounts();
    void runUploadWorker();
  }

  async function refreshLocalCounts() {
    const items = await queueItems();
    const count = (state) => items.filter((item) => item.state === state).length;
    document.querySelector("#count-captured").textContent = String(items.length);
    document.querySelector("#count-pending").textContent = String(
      count(STATES.LOCAL_PENDING) + count(STATES.RETRY_WAIT),
    );
    document.querySelector("#count-uploading").textContent = String(count(STATES.UPLOADING));
    document.querySelector("#count-acknowledged").textContent = String(count(STATES.ACKNOWLEDGED));
    document.querySelector("#count-failed").textContent = String(count(STATES.FAILED_MANUAL));
  }

  function updateServerStatus(payload) {
    const counts = payload.counts || {};
    document.querySelector("#count-review").textContent = String(counts.review_required || 0);
    document.querySelector("#server-queued").textContent = String(counts.queued || 0);
    document.querySelector("#server-processing").textContent = String(counts.processing || 0);
    document.querySelector("#server-mobile-total").textContent = String(counts.mobile_total || 0);
    elements.recentJobs.replaceChildren();
    const recent = payload.recent || [];
    if (!recent.length) {
      const item = document.createElement("li");
      item.textContent = "还没有服务器任务";
      elements.recentJobs.append(item);
    } else {
      recent.slice(0, 8).forEach((job) => {
        const item = document.createElement("li");
        item.textContent = `${job.capture_job_id.slice(0, 8)} · ${job.state}`;
        elements.recentJobs.append(item);
      });
    }
  }

  async function pollServer() {
    window.clearTimeout(pollTimer);
    try {
      const health = await fetch("/mobile-capture/health.json", { cache: "no-store" });
      const healthPayload = await health.json();
      if (!health.ok || !healthPayload.ok) throw new Error("服务不可用");
      elements.serviceState.textContent = "USB 服务正常";
      elements.serviceState.classList.remove("is-offline");
      const response = await fetch(
        `/sessions/${encodeURIComponent(SESSION_ID)}/capture/status.json`,
        { cache: "no-store" },
      );
      const payload = await response.json();
      if (!response.ok || !payload.ok) throw new Error(payload.message || "状态读取失败");
      updateServerStatus(payload);
      void runUploadWorker();
    } catch (error) {
      elements.serviceState.textContent = "服务连接中断";
      elements.serviceState.classList.add("is-offline");
    } finally {
      pollTimer = window.setTimeout(
        pollServer,
        document.hidden ? BACKGROUND_POLL_MS : FOREGROUND_POLL_MS,
      );
    }
  }

  function showCaptureMessage(message, isError) {
    elements.captureMessage.textContent = message;
    elements.captureMessage.classList.toggle("is-error", isError);
  }

  async function initialize() {
    if (!SESSION_ID || !navigator.mediaDevices?.getUserMedia || !window.indexedDB) {
      storageBlocked = true;
      showCaptureMessage("此浏览器不支持所需的摄像头或本地持久存储能力。", true);
      return;
    }
    try {
      database = await openDatabase();
      await recoverInterruptedUploads();
      await refreshLocalCounts();
      void runUploadWorker();
      void pollServer();
    } catch (error) {
      storageBlocked = true;
      showCaptureMessage(`无法使用手机本地队列：${error.message}`, true);
    }
  }

  elements.start.addEventListener("click", () => void startCamera());
  elements.capture.addEventListener("click", () => void capture());
  elements.stop.addEventListener("click", () => stopCamera());
  elements.retry.addEventListener("click", () => void retryFailed());
  elements.cameraSelect.addEventListener("change", (event) => void startCamera(event.target.value));
  window.addEventListener("pagehide", () => stopCamera("页面已退出，摄像头已停止"));
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      stopCamera("页面进入后台，摄像头已停止");
    } else {
      void pollServer();
    }
  });

  void initialize();
})();
