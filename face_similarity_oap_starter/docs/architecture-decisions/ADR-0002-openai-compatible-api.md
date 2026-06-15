# ADR-0002: OpenAI-Compatible API Surface

## Status
Accepted

## Context
The service should be callable with OpenAI-style clients and examples. The goal is compatibility for developer ergonomics, not general LLM behavior.

## Decision
The project will expose `/v1/models` and `/v1/chat/completions` for MVP. The OpenAI-compatible endpoint will accept supported image-containing requests and return face-similarity results wrapped in an assistant response.

## Consequences
- OpenAI compatibility must be documented and tested.
- Unsupported OpenAI features must return clear structured errors.
- The native API remains the canonical internal face-similarity contract.
- The service must not pretend to be a general-purpose text-generation model.

## Revisit Condition
Add `/v1/responses` after the chat-completions path is stable, if needed for modern OpenAI-style compatibility.
