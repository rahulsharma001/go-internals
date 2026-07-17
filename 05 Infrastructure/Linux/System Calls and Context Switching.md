---
type: canonical
domain: infrastructure
topic: linux-syscalls-context
status: learning
---

# System Calls and Context Switching

## Problem and mental model

Explains the boundary where user code requests kernel work and where scheduling overhead appears.

## Internal/end-to-end flow

Go call may enter `read/write/epoll/futex` → kernel blocks or completes → scheduler wakes task. Voluntary switch waits; involuntary switch is preemption. Go netpoller avoids one blocked OS thread per idle socket.

## Failure modes and troubleshooting

`strace -c` for syscall mix, `pidstat -w`, `perf`/eBPF only with expertise and approval. High switches can reflect contention/tiny work; D state suggests uninterruptible IO wait.

## Production security, scaling and trade-offs

Batch work, avoid lock contention and excessive tiny goroutines/threads based on profiles. Syscalls and copies have cost, but optimize only measured hot paths.

## Interview questions and five-minute revision

User/kernel mode, syscall, switch and Go scheduler relationship? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Go Scheduler]] · [[TCP Connection Lifecycle]]

## Source metadata

Curated from the networking-focused Go interview extracts and established Linux/Go operational mechanics. Kernel, cgroup and distribution-specific behavior is `needs-verification`.
