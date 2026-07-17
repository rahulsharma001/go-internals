---
type: canonical
domain: infrastructure
topic: docker-layers-cache
status: learning
---

# Docker Layers and Build Cache

## Problem and mental model

Speeds reproducible builds by reusing unchanged filesystem/instruction results.

## Internal/end-to-end flow

Each Dockerfile instruction can produce a layer/cache key. Copy dependency manifests and download modules before copying frequently changing source; `.dockerignore` shrinks context; BuildKit cache mounts/external cache accelerate ephemeral CI.

## Failure modes and troubleshooting

Use `docker build --progress=plain`; inspect which step misses cache. Changing an early `COPY . .` invalidates all later work; mutable base tags make identical Dockerfiles differ over time.

## Production security, scaling and trade-offs

Cache is an optimization, not provenance. Pin/refresh base digest deliberately, isolate secrets with secret mounts, never bake credentials, and rebuild for patched bases.

## Interview questions and five-minute revision

Why order `COPY go.mod go.sum` before source? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Multi Stage Builds for Go]] · [[Container Security]]

## Source metadata

Curated from *Docker VPN Subnet Conflict* (2025-01-27, `6797b48a-68b4-8013-a35d-bcc3ed7e533c`) plus Docker official documentation. Runtime/version behavior is `needs-verification`.
