# Privacy

## Privacy Position
This service processes face images. Face images and face embeddings can be sensitive. The default design minimizes retention.

## Default Retention Policy
By default, the service:
- decodes uploaded images in memory only;
- processes uploaded images in memory;
- does not store uploaded user images;
- does not store decoded images;
- does not store user face embeddings;
- does not retain request bodies;
- does not create user biometric profiles;
- does not enroll users.
- generates embeddings only in memory when the model is available;
- does not return raw embedding vectors in the public API by default;
- does not persist embeddings or aligned face crops.
- treats gallery embeddings as local model artifacts that are loaded from disk, not user data;
- does not retain gallery search queries beyond the request;
- does not create a user enrollment store.
- The offline sample-gallery builder processes local sample images in memory and writes only gallery artifacts and a build report.

## Output Language
The service returns similarity results. It must not describe results as verified identity, authentication, or proof that the subject is a specific person.

Recommended disclaimer:

```text
Similarity result only; not identity verification.
```

## Browser Demo Privacy
The browser demo must:
- request camera permission explicitly;
- explain that one captured frame is sent only when the user clicks Capture frame, and repeated frames are sent only when live polling is explicitly enabled;
- not record video;
- not store frames by default.
- when face boxes are shown, draw them locally from the API response only.
- Live polling in the browser demo must remain opt-in, client-side, and throttled.
- Live polling must not store frames, API responses, or API keys in browser storage.
- Live polling must stop when the camera stops and when the tab becomes hidden.

## Release Tooling Privacy
The smoke-test and benchmark scripts must:
- operate only against the configured local or supplied base URL;
- not store API keys in reports;
- not store base64 image payloads in reports;
- not store decoded image bytes or embeddings;
- not send data to external services.
- The release-candidate test-client dependency change to `httpx2` does not alter these privacy rules.
- The [pilot-readiness-checklist.md](pilot-readiness-checklist.md) and [operator-runbook.md](operator-runbook.md) document the human checks that should be completed before a controlled pilot.

## Container Privacy
- The container image must not include user images, user embeddings, or request bodies.
- The serving container does not persist uploaded images by default.
- Local model and gallery artifacts are operator-managed inputs, not user data.
- The protected startup diagnostics endpoint does not return images, base64 payloads, embeddings, or API keys.

## Debug Mode
If a future debug mode saves images, it must be:
- disabled by default;
- clearly named;
- documented;
- excluded from production/pilot defaults;
- covered in security/privacy docs.

## Deployment Caution
Any real deployment involving people should be reviewed for consent, data-protection obligations, institutional policy, and legal basis. This repository does not itself provide legal approval.

## Privacy Tests
Where practical, tests should verify that normal requests do not create saved image or embedding files.

## Current Image Handling
- Uploaded image bytes are decoded in memory only.
- No image retention exists by default.
- Embeddings are transient in memory only.
- No embedding retention exists by default.
- Model files are local operator-managed assets, not user data.
- Gallery embeddings are local operator-managed model artifacts.
- Public API responses do not include raw query embeddings.
- Builder outputs are local model artifacts, not user data.
- The offline gallery builder writes only derived local artifacts and build reports; it does not retain source images or embeddings beyond the build process.
- The OpenAI-compatible chat adapter decodes images in memory only and reuses the native pipeline; it does not echo base64 payloads or retain request images.
- Streaming chat completions emit the same privacy-filtered payload as the non-streaming adapter; stream frames do not add any embedding retention or image storage.
