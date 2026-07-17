---
type: canonical
domain: infrastructure
topic: linux-file-descriptors
status: learning
---

# File Descriptors

## Problem and mental model

Unifies files, sockets, pipes and event handles behind per-process integer references.

## Internal/end-to-end flow

`open/socket/accept` allocates FD → Go netpoller registers readiness → handler reads/writes → close returns FD. Limits exist per process/system; leaked bodies/connections/files exhaust them.

## Failure modes and troubleshooting

`ulimit -n`; `ls /proc/<pid>/fd`; `lsof -p`; `ss -s`; process `open_fds` metric. `too many open files` with rising TCP states often means leak or connection storm.

## Production security, scaling and trade-offs

Close HTTP response bodies/rows/files, bound clients/connections, set idle timeouts, monitor headroom and tune limits only after lifecycle correctness.

## Interview questions and five-minute revision

How does an HTTP response-body leak become FD exhaustion? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Connection Pooling]] · [[TCP Connection Lifecycle]] · [[Gin HTTP Services]]

## Source metadata

Curated from the networking-focused Go interview extracts and established Linux/Go operational mechanics. Kernel, cgroup and distribution-specific behavior is `needs-verification`.
