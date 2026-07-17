---
type: canonical
domain: infrastructure
topic: docker-volumes
status: learning
---

# Volumes and Persistence

## Problem and mental model

Separates durable/mutable data from disposable container writable layers.

## Internal/end-to-end flow

Named volume is runtime-managed storage mounted into container; bind mount maps a host path; tmpfs is memory-backed. Container replacement preserves an attached volume but does not replicate or back it up.

## Failure modes and troubleshooting

Inspect mounts, ownership/SELinux/AppArmor context, disk/inodes and application fsync/lock errors. A missing mount can make app write silently into ephemeral layer.

## Production security, scaling and trade-offs

Use volumes for local durable data and explicit backup/restore. Bind mounts aid development but couple host layout and permissions. Prefer managed storage for production databases.

## Interview questions and five-minute revision

Volume versus bind mount versus Kubernetes PVC? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[StatefulSets and Persistent Storage]] · [[Linux Production Debugging]]

## Source metadata

Curated from *Docker VPN Subnet Conflict* (2025-01-27, `6797b48a-68b4-8013-a35d-bcc3ed7e533c`) plus Docker official documentation. Runtime/version behavior is `needs-verification`.
