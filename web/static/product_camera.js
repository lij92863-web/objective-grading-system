async function startProductCamera() {
  const status = document.querySelector("#camera-status");
  try {
    const stream = await navigator.mediaDevices.getUserMedia({video: true, audio: false});
    document.querySelector("#camera-video").srcObject = stream;
    status.textContent = "摄像头已连接。";
  } catch (error) {
    status.textContent = "浏览器未发现或未获准使用摄像头，可改用图片上传。";
  }
}
async function captureProductPhoto(sessionId) {
  const video = document.querySelector("#camera-video");
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  canvas.toBlob(async (blob) => {
    const form = new FormData(); form.append("image", blob, "browser-camera.jpg");
    const response = await fetch(`/sessions/${sessionId}/capture/browser-camera`, {method: "POST", body: form});
    if (response.redirected) location.href = response.url; else location.reload();
  }, "image/jpeg", 0.92);
}
