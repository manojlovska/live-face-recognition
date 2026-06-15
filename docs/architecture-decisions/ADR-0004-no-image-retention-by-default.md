# ADR-0004: No Image Retention by Default

## Status
Accepted

## Context
The service processes face images. Face data is sensitive. A professional first release should minimize retained biometric data.

## Decision
Uploaded user images and user embeddings are processed in memory and discarded by default. Persistent storage of user images or embeddings is not allowed in MVP/RC1 unless a later ADR explicitly adds a retention mode with safeguards.

## Consequences
- Logging must exclude raw images, base64 payloads, and embeddings.
- Debug image saving must be disabled by default.
- Tests should verify retention defaults where practical.
- Documentation must state no-retention behavior clearly.

## Revisit Condition
Revisit only if a future product requirement requires opt-in retention, audit storage, or dataset creation. Such a change must include privacy, security, and legal review.
