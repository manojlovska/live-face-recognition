# Threat Model

## Scope
This threat model covers the CPU-only face-similarity API, local gallery artifacts, one-key authentication, and later browser demo.

## Assets
- API key
- Uploaded face images
- User face embeddings generated transiently
- CelebA gallery artifacts
- Model files
- Server logs
- Documentation and release claims

## Trust Boundaries
- Client to API server
- API server to local model/gallery files
- Browser camera to backend API
- Offline gallery build environment to runtime deployment

## Threats and Mitigations

| Threat | Risk | Mitigation |
|---|---|---|
| Leaked API key | Unauthorized use | env-based key, no logging, rotate manually |
| Oversized image | memory/CPU exhaustion | request size and image dimension limits |
| Malformed image | decoder crash or exception | defensive decoding and structured errors |
| Image retention | privacy violation | no storage by default |
| Embedding retention | biometric profile creation | no storage by default |
| Logs contain sensitive data | accidental disclosure | safe logging rules |
| Dataset misuse | legal/reputational risk | dataset/licensing docs and honest release claims |
| False identity claim | user harm | similarity-only wording and disclaimer |
| Dependency vulnerability | compromise | dependency audit before RC1 |
| Gallery tampering | wrong results | manifest and checksums |
| Browser frame over-sending | performance/privacy issue | client-side throttling |

## Out of Scope for MVP
- Multi-user authorization
- Quotas per user
- Production key rotation system
- Secure enclave processing
- Formal compliance certification
- Penetration testing

## RC1 Requirement
Before RC1, every high or medium threat listed here should have either:
- an implemented mitigation;
- a documented limitation;
- or a clear release blocker.
