# RC1 Post-publication Verification

## Candidate

`v0.1.0-rc1`

## Tag verification

- Tag exists locally and remotely.
- The published GitHub Release uses the existing `v0.1.0-rc1` tag.

Verification commands:

```bash
git tag --list v0.1.0-rc1
git ls-remote --tags origin v0.1.0-rc1
```

## GitHub Release verification

- Release URL: https://github.com/manojlovska/live-face-recognition/releases/tag/v0.1.0-rc1
- Release title: `v0.1.0-rc1 — Release Candidate 1`
- The release is published, not a draft.
- No release assets are attached.
- The release notes preserve release-candidate wording, not-final-release wording, not identity verification wording, and local-machine-specific benchmark caution.

Verification commands:

```bash
gh release view v0.1.0-rc1 --json tagName,name,isDraft,isPrerelease,url,assets,publishedAt
```

## Repository safety audit

- No ONNX files are tracked.
- No gallery artifacts are tracked.
- No raw benchmark reports are tracked.
- No external/sample data is tracked.
- No `.env` or real secrets are tracked.

Verification commands:

```bash
git ls-files | grep -E '(^models/.*\\.onnx$|^data/gallery/|^reports/|^external/|\\.env$|\\.env\\.)' || true
git check-ignore -v models/face_detection_yunet.onnx || true
git check-ignore -v models/face_recognition_sface.onnx || true
git check-ignore -v data/gallery/gallery_embeddings.npy || true
git check-ignore -v reports/benchmark-rc-ready-generated-image.json || true
git check-ignore -v external/validation_sample || true
git check-ignore -v .env || true
```

## Test verification

- `python3.12 -m ruff check .` passed.
- `python3.12 -m ruff format --check .` passed.
- `python3.12 -m pytest -W error` passed.

Verification commands:

```bash
python3.12 -m ruff check .
python3.12 -m ruff format --check .
python3.12 -m pytest -W error
```

## Docker verification

- `docker build -t live-face-recognition:rc1-postpub .` passed locally.
- Docker validation used the CPU-only image path.

Verification command:

```bash
docker build -t live-face-recognition:rc1-postpub .
```

## Release wording verification

- The release remains a release candidate.
- The release is not a final release.
- The release is not identity verification.
- The release is not commercial-ready beyond the approved RC1 publication scope.
- Benchmark numbers are local-machine-specific.

## Release asset verification

- No release assets are attached.
- No ONNX files, CelebA data, gallery artifacts, reports, API keys, or `.env` files were attached.

## Remaining scope limits

- Broader or external use remains subject to the documented approved scope and any dataset/legal conditions.
- The full CelebA workflow is not bundled in the repository.
- The release candidate remains a face-similarity service, not identity verification.

## Result

The published `v0.1.0-rc1` release passed post-publication verification for tag, release object, wording, repository safety, tests, and Docker build checks.
