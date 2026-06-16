# Pilot Readiness Checklist

This checklist is for a controlled pilot of the CPU-only face-similarity service. It is not a declaration of final release, commercial readiness, or identity verification.

## Code and tests

- [ ] `python3.12 -m ruff check .` passes.
- [ ] `python3.12 -m ruff format --check .` passes.
- [ ] `python3.12 -m pytest -W error` passes.
- [ ] Relevant regression tests for auth, readiness, gallery loading, chat compatibility, browser demo, smoke checks, and startup diagnostics pass.

## Dependency and packaging checks

- [ ] Runtime dependencies remain CPU-only and bounded in `pyproject.toml`.
- [ ] Test dependencies remain separated from local-script dependencies.
- [ ] No GPU, database, Redis, Celery, or frontend build dependencies are present.
- [ ] [testing-strategy.md](testing-strategy.md) reflects the current warning policy.
- [ ] [release-readiness.md](release-readiness.md) reflects the current release gate status.

## Docker checks

- [ ] `docker build -t live-face-recognition:local .` passes on a Docker-capable machine.
- [ ] The container runs as a non-root user.
- [ ] The container exposes port 8000.
- [ ] `models/`, `data/gallery/`, `reports/`, and `.env` are not baked into the image.
- [ ] Model and gallery artifacts are mounted read-only for serving.

## Configuration checks

- [ ] `APP_ENV` is set intentionally.
- [ ] `STRICT_STARTUP_VALIDATION` matches the deployment mode.
- [ ] `STARTUP_VALIDATE_ASSETS` matches the deployment mode.
- [ ] `DEBUG_IMAGE_RETENTION` is disabled unless explicitly required for a private debug workflow.
- [ ] `FACE_API_KEY` is not the default local placeholder in any pilot environment.
- [ ] [deployment.md](deployment.md) matches the intended runtime configuration.

## Model asset checks

Required before any pilot that expects live similarity:

- [ ] YuNet model file is present.
- [ ] SFace model file is present.
- [ ] Model manifest is present and consistent.
- [ ] `GET /readyz` reports the expected model status.
- [ ] `GET /v1/diagnostics/startup` reports no unsafe configuration errors.

## Gallery artifact checks

Required before any pilot that expects similarity results from a gallery:

- [ ] Gallery embeddings file is present.
- [ ] Gallery metadata file is present.
- [ ] Gallery manifest is present.
- [ ] Gallery embedding dimension matches the model output dimension.
- [ ] Gallery scope and filters are documented.
- [ ] Local gallery artifacts are user-supplied and not bundled into the repo.

## API checks

Required before any pilot:

- [ ] `/healthz` returns 200.
- [ ] `/readyz` returns 200 when the runtime is expected to serve similarity results.
- [ ] `/v1/models` remains protected and returns the expected model ID.
- [ ] `/v1/face/similarity` accepts a valid authenticated request.
- [ ] `/v1/chat/completions` accepts the documented OpenAI-compatible image request.
- [ ] `/v1/diagnostics/startup` returns sanitized diagnostics when authenticated.

## OpenAI compatibility checks

Required before any pilot using OpenAI-style clients:

- [ ] Non-streaming chat completions work with the documented image request.
- [ ] `stream=true` returns SSE chunks and no fake LLM output.
- [ ] Unsupported OpenAI features fail with structured errors.
- [ ] OpenAI client compatibility tests pass.

## Browser demo checks

Required before any pilot that includes the browser demo:

- [ ] `/demo` loads.
- [ ] One-frame capture works.
- [ ] Optional face-box overlay works.
- [ ] Opt-in low-rate live polling works.
- [ ] Live polling stays client-side and single-flight.
- [ ] Camera permission handling and stop behavior work.
- [ ] No third-party scripts or CDNs are loaded.

## Privacy checks

- [ ] Uploaded images are not stored by default.
- [ ] User embeddings are not stored by default.
- [ ] API keys are not persisted in browser storage.
- [ ] Smoke and benchmark reports do not contain API keys or base64 image payloads.
- [ ] Public API responses do not include raw embeddings.

## Security checks

- [ ] Invalid or missing API keys are rejected.
- [ ] Default local API keys are not used in production.
- [ ] Logs do not contain Authorization headers, image payloads, or embeddings.
- [ ] Request size and image-format limits are documented.
- [ ] Startup diagnostics remain sanitized.

## Dataset/licensing checks

Required before any external or commercial use:

- [ ] [dataset-and-licensing.md](dataset-and-licensing.md) has been reviewed.
- [ ] Legal review has confirmed the intended dataset use.
- [ ] The release notes do not claim commercial readiness.
- [ ] The release notes do not claim verified identity recognition.

## Benchmark checks

- [ ] [benchmark-plan.md](benchmark-plan.md) has been reviewed.
- [ ] Benchmarks were measured on the intended runtime.
- [ ] [benchmark-results.md](benchmark-results.md) contains only measured results.
- [ ] No fabricated benchmark numbers are present.
- [ ] The benchmark report notes the model/gallery asset set that was used.

## Known limitations

- The project is still a research/demo face-similarity service.
- The full CelebA workflow is not bundled in the repo.
- Benchmark results are not authoritative until a dated run is recorded.
- Legal and dataset review are required before any broader use.

## Go / no-go decision

- [ ] Go only if every required-before-pilot item is checked.
- [ ] No-go if any required model, gallery, API, security, privacy, or legal item is unchecked.
- [ ] No-go if the environment cannot reproduce the documented checks.
