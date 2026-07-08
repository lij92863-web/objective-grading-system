const state = {
  classes: [],
  students: [],
  history: [],
  activeClass: "",
  step: 0,
  sessionId: "",
  preview: null,
  result: null,
  answerMode: "table",
  answerConfirmed: false,
  answerRows: [],
  submissionMode: "file",
  cameraMode: "webcam",
  devices: [],
  stream: null,
  capturedImages: []
};

const steps = ["考试信息", "标准答案", "学生作答", "异常确认", "开始批改", "完成"];
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function toast(message) {
  const box = $("#toast");
  box.textContent = message;
  box.classList.add("show");
  clearTimeout(box.timer);
  box.timer = setTimeout(() => box.classList.remove("show"), 2600);
}

function showView(name) {
  $$(".view").forEach((view) => view.classList.toggle("active-view", view.id === name));
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === name));
  if (name === "classes") loadClasses();
  if (name === "history" || name === "reports") loadHistory();
  if (name === "home") loadHistory(true);
}

async function api(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok || data.ok === false) throw new Error(data.message || "操作失败");
  return data;
}

function renderStepper() {
  $("#stepper").innerHTML = steps.map((label, index) => {
    const cls = index === state.step ? "active" : index < state.step ? "done" : "";
    return `<div class="step-pill ${cls}">${index + 1} ${label}</div>`;
  }).join("");
  $$(".wizard-step").forEach((step) => step.classList.toggle("active-step", Number(step.dataset.step) === state.step));
  $("#prevStep").disabled = state.step === 0;
  $("#nextStep").classList.toggle("hidden", state.step === 4 || state.step === 5);
  $("#nextStep").textContent = state.step === 3 ? "下一步" : "下一步";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
}

function table(headers, rows) {
  if (!rows || !rows.length) return `<div class="empty-state">暂无数据</div>`;
  return `<table><thead><tr>${headers.map((h) => `<th>${h.label}</th>`).join("")}</tr></thead><tbody>${
    rows.map((row) => `<tr>${headers.map((h) => `<td>${row[h.key] ?? ""}</td>`).join("")}</tr>`).join("")
  }</tbody></table>`;
}

async function loadClasses() {
  const data = await api("/api/classes");
  state.classes = data.classes || [];
  const list = $("#classList");
  list.innerHTML = state.classes.length ? state.classes.map((item) => `
    <div class="class-item ${state.activeClass === item.class_name ? "active" : ""}" data-class="${item.class_name}">
      <strong>${item.class_name}</strong>
      <span>${item.student_count || 0} 名学生 · ${item.updated_at || "未更新"}</span>
    </div>
  `).join("") : `<div class="empty-state">还没有班级，请先导入名单。</div>`;
  $("#examClassSelect").innerHTML = state.classes.length
    ? state.classes.map((item) => `<option value="${item.class_name}">${item.class_name}</option>`).join("")
    : `<option value="">请先导入班级名单</option>`;
}

async function loadClassDetail(className) {
  state.activeClass = className;
  const data = await api(`/api/class?class_name=${encodeURIComponent(className)}`);
  state.students = data.students || [];
  $("#classDetailTitle").textContent = className;
  $("#classDetailMeta").textContent = `共 ${state.students.length} 名学生`;
  renderStudents();
  loadClasses();
}

function renderStudents() {
  const keyword = ($("#studentSearch").value || "").trim();
  const rows = state.students.filter((row) => !keyword || row.student_id.includes(keyword) || row.name.includes(keyword));
  $("#studentTable").innerHTML = table([
    { key: "student_id", label: "学号" },
    { key: "name", label: "姓名" }
  ], rows);
}

async function importClass(event) {
  event.preventDefault();
  const form = new FormData(event.target);
  toast("正在导入名单...");
  const data = await api("/api/classes/import", { method: "POST", body: form });
  toast(data.message || "名单导入完成");
  event.target.reset();
  await loadClasses();
}

async function loadHistory(homeOnly = false) {
  const data = await api("/api/exams/history");
  state.history = data.items || [];
  renderHistory();
  renderReports();
  if (homeOnly) renderRecent();
}

