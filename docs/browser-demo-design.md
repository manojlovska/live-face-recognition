# Browser Demo Design

## Goal
Provide a simple HTML5 interface where a user grants camera permission, sees a live preview, captures a single frame on demand, optionally enables low-rate live polling, sends those frames to the API, and reads the JSON result in the same browser window.

## Stage
Browser demo is a local UI shell. It is intentionally smaller than a full live webcam product and uses client-side polling rather than server-side video streaming.

## Architecture

```text
Browser camera
  -> <video> preview
  -> hidden capture canvas
  -> compressed JPEG frame
  -> POST /v1/face/similarity
  -> result JSON
  -> JSON result display
  -> overlay canvas draws face boxes
  -> optional low-rate live polling loop
```

## UI Requirements
- API base URL input
- API key input
- start/stop camera buttons
- capture-frame button
- start/stop live polling buttons
- polling interval input with a 500 ms minimum enforced client-side
- video preview
- captured-frame preview area
- overlay canvas
- show face boxes toggle
- live status and last-success/last-error indicators
- simple request counters and latency display
- top-k result display
- privacy notice
- error display

The current implementation keeps the API endpoint fixed to the local native endpoint. It can draw boxes from single-frame responses and from live-polling responses, but it does not provide live continuous capture.

## Privacy Requirements
- Camera permission must be explicit.
- The frame is sent only when the user clicks Capture frame or when explicit live polling is enabled.
- Frames are not recorded by the browser UI.
- Backend must not store frames by default.
- API key is kept in the page only for the current session and is not persisted.
- Captured frames are not persisted in browser storage.
- Live polling is opt-in, single-flight, and client-side only.
- Live polling uses the same-origin `/v1/face/similarity` endpoint only.
- The demo does not load third-party scripts or send data to third-party origins.

## Overlay Behavior
- Face boxes are drawn from `faces[].box` in the API response.
- Coordinates are scaled from the original image size to the displayed preview canvas.
- Zero-face results clear the overlay and keep the JSON result visible.
- Labels are optional and should not invent names.
- The overlay is redrawn when the toggle changes or a new frame is captured.
- Live polling reuses the same render path as one-frame capture so the overlay and JSON result stay in sync with the most recent successful response.

## Performance Requirements
- Do not start live polling automatically on page load.
- Send one request per polling tick.
- Never overlap requests; use a single-flight loop with `setTimeout` rather than `setInterval`.
- Stop polling immediately when the user clicks Stop live polling.
- Stopping the camera also stops live polling.
- When the tab becomes hidden, stop live polling until the user restarts it.
- Show the most recent result or error clearly.

## Non-Goals
- React/Vue frontend in first demo
- account login
- video recording
- live continuous streaming
- WebSockets
- SSE in the browser demo
- server-side video streaming
- browser-side recognition model
- browser-side face detection
