# ADR-0003: YuNet and SFace Model Stack

## Status
Accepted for initial implementation

## Context
The project needs a lightweight CPU-friendly face detector and face embedding model. A face-specific detector is preferred over a general object detector.

## Decision
Use OpenCV YuNet for face detection and OpenCV SFace for face alignment/embedding in the initial implementation.

## Consequences
- The service can remain lightweight and CPU-first.
- Face landmarks are available for alignment.
- The model stack is simple enough for a professional MVP.
- Alternative stacks such as InsightFace, YOLO-based detectors, or custom training are postponed.

## Revisit Condition
Revisit if benchmarks show unacceptable accuracy or latency, or if licensing/deployment constraints require a different model stack.