function examCard(item) {
  const actions = [
    item.index_url ? `<a class="small-link" target="_blank" href="${item.index_url}">完整报告</a>` : "",
    item.teaching_url ? `<a class="small-link" target="_blank" href="${item.teaching_url}">讲评建议</a>` : "",
    item.dashboard_url ? `<a class="small-link" target="_blank" href="${item.dashboard_url}">学情分析</a>` : ""
  ].join("");
  return `<article class="exam-card">
    <div>
      <h3>${item.exam_name || "未命名考试"}</h3>
      <div class="exam-meta">${item.class_name || "未填写班级"} · ${item.exam_date || "未填写日期"} · ${item.student_count || "-"} 人 · 平均分 ${item.average || "-"}</div>
    </div>
    <div class="exam-actions">${actions}<span class="chip ok">${item.status}</span></div>
  </article>`;
}

function renderRecent() {
  const target = $("#recentExamList");
  target.classList.remove("skeleton-lines");
  const rows = state.history.slice(0, 4);
  target.innerHTML = rows.length ? rows.map(examCard).join("") : `<div class="empty-state">还没有考试记录。</div>`;
}

function renderHistory() {
  const target = $("#historyList");
  if (!target) return;
  const keyword = ($("#historySearch")?.value || "").trim();
  const rows = state.history.filter((item) => !keyword || `${item.exam_name}${item.class_name}`.includes(keyword));
  target.innerHTML = rows.length ? rows.map(examCard).join("") : `<div class="empty-state">没有找到考试记录。</div>`;
}

function renderReports() {
  const target = $("#reportList");
  if (!target) return;
  const rows = state.history.slice(0, 12);
  target.innerHTML = rows.length ? rows.map((item) => `
    <article class="report-card">
      <h2>${item.exam_name || "未命名考试"}</h2>
      <p>${item.class_name || "未填写班级"} · ${item.exam_date || "未填写日期"}</p>
      <div class="exam-actions" style="margin-top:14px">
        ${item.teaching_url ? `<a class="small-link" target="_blank" href="${item.teaching_url}">讲评计划</a>` : ""}
        ${item.dashboard_url ? `<a class="small-link" target="_blank" href="${item.dashboard_url}">完整分析</a>` : ""}
        ${item.index_url ? `<a class="small-link" target="_blank" href="${item.index_url}">报告首页</a>` : ""}
      </div>
    </article>
  `).join("") : `<div class="empty-state">暂无可打开的报告。</div>`;
}

function validateStep() {
  const form = $("#examWizard");
  const current = $(`.wizard-step[data-step="${state.step}"]`);
  const inputs = Array.from(current.querySelectorAll("input[required], select[required]"));
  for (const input of inputs) {
    if (!input.value) {
      input.focus();
      toast("请先填写当前步骤的信息。");
      return false;
    }
  }
  if (state.step === 3 && !state.preview) {
    toast("请先点击“检查数据”。");
    return false;
  }
  if (state.step === 1 && !state.answerConfirmed) {
    toast("请先确认标准答案。");
    return false;
  }
  return form.reportValidity();
}

function nextStep() {
  if (!validateStep()) return;
  state.step = Math.min(5, state.step + 1);
  renderStepper();
  if (state.step === 4) renderGradeSummary();
}

function prevStep() {
  state.step = Math.max(0, state.step - 1);
  renderStepper();
}

async function previewExam() {
  const form = $("#examWizard");
  if (!form.reportValidity()) return;
  const formData = new FormData(form);
  if (state.sessionId) formData.set("session_id", state.sessionId);
  $("#previewButton").disabled = true;
  $("#validationArea").innerHTML = `<div class="validation-card"><span class="chip">检查中</span><p style="margin-top:12px">正在读取文件，请稍候。</p></div>`;
  try {
    const data = await api("/api/exams/preview", { method: "POST", body: formData });
    state.sessionId = data.session_id;
    state.preview = data;
    renderValidation(data);
    $("#gradeButton").disabled = data.blocking;
    toast(data.blocking ? "发现需要先处理的问题" : "数据检查完成，可以继续批改");
  } catch (error) {
    $("#validationArea").innerHTML = `<div class="validation-card"><span class="chip error">检查失败</span><p style="margin-top:12px">${error.message}</p></div>`;
    toast(error.message);
  } finally {
    $("#previewButton").disabled = false;
  }
}

function setAnswerMode(mode) {
  state.answerMode = mode;
  $$("[data-answer-mode]").forEach((card) => card.classList.toggle("active", card.dataset.answerMode === mode));
  const file = $("#answerSourceFile");
  const manual = $("#manualAnswerText");
  manual.classList.toggle("hidden", mode !== "manual");
  file.closest(".file-drop").classList.toggle("hidden", mode === "manual");
  if (mode === "table") file.accept = ".xlsx,.xls,.csv";
  if (mode === "document") file.accept = ".docx,.pdf";
  if (mode === "image") file.accept = ".jpg,.jpeg,.png,.webp,.pdf";
}

