# RC1 Sign-off Request

## Candidate

`v0.1.0-rc1`

This is a release candidate, not a final release.
This is face similarity, not identity verification.
This is not commercial-ready unless legal/dataset and product approval explicitly say so.
Dataset/legal approval remains pending unless a human approver completes that section.
Benchmark numbers are local-machine-specific.
Model files, sample images, gallery artifacts, raw benchmark reports, API keys, and `.env` are not committed.

## Summary for reviewers

The RC1 package has been prepared for human review. The repository documents a local ready-path validation run with Docker, mounted YuNet/SFace models, a small gallery, smoke checks, and ready-path benchmarks. The GitHub Release is still a draft and has not been published.

## What reviewers are approving

- Whether the RC1 candidate is acceptable for the reviewer’s area of responsibility.
- Whether the evidence package is sufficient for the scope being reviewed.
- Whether any conditions or blockers should be recorded before the next step.

## What reviewers are not approving

- Final release publication.
- Commercial readiness.
- Identity verification.
- Broader or external use without dataset/legal approval.
- Any unreviewed change outside the stated scope.

## Evidence package

- [RC1 human approval notes](rc1-human-approval-notes.md)
- [RC1 release checklist](rc1-release-checklist.md)
- [RC1 release manifest](rc1-release-manifest.md)
- [RC1 release notes draft](release-notes-rc1.md)
- [GitHub Release draft](github-release-draft-v0.1.0-rc1.md)
- [Internal RC1 announcement draft](internal-rc1-announcement.md)
- [Benchmark results](benchmark-results.md)
- [Pilot readiness checklist](pilot-readiness-checklist.md)
- [Security](security.md)
- [Privacy](privacy.md)
- [Dataset and licensing](dataset-and-licensing.md)

## Approval roles

- Engineering
- Security/privacy
- Dataset/legal
- Pilot operator
- Final release approver

## Engineering review checklist

- Tests and lint pass.
- RC1 docs and release notes stay candidate-only.
- The release package reflects the validated runtime path.

## Security/privacy review checklist

- No secrets are committed.
- No user images or embeddings are retained by default.
- Diagnostics remain sanitized.
- Public APIs do not return raw embeddings.

## Dataset/legal review checklist

- Dataset usage is reviewed for the intended scope.
- Broader or external use remains gated until review is complete.
- The release candidate does not claim commercial readiness.

## Pilot operator checklist

- The runtime path is documented.
- Smoke tests and benchmarks are documented.
- The local operating scope is clear.

## Final release approver checklist

- The GitHub Release draft is ready for publication decision.
- No unresolved blockers remain for the intended scope.
- Final publication is still a human decision.

## Decision options

- `approved`
- `approved with conditions`
- `rejected`
- `pending`
- `not applicable`

## How to record a decision

Use the human approval notes table in [RC1 human approval notes](rc1-human-approval-notes.md) or the comment template in [RC1 review comment template](rc1-review-comment-template.md).
Record the approver name, role, decision, date, and the exact scope covered.
Do not mark dataset/legal approval as complete unless the reviewer explicitly approves it.
