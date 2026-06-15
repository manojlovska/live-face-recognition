# Browser Demo Design

## Goal
Provide a simple HTML5 interface where a user grants camera permission, sees a live preview, captures a single frame on demand, sends that frame to the API, and reads the JSON result in the same browser window.

## Stage
Browser demo is a local UI shell. It is intentionally smaller than the eventual live webcam demo and does not continuously stream frames.

## Architecture

```text
Browser camera
  -> <video> preview
  -> <canvas> capture on button click
  -> compressed JPEG frame
  -> POST /v1/face/similarity
  -> result JSON
  -> JSON result display
```

## UI Requirements
- API base URL input
- API key input
- start/stop camera buttons
- capture-frame button
- video preview
- top-k result display
- privacy notice
- error display

The current implementation keeps the API endpoint fixed to the local native endpoint and does not provide a live overlay yet.

## Privacy Requirements
- Camera permission must be explicit.
- The frame is sent only when the user clicks Capture frame.
- Frames are not recorded by the browser UI.
- Backend must not store frames by default.

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
