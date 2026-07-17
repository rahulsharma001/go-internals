> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Replication]].

---
type: canonical
domain: system-design
topic: replication
status: learning
source_conversations:
  - "PostgreSQL for Production Systems | 2026-06-28 | 6a41070b-052c-83ee-bf6b-ceb1d4910e0e"
---
# Replication

## Problem it solves

Replication copies data across failure domains for availability, read scale, locality, and recovery.

## Mental model and how it works

One leader plus followers centralizes write order; followers apply a log synchronously or asynchronously. Multi-leader accepts writes in several regions but requires conflict rules. Leaderless/quorum models coordinate versions across replicas. Replication is not backup: corruption and deletes can replicate.

## Concrete example and dry run

An order write commits on the PostgreSQL primary and streams WAL to replicas. The API returns after the chosen durability threshold. A detail read routed immediately to an async replica may see old state; read-your-writes routes to primary or waits for a version/LSN. If primary fails, a sufficiently current replica is promoted and clients reconnect through a stable endpoint.

## Success and failure scenarios

Success: replica loss does not lose committed data or take down reads. Failure: automatic failover promotes a stale replica; old primary returns and accepts writes (split brain); lag breaks authorization/inventory. Use fencing, consensus/control-plane ownership, lag thresholds, write quiescing, and reconciliation.

## Scaling and production choices

Examples: relational streaming replication, quorum databases, object-storage cross-region replication. Observe apply lag, durable log position, replication errors, read skew, failover time, and recovery point. Test restore separately.

## Trade-offs and when not to use

Synchronous replicas improve durability but add write latency and can reduce availability; async replicas improve latency but allow data loss/staleness. More replicas cost storage/network and do not scale writes. Do not route consistency-critical reads blindly to followers.

## Interview mistakes and follow-ups

Replica equals backup; zero-lag assumption; failover without fencing; “add replicas” for write scaling. Follow-ups: RPO/RTO? replica lag? region loss? promotion? stale reads?

## Five-minute recall

Purpose → topology → sync/async ack → read consistency → failure detection → promotion/fencing → lag/restore tests.

Related: [[Consistency Models]], [[Disaster Recovery]], [[Multi Region Architecture]], [[Partitioning and Sharding]].

## Source metadata

Technical sections from sanitized PostgreSQL source; exact product/version configuration needs verification.
