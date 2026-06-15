const elements = {
  apiKey: document.getElementById("api-key"),
  topK: document.getElementById("top-k"),
  showFaceBoxes: document.getElementById("show-face-boxes"),
  startCamera: document.getElementById("start-camera"),
  captureFrame: document.getElementById("capture-frame"),
  stopCamera: document.getElementById("stop-camera"),
  video: document.getElementById("video"),
  frameCanvas: document.getElementById("frame-canvas"),
  overlayCanvas: document.getElementById("overlay-canvas"),
  status: document.getElementById("status"),
  httpStatus: document.getElementById("http-status"),
  result: document.getElementById("result"),
  error: document.getElementById("error"),
};

const context = {
  frame: elements.frameCanvas.getContext("2d"),
  overlay: elements.overlayCanvas.getContext("2d"),
};

let mediaStream = null;
let lastSuccessfulResponse = null;
let lastCapture = null;

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

function clearOverlay() {
  if (!context.overlay) {
    return;
  }
  context.overlay.clearRect(0, 0, elements.overlayCanvas.width, elements.overlayCanvas.height);
}

function setOverlayVisibility() {
  elements.overlayCanvas.hidden = !elements.showFaceBoxes.checked;
  if (!elements.showFaceBoxes.checked) {
    clearOverlay();
    return;
  }
  redrawOverlay();
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

function captureFrameToDataUrl() {
  const width = elements.video.videoWidth || 640;
  const height = elements.video.videoHeight || 480;
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  const drawingContext = canvas.getContext("2d");
  if (!drawingContext) {
    throw new Error("Canvas is not available.");
  }
  drawingContext.drawImage(elements.video, 0, 0, width, height);
  return canvas.toDataURL("image/jpeg", 0.9);
}

function normalizeTopK(value) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) {
    return 5;
  }
  return Math.min(20, Math.max(1, parsed));
}

function loadImage(dataUrl) {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Unable to decode the captured frame."));
    image.src = dataUrl;
  });
}

async function renderCapturedFrame(dataUrl) {
  const image = await loadImage(dataUrl);
  const width = image.naturalWidth || image.width || 0;
  const height = image.naturalHeight || image.height || 0;
  if (!width || !height) {
    throw new Error("Captured frame has no dimensions.");
  }

  elements.frameCanvas.width = width;
  elements.frameCanvas.height = height;
  elements.overlayCanvas.width = width;
  elements.overlayCanvas.height = height;

  if (!context.frame) {
    throw new Error("Canvas is not available.");
  }

  context.frame.clearRect(0, 0, width, height);
  context.frame.drawImage(image, 0, 0, width, height);
  clearOverlay();

  return { width, height };
}

function formatSimilarity(value) {
  return Number.isFinite(value) ? value.toFixed(3) : "";
}

function buildBoxLabel(face, index) {
  const parts = [`Face ${index + 1}`];
  const matches = Array.isArray(face.top_matches) ? face.top_matches : [];
  const topMatch = matches[0];
  if (topMatch && typeof topMatch === "object") {
    const rank = Number.isFinite(topMatch.rank) ? topMatch.rank : index + 1;
    const identityId =
      typeof topMatch.celeba_identity_id === "string" && topMatch.celeba_identity_id
        ? topMatch.celeba_identity_id
        : null;
    const displayName =
      typeof topMatch.display_name === "string" && topMatch.display_name
        ? topMatch.display_name
        : null;
    const similarity = formatSimilarity(topMatch.similarity);

    parts.push(`rank ${rank}`);
    if (identityId) {
      parts.push(identityId);
    }
    if (displayName) {
      parts.push(displayName);
    }
    if (similarity) {
      parts.push(similarity);
    }
  }
  return parts.join(" · ");
}

function drawFaceBoxes(response) {
  if (!elements.showFaceBoxes.checked) {
    clearOverlay();
    return;
  }

  if (!context.overlay || !lastCapture || !response) {
    clearOverlay();
    return;
  }

  const faces = Array.isArray(response.faces) ? response.faces : [];
  clearOverlay();

  if (!faces.length) {
    return;
  }

  const scaleX = elements.overlayCanvas.width / lastCapture.width;
  const scaleY = elements.overlayCanvas.height / lastCapture.height;
  const lineWidth = Math.max(2, Math.round(Math.min(scaleX, scaleY) * 3));
  context.overlay.lineWidth = lineWidth;
  context.overlay.font = "600 14px Inter, system-ui, sans-serif";
  context.overlay.textBaseline = "top";

  faces.forEach((face, index) => {
    if (!face || !Array.isArray(face.box) || face.box.length < 4) {
      return;
    }

    const [x, y, width, height] = face.box.map((value) => Number(value));
    if ([x, y, width, height].some((value) => Number.isNaN(value))) {
      return;
    }

    const scaledX = x * scaleX;
    const scaledY = y * scaleY;
    const scaledWidth = width * scaleX;
    const scaledHeight = height * scaleY;
    const label = buildBoxLabel(face, index);

    context.overlay.strokeStyle = "#7c2d12";
    context.overlay.fillStyle = "rgba(124, 45, 18, 0.18)";
    context.overlay.fillRect(scaledX, scaledY, scaledWidth, scaledHeight);
    context.overlay.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

    context.overlay.fillStyle = "rgba(24, 18, 15, 0.82)";
    const textWidth = context.overlay.measureText(label).width;
    const labelHeight = 22;
    const labelX = scaledX;
    const labelY = Math.max(0, scaledY - labelHeight - 4);
    context.overlay.fillRect(labelX, labelY, textWidth + 12, labelHeight);
    context.overlay.fillStyle = "#f7efe8";
    context.overlay.fillText(label, labelX + 6, labelY + 4);
  });
}

function redrawOverlay() {
  drawFaceBoxes(lastSuccessfulResponse);
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
    lastCapture = null;
    lastSuccessfulResponse = null;
    const framePreview = await renderCapturedFrame(payload.image);
    lastCapture = { ...framePreview, imageDataUrl: payload.image };

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
      clearOverlay();
      setStatus("Request failed.");
      return;
    }

    lastSuccessfulResponse = responseJson;
    renderJson(elements.result, responseJson);
    elements.error.textContent = "{}";
    drawFaceBoxes(responseJson);
    setStatus("Frame processed successfully.");
  } catch (error) {
    clearOverlay();
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
elements.showFaceBoxes.addEventListener("change", setOverlayVisibility);
window.addEventListener("beforeunload", stopCamera);

setOverlayVisibility();
