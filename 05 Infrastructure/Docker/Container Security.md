---
type: canonical
domain: infrastructure
topic: container-security
status: learning
---

# Container Security

## Problem and mental model

Reduces image supply-chain and runtime blast radius.

## Internal/end-to-end flow

Trusted source → pinned dependencies/base → reproducible build/SBOM/sign → registry policy → runtime verifies → non-root process with minimal capabilities, seccomp and read-only filesystem → scoped network/secrets.

## Failure modes and troubleshooting

Scan findings require reachability/version/context. Inspect effective user/capabilities/mounts, image provenance and secret exposure. Never copy build tokens or Docker socket into image.

## Production security, scaling and trade-offs

Patch rebuilds, rootless where suitable, drop capabilities, no privileged mode, resource/PID limits, immutable deployment and workload identity. Minimal image complicates live debugging.

## Interview questions and five-minute revision

Why is non-root insufficient by itself? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[RBAC and Service Accounts]] · [[Network Policies]] · [[ConfigMaps Secrets and Configuration]]

## Source metadata

Curated from *Docker VPN Subnet Conflict* (2025-01-27, `6797b48a-68b4-8013-a35d-bcc3ed7e533c`) plus Docker official documentation. Runtime/version behavior is `needs-verification`.