async function parseAnswerDraft() {
  const form = $("#examWizard");
  const formData = new FormData(form);
  if (state.sessionId) formData.set("session_id", state.sessionId);
  formData.set("manual_text", $("#manualAnswerText").value || "");
  $("#parseAnswerButton").disabled = true;
  try {
    const data = await api("/api/answer/parse", { method: "POST", body: formData });
    state.sessionId = data.session_id;
    state.answerRows = data.review_rows || [];
    state.answerConfirmed = false;
    renderAnswerDraft(data.draft || {});
    toast("已生成标准答案草稿，请确认。");
  } catch (error) {
    toast(error.message);
  } finally {
    $("#parseAnswerButton").disabled = false;
  }
}

function renderAnswerDraft(draft) {
  $("#answerDraftArea").classList.remove("hidden");
  const warnings = draft.warnings || [];
  $("#answerWarnings").innerHTML = warnings.map((message) => `<div class="notice">${escapeHtml(message)}</div>`).join("");
  renderAnswerRows();
}

function renderAnswerRows() {
  const headers = ["题号", "题型", "标准答案", "分值", "部分给分", "知识点", "难度", "自动批改", "置信度", "警告", "操作"];
  const body = state.answerRows.map((row, index) => {
    const confidence = Number(row.confidence || 0);
    const low = confidence && confidence < 0.85;
    return `<tr class="${low || !row.answer ? "low-confidence" : ""}" data-answer-row="${index}">
      <td><input data-field="question" value="${escapeHtml(row.question)}"></td>
      <td><select data-field="type">
        ${["single_choice", "multiple_choice", "blank", "true_false"].map((type) => `<option value="${type}" ${row.type === type ? "selected" : ""}>${typeLabel(type)}</option>`).join("")}
      </select></td>
      <td><input data-field="answer" value="${escapeHtml(row.answer)}" placeholder="例如 A 或 ABCD"></td>
      <td><input data-field="points" value="${escapeHtml(row.points || 1)}"></td>
      <td><select data-field="partial_credit"><option value="false">否</option><option value="true" ${String(row.partial_credit) === "true" || row.partial_credit === true ? "selected" : ""}>是</option></select></td>
      <td><input data-field="tags" value="${escapeHtml(row.tags)}"></td>
      <td><input data-field="difficulty" value="${escapeHtml(row.difficulty)}"></td>
      <td><select data-field="auto_gradable"><option value="true">是</option><option value="false" ${String(row.auto_gradable) === "false" ? "selected" : ""}>否</option></select></td>
      <td>${confidence ? Math.round(confidence * 100) + "%" : "待确认"}</td>
      <td><input data-field="warnings" value="${escapeHtml(Array.isArray(row.warnings) ? row.warnings.join(";") : row.warnings)}"></td>
      <td class="row-actions"><button type="button" data-delete-answer="${index}">删除</button></td>
    </tr>`;
  }).join("");
  $("#answerReviewTable").innerHTML = `<table><thead><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table>`;
}

function typeLabel(type) {
  return { single_choice: "单选题", multiple_choice: "多选题", blank: "填空题", true_false: "判断题" }[type] || "客观题";
}

function collectAnswerRows() {
  $$("[data-answer-row]").forEach((tr) => {
    const index = Number(tr.dataset.answerRow);
    tr.querySelectorAll("[data-field]").forEach((input) => {
      state.answerRows[index][input.dataset.field] = input.value;
    });
  });
}

async function confirmAnswer() {
  collectAnswerRows();
  const missing = state.answerRows.find((row) => !row.question || !row.answer);
  if (missing) {
    toast("请先补齐题号和标准答案。");
    return;
  }
  try {
    const data = await api("/api/answer/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, rows: state.answerRows })
    });
    state.answerConfirmed = true;
    toast(data.message || "标准答案已确认");
  } catch (error) {
    toast(error.message);
  }
}

function addAnswerRow() {
  collectAnswerRows();
  state.answerRows.push({ question: state.answerRows.length + 1, type: "single_choice", answer: "", points: 1, partial_credit: "false", tags: "", difficulty: "", auto_gradable: "true", confidence: 1, warnings: "" });
  renderAnswerRows();
}

