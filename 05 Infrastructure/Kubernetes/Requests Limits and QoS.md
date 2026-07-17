---
type: canonical
domain: infrastructure
topic: kubernetes-resources-qos
status: learning
---

# Requests Limits and QoS

## Problem and mental model

Schedules capacity and constrains container resource consumption to reduce noisy-neighbor and node-pressure risk.

## Internal and end-to-end flow

Scheduler uses requests. CPU limit is enforced as quota/throttling; memory limit is a hard cgroup boundary that can cause OOM. Pod QoS class derives from resource declarations and affects eviction preference, not guaranteed application latency.

## Failure modes and troubleshooting

Correlate user latency with throttled periods, CPU profiles and node saturation. For memory, separate Go heap from RSS/cgroup and node pressure; inspect termination reason and profiles. Requests too low overpack nodes; too high wastes capacity.

## Production choices, security and trade-offs

Right-size from load tests and percentiles; leave memory headroom for non-heap/native/runtime. Verify Go container-aware CPU/memory behavior for the deployed version; link runtime tuning to evidence.

## Interview lens and five-minute revision

Why can low CPU usage coexist with throttling? Request versus limit versus HPA signal? Recall: Schedules capacity and constrains container resource consumption to reduce noisy-neighbor and node-pressure risk.

## Related notes

[[Kubernetes Production Failures]] · [[Linux Memory and Virtual Memory]] · [[Go Garbage Collector]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

