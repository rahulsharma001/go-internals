---
type: canonical
domain: infrastructure
topic: linux-production-debugging
status: learning
---

# Linux Production Debugging

## Problem and mental model

Provides an evidence-preserving sequence for a failing host/container.

## Internal/end-to-end flow

Scope/time/change → service/process state → resource saturation → listener/DNS/route/TLS → dependency → logs/traces → targeted profile/capture. Compare across replica/node/version.

## Failure modes and troubleshooting

Commands: `systemctl status`/journal where applicable, `ps`, `ss`, `vmstat`, `iostat`, `df -i`, `ip route get`, `curl -v`. Do not restart before collecting exit/OOM/event/log evidence unless user safety requires it.

## Production security, scaling and trade-offs

Use least privilege, immutable repair/replacement, runbooks and post-incident prevention. Live patching creates drift; emergency change must be recorded and reconciled.

## Interview questions and five-minute revision

What evidence do you preserve before restart? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Incident Investigation]] · [[Network Troubleshooting]] · [[Docker Production Failures]]

## Source metadata

Curated from the networking-focused Go interview extracts and established Linux/Go operational mechanics. Kernel, cgroup and distribution-specific behavior is `needs-verification`.