function deleteAnswerRow(index) {
  collectAnswerRows();
  state.answerRows.splice(index, 1);
  renderAnswerRows();
}

function setSubmissionMode(mode) {
  state.submissionMode = mode;
  $$("[data-submission-mode]").forEach((card) => card.classList.toggle("active", card.dataset.submissionMode === mode));
  $("#submissionFilePanel").classList.toggle("hidden", mode !== "file");
  $("#cameraPanel").classList.toggle("hidden", mode !== "camera");
  if (mode === "camera") {
    renderCameraHelp();
    refreshCameras();
  } else {
    closeCamera();
  }
}

function setCameraMode(mode) {
  state.cameraMode = mode;
  $$("[data-camera-mode]").forEach((card) => card.classList.toggle("active", card.dataset.cameraMode === mode));
  renderCameraHelp();
}

function renderCameraHelp() {
  const webcam = `<strong>使用电脑或外接摄像头：</strong><ol><li>请确认摄像头或高拍仪已经连接电脑。</li><li>点击“打开摄像头”。</li><li>如果画面不是想用的摄像头，请点击“切换摄像头”或在下拉框中选择。</li><li>将答题卡放入取景框内，保持光线充足后点击“拍一张”。</li></ol>`;
  const phone = `<strong>使用手机摄像头：</strong><ol><li>用数据线连接手机和电脑。</li><li>在手机上选择“摄像头 / Webcam / USB 摄像头”模式。</li><li>回到本页面，点击“打开摄像头”。</li><li>如果画面不是手机摄像头，请点击“切换摄像头”或在下拉框中选择。</li><li>如果没有看到手机摄像头，请确认数据线支持数据传输，或尝试 DroidCam 等工具。</li></ol><p style="margin-top:8px">软件不会直接控制手机，只会调用电脑系统已经识别出的摄像头设备。</p>`;
  $("#cameraHelp").innerHTML = state.cameraMode === "phone" ? phone : webcam;
}

async function refreshCameras() {
  if (!navigator.mediaDevices?.enumerateDevices) {
    toast("当前浏览器不支持摄像头拍照，请改用上传图片。");
    return;
  }
  const devices = await navigator.mediaDevices.enumerateDevices();
  state.devices = devices.filter((device) => device.kind === "videoinput");
  $("#cameraSelect").innerHTML = state.devices.length
    ? state.devices.map((device, index) => `<option value="${device.deviceId}">${device.label || `摄像头 ${index + 1}`}</option>`).join("")
    : `<option value="">未检测到摄像头</option>`;
}

function cameraErrorMessage(error) {
  const text = String(error?.name || error || "");
  if (text.includes("NotAllowed")) return "浏览器没有摄像头权限，请在地址栏左侧允许摄像头后重试。";
  if (text.includes("NotReadable")) return "摄像头可能正在被其他软件占用，请关闭其他摄像头软件后重试。";
  if (state.cameraMode === "phone") return "电脑暂时没有识别到手机摄像头。请确认手机已选择 USB 摄像头模式，或尝试更换数据线。";
  return "没有检测到可用摄像头。请检查摄像头、高拍仪或手机是否已经连接。";
}

async function openCamera() {
  try {
    closeCamera(false);
    const selected = $("#cameraSelect").value;
    const constraints = { video: selected ? { deviceId: { exact: selected } } : true, audio: false };
    state.stream = await navigator.mediaDevices.getUserMedia(constraints);
    $("#cameraVideo").srcObject = state.stream;
    await refreshCameras();
    toast("摄像头已打开");
  } catch (error) {
    toast(cameraErrorMessage(error));
  }
}

function closeCamera(showToast = true) {
  if (state.stream) {
    state.stream.getTracks().forEach((track) => track.stop());
    state.stream = null;
  }
  $("#cameraVideo").srcObject = null;
  if (showToast) toast("摄像头已关闭");
}

async function switchCamera() {
  if (!state.devices.length) await refreshCameras();
  if (!state.devices.length) return toast("没有检测到可用摄像头。请检查摄像头、高拍仪或手机是否已经连接。");
  const select = $("#cameraSelect");
  const index = state.devices.findIndex((device) => device.deviceId === select.value);
  const next = state.devices[(index + 1) % state.devices.length];
  select.value = next.deviceId;
  await openCamera();
}

