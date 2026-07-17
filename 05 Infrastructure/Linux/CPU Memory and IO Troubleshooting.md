---
type: canonical
domain: infrastructure
topic: linux-cpu-memory-io
status: learning
---

# CPU Memory and IO Troubleshooting

## Problem and mental model

Diagnoses saturation by resource and queue rather than blaming high utilization alone.

## Internal/end-to-end flow

CPU: run queue/user/system/steal/throttle. Memory: RSS/reclaim/fault/swap/OOM. IO: latency/queue depth/IO wait/device saturation/filesystem. Application queues/pools connect resource pressure to user latency.

## Failure modes and troubleshooting

`uptime`; `vmstat 1`; `pidstat`; `iostat -xz 1`; `free`; `df -h`; `df -i`; `top`; cgroup stats; Go pprof. Compare healthy host/Pod and incident onset.

## Production security, scaling and trade-offs

Mitigate protected bottleneck: shed/scale/rollback/free disk. Permanent fix comes from profile/query/IO evidence and capacity model. More replicas can overload shared storage.

## Interview questions and five-minute revision

Why can 100% CPU be healthy but 20% CPU be slow? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Kubernetes Production Failures]] · [[Incident Investigation]]

## Source metadata

Curated from the networking-focused Go interview extracts and established Linux/Go operational mechanics. Kernel, cgroup and distribution-specific behavior is `needs-verification`.
