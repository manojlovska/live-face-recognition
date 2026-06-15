# ADR-0001: CPU-Only Inference

## Status
Accepted

## Context
The project must run without a GPU. The human lead explicitly requires CPU-only operation. The first release should be usable on ordinary machines and in simple deployment environments.

## Decision
The project will be CPU-only for MVP and RC1. Implementation must not require CUDA, GPU drivers, GPU-only packages, or GPU-specific model execution.

## Consequences
- Use lightweight CPU-capable models.
- Benchmark on CPU.
- Avoid GPU-only dependencies.
- Keep image sizes and frame rates realistic.
- Prefer offline precomputed gallery artifacts.

## Revisit Condition
This decision may be revisited after RC1 if there is a separate GPU deployment target. CPU support must remain available unless explicitly retired by a later ADR.
