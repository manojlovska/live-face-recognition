# Project Brief

## Working Name
CelebA Face Similarity API

## One-Sentence Description
A CPU-only, OpenAI-compatible web service that receives face images and returns the most similar identities from a precomputed CelebA-derived embedding gallery.

## Product Goal
The project aims to provide a professional, test-backed API for face-similarity experiments. Users should be able to call the service with the OpenAI Python client by setting a custom `base_url`, API key, and model name.

The service should detect faces, align them, compute embeddings, search a CelebA-derived gallery, and return ranked similarity results.

## Intended Users
- Computer vision researchers
- Instructors and workshop participants
- Internal demos and controlled pilots
- Developers who want an OpenAI-compatible API surface for non-LLM vision inference

## Human Product Owner
The human lead is the domain expert and release authority. The strategic AI may advise; the execution agent may implement; release responsibility remains with the human/organization.

## Core Constraints
- CPU-only operation; no GPU required.
- One API key in MVP/RC1.
- OpenAI-compatible API surface.
- CelebA-derived gallery for similarity search.
- No user image retention by default.
- No user embedding retention by default.
- No verified identity claim.
- No commercial CelebA claim without legal review.

## Product Promise
A caller can send an image through an OpenAI-style or native endpoint and receive a structured result containing detected faces and top-k similar CelebA identities.

## Non-Promise
This project does not promise to identify a person, authenticate identity, verify a celebrity match, or operate as a production biometric identification system.

## First Release Language
Use: "CPU-only research/demo face-similarity service."

Avoid: "production celebrity recognition" or "identity verification."
