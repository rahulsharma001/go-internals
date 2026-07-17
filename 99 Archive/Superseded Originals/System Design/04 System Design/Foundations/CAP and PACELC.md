> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[CAP and PACELC]].

---
type: canonical
domain: system-design
topic: cap-pacelc
status: learning
---
# CAP and PACELC

## Problem it solves

CAP frames behavior during a network partition; PACELC adds the normal-operation latency-versus-consistency choice.

## Mental model and how it works

During a partition, a replicated system cannot both make every request succeed and guarantee one consistent value. It chooses consistency (reject/delay conflicting operations) or availability (accept operations that may diverge). Partition tolerance is not an optional product checkbox in distributed deployments. PACELC asks: if partitioned, A or C; else, lower latency or stronger consistency.

## Concrete example and dry run

Two regions own the same driver assignment. The link fails. If both accept assignment writes, one driver may receive two rides: available but inconsistent. If only the lease/consensus owner accepts and the other rejects, ownership stays consistent but some requests fail. For driver location display, both regions may accept updates and reconcile because stale/divergent location is tolerable.

## Success and failure scenarios

Success: choices are per operation, not one label for the whole company. Failure: “the system is AP” while payment capture actually requires a single owner. Document partition response, timeout, conflict resolution, and user behavior.

## Scaling and production choices

Consensus systems, conditional writes, quorum reads/writes, regional ownership, and asynchronous replicas implement different points. Quorums do not automatically guarantee linearizability; definitions and failure assumptions matter.

## Trade-offs and when not to use

CAP is not a database-selection shortcut and says little about normal latency, durability, isolation, cost, or failure detection. Use it only after defining the operation and partition.

## Interview mistakes and follow-ups

Choosing two of three at all times; treating partition tolerance as optional; applying one CAP label to all paths. Follow-ups: which operations reject? how detect partition? split-brain repair? regional owner unavailable?

## Five-minute recall

Partition: consistent or available for this operation. Else: stronger coordination or lower latency. State user-visible consequence.

Related: [[Consistency Models]], [[Multi Region Architecture]], [[Leader Election]].

## Source metadata

Curated foundation; no project claim. Technology behavior requires product-specific verification.
