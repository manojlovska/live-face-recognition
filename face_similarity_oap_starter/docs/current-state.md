# Current State

## Status
Initial strategic documentation state. Implementation has not started.

## Current Truth
- Project goal is defined.
- CPU-only constraint is accepted.
- OpenAI-compatible API requirement is accepted.
- One-key auth requirement is accepted.
- YuNet + SFace is the proposed initial model stack.
- CelebA is the proposed gallery base, with licensing caution.
- No image or embedding retention by default is accepted.

## Implemented
- No code implemented yet in this initial state.

## Missing
- Repository scaffold
- Python package setup
- FastAPI app
- Auth dependency
- Health/readiness endpoints
- OpenAI-compatible endpoints
- Native face-similarity endpoint
- Model downloader/loader
- Gallery artifacts and builder
- Tests
- Benchmarks
- Browser demo

## Known Risks
- CelebA licensing may limit use to non-commercial research/demo contexts.
- Face data is sensitive and may trigger biometric-data obligations depending on deployment context.
- CPU performance must be measured, not assumed.
- OpenAI compatibility must be explicitly scoped; this is not a general LLM API.

## Next Recommended Task
Create the project scaffold:
- `pyproject.toml`
- minimal `app/main.py`
- config model
- `/healthz`
- test setup
- ruff setup
- README quickstart

## Do Not Do Next
- Do not add browser UI before the API exists.
- Do not process the full CelebA dataset before the gallery-builder design is implemented.
- Do not add GPU dependencies.
- Do not claim production readiness.
