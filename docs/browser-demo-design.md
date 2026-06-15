# Browser Demo Design

## Goal
Provide a simple HTML5 interface where a user grants camera permission, sees a live preview, captures a single frame on demand, sends that frame to the API, and reads the JSON result in the same browser window.

## Stage
Browser demo is a local UI shell. It is intentionally smaller than the eventual live webcam demo and does not continuously stream frames.

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
```

## UI Requirements
- API base URL input
- API key input
- start/stop camera buttons
- capture-frame button
- video preview
- captured-frame preview area
- overlay canvas
- show face boxes toggle
- top-k result display
- privacy notice
- error display

The current implementation keeps the API endpoint fixed to the local native endpoint. It does not provide live continuous capture, but it can draw boxes from the single-frame API response.

## Privacy Requirements
- Camera permission must be explicit.
- The frame is sent only when the user clicks Capture frame.
- Frames are not recorded by the browser UI.
- Backend must not store frames by default.
- API key is kept in the page only for the current session and is not persisted.
- Captured frames are not persisted in browser storage.

## Overlay Behavior
- Face boxes are drawn from `faces[].box` in the API response.
- Coordinates are scaled from the original image size to the displayed preview canvas.
- Zero-face results clear the overlay and keep the JSON result visible.
- Labels are optional and should not invent names.
- The overlay is redrawn when the toggle changes or a new frame is captured.

## Performance Requirements
- Do not loop frames continuously.
- Send one request per capture click.
- Show the most recent result or error clearly.

## Non-Goals
- React/Vue frontend in first demo
- account login
- video recording
- live continuous streaming
- browser-side recognition model
- browser-side face detection
