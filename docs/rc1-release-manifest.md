# RC1 Release Manifest

## Candidate

- Candidate name: `v0.1.0-rc1`
- Intended tag: `v0.1.0-rc1`
- Source branch: `feature/wo-025-rc1-release-package`
- Validation baseline: `feature/wo-024r-sudo-ready-path-validation` (`fa93191`)

## Included docs

- `README.md`
- `docs/current-state.md`
- `docs/handoff.md`
- `docs/github-release-draft-v0.1.0-rc1.md`
- `docs/internal-rc1-announcement.md`
- `docs/pilot-readiness-checklist.md`
- `docs/operator-runbook.md`
- `docs/release-readiness.md`
- `docs/release-notes-rc1.md`
- `docs/rc1-human-approval-notes.md`
- `docs/rc1-release-checklist.md`
- `docs/rc1-release-manifest.md`
- `docs/benchmark-results.md`
- `docs/deployment.md`
- `docs/security.md`
- `docs/privacy.md`
- `docs/dataset-and-licensing.md`
- `docs/testing-strategy.md`

## Excluded artifacts

- `models/*.onnx`
- `data/gallery/*`
- `reports/*`
- `external/*`
- `.env`
- `*.env`
- sample images
- identity files
- raw benchmark JSON reports

## Validation summary

- Local ready-path Docker validation passed with mounted YuNet/SFace models and a small gallery.
- `/readyz` returned `200 ready` in the mounted-assets validation run.
- Native, chat, and chat-stream ready-path benchmarks were measured locally.
- The benchmark numbers are local-machine-specific and not general performance claims.

## Remaining human gates

- Dataset/legal review for broader or external use.
- Final human approval for RC1 tagging.

## Commands to reproduce tests

```bash
python3.12 -m ruff check .
python3.12 -m ruff format --check .
python3.12 -m pytest -W error
docker build -t live-face-recognition:rc1 .
python scripts/smoke_release.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --check-diagnostics
python scripts/benchmark_api.py --base-url http://localhost:8000 --api-key "$FACE_API_KEY" --endpoint all --requests 20 --warmup 3
```

## Notes

- This manifest is for an RC1 candidate, not a final release.
- No secrets, raw reports, embeddings, or base64 payloads are included here.
- The GitHub Release draft should remain unpublished until the maintainer chooses otherwise.
