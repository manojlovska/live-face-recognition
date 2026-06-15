# CelebA Face Similarity API

CPU-only FastAPI scaffold for the CelebA face-similarity service.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Run the app

```bash
uvicorn app.main:app --reload
```

Open the browser demo at:

```text
http://localhost:8000/demo
```

Browser camera access usually requires `localhost` or HTTPS.

## Health check

```bash
curl http://127.0.0.1:8000/healthz
```

`/healthz` is a public liveness check. It only reports that the process is up.

## Readiness check

```bash
curl http://127.0.0.1:8000/readyz
```

`/readyz` is public too, but it currently returns `503 not_ready` until the detector, embedder, and gallery are all loaded.
The response now includes model-asset and gallery status so you can tell whether YuNet and SFace files are missing, present, loaded, or in error.

## Authentication

Protected endpoints require:

```http
Authorization: Bearer <FACE_API_KEY>
```

Set `FACE_API_KEY` locally in `.env` before using protected routes.

```bash
export FACE_API_KEY="change-me-local-dev-key"
# Current and future protected endpoints use:
# curl -H "Authorization: Bearer $FACE_API_KEY" http://127.0.0.1:8000/...
```

## Model list

```bash
curl -H "Authorization: Bearer change-me-local-dev-key" \
  http://localhost:8000/v1/models
```

`/v1/models` is protected and lists the configured model ID. The similarity engine is still not fully ready until the gallery loads.

## Native similarity

Valid `POST /v1/face/similarity` image requests are decoded and validated in memory. If YuNet is loaded, the service returns detection-only face boxes. If YuNet and SFace are both loaded, the service generates embeddings internally, and if a local gallery artifact is also loaded the service returns gallery-backed `top_matches`. Raw embedding vectors are still never returned. The current gallery support is artifact-based and uses a tiny local fixture gallery for tests; it is not a full CelebA build.

Model files are expected under `models/` by default:

- `models/face_detection_yunet.onnx`
- `models/face_recognition_sface.onnx`
- `models/model_manifest.json`

To test real YuNet detection manually:

1. Place the YuNet ONNX file at the configured `YUNET_MODEL_PATH`.
2. Set `MODEL_AUTO_LOAD=true`.
3. Start the server.
4. Send a valid `POST /v1/face/similarity` request.
5. A detection-only result should be returned when the detector loads successfully.

If you also provide the SFace ONNX file and set `MODEL_AUTO_LOAD=true`, the service will generate embeddings internally while still returning only public metadata. If you also provide a local gallery artifact and set `GALLERY_AUTO_LOAD=true`, the service can return similarity results with `top_matches`.

## OpenAI-compatible chat completions

The service also exposes a minimal non-streaming OpenAI-compatible adapter for image similarity requests. The adapter reuses the same native pipeline and returns the similarity result as JSON text in the assistant message.

```python
from openai import OpenAI

client = OpenAI(
    api_key="change-me-local-dev-key",
    base_url="http://localhost:8000/v1",
)

response = client.chat.completions.create(
    model="celeba-face-similarity-cpu",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Who is this face most similar to?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,..."},
                },
            ],
        }
    ],
)
```

`stream=true` is supported and returns SSE chat-completion chunks.

```python
stream = client.chat.completions.create(
    model="celeba-face-similarity-cpu",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Who is this face most similar to?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/jpeg;base64,..."},
                },
            ],
        }
    ],
    stream=True,
)

for chunk in stream:
    print(chunk.choices[0].delta)
```

`stream=True` returns SSE chat-completion chunks, not live video streaming.

## Browser demo

The built-in browser demo captures one webcam frame on demand and sends it to the native API. It can optionally draw face-box overlays from the single-frame response. It does not continuously stream video and it does not store API keys or images in browser storage.

## Build gallery

Use the sample builder to create a local gallery artifact from a small CelebA-like directory:

```bash
python scripts/build_gallery.py \
  --images-dir /path/to/sample/images \
  --identity-file /path/to/identity_sample.txt \
  --output-dir data/gallery \
  --gallery-version sample-gallery-v1 \
  --limit 100
```

This is sample-scale only. It does not process the full CelebA dataset yet.

For a local CelebA-style directory layout, you can also use:

```bash
python scripts/build_gallery.py \
  --celeba-root /path/to/celeba \
  --output-dir data/gallery \
  --gallery-version celeba-local-v1 \
  --limit 1000 \
  --include-partitions train,val
```

The builder discovers `img_align_celeba/`, `identity_CelebA.txt`, and an optional `list_eval_partition.txt` under that root. It stays local-only and does not download CelebA.

## Quality checks

```bash
ruff check .
ruff format --check .
pytest
```

## Environment

Copy `.env.example` to `.env` if you want to override defaults locally.

Project documentation lives under `docs/`.
