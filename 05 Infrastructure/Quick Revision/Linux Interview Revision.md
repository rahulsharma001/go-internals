---
type: quick-revision
domain: infrastructure
status: active
---

# Linux Interview Revision

## Process model

Process owns address space/FD table; threads share process state; Go schedules goroutines on OS threads. SIGTERM enables graceful shutdown; SIGKILL does not. PID 1 must receive/forward signals and reap.

## Memory

VSZ ≠ RSS ≠ Go heap. Check RSS/cgroup, live heap/allocation, page faults/reclaim/swap and OOM reason. Container OOM differs from node pressure. Bound caches/queues before raising limits.

## FDs and networking

Files/sockets/pipes are FDs. Leaked HTTP bodies/rows/connections cause `too many open files`. Use `/proc/<pid>/fd`, `lsof`, `ss`. DNS → route → listener → TCP → TLS → HTTP is the debug order.

## CPU and IO

CPU: usage, run queue, throttling, context switches, profile. IO: latency/queue/IO wait/disk/inodes. High utilization can be healthy; queues plus user latency reveal saturation.

## Command ladder

`ps -eLf`; `top -H`; `vmstat 1`; `pidstat`; `iostat -xz 1`; `free`; `df -h`; `df -i`; `ss -s`; `ip route get`; `curl -v`; targeted `strace`/profile with approval.

## Production answer

Scope/time/change → preserve evidence → identify first saturated/failed boundary → reversible mitigation → verify user signal → permanent fix/capacity/runbook.

## Related

[[Linux Production Debugging]] · [[CPU Memory and IO Troubleshooting]]

Return: [[Infrastructure Dashboard]]
