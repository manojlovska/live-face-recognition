# Benchmark Plan

## Purpose
Benchmarking supports CPU-only performance claims. Numbers must be measured and reproducible.

## Current Tooling
The repository now includes `scripts/benchmark_api.py` for local sequential benchmarking against a running service.

## Targets
Supported benchmark targets:
- `native`
- `chat`
- `chat-stream`
- `all`

## Design
- Benchmarks are local-only and sequential by default.
- The default image is a generated tiny data URL.
- An optional `--image-file` path may replace the generated image.
- Warmup requests are run before recorded requests.
- Concurrency and load testing are intentionally out of scope.

## Metrics Collected
Per target, record:
- wall-clock latency per recorded request;
- `min`, `mean`, `median`, `p95`, and `max` latency;
- status-code counts;
- result-mode counts;
- for `chat-stream`, time to first SSE chunk when practical;
- notes about ready vs not-ready responses.

## Interpretation
- `engine_not_ready` is a valid local not-ready outcome and should still produce a useful report.
- Any invalid response shape, unexpected status code, or request failure is a broken benchmark run.
- The scripts must not store API keys or image payloads in reports.

## Limitations
- No concurrent benchmarking.
- No production load testing.
- No distributed benchmarking.
- No memory profiler.
- No browser automation.

## Rule
Do not place guessed numbers in `benchmark-results.md`.
Record only measured runs and keep the result template in sync with the pilot checklist.
