# Streaming Design

## Two Meanings of Streaming
This project uses the word streaming in two different ways. They must not be confused.

## 1. OpenAI-Style Response Streaming
The client sends one request. The server streams response chunks back, typically as server-sent events.

Example use case:
- request contains one image;
- server emits progress/result chunks;
- final chunk contains the completed face-similarity result.

Target stage: v0.3 / RC1.

## 2. Live Camera Frame Processing
The browser captures many frames over time and sends them to the backend repeatedly. Each frame receives a result.

Example use case:
- browser captures webcam frame every 200-500 ms;
- sends frame to `/v1/face/similarity`;
- draws boxes and labels on canvas;
- repeats until stopped.

Target stage: v0.4/v0.5.

## MVP Decision
MVP does not require streaming. Implement single-image request/response first.

## RC1 Decision
RC1 should support:
- OpenAI-style `stream=true` response streaming;
- browser live mode using repeated HTTP frame posting.

WebSocket is optional and should be added only if repeated HTTP posting is insufficient.

## WebSocket Revisit Condition
Add WebSocket if:
- browser demo latency is unacceptable with repeated HTTP POST;
- connection setup overhead dominates;
- the UI needs session-level state;
- benchmarks justify the added complexity.
