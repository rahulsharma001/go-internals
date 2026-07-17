---
type: quick-revision
domain: infrastructure
status: active
---

# Docker Interview Revision

## Model

Image = immutable content-addressed layers/manifest. Container = process plus namespaces, cgroups, mounts and network using host kernel. Writable layer is disposable.

## Build

Order stable dependency steps first; small `.dockerignore`; multi-stage builder/test → minimal non-root runtime. Pin/refresh base digest, use secret mounts, produce SBOM/signature. For Go, confirm CGO/CA/time-zone and target architecture.

## Runtime

Bridge creates veth/bridge/NAT; published port forwards host traffic; app must listen on correct address. Volume persists beyond container; bind mount couples host path; tmpfs is ephemeral memory.

## Failure ladder

Image/digest/architecture → command/PID1/signal → env/config → user/permissions/mount → CPU/memory/PID → port/DNS/route/VPN overlap → dependency. Preserve inspect/events/exit/previous logs before recreation.

## Security

Trusted image, minimal packages, non-root, drop capabilities, read-only FS, seccomp, no Docker socket/privileged mode, workload identity and bounded resources. Container is not a VM boundary.

## Commands

`docker inspect`; `logs`; `events`; `stats`; `network inspect`; `exec`; host `ss`/`ip route`. Restart is mitigation only when root cause and recurrence are addressed.

## Related

[[Containers and Images]] · [[Docker Production Failures]]

Return: [[Infrastructure Dashboard]]
