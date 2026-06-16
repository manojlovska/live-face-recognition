# Dataset and Licensing

## Dataset Base
The intended gallery base is CelebA.

CelebA provides many celebrity face images and identity annotations. This project uses CelebA to build a face-similarity gallery.
The repository does not download or redistribute CelebA data. Operators must supply local dataset files themselves.

## Use Limitation
CelebA must be treated cautiously. Do not claim commercial readiness or broad public deployment unless dataset licensing and image rights are reviewed.

## Identity Names
Return CelebA identity IDs by default.

Do not invent human-readable celebrity names. Add display names only from a legally reviewed and documented mapping.

## Model Licenses
Document the licenses and sources of the detector and embedder model files when they are added.

Required fields:
- model name;
- source URL;
- license;
- checksum;
- version/date;
- local path;
- any usage limitation.

## Generated Gallery Artifacts
Generated gallery artifacts should include a manifest recording:
- dataset name and version/date;
- model stack;
- preprocessing settings;
- image count attempted;
- image count succeeded;
- identity count;
- embedding dimension;
- creation timestamp;
- checksums.

The Work Order 9 sample-gallery builder is intentionally limited to a local CelebA-like sample directory and does not process the full CelebA dataset yet.
The Work Order 10 builder adds local CelebA-root discovery, partition filtering, and quality/performance reporting, but it still relies on user-supplied local data and does not download CelebA.

## Release Wording
Allowed:
- "CelebA-derived research gallery"
- "similarity to CelebA identity IDs"
- "research/demo use"

Avoid unless legally cleared:
- "commercial celebrity recognition"
- "production identity database"
- "verified celebrity identity"

For any pilot or broader release, review [pilot-readiness-checklist.md](pilot-readiness-checklist.md) and [release-notes-rc1.md](release-notes-rc1.md) alongside this document.
