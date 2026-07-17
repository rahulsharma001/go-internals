---
type: canonical
domain: infrastructure
topic: realtime-transports
status: learning
---

# WebSocket Polling Webhook and SSE

## Problem and mental model

Selects communication direction and latency/operational model.

## Packet or connection flow

Polling: client repeatedly GETs. Long polling holds until event/timeout. SSE: one HTTP stream server→client with reconnect cursor. WebSocket: HTTP Upgrade then bidirectional frames/heartbeat. Webhook: server POSTs to client endpoint with signature, retry and idempotency.

## Failure modes and senior diagnosis

Diagnose DNS/TCP/TLS/upgrade, proxy idle timeout, heartbeat, close codes, buffers and reconnect cursor. Webhooks need delivery attempts/DLQ; SSE/WebSocket need backpressure and drain.

## Production security, scaling and trade-offs

Polling simplest but wasteful; SSE simple one-way browser stream; WebSocket for bidirectional low latency but stateful operations; webhook for server-to-server callbacks. Never rely on a live socket as durable state.

## Interview questions and five-minute revision

Choose for job progress, chat, payment notification and explain failure recovery. Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[API Gateway WebSockets]] · [[Load Balancing]] · [[Kubernetes Production Failures]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
