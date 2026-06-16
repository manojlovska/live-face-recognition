const elements = {
  apiKey: document.getElementById("api-key"),
  topK: document.getElementById("top-k"),
  pollingInterval: document.getElementById("polling-interval"),
  showFaceBoxes: document.getElementById("show-face-boxes"),
  startCamera: document.getElementById("start-camera"),
  captureFrame: document.getElementById("capture-frame"),
  stopCamera: document.getElementById("stop-camera"),
  startLivePolling: document.getElementById("start-live-polling"),
  stopLivePolling: document.getElementById("stop-live-polling"),
  video: document.getElementById("video"),
  frameCanvas: document.getElementById("frame-canvas"),
  overlayCanvas: document.getElementById("overlay-canvas"),
  status: document.getElementById("status"),
  httpStatus: document.getElementById("http-status"),
  liveStatus: document.getElementById("live-status"),
  lastSuccess: document.getElementById("last-success"),
  lastError: document.getElementById("last-error"),
  framesSent: document.getElementById("frames-sent"),
  successfulResponses: document.getElementById("successful-responses"),
  failedResponses: document.getElementById("failed-responses"),
  lastLatency: document.getElementById("last-latency"),
  result: document.getElementById("result"),
  error: document.getElementById("error"),
};

const context = {
  frame: elements.frameCanvas.getContext("2d"),
  overlay: elements.overlayCanvas.getContext("2d"),
};

const MIN_POLLING_INTERVAL_MS = 500;
const DEFAULT_POLLING_INTERVAL_MS = 1500;

let mediaStream = null;
let lastSuccessfulResponse = null;
let lastOverlayResponse = null;
let lastCapture = null;

const livePolling = {
  active: false,
  timerId: null,
  abortController: null,
  requestInFlight: false,
  requestKind: null,
  intervalMs: DEFAULT_POLLING_INTERVAL_MS,
};

const stats = {
  framesSent: 0,
  successfulResponses: 0,
  failedResponses: 0,
  lastLatencyMs: null,
};

function setStatus(message) {
  elements.status.textContent = message;
}

function setHttpStatus(message) {
  elements.httpStatus.textContent = message;
}

function renderJson(target, value) {
  target.textContent = JSON.stringify(value, null, 2);
}

function setBrowserError(message, code = null) {
  const error = {
    message,
  };

  if (code) {
    error.code = code;
  }

  renderJson(elements.error, {
    error,
  });
}

function clearBrowserError() {
  renderJson(elements.error, {});
}

function updateCounters() {
  elements.framesSent.textContent = String(stats.framesSent);
  elements.successfulResponses.textContent = String(stats.successfulResponses);
  elements.failedResponses.textContent = String(stats.failedResponses);
  elements.lastLatency.textContent = Number.isFinite(stats.lastLatencyMs)
    ? `${Math.round(stats.lastLatencyMs)} ms`
    : "—";
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
  drawFaceBoxes(lastOverlayResponse);
}

function getPollingIntervalMs() {
  const parsed = Number.parseInt(elements.pollingInterval.value, 10);
  if (Number.isNaN(parsed)) {
    return DEFAULT_POLLING_INTERVAL_MS;
  }

  return Math.max(MIN_POLLING_INTERVAL_MS, parsed);
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

function syncLiveControls() {
  elements.startLivePolling.disabled = !mediaStream || livePolling.active;
  elements.stopLivePolling.disabled = !livePolling.active;
  if (!livePolling.active) {
    elements.liveStatus.textContent = "Live polling is stopped.";
    return;
  }

  elements.liveStatus.textContent = livePolling.requestInFlight
    ? "Live polling is running. Request in flight."
    : "Live polling is running.";
}

function scheduleNextLiveTick(delayMs) {
  if (!livePolling.active) {
    return;
  }

  const nextDelay = Number.isFinite(delayMs) ? Math.max(0, delayMs) : livePolling.intervalMs;
  if (livePolling.timerId !== null) {
    window.clearTimeout(livePolling.timerId);
  }

  livePolling.timerId = window.setTimeout(() => {
    void runLivePollingTick();
  }, nextDelay);
}

function stopLivePolling(reason) {
  if (livePolling.timerId !== null) {
    window.clearTimeout(livePolling.timerId);
    livePolling.timerId = null;
  }

  if (livePolling.requestKind === "live" && livePolling.abortController) {
    livePolling.abortController.abort();
  }

  livePolling.active = false;
  livePolling.intervalMs = getPollingIntervalMs();
  setStatus(reason || "Live polling is stopped.");
  syncLiveControls();
}

function startLivePolling() {
  clearBrowserError();

  if (!mediaStream) {
    setStatus("Start the camera before live polling.");
    setBrowserError("Start the camera before live polling.", "camera_not_running");
    return;
  }

  if (livePolling.active) {
    setStatus("Live polling is already running.");
    return;
  }

  livePolling.active = true;
  livePolling.intervalMs = getPollingIntervalMs();
  elements.pollingInterval.value = String(livePolling.intervalMs);
  setStatus(`Live polling is running every ${livePolling.intervalMs} ms.`);
  syncLiveControls();
  scheduleNextLiveTick(0);
}

function stopCamera() {
  stopLivePolling("Live polling stopped because the camera stopped.");

  if (mediaStream) {
    for (const track of mediaStream.getTracks()) {
      track.stop();
    }
  }

  mediaStream = null;
  elements.video.srcObject = null;
  elements.captureFrame.disabled = true;
  setStatus("Camera is stopped.");
  syncLiveControls();
}

async function startCamera() {
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
    syncLiveControls();
  } catch (error) {
    setStatus(`Camera error: ${error?.message || "Unable to start camera."}`);
  }
}

