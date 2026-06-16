# v0.1.0-rc1 — Release Candidate 1

This is a release candidate, not a final release.

## Status

- Tag: `v0.1.0-rc1`
- Candidate type: internal / controlled-pilot release candidate
- GitHub Release: draft only; do not publish until the maintainer chooses to do so
- Current pilot status: partially ready for controlled pilot
- Dataset/legal review: still pending before broader, external, or commercial use

## Highlights

- CPU-only FastAPI face-similarity service with one-key auth.
- Native `/v1/face/similarity` API.
- Minimal OpenAI-compatible `/v1/models` and `/v1/chat/completions` support.
- Browser demo with one-frame capture, optional face-box overlay, and opt-in low-rate live polling.
- CPU-only Docker packaging with startup diagnostics, smoke tests, and benchmark tooling.

## Validated runtime path

- Ready-path Docker validation passed locally with mounted YuNet/SFace models and a small gallery.
- `/readyz` returned `200 ready` in the mounted-assets validation run.
- The validation run used a small local gallery with 10 attempted images, 10 successful embeddings, 0 skips, 2 identities, and 128-dimensional embeddings.

## API surface

- `GET /healthz`
- `GET /readyz`
- `GET /v1/models`
- `GET /v1/diagnostics/startup`
- `POST /v1/face/similarity`
- `POST /v1/chat/completions`

The public APIs return similarity results, not identity proof.

## Browser demo

- Local `/demo` page.
- One-frame capture by explicit user action.
- Optional face-box overlays.
- Explicit low-rate live polling from the browser.

## Docker

- CPU-only Docker image built successfully on a Docker-capable machine.
- The image runs as a non-root user on port 8000.
- Model and gallery artifacts are mounted at runtime.
- Model files, gallery artifacts, and reports are not baked into the image.

## Benchmarks

Local-machine-specific ready-path results from Work Order 24R:

| Endpoint | Requests | Warmup | Result mode | Mean ms | P95 ms | Errors |
|---|---:|---:|---|---:|---:|---:|
| native | 20 | 3 | similarity | 92.756 | 103.230 | 0 |
| chat | 20 | 3 | similarity | 94.117 | 102.506 | 0 |
| chat-stream | 20 | 3 | similarity | 104.155 | 109.597 | 0 |

The benchmark numbers are local-machine-specific and should not be generalized.

## Security and privacy

- Secrets are not persisted in browser storage.
- Uploaded images are not stored by default.
- User embeddings are not stored by default.
- Diagnostics are sanitized.
- Raw embeddings are not returned by public APIs.

## Dataset and legal status

- CelebA-derived gallery use remains a research/demo workflow.
- Legal/dataset review remains pending before broader, external, or commercial use.
- This is face similarity, not identity verification.
- This is not commercial-ready.

## Known limitations

- Full CelebA workflow is not bundled in the repository.
- Benchmark numbers are environment-specific.
- The browser demo is client-side polling, not server-side video streaming.
- The release candidate does not claim final release or verified identity recognition.

## Not included

- ONNX model files
- CelebA images
- sample images
- identity files
- gallery artifacts
- raw benchmark reports

## Before broader or external use

- Review dataset and licensing approvals.
- Review security and privacy signoff.
- Verify the intended runtime target.
- Keep the GitHub Release as a draft until the maintainer chooses to publish it.
- Do not treat this candidate as a final release.
