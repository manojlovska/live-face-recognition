# RC1 Release Notes Draft

## Status

Draft for controlled-pilot review only. This is not a final release note and does not claim commercial readiness.
This worktree has a measured local smoke/benchmark baseline, but full RC validation is still blocked here because Docker and the real model/gallery assets were unavailable.

## What is included

- CPU-only FastAPI service for face similarity.
- One-key Bearer authentication.
- Native `/v1/face/similarity` endpoint.
- OpenAI-compatible `/v1/models` and `/v1/chat/completions` endpoints.
- Image validation, readiness, and startup diagnostics.
- Browser demo with one-frame capture, face-box overlay, and opt-in low-rate live polling.
- Smoke-test and benchmark tooling.
- CPU-only Docker packaging.

## API surface

- Native similarity API for direct image requests.
- Minimal OpenAI-compatible chat-completions adapter for image similarity.
- Protected startup diagnostics endpoint.

## Browser demo

- Local demo at `/demo`.
- One-frame capture by user action.
- Optional face-box overlay from API response.
- Explicit low-rate live polling from the browser.

## Gallery builder

- Local sample-gallery builder.
- CelebA-style local layout support.
- Gallery artifacts remain operator-supplied and local.

## Deployment

- Local Python run supported.
- CPU-only Docker image supported.
- Model and gallery artifacts are mounted at runtime.
- `/healthz` is the healthcheck target.

## Security and privacy posture

- Uploaded images are not stored by default.
- User embeddings are not stored by default.
- API keys are not persisted in browser storage.
- Diagnostics are sanitized.
- Raw embeddings are not returned by public APIs.

## Testing and release checks

- `ruff check .`
- `ruff format --check .`
- `pytest -W error`
- Smoke tests against the intended runtime
- Docker build verification on a Docker-capable machine
- Benchmarks measured and recorded in [benchmark-results.md](benchmark-results.md)
  - The current recorded benchmark is a local not-ready baseline, not a pilot benchmark.

## Known limitations

- This is a controlled-pilot research service, not a final commercial release.
- The full CelebA workflow is not bundled in the repository.
- Benchmark numbers are environment-specific and must be measured.
- The browser demo is client-side polling, not server-side video streaming.

## Not included

- Verified identity recognition.
- Commercial readiness claims.
- Cloud deployment manifests.
- Server-side video streaming.
- WebSockets for the browser demo.
- ONNX model files are not bundled.
- CelebA data is not bundled.

## Required manual verification before tagging

- Verify model assets and gallery artifacts on the target machine.
- Verify `/healthz`, `/readyz`, `/v1/models`, `/v1/face/similarity`, `/v1/chat/completions`, and `/v1/diagnostics/startup`.
- Verify the browser demo in the intended browser environment.
- Verify the Docker image build on a Docker-capable machine.
- Verify smoke tests and benchmark results against the intended runtime.
- Verify dataset and licensing review before any external or commercial use.
