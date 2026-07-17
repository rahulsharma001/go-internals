---
type: canonical
domain: infrastructure
topic: linux-memory
status: learning
---

# Linux Memory and Virtual Memory

## Problem and mental model

Maps process addresses to physical/page-cache/swap/cgroup resources and explains OOM.

## Internal/end-to-end flow

Virtual mappings → page faults → anonymous/file-backed pages → page cache/reclaim → cgroup/node pressure → OOM decision. RSS, Go heap and virtual size differ; memory-mapped files and native allocations matter.

## Failure modes and troubleshooting

`free -m`; `vmstat 1`; `cat /proc/<pid>/smaps_rollup`; `pmap`; `dmesg`/journal OOM; cgroup events. Correlate RSS, page faults, swap/reclaim, Go heap/profile and workload.

## Production security, scaling and trade-offs

Set container memory with headroom, bound caches/queues, profile retention, avoid swap assumptions, and protect nodes. More cache can improve IO while raising RSS.

## Interview questions and five-minute revision

Why can VSZ be huge but RSS safe? Container OOM versus node eviction? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Go Garbage Collector]] · [[Requests Limits and QoS]]

## Source metadata

Curated from the networking-focused Go interview extracts and established Linux/Go operational mechanics. Kernel, cgroup and distribution-specific behavior is `needs-verification`.
