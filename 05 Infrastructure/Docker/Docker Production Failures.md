---
type: canonical
domain: infrastructure
topic: docker-production-failures
status: learning
---

# Docker Production Failures

## Problem and mental model

Provides a hop-first runbook for container-specific incidents.

## Internal/end-to-end flow

Symptom → image/start command → process/signal → cgroup resources → filesystem/mount → DNS/route/port → dependency. Preserve exit reason and previous logs before recreation.

## Failure modes and troubleshooting

Common cases: exit 137/OOM, CrashLoop from missing env, app bound localhost, permission denied on non-root volume, disk full, architecture mismatch, VPN subnet overlap, TLS CA absent. Use `inspect`, `logs`, `events`, `stats`, `network inspect`, `df -i`, `ss`.

## Production security, scaling and trade-offs

Mitigate by rollback/cap/load shed/route correction; permanently fix build contract, health check, bounds and address planning. Adding privileged mode or unlimited resources hides root cause.

## Interview questions and five-minute revision

Contrast image failure, runtime failure and application failure. Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Kubernetes Production Failures]] · [[CPU Memory and IO Troubleshooting]] · [[Network Troubleshooting]]

## Source metadata

Curated from *Docker VPN Subnet Conflict* (2025-01-27, `6797b48a-68b4-8013-a35d-bcc3ed7e533c`) plus Docker official documentation. Runtime/version behavior is `needs-verification`.
