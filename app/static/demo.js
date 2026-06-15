const elements = {
  apiKey: document.getElementById("api-key"),
  topK: document.getElementById("top-k"),
  startCamera: document.getElementById("start-camera"),
  captureFrame: document.getElementById("capture-frame"),
  stopCamera: document.getElementById("stop-camera"),
  video: document.getElementById("video"),
  status: document.getElementById("status"),
  httpStatus: document.getElementById("http-status"),
  result: document.getElementById("result"),
  error: document.getElementById("error"),
};

let mediaStream = null;

function setStatus(message) {
  elements.status.textContent = message;
}

function setHttpStatus(message) {
  elements.httpStatus.textContent = message;
}

function renderJson(target, value) {
  target.textContent = JSON.stringify(value, null, 2);
}

function clearOutput() {
  renderJson(elements.result, {});
  renderJson(elements.error, {});
  setHttpStatus("");
}

async function startCamera() {
  clearOutput();

  if (!navigator.mediaDevices?.getUserMedia) {
    setStatus("Camera access is not supported in this browser.");
    return;
  }

  if (mediaStream) {
    setStatus("Camera is already running.");
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });
    elements.video.srcObject = mediaStream;
    await elements.video.play();
    elements.captureFrame.disabled = false;
    setStatus("Camera is running.");
  } catch (error) {
    setStatus(`Camera error: ${error?.message || "Unable to start camera."}`);
  }
}

function stopCamera() {
  if (mediaStream) {
    for (const track of mediaStream.getTracks()) {
      track.stop();
    }
  }
  mediaStream = null;
  elements.video.srcObject = null;
  elements.captureFrame.disabled = true;
  setStatus("Camera is stopped.");
}

function captureFrameToDataUrl() {
  const width = elements.video.videoWidth || 640;
  const height = elements.video.videoHeight || 480;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d");
  if (!context) {
    throw new Error("Canvas is not available.");
  }
  context.drawImage(elements.video, 0, 0, width, height);
  return canvas.toDataURL("image/jpeg", 0.9);
}

function normalizeTopK(value) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    return 5;
  }
  return Math.min(20, Math.max(1, parsed));
}

async function captureFrame() {
  clearOutput();

  if (!mediaStream) {
    setStatus("Start the camera before capturing a frame.");
    return;
  }

  const apiKey = elements.apiKey.value.trim();
  if (!apiKey) {
    setStatus("Enter the API key first.");
    return;
  }

  const payload = {
    image: captureFrameToDataUrl(),
    top_k: normalizeTopK(elements.topK.value),
    return_face_boxes: true,
  };

  try {
    setStatus("Sending one captured frame to the API...");
    const response = await fetch("/v1/face/similarity", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const responseJson = await response.json();
    setHttpStatus(`HTTP ${response.status}`);

    if (!response.ok) {
      renderJson(elements.error, responseJson);
      setStatus("Request failed.");
      return;
    }

    renderJson(elements.result, responseJson);
    elements.error.textContent = "{}";
    setStatus("Frame processed successfully.");
  } catch (error) {
    setStatus("Request failed before a response arrived.");
    renderJson(elements.error, {
      error: {
        message: error?.message || "Unexpected browser error.",
      },
    });
  }
}

elements.startCamera.addEventListener("click", startCamera);
elements.captureFrame.addEventListener("click", captureFrame);
elements.stopCamera.addEventListener("click", stopCamera);
window.addEventListener("beforeunload", stopCamera);
