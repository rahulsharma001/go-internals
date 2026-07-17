---
type: canonical
domain: infrastructure
topic: containers-images
status: learning
---

# Containers and Images

## Problem and mental model

Packages a process filesystem/config while sharing the host kernel; an image is immutable content-addressed layers and a container is a runtime instance.

## Internal/end-to-end flow

Build context → Dockerfile/BuildKit → image layers/manifest → registry → runtime pulls by digest → creates namespaces/cgroups/filesystem/network → starts PID 1. Image does not contain a kernel.

## Failure modes and troubleshooting

Inspect image digest/config, container state/exit, runtime logs, mounts, network and cgroups. `docker inspect`; `docker logs`; `docker events`; `docker exec`; `docker stats`. Restarting loses writable-layer state.

## Production security, scaling and trade-offs

Pin digest, minimal runtime, one foreground process, explicit signal handling, non-root/read-only where possible. Containers improve packaging/isolation but are not a VM security boundary.

## Interview questions and five-minute revision

Why does `containerPort`/EXPOSE not publish a port? What does PID 1 need to do? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Docker Layers and Build Cache]] · [[Container Security]] · [[Pods Deployments and ReplicaSets]]

## Source metadata

Curated from *Docker VPN Subnet Conflict* (2025-01-27, `6797b48a-68b4-8013-a35d-bcc3ed7e533c`) plus Docker official documentation. Runtime/version behavior is `needs-verification`.