function capturePhoto() {
  const video = $("#cameraVideo");
  if (!state.stream || !video.videoWidth) return toast("拍摄失败，请重新打开摄像头后再试。");
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
  const device = state.devices.find((item) => item.deviceId === $("#cameraSelect").value) || {};
  state.capturedImages.push({
    id: Date.now().toString(36),
    sourceMode: state.cameraMode,
    deviceId: device.deviceId || "",
    deviceLabel: device.label || "摄像头",
    dataUrl,
    previewUrl: dataUrl,
    filename: `answer_sheet_${String(state.capturedImages.length + 1).padStart(3, "0")}.jpg`,
    capturedAt: new Date().toISOString(),
    status: "pending"
  });
  $("#shutterFlash").classList.remove("active");
  void $("#shutterFlash").offsetWidth;
  $("#shutterFlash").classList.add("active");
  renderCaptures();
  toast(`已拍摄 ${state.capturedImages.length} 张`);
}

function renderCaptures() {
  $("#captureCount").textContent = `已拍图片 ${state.capturedImages.length} 张`;
  $("#thumbList").innerHTML = state.capturedImages.map((image, index) => `
    <div class="thumb-item">
      <img src="${image.previewUrl}" alt="已拍图片 ${index + 1}">
      <div class="thumb-actions">
        <button type="button" data-view-capture="${index}">大图</button>
        <button type="button" data-delete-capture="${index}">删除</button>
      </div>
    </div>`).join("");
}

async function uploadCaptures() {
  if (!state.capturedImages.length) return toast("还没有拍摄图片。");
  try {
    const data = await api("/api/captures/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, images: state.capturedImages })
    });
    state.sessionId = data.session_id;
    toast(data.message || "拍照图片已保存");
  } catch (error) {
    toast(error.message);
  }
}

function renderValidation(data) {
  const errors = (data.validation_rows || []).filter((row) => row.severity === "error");
  const warnings = (data.validation_rows || []).filter((row) => row.severity === "warning");
  const unmatched = data.unmatched_students || [];
  const card = (title, chip, rows, headers) => `
    <article class="validation-card">
      <div class="section-title-row"><h2>${title}</h2>${chip}</div>
      ${rows.length ? table(headers, rows.slice(0, 8)) : `<div class="empty-state">暂无需要处理的内容</div>`}
    </article>`;
  $("#validationArea").innerHTML = [
    card("未匹配学生", `<span class="chip ${unmatched.length ? "warning" : "ok"}">${unmatched.length} 项</span>`, unmatched, [
      { key: "recognized_student_id", label: "识别学号" },
      { key: "suggested_name", label: "建议学生" },
      { key: "confidence", label: "置信度" },
      { key: "action", label: "处理状态" }
    ]),
    card("阻塞错误", `<span class="chip ${errors.length ? "error" : "ok"}">${errors.length} 项</span>`, errors, [
      { key: "scope", label: "范围" },
      { key: "item", label: "项目" },
      { key: "message", label: "说明" }
    ]),
    card("数据提醒", `<span class="chip ${warnings.length ? "warning" : "ok"}">${warnings.length} 项</span>`, warnings, [
      { key: "scope", label: "范围" },
      { key: "item", label: "项目" },
      { key: "message", label: "说明" }
    ])
  ].join("");
  $("#submissionPreview").innerHTML = data.preview_rows?.length
    ? table(Object.keys(data.preview_rows[0]).slice(0, 6).map((key) => ({ key, label: key })), data.preview_rows)
    : "暂无预览";
}

function renderGradeSummary() {
  const data = state.preview || {};
  $("#gradeSummary").innerHTML = `
    <div class="result-grid">
      <div class="metric-card"><span>题目数量</span><b>${data.question_count || "-"}</b></div>
      <div class="metric-card"><span>作答人数</span><b>${data.student_count || "-"}</b></div>
      <div class="metric-card"><span>数据状态</span><b>${data.blocking ? "需处理" : "可批改"}</b></div>
    </div>`;
}

async function gradeExam() {
  if (!state.sessionId) {
    toast("请先检查数据。");
    return;
  }
  $("#gradeButton").disabled = true;
  $("#loadingState").classList.remove("hidden");
  try {
    const response = await fetch("/api/exams/grade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, allow_errors: $("#allowErrors").checked })
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.message || "批改暂停");
    state.result = data;
    state.step = 5;
    renderStepper();
    renderResult(data);
    await loadHistory(true);
    toast("批改完成，可查看报告");
  } catch (error) {
    toast(error.message);
    $("#gradeButton").disabled = false;
  } finally {
    $("#loadingState").classList.add("hidden");
  }
}

