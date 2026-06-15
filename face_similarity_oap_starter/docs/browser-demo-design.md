# Browser Demo Design

## Goal
Provide a simple HTML5 interface where a user grants camera permission, sees a live preview, sends throttled frames to the API, and sees face boxes and similarity results drawn in the same browser window.

## Stage
Browser demo is not part of MVP. Target for v0.5 / RC1.

## Architecture

```text
Browser camera
  -> <video> preview
  -> <canvas> capture every 200-500 ms
  -> compressed JPEG/WebP frame
  -> POST /v1/face/similarity
  -> result JSON
  -> overlay canvas draws boxes and labels
```

## UI Requirements
- API base URL input
- API key input
- start/stop camera buttons
- video preview
- overlay canvas
- frame rate/throttle setting
- top-k result display
- privacy notice
- error display

## Privacy Requirements
- Camera permission must be explicit.
- Frames are sent to the configured backend.
- Frames are not recorded by the browser UI.
- Backend must not store frames by default.

## Performance Requirements
- Do not send 30 FPS by default.
- Resize frames before sending.
- Avoid overlapping requests by default.
- Show last successful result while next request is pending.

## Non-Goals
- React/Vue frontend in first demo
- account login
- video recording
- WebRTC streaming
- browser-side recognition model
