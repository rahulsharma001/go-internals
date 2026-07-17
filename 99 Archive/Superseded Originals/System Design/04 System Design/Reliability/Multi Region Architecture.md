> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Multi-Region Design]].

---
status: learning
type: canonical
area: system-design
sources:
  - "Curated system-design synthesis"
---

# Multi Region Architecture

## Problem it solves

Users need low latency and service must tolerate regional failure, data-residency constraints, or both.

## Mental model

Regions are independent failure cells. Decide where each entity is written, how authority moves, and what consistency is sacrificed across distance.

## How it works

Common models: active-passive, active-active with home-region/single writer, or multi-writer with explicit conflict resolution. Global routing chooses healthy regions; data replicates asynchronously or synchronously according to invariant; epochs/fencing protect authority transfer.

## Concrete example and detailed dry run

An active trip is homed to region A with epoch 12. A fails; failover policy verifies loss, advances ownership in region B to epoch 13, and routes new commands there. A late epoch-12 command is rejected. Some recent location soft state may be rebuilt, while durable trip/payment records follow the agreed replication RPO.

## Success scenario

Regional failure moves or sheds traffic without double ownership; critical data meets its recovery objective; clients reconnect and receive authoritative state.

## Failure scenario

Network partition leaves both regions accepting the same entity. Without home-region routing, quorum, or fencing, divergent writes occur. Resolution may require domain-specific merge/compensation rather than last-write-wins.

## Scaling considerations

Keep most traffic/data regional, partition ownership by tenant/entity, control cross-region egress, pre-provision failover capacity, test global routing and dependency readiness, and prevent thundering reconnect/replay.

## Production technology choices

Global DNS/anycast/load balancing; regional clusters; database read replicas or globally distributed databases; Kafka mirroring/event replication; object replication. Exact consistency/failover semantics require current official verification.

## Trade-offs

Active-passive is simpler but wastes/warms capacity and has failover delay. Active-active improves latency/utilization but magnifies consistency, operations, cost, and testing. Synchronous cross-region writes protect RPO but add WAN latency and quorum availability constraints.

## When not to use it

Avoid multi-region when one region plus multi-zone HA meets objectives, the team cannot operate/test it, or data sovereignty and conflict semantics are unresolved.

## Common interview mistakes

Drawing two regions without write authority; assuming DNS failover is instant; ignoring dependencies/data; no split-brain fencing; no failback plan.

## Interview questions and follow-ups

Where does each entity write? What happens during partition? What data can be lost? Is failover automatic? How is capacity and failback tested?

## Five-minute recall

Define goal → choose active/passive or active/active → assign write authority → replication/consistency → health/routing → fencing → capacity → reconciliation/failback.

## Related notes

[[Disaster Recovery]] · [[Consistency Models]] · [[Replication]] · [[Leader Election]] · [[CAP and PACELC]]

## Source metadata

Curated interview synthesis. Region, residency, RPO/RTO, and vendor behavior are `status: needs-verification`.
