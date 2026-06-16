# RC1 Release Checklist

## Before tagging

- Confirm the release package is the intended RC1 candidate: `v0.1.0-rc1`.
- Confirm the human approval notes are complete enough for review.
- Confirm the release notes still describe a draft/candidate, not a final release.

## Git hygiene

- `git status --short`
- `git log --oneline -5`
- Confirm no ONNX files, sample images, identity files, gallery artifacts, raw benchmark reports, real API keys, or `.env` files are staged.

## Test verification

- `python3.12 -m ruff check .`
- `python3.12 -m ruff format --check .`
- `python3.12 -m pytest -W error`

## Docker verification

- `docker build -t live-face-recognition:rc1 .`
- Confirm the image runs as a non-root user on port 8000.
- Confirm the image does not bake in model files, gallery artifacts, reports, API keys, or `.env`.

## Runtime validation

- `python scripts/smoke_release.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --check-diagnostics`
- `python scripts/benchmark_api.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --endpoint all --requests 20 --warmup 3`
- Confirm `/readyz` returns `200 ready` when the intended models and gallery are mounted.

## Privacy/security verification

- Confirm uploaded images are not stored by default.
- Confirm embeddings are not returned in raw form.
- Confirm diagnostics are sanitized and protected.
- Confirm API keys are not logged or committed.

## Dataset/legal verification

- Confirm dataset and licensing review is complete for the intended use.
- Confirm the release notes do not claim commercial readiness.
- Confirm the release notes do not claim identity verification.

## Documentation verification

- Confirm the RC1 human approval notes are present.
- Confirm the RC1 release checklist is present.
- Confirm the RC1 release manifest is present.
- Confirm the RC1 release notes remain a draft/candidate.
- Confirm the handoff points to Work Order 26.

## Tagging

Run the tag commands only after human approval:

```bash
git tag -a v0.1.0-rc1 -m "v0.1.0-rc1"
git push origin v0.1.0-rc1
```

## Post-tag checks

- Verify the tag points at the intended commit.
- Verify the release package documents still match the tagged state.
- Verify no release artifacts were accidentally committed.

## Do not release if

- Any required human approval is missing.
- The target runtime has not been smoke-tested.
- The Docker image fails to build.
- The release notes claim final release, commercial readiness, or identity verification.
- The model/gallery artifacts or benchmark reports are unverified for the intended target.
