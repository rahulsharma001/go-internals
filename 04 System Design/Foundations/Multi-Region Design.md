---
type: canonical
domain: system-design
topic: multi-region-design
status: active
last_verified: 2026-07-17
---
# Multi-Region Design

## 1. Problem it solves

Global latency, regional outages, data residency, and disaster recovery require explicit placement and authority. Drawing two regions without write/failover semantics creates hidden split brain.

## 2. Simple mental model

Place users and reads close; keep each invariant under one authority unless operations truly merge. Define home region, replication, failover epoch, RPO/RTO, degraded mode, and failback.

## 3. How it works

Active-passive keeps one writer and warm/ready standby. Active-read uses regional replicas/caches with home writes. Active-active partitions ownership by tenant/key or uses conflict-safe operations. Global traffic routing selects healthy allowed region.

## 4. Concrete example

Payment intents have a home region. Metadata replicates async; failover promotes a standby with a higher epoch after fencing old writers. During uncertain partition, new charges may pause while status reads continue.

## 5. Detailed success flow

Edge routes to home/nearest read; write commits under current epoch; replication advances; health/SLO triggers controlled failover; new authority fences old; recovery reconciles and later fails back deliberately.

## 6. Detailed failure flow

DNS points to region B while A still writes. Without quorum/epoch, both accept same seat/payment. Correct design stops/fences A, promotes B only with known recovery point, surfaces pending, then reconciles.

## 7. Scaling behaviour

Cross-region bandwidth, RTT, replication lag, global indexes, data movement, and failover capacity dominate. Pre-provision/regularly exercise standby. Regional skew and residency constrain routing.

## 8. Data consistency implications

Synchronous cross-region quorum improves RPO/consistency but adds latency and partition unavailability. Async improves locality/availability but accepts lag/loss/conflict. Per-key home regions narrow coordination.

## 9. Real implementation choices

Global DNS/anycast, regional load balancers, PostgreSQL replicas/distributed SQL, Dynamo-style global tables for mergeable state, object replication, Kafka mirroring with explicit ownership.

## 10. Trade-offs

Active-passive is simpler but slower failover/idle cost. Active-active lowers latency but raises conflicts, fencing, operations, and testing. More replicas improve reads but increase cost and stale-read risk.

## 11. When not to use it

Do not add multi-region when requirements need only multi-zone and restore. Complexity can reduce reliability.

## 12. Common interview mistakes

No write authority; DNS as correctness; RPO/RTO invented; failover but no failback; replica lag ignored; global strong consistency claimed free; data residency omitted.

## 13. How it appears inside larger systems

Payments, booking, chat, file sync, video playback, global API gateway, and monitoring. Soft state may rebuild; ledgers need stricter recovery.

## 14. Likely interviewer follow-ups

Who writes during partition? How fence old region? RPO/RTO? What remains available? How reconcile? Failback? residency? region capacity? global unique IDs?

## 15. Five-minute revision

Reason: latency/outage/residency. Choose topology, home/owner, replication/ack, epoch/fence, degraded mode, RPO/RTO, restore/reconcile/failback. Multi-zone first.

## 16. Related notes

[[CAP and PACELC]] · [[Replication]] · [[Leader Election]] · [[Reliability and Failure Analysis]]

## 17. Verified further reading

- [Google Cloud reliability framework](https://cloud.google.com/architecture/framework/reliability) — official failure-domain and reliability guidance.\n- [AWS disaster recovery guidance](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) — official RPO/RTO and strategy overview.

