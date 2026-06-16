# Pilot Readiness Checklist

This checklist is for a controlled pilot of the CPU-only face-similarity service. It is not a declaration of final release, commercial readiness, or identity verification.

Status legend:
- `[ ]` not done
- `[x]` done
- `[~]` partially done
- `[!]` blocked

## Code and tests

- [x] `python3.12 -m ruff check .` passes.
- [x] `python3.12 -m ruff format --check .` passes.
- [x] `python3.12 -m pytest -W error` passes.
- [x] Relevant regression tests for auth, readiness, gallery loading, chat compatibility, browser demo, smoke checks, and startup diagnostics pass.

## Dependency and packaging checks

- [x] Runtime dependencies remain CPU-only and bounded in `pyproject.toml`.
- [x] Test dependencies remain separated from local-script dependencies.
- [x] No GPU, database, Redis, Celery, or frontend build dependencies are present.
- [x] [testing-strategy.md](testing-strategy.md) reflects the current warning policy.
- [~] [release-readiness.md](release-readiness.md) reflects the current release gate status.

## Docker checks

- [x] `docker build -t live-face-recognition:local .` passes on a Docker-capable machine.
- [x] The container runs as a non-root user.
- [x] The container exposes port 8000.
- [x] `models/`, `data/gallery/`, `reports/`, and `.env` are not baked into the image.
- [x] Model and gallery artifacts are mounted read-only for serving.

## Configuration checks

- [x] `APP_ENV` is set intentionally.
- [x] `STRICT_STARTUP_VALIDATION` matches the deployment mode.
- [x] `STARTUP_VALIDATE_ASSETS` matches the deployment mode.
- [x] `DEBUG_IMAGE_RETENTION` is disabled unless explicitly required for a private debug workflow.
- [~] `FACE_API_KEY` is not the default local placeholder in any pilot environment.
- [x] [deployment.md](deployment.md) matches the intended runtime configuration.

## Model asset checks

Required before any pilot that expects live similarity:

- [x] YuNet model file is present.
- [x] SFace model file is present.
- [x] Model manifest is present and consistent.
- [x] `GET /readyz` reports the expected model status.
- [x] `GET /v1/diagnostics/startup` reports no unsafe configuration errors.

## Gallery artifact checks

Required before any pilot that expects similarity results from a gallery:

- [x] Gallery embeddings file is present.
- [x] Gallery metadata file is present.
- [x] Gallery manifest is present.
- [x] Gallery embedding dimension matches the model output dimension.
- [x] Gallery scope and filters are documented.
- [x] Local gallery artifacts are user-supplied and not bundled into the repo.

## API checks

Required before any pilot:

- [x] `/healthz` returns 200.
- [x] `/readyz` returns 200 when the runtime is expected to serve similarity results.
- [x] `/v1/models` remains protected and returns the expected model ID.
- [x] `/v1/face/similarity` accepts a valid authenticated request.
- [x] `/v1/chat/completions` accepts the documented OpenAI-compatible image request.
- [x] `/v1/diagnostics/startup` returns sanitized diagnostics when authenticated.

## OpenAI compatibility checks

Required before any pilot using OpenAI-style clients:

- [x] Non-streaming chat completions work with the documented image request.
- [x] `stream=true` returns SSE chunks and no fake LLM output.
- [x] Unsupported OpenAI features fail with structured errors.
- [x] OpenAI client compatibility tests pass.

## Browser demo checks

Required before any pilot that includes the browser demo:

- [x] `/demo` loads.
- [x] One-frame capture works.
- [x] Optional face-box overlay works.
- [x] Opt-in low-rate live polling works.
- [x] Live polling stays client-side and single-flight.
- [x] Camera permission handling and stop behavior work.
- [x] No third-party scripts or CDNs are loaded.

## Privacy checks

- [x] Uploaded images are not stored by default.
- [x] User embeddings are not stored by default.
- [x] API keys are not persisted in browser storage.
- [x] Smoke and benchmark reports do not contain API keys or base64 image payloads.
- [x] Public API responses do not include raw embeddings.

## Security checks

- [x] Invalid or missing API keys are rejected.
- [x] Default local API keys are not used in production.
- [x] Logs do not contain Authorization headers, image payloads, or embeddings.
- [x] Request size and image-format limits are documented.
- [x] Startup diagnostics remain sanitized.

## Dataset/licensing checks

Required before any external or commercial use:

- [x] [dataset-and-licensing.md](dataset-and-licensing.md) has been reviewed.
- [!] Legal review has confirmed the intended dataset use.
- [x] The release notes do not claim commercial readiness.
- [x] The release notes do not claim verified identity recognition.

## Benchmark checks

- [x] [benchmark-plan.md](benchmark-plan.md) has been reviewed.
- [x] Benchmarks were measured on the intended runtime.
- [x] [benchmark-results.md](benchmark-results.md) contains only measured results.
- [x] No fabricated benchmark numbers are present.
- [x] The benchmark report notes the model/gallery asset set that was used.

## Known limitations

- The project is still a research/demo face-similarity service.
- The full CelebA workflow is not bundled in the repo.
- Benchmark results are local and remain subject to the target machine and gallery asset set.
- Legal and dataset review are required before any broader use.

## Go / no-go decision

- [ ] Go only if every required-before-pilot item is checked.
- [x] No-go if any required model, gallery, API, security, privacy, or legal item is unchecked.
- [x] No-go if the environment cannot reproduce the documented checks.

## RC1 release package

- [x] RC1 human approval notes are prepared.
- [x] RC1 release checklist is prepared.
- [x] RC1 release manifest is prepared.
- [x] RC1 release notes remain a candidate draft only.
- [x] Tagging instructions are documented but gated on human approval.
