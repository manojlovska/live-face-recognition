# Gallery Build

## Purpose
The live API must not scan CelebA images at request time. Instead, an offline build process creates gallery artifacts used by the runtime service.
The gallery build workflow remains future work; this repository currently only manages model assets and loader status.

## Planned Inputs
- CelebA image directory
- CelebA identity annotation file
- Optional CelebA landmark annotation file
- YuNet model file
- SFace model file

## Planned Outputs

```text
data/gallery/
  gallery_embeddings.npy
  gallery_metadata.sqlite
  gallery_manifest.json
  failed_images.csv
```

Exact filenames may change, but the manifest is required.

## Build Steps
1. Validate dataset paths.
2. Load detector and embedder.
3. Iterate CelebA images.
4. Detect face and landmarks.
5. Align face.
6. Compute normalized embedding.
7. Associate embedding with CelebA identity ID.
8. Aggregate per-image or per-identity representations.
9. Save embeddings and metadata.
10. Write manifest and failure report.

## Runtime Rule
The runtime service loads gallery artifacts. It does not require raw CelebA images.
Until the gallery exists, `/readyz` must continue to report `gallery: not_loaded`.

## Failure Handling
Some images may fail detection or decoding. The builder must report:
- number attempted;
- number succeeded;
- number failed;
- failure reasons where practical.

## Reproducibility
The build command and model versions must be documented. The manifest must include enough metadata to understand how the gallery was produced.

## MVP Shortcut
MVP may use a tiny synthetic or test gallery to validate API behavior. Full CelebA gallery build is required before RC1.
