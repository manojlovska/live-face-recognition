# Internal RC1 Announcement Draft

## Summary

The `v0.1.0-rc1` tag exists and the RC1 candidate is ready for internal review.
GitHub Release is not published yet.
This is a controlled-pilot release candidate, not a final release.

## What changed

- CPU-only FastAPI face-similarity service is packaged for local/container use.
- Native similarity, minimal OpenAI-compatible chat completions, browser demo, smoke tests, and benchmark tooling are in place.
- Release-candidate documentation now includes human approval notes, a release checklist, a release manifest, and a GitHub Release draft.

## What was validated

- Docker build passed on a Docker-capable machine.
- Ready-path Docker validation passed locally with mounted YuNet/SFace models and a small gallery.
- `/readyz` returned `200 ready` with mounted assets.
- Native, chat, and chat-stream ready-path benchmarks were measured locally.
- The benchmark numbers are local-machine-specific.

## What remains gated

- Legal/dataset approval remains pending before broader or external use.
- Security/privacy signoff remains pending unless explicitly recorded elsewhere.
- The GitHub Release must remain a draft unless the maintainer chooses to publish it.
- This candidate is not commercial-ready and does not claim identity verification.

## How to try it locally

```bash
python3.12 -m pytest -W error
docker build -t live-face-recognition:rc1 .
python scripts/smoke_release.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --check-diagnostics
python scripts/benchmark_api.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --endpoint all --requests 20 --warmup 3
```

## Who should review

- Engineering
- Security/privacy
- Dataset/legal
- Pilot operator
- Final release approver

## Suggested next steps

- Review the RC1 human approval notes and release checklist.
- Confirm the GitHub Release draft text matches the tagged candidate.
- Keep the release draft unpublished until explicit approval is given.
- Resolve the pending dataset/legal gate before any broader or external use.
