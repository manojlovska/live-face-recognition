# Roadmap

## Release Ladder

| Version | Name | Purpose |
|---|---|---|
| v0.0 | Scaffold | Constitution, docs, FastAPI skeleton, health endpoints |
| v0.1 | MVP | End-to-end CPU single-image similarity service |
| v0.2 | Full gallery | Reproducible CelebA gallery build and validation |
| v0.3 | OpenAI compatibility | Minimal chat completions compatibility and SSE response streaming |
| v0.4 | Live API | Repeated-frame API suitable for webcam workflows |
| v0.5 | Browser demo | HTML5 one-frame camera interface with overlay and opt-in low-rate live polling |
| v0.6 | Hardening | Benchmarks, tests, docs, security, packaging |
| v1.0-rc1 | RC1 | Controlled-pilot-ready research service |

## MVP Definition
MVP proves the core idea end-to-end:

- CPU-only FastAPI service
- one-key auth
- `/healthz`
- `/readyz`
- `/v1/models`
- `/v1/face/similarity`
- non-streaming `/v1/chat/completions`
- `stream=true` SSE `/v1/chat/completions`
- YuNet face detection
- SFace embeddings
- small gallery support
- top-k similarity results
- OpenAI Python client example
- basic tests and docs

## MVP Non-Goals
- no browser webcam UI
- no WebSocket
- no user accounts
- no database server
- no persistent user image or embedding storage
- no GPU support
- no commercial-readiness claim
- no celebrity display names unless legally provided

## RC1 Definition
RC1 is a controlled-pilot-ready research service with:

- full/reproducible CelebA gallery workflow
- OpenAI-compatible response streaming
- browser webcam demo with one-frame capture and explicit live polling
- benchmark results on CPU
- privacy/security/model documentation
- expanded tests
- release-readiness checklist completed

## PR Sequence
1. Project scaffold and constitution
2. Config and one-key authentication
3. Health, readiness, and model-list endpoints
4. Image decoding and validation
5. Native face-similarity API with stub engine
6. YuNet/SFace model loader
7. Face detection and alignment
8. Embedding generation
9. Small test gallery support
10. Similarity search
11. OpenAI-compatible chat completions
12. OpenAI client compatibility tests
13. CelebA gallery builder
14. Gallery validation and benchmark scripts
15. SSE response streaming
16. Low-rate browser live polling
17. HTML5 webcam demo
18. Privacy/model/API documentation hardening
19. Packaging and optional Dockerfile
20. RC1 hardening and release checklist

## Revisit Triggers
Revisit this roadmap if:
- CPU performance is insufficient;
- CelebA licensing blocks intended use;
- OpenAI compatibility requirements change substantially;
- browser live mode requires WebSocket earlier than expected;
- a different model stack is approved by ADR.

## Scaffold Status
The initial scaffold work is complete. One-key authentication, readiness routing, `/v1/models`, the native face-similarity contract, image decoding/validation, model asset management, CPU-only YuNet/SFace loading skeleton, YuNet detection-only output, internal SFace embedding generation, local gallery loading/search, an offline sample-gallery builder skeleton, an OpenAI-compatible chat adapter with non-streaming and SSE streaming support, and a small built-in browser demo with optional face-box overlays and low-rate live polling are now implemented. The builder now also supports CelebA-style layout discovery, partition parsing, and local quality/performance reporting. Local smoke-test tooling, sequential benchmark tooling, CPU-only Docker packaging, startup configuration validation, release-candidate dependency cleanup, and RC1 documentation/checklist artifacts are now implemented. The next milestone is controlled-pilot validation on a Docker-capable machine with real assets.

## Work Order Status
- Work Order 1: complete.
- Work Order 2: complete.
- Work Order 3: complete.
- Work Order 4: complete.
- Work Order 5: complete.
- Work Order 6: complete.
- Work Order 7: complete.
- Work Order 8: complete.
- Work Order 9: complete.
- Work Order 10: complete.
- Work Order 11: complete.
- Work Order 12: complete.
- Work Order 13: complete.
- Work Order 14: complete.
- Work Order 15: complete.
- Work Order 16: complete.
- Work Order 17: complete.
- Work Order 18: complete.
- Work Order 19: complete.
- Work Order 20: complete.
- Work Order 21: next.
