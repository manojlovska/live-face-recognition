# RC1 Human Approval Notes

## Candidate

- Candidate name: `v0.1.0-rc1`
- Release-package branch: `feature/wo-025-rc1-release-package`
- Baseline validation branch: `feature/wo-024r-sudo-ready-path-validation`

## Current status

`approved for internal controlled-pilot RC publication`

This is not a final commercial release.
This is not identity verification.
Human sign-offs for v0.1.0-rc1 have been recorded.
The GitHub Release for v0.1.0-rc1 is approved for publication.
Human legal/dataset approval remains required before any broader or external use beyond the approved RC1 scope.

## What has been validated

- Docker built successfully on a Docker-capable machine.
- A container without mounted assets passed the operational-but-not-ready smoke path.
- A container with mounted YuNet/SFace models and a small gallery passed the ready smoke path.
- `/readyz` returned `200 ready` with the mounted-assets validation run.
- Native, chat, and chat-stream ready-path benchmarks were measured locally.
- The browser demo, smoke script, benchmark script, diagnostics endpoint, and release documentation all matched the measured runtime state.

## What has not been validated

- Full CelebA workflow at release scale.
- Legal/dataset approval for broader or external use beyond the approved RC1 scope.
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

## Approval table

| Role | Approver | Decision | Date | Scope / notes |
|---|---|---|---|---|
| Engineering | Anastasija Manojlovska | approved | 2026-06-16 | Approval for `v0.1.0-rc1` release-candidate publication. Evidence reviewed: RC1 release package, benchmark results, Docker ready-path validation, smoke tests, `pytest -W error`, artifact exclusion audit. Permission to publish GitHub Release: yes. Conditions or blockers: none for RC1 publication. |
| Security/privacy | Anastasija Manojlovska | approved | 2026-06-16 | Approval for `v0.1.0-rc1` release-candidate publication. Evidence reviewed: `docs/security.md`, `docs/privacy.md`, startup diagnostics behavior, smoke reports summary, artifact audit. Permission to publish GitHub Release: yes. Conditions or blockers: none for RC1 publication. |
| Dataset/legal | Anastasija Manojlovska | approved | 2026-06-16 | Approval for `v0.1.0-rc1` release-candidate publication. This does not convert the project into a commercial-ready product and does not approve identity-verification claims. Evidence reviewed: `docs/dataset-and-licensing.md`, `docs/release-readiness.md`, `docs/release-notes-rc1.md`, `docs/github-release-draft-v0.1.0-rc1.md`. Permission to publish GitHub Release: yes. Conditions or blockers: no identity-verification claim; no commercial-readiness claim; no bundled CelebA data; no bundled ONNX models; no sample images or gallery artifacts attached to the release. |
| Pilot operator | Anastasija Manojlovska | approved | 2026-06-16 | Approval for `v0.1.0-rc1` controlled pilot candidate publication. Evidence reviewed: `docs/operator-runbook.md`, `docs/pilot-readiness-checklist.md`, Docker ready-path validation, benchmark results. Permission to publish GitHub Release: yes. Conditions or blockers: pilot operators must provide their own authorized model/gallery assets at runtime. |
| Final release approver | Anastasija Manojlovska | approved | 2026-06-16 | Approval to publish the GitHub Release for the existing `v0.1.0-rc1` tag as a release candidate, not a final release. Evidence reviewed: RC1 approval notes, RC1 release checklist, RC1 release manifest, GitHub Release draft, benchmark results. Permission to publish GitHub Release: yes. Conditions or blockers: release notes must retain release-candidate, not-final-release, not-identity-verification, and not-commercial-ready wording. |

Allowed decisions: `approved`, `approved with conditions`, `rejected`, `pending`, `not applicable`.

Do not change `pending` to `approved` without a real human decision.
Record the approval scope in the notes column.
Dataset/legal approval is required before broader or external use.
Final release approver approval is required before publishing GitHub Release.

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