function renderResult(data) {
  const stats = data.stats || {};
  $("#resultSummary").innerHTML = `
    <div class="metric-card"><span>平均分</span><b>${stats.average ?? "-"}</b></div>
    <div class="metric-card"><span>最高分</span><b>${stats.highest ?? "-"}</b></div>
    <div class="metric-card"><span>最低分</span><b>${stats.lowest ?? "-"}</b></div>
    <div class="metric-card"><span>及格率</span><b>${stats.pass_rate ?? 0}%</b></div>
    <div class="metric-card"><span>重点讲评题</span><b>${data.priority_counts?.["重点讲评"] || 0}</b></div>
    <div class="metric-card"><span>薄弱知识点</span><b>${data.weak_tag_count || 0}</b></div>
    <a class="report-card" target="_blank" href="${data.index_url || "#"}"><h2>查看完整报告</h2><p>打开本次批改的报告首页。</p></a>
    <a class="report-card" target="_blank" href="${data.teaching_url || "#"}"><h2>查看讲评建议</h2><p>先看哪些题重点讲、哪些题略讲。</p></a>
    <button class="report-card" data-view="home"><h2>返回首页</h2><p>回到工作台继续操作。</p></button>
  `;
}

function bindEvents() {
  document.body.addEventListener("click", (event) => {
    const viewButton = event.target.closest("[data-view]");
    if (viewButton) showView(viewButton.dataset.view);
    const classItem = event.target.closest(".class-item");
    if (classItem) loadClassDetail(classItem.dataset.class);
    const answerCard = event.target.closest("[data-answer-mode]");
    if (answerCard) setAnswerMode(answerCard.dataset.answerMode);
    const submissionCard = event.target.closest("[data-submission-mode]");
    if (submissionCard) setSubmissionMode(submissionCard.dataset.submissionMode);
    const cameraCard = event.target.closest("[data-camera-mode]");
    if (cameraCard) setCameraMode(cameraCard.dataset.cameraMode);
    const deleteAnswer = event.target.closest("[data-delete-answer]");
    if (deleteAnswer) deleteAnswerRow(Number(deleteAnswer.dataset.deleteAnswer));
    const deleteCapture = event.target.closest("[data-delete-capture]");
    if (deleteCapture) {
      state.capturedImages.splice(Number(deleteCapture.dataset.deleteCapture), 1);
      renderCaptures();
    }
    const viewCapture = event.target.closest("[data-view-capture]");
    if (viewCapture) window.open(state.capturedImages[Number(viewCapture.dataset.viewCapture)]?.previewUrl, "_blank");
  });
  $("#classImportForm").addEventListener("submit", importClass);
  $("#studentSearch").addEventListener("input", renderStudents);
  $("#refreshClasses").addEventListener("click", loadClasses);
  $("#refreshHistory").addEventListener("click", () => loadHistory());
  $("#refreshHomeHistory").addEventListener("click", () => loadHistory(true));
  $("#historySearch").addEventListener("input", renderHistory);
  $("#prevStep").addEventListener("click", prevStep);
  $("#nextStep").addEventListener("click", nextStep);
  $("#previewButton").addEventListener("click", previewExam);
  $("#gradeButton").addEventListener("click", gradeExam);
  $("#parseAnswerButton").addEventListener("click", parseAnswerDraft);
  $("#confirmAnswerButton").addEventListener("click", confirmAnswer);
  $("#addAnswerRow").addEventListener("click", addAnswerRow);
  $("#backToUploadMode").addEventListener("click", () => setSubmissionMode("file"));
  $("#openCamera").addEventListener("click", openCamera);
  $("#switchCamera").addEventListener("click", switchCamera);
  $("#capturePhoto").addEventListener("click", capturePhoto);
  $("#closeCamera").addEventListener("click", () => closeCamera(true));
  $("#uploadCaptures").addEventListener("click", uploadCaptures);
  window.addEventListener("beforeunload", () => closeCamera(false));
}

async function init() {
  bindEvents();
  renderStepper();
  setAnswerMode("table");
  setSubmissionMode("file");
  setCameraMode("webcam");
  await loadClasses();
  await loadHistory(true);
}

init().catch((error) => toast(error.message));
