# Model Card

## Model Stack
Initial planned stack:

- Face detector: OpenCV YuNet
- Face embedder: OpenCV SFace
- Similarity gallery: local gallery artifacts, later CelebA-derived embeddings
- Runtime: CPU-only Python service
- Model assets are loaded from local paths under `models/` by default.

## Intended Use
- Research/demo face-similarity service
- OpenAI-compatible API experiments
- Controlled internal or workshop use
- CPU-only computer vision service example

## Not Intended For
- Identity verification
- Authentication
- Law enforcement
- Surveillance
- Production biometric identification
- Commercial CelebA-backed deployment without legal review

## Inputs
- JPEG/PNG/WebP image, subject to implemented validation rules
- One or more visible faces

## Outputs
- Face bounding boxes
- Detection scores
- Top-k similar gallery item IDs
- Similarity scores
- Disclaimer

## Current Output State
- YuNet detector output exists when the detector is supplied and loaded.
- Detection-only responses include face boxes and landmarks, but not embeddings.
- SFace embedding output exists internally when the embedder is supplied and loaded.
- Raw embeddings are not returned in the public API.
- Local gallery artifact search exists when the gallery is supplied and loaded.
- Similarity responses include `top_matches` built from loaded gallery metadata.
- No identity verification claim is made.
- A sample-gallery builder can produce runtime gallery artifacts from local sample directories.
- The builder also understands common local CelebA-style layouts and partition files.
- Builder reports include quality and performance summaries.

## Limitations
- Similarity score is not identity proof.
- CelebA may have demographic and image-source biases.
- Results depend on detector and embedding quality.
- CPU latency depends on hardware, image size, and gallery size.
- Display names are not provided unless a legal mapping is added.

## Safety and Privacy
Uploaded images and user embeddings are not stored by default. Logs must not contain raw images or embeddings.
Gallery embeddings are operator-managed local artifacts, not user enrollment data.
The sample-gallery builder processes local image files only and does not download dataset images at runtime.
The local-layout builder extension still does not download CelebA or return raw embedding vectors.

## Performance
Actual performance must be recorded in `docs/benchmark-results.md`. Do not invent latency or FPS numbers.

## Evaluation Plan
At minimum:
- no-face behavior;
- one-face behavior;
- multi-face behavior;
- repeated-frame latency;
- gallery search correctness on known fixtures;
- OpenAI client compatibility.
