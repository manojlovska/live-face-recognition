# Benchmark Plan

## Purpose
Benchmarking supports CPU-only performance claims. Benchmark numbers must be measured and reproducible.

## Metrics
Measure:
- service startup time;
- model load time;
- gallery load time;
- image decode time;
- face detection latency;
- alignment/embedding latency;
- gallery search latency;
- full native request latency;
- full OpenAI-compatible request latency;
- repeated-frame average latency;
- memory usage after startup;
- maximum tested image size.

## Environments
Each benchmark result must record:
- CPU model;
- RAM;
- operating system;
- Python version;
- model versions;
- gallery version;
- image size;
- request count;
- concurrency setting.

## Suggested Targets for RC1
Targets must be confirmed by measurement. Initial desired direction:
- single-image request usable interactively on CPU;
- browser demo throttled to a realistic frame rate;
- no model reload per request;
- no gallery rebuild at runtime.

## Benchmark Command
A future script should provide:

```bash
python scripts/benchmark.py --image tests/fixtures/face.jpg --requests 50
```

## Rule
Do not place guessed numbers in `benchmark-results.md`.
