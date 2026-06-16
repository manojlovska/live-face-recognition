# RC1 Human Approval Notes

## Candidate

- Candidate name: `v0.1.0-rc1`
- Release-package branch: `feature/wo-025-rc1-release-package`
- Baseline validation branch: `feature/wo-024r-sudo-ready-path-validation`

## Current status

`partially ready for controlled pilot`

This is not a final commercial release.
This is not identity verification.
Human legal/dataset approval is still pending before any broader or external use.

## What has been validated

- Docker built successfully on a Docker-capable machine.
- A container without mounted assets passed the operational-but-not-ready smoke path.
- A container with mounted YuNet/SFace models and a small gallery passed the ready smoke path.
- `/readyz` returned `200 ready` with the mounted-assets validation run.
- Native, chat, and chat-stream ready-path benchmarks were measured locally.
- The browser demo, smoke script, benchmark script, diagnostics endpoint, and release documentation all matched the measured runtime state.

## What has not been validated

- Full CelebA workflow at release scale.
- Legal/dataset approval for broader or external use.
- Commercial deployment readiness.
- Identity verification claims.
- General benchmark generality beyond the local validation machine and gallery set.

## Legal and dataset approval gate

Legal and dataset approval remains a required human gate.
Do not tag or publish RC1 for broader or external use until that gate is completed.

## Security and privacy review

- API keys are not committed.
- `.env` files are not committed.
- Uploaded images are not stored by default.
- User embeddings are not stored by default.
- Diagnostics remain sanitized and protected.
- Public APIs do not return raw embeddings.

## Model and gallery asset handling

- YuNet and SFace ONNX files were downloaded locally for validation only.
- Sample images and identity files were used locally for gallery construction only.
- Gallery artifacts were generated locally and are not committed.
- Raw benchmark reports are not committed.

## Docker and deployment status

- CPU-only Docker build passed on a Docker-capable machine.
- The image runs as a non-root user on port 8000.
- Model and gallery artifacts are mounted at runtime.
- Docker packaging does not bake in API keys, model files, gallery artifacts, or `.env`.

## Benchmark summary

Local-machine-specific ready-path results from Work Order 24R:

| Endpoint | Requests | Warmup | Result mode | Min ms | Mean ms | Median ms | P95 ms | Max ms | Errors |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| native | 20 | 3 | similarity | 76.267 | 92.756 | 93.607 | 103.230 | 106.154 | 0 |
| chat | 20 | 3 | similarity | 78.909 | 94.117 | 93.524 | 102.506 | 107.238 | 0 |
| chat-stream | 20 | 3 | similarity | 91.662 | 104.155 | 103.746 | 109.597 | 112.402 | 0 |

These numbers are local-machine-specific and should not be generalized.

## Known limitations

- The service is a face-similarity research/pilot candidate, not a final commercial release.
- The service does not claim identity verification.
- The full CelebA workflow is not bundled in the repository.
- Benchmark numbers are environment-specific.
- Dataset/legal approval is still pending.

## Required human decisions

- Decide whether the current release package is acceptable for RC1 tagging.
- Decide whether any further runtime validation is needed on the target release machine.
- Decide whether dataset/legal approval is sufficient for the intended pilot scope.
- Decide whether the tag should be created now or held.

## Tagging instructions

Only run the tag commands after explicit human approval:

```bash
git tag -a v0.1.0-rc1 -m "v0.1.0-rc1"
git push origin v0.1.0-rc1
```

## Rollback / no-go instructions

- If any required human gate fails, do not tag.
- If the target machine differs materially from the validated runtime, rerun smoke and benchmark checks there first.
- If legal/dataset review is incomplete, stop before external or commercial release actions.

## Approval sign-off

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Engineering |  | TBD |  |  |
| Security/privacy |  | TBD |  |  |
| Dataset/legal |  | TBD |  |  |
| Pilot operator |  | TBD |  |  |
| Final release approver |  | TBD |  |  |