function createSimilarityPayload(imageDataUrl) {
  return {
    image: imageDataUrl,
    top_k: normalizeTopK(elements.topK.value),
    return_face_boxes: true,
  };
}

async function captureCurrentFrame() {
  const imageDataUrl = captureFrameToDataUrl();
  const framePreview = await renderCapturedFrame(imageDataUrl);
  lastCapture = framePreview;
  lastOverlayResponse = null;
  return createSimilarityPayload(imageDataUrl);
}

async function submitSimilarityRequest(payload, source) {
  if (livePolling.requestInFlight) {
    if (source === "manual") {
      setStatus("A request is already in flight.");
      setBrowserError("A request is already in flight.", "request_in_flight");
    }
    return false;
  }

  livePolling.requestInFlight = true;
  livePolling.requestKind = source;
  livePolling.abortController = source === "live" ? new AbortController() : null;
  stats.framesSent += 1;
  updateCounters();
  setHttpStatus("");
  syncLiveControls();

  if (source === "live") {
    setStatus("Live polling is running. Request in flight.");
  } else {
    setStatus("Sending one captured frame to the API...");
  }

  const startedAt = performance.now();

  try {
    const response = await fetch("/v1/face/similarity", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${elements.apiKey.value.trim()}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: livePolling.abortController?.signal,
    });

    const elapsedMs = Math.round(performance.now() - startedAt);
    stats.lastLatencyMs = elapsedMs;
    updateCounters();

    let responseJson;
    try {
      responseJson = await response.json();
    } catch (_jsonError) {
      responseJson = {
        error: {
          message: "Unable to parse the API response.",
        },
      };
    }

    setHttpStatus(`HTTP ${response.status}`);

    if (!response.ok) {
      stats.failedResponses += 1;
      updateCounters();
      renderJson(elements.error, responseJson);

      const errorCode =
        responseJson && responseJson.error && typeof responseJson.error.code === "string"
          ? responseJson.error.code
          : null;

      if (response.status === 401 || errorCode === "invalid_api_key") {
        setLastError(`Last error: authentication failed in ${elapsedMs} ms.`);
        stopLivePolling("Live polling stopped.");
        setStatus("Authentication failed. Live polling stopped.");
        return false;
      }

      setLastError(
        `Last error: HTTP ${response.status}${errorCode ? ` ${errorCode}` : ""} in ${elapsedMs} ms.`,
      );
      setStatus(source === "live" ? "Live polling is running." : "Request failed.");
      return false;
    }

    lastSuccessfulResponse = responseJson;
    lastOverlayResponse = responseJson;
    stats.successfulResponses += 1;
    updateCounters();
    renderJson(elements.result, responseJson);
    clearBrowserError();
    setLastSuccess(`Last success: HTTP ${response.status} in ${elapsedMs} ms.`);
    drawFaceBoxes(responseJson);
    setStatus(source === "live" ? "Live polling is running." : "Frame processed successfully.");
    return true;
  } catch (error) {
    if (error?.name === "AbortError" && source === "live") {
      setHttpStatus("Request aborted.");
      return false;
    }

    stats.failedResponses += 1;
    updateCounters();
    setHttpStatus("No HTTP response");
    renderJson(elements.error, {
      error: {
        message: error?.message || "Unexpected browser error.",
      },
    });
    setLastError(`Last error: ${error?.message || "Unexpected browser error."}`);
    setStatus(source === "live" ? "Live polling is running." : "Request failed before a response arrived.");
    return false;
  } finally {
    livePolling.requestInFlight = false;
    livePolling.requestKind = null;
    syncLiveControls();
    if (source === "live") {
      livePolling.abortController = null;
      if (livePolling.active && !document.hidden && mediaStream) {
        const elapsedMs = performance.now() - startedAt;
        livePolling.intervalMs = getPollingIntervalMs();
        scheduleNextLiveTick(Math.max(0, livePolling.intervalMs - elapsedMs));
      }
    }
  }
}

