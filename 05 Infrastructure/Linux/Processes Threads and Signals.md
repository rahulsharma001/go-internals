---
type: canonical
domain: infrastructure
topic: linux-processes-signals
status: learning
---

# Processes Threads and Signals

## Problem and mental model

Explains execution units and controlled service lifecycle.

## Internal/end-to-end flow

Process owns virtual address space/FD table; threads share process resources and are scheduled tasks. Go runtime multiplexes goroutines onto OS threads. SIGTERM requests graceful stop; SIGKILL cannot be handled; PID 1/container signal forwarding/reaping matters.

## Failure modes and troubleshooting

`ps -eLf`; `top -H`; `cat /proc/<pid>/status`; `kill -TERM`; `strace -p` with approval. Diagnose state (R/S/D/Z), thread/goroutine growth and blocked syscalls. Preserve stack/profile evidence.

## Production security, scaling and trade-offs

Go should handle SIGTERM with `signal.NotifyContext`, fail readiness, call `http.Server.Shutdown` with deadline, stop accepting jobs and exit. Avoid unbounded grace.

## Interview questions and five-minute revision

Process vs thread vs goroutine; why SIGKILL prevents cleanup? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Goroutines and Lifecycle]] · [[Rolling Deployments and Rollbacks]]

## Source metadata

Curated from the networking-focused Go interview extracts and established Linux/Go operational mechanics. Kernel, cgroup and distribution-specific behavior is `needs-verification`.
