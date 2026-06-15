# Architecture

## Overview
The service is a CPU-only face-similarity API with two public API surfaces:

1. Native vision API for direct face-similarity calls.
2. OpenAI-compatible API adapter for clients that use OpenAI-style `/v1/*` endpoints.

The inference pipeline is shared by both API surfaces.

## System Diagram

```text
Client
  |-- OpenAI Python SDK
  |-- curl/native client
  |-- browser demo later
        |
        v
FastAPI application
        |
        +-- Auth middleware/dependency
        +-- Health/readiness routes
        +-- OpenAI-compatible routes
        +-- Native face routes
        |
        v
Inference service
        |
        +-- image decoder and validator
        +-- face detector: YuNet
        +-- face aligner: SFace/OpenCV alignment
        +-- face embedder: SFace
        +-- similarity search
        |
        v
Gallery store
        +-- embeddings
        +-- metadata
        +-- manifest
```

## Components

### API Layer
Responsible for HTTP routing, auth, validation, response schemas, and error formatting.

### OpenAI Compatibility Adapter
Translates supported OpenAI-style requests into native inference calls and wraps results in OpenAI-style responses.

### Native Vision API
Provides direct, simpler request/response contracts for face similarity and later browser demo integration.

### Inference Engine
Owns model loading, image preprocessing, detection, alignment, embedding, and similarity search.

### Gallery Store
Loads precomputed CelebA embeddings and metadata from local artifacts. The full CelebA dataset is never scanned during normal API requests.

### Browser Demo
Later phase. Uses browser camera APIs, throttles frames, calls the native API, and draws results on a canvas overlay.

## Data Flow
1. Client sends image.
2. API validates key and request size/type.
3. Image is decoded in memory.
4. Detector finds faces and landmarks.
5. Face is aligned.
6. Embedder computes normalized embedding.
7. Embedding is compared with gallery.
8. API returns boxes, scores, top-k identity IDs, model metadata, and disclaimer.
9. Uploaded image is discarded unless explicit debug retention is enabled.

## Runtime State
Runtime state includes loaded models and gallery artifacts. It should be rebuildable from repository code, model files, dataset files, and documented gallery build commands.

## Durable Project Truth
Durable truth lives in:
- Git history
- documentation
- tests
- gallery manifests
- benchmark reports
- release notes

It does not live in a local agent VM, an uncommitted notebook, or a manually built gallery with no manifest.