async function captureFrame() {
  clearBrowserError();

  if (!mediaStream) {
    setStatus("Start the camera before capturing a frame.");
    setBrowserError("Start the camera before capturing a frame.", "camera_not_running");
    return;
  }

  const apiKey = elements.apiKey.value.trim();
  if (!apiKey) {
    setStatus("Enter the API key first.");
    setBrowserError("Enter the API key first.", "missing_api_key");
    return;
  }

  if (livePolling.requestInFlight) {
    setStatus("A request is already in flight.");
    setBrowserError("A request is already in flight.", "request_in_flight");
    return;
  }

  try {
    const payload = await captureCurrentFrame();
    setStatus("Sending one captured frame to the API...");
    await submitSimilarityRequest(payload, "manual");
  } catch (error) {
    setStatus("Request failed before a response arrived.");
    setBrowserError(error?.message || "Unexpected browser error.", "capture_failed");
  }
}

async function runLivePollingTick() {
  if (!livePolling.active) {
    return;
  }

  if (!mediaStream) {
    stopLivePolling("Live polling stopped because the camera stopped.");
    return;
  }

  if (document.hidden) {
    stopLivePolling("Live polling stopped because the tab was hidden.");
    return;
  }

  if (livePolling.requestInFlight) {
    scheduleNextLiveTick(livePolling.intervalMs);
    return;
  }

  const apiKey = elements.apiKey.value.trim();
  if (!apiKey) {
    setStatus("Enter the API key first.");
    setBrowserError("Enter the API key first.", "missing_api_key");
    stopLivePolling("Live polling stopped.");
    return;
  }

  try {
    const payload = await captureCurrentFrame();
    setStatus("Live polling is running. Request in flight.");
    await submitSimilarityRequest(payload, "live");
  } catch (error) {
    setStatus("Live polling is running.");
    setBrowserError(error?.message || "Unexpected browser error.", "capture_failed");
    stats.failedResponses += 1;
    updateCounters();
    setHttpStatus("No HTTP response");
    if (livePolling.active && !document.hidden) {
      scheduleNextLiveTick(livePolling.intervalMs);
    }
  }
}

function setLastSuccess(message) {
  elements.lastSuccess.textContent = message;
}

function setLastError(message) {
  elements.lastError.textContent = message;
}

function handleVisibilityChange() {
  if (document.hidden && livePolling.active) {
    stopLivePolling("Live polling stopped because the tab was hidden.");
  }
}

function handleBeforeUnload() {
  stopLivePolling("Live polling stopped.");
  if (mediaStream) {
    for (const track of mediaStream.getTracks()) {
      track.stop();
    }
  }
}

elements.startCamera.addEventListener("click", startCamera);
elements.captureFrame.addEventListener("click", captureFrame);
elements.stopCamera.addEventListener("click", stopCamera);
elements.startLivePolling.addEventListener("click", startLivePolling);
elements.stopLivePolling.addEventListener("click", () => {
  stopLivePolling("Live polling stopped.");
});
elements.showFaceBoxes.addEventListener("change", setOverlayVisibility);
elements.pollingInterval.addEventListener("change", () => {
  livePolling.intervalMs = getPollingIntervalMs();
  elements.pollingInterval.value = String(livePolling.intervalMs);
  if (livePolling.active) {
    setStatus(`Live polling is running every ${livePolling.intervalMs} ms.`);
  }
});
document.addEventListener("visibilitychange", handleVisibilityChange);
window.addEventListener("beforeunload", handleBeforeUnload);

renderJson(elements.result, {});
renderJson(elements.error, {});
updateCounters();
syncLiveControls();
setOverlayVisibility();
