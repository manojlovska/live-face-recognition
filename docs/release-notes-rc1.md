# RC1 Release Notes Draft

## Candidate

v0.1.0-rc1

## Status

This is a release-candidate draft, not a final release.
Draft for controlled-pilot review only. This is not a final release note and does not claim commercial readiness.
Status: partially ready for controlled pilot.
Ready-path validation passed locally with Docker, mounted YuNet/SFace models, and a small local gallery.
Benchmark numbers are local-machine-specific and the ready-path run used a small local gallery.
Legal/dataset review remains pending before any broader or external use.
The GitHub Release remains a draft in docs and has not been published.

## Ready-path validation summary

- Docker build passed on a Docker-capable machine.
- No-assets container smoke passed with the expected `not_ready` baseline.
- Mounted-assets container smoke passed with `/readyz` returning `200 ready`.
- Native, chat, and chat-stream ready-path benchmarks were measured locally.
- The measured ready-path numbers are specific to the local validation machine and gallery set.

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
  - The current recorded benchmarks include both a local not-ready baseline and a ready-path validation run.
  - The ready-path results are local-machine-specific and not a general performance guarantee.

## Known limitations

- This is a controlled-pilot research service, not a final commercial release.
- The full CelebA workflow is not bundled in the repository.
- Benchmark numbers are environment-specific and must be measured.
- The browser demo is client-side polling, not server-side video streaming.
- Dataset/legal approval is still required before any broader use.
- Model files, sample images, gallery artifacts, raw benchmark reports, API keys, and `.env` are not committed.

## Not included

- Verified identity recognition.
- Commercial readiness claims.
- Cloud deployment manifests.
- Server-side video streaming.
- WebSockets for the browser demo.
- ONNX model files are not bundled.
- CelebA data is not bundled.
- This release remains a face-similarity service, not identity verification.

## Required manual verification before tagging

- Verify model assets and gallery artifacts on the target machine if the release target differs from the validated local runtime.
- Verify `/healthz`, `/readyz`, `/v1/models`, `/v1/face/similarity`, `/v1/chat/completions`, and `/v1/diagnostics/startup`.
- Verify the browser demo in the intended browser environment.
- Verify the Docker image build on a Docker-capable machine.
- Verify smoke tests and benchmark results against the intended runtime.
- Verify dataset and licensing review before any external or commercial use.
- Verify the release checklist and human approval notes before creating the tag.
- Verify the GitHub Release draft text before any publication decision.
