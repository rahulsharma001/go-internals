> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Partitioning and Sharding]].

---
type: canonical
domain: system-design
topic: partitioning-sharding
status: learning
source_conversations:
  - "System Design Patterns | 2026-07-05 | 6a4aa703-f2d8-83ee-aac3-020aa67e9afb"
---
# Partitioning and Sharding

## Problem it solves

Partitioning divides data/work so storage, throughput, or parallelism exceed one node’s limit. Sharding usually means partitions placed across independent database nodes.

## Mental model and how it works

Choose a key that keeps required operations local and distributes load. Hash partitioning balances random keys; range partitioning supports ordered scans but risks hot ranges; geographic/tenant partitioning isolates locality but can skew. Maintain routing metadata and an online split/move process.

## Concrete example and dry run

Ride locations partition by city then geospatial cell. Delhi traffic stays local to matching workers. A stadium cell becomes hot, so split it into finer cells or salt write partitions while preserving a query fan-out boundary. Durable rides may shard by region plus hashed ride ID; cross-region history is served by a separate view.

## Success and failure scenarios

Success: most requests touch one shard and load is balanced. Failure: celebrity/large tenant overloads one shard; scatter-gather amplifies tail latency; resharding blocks writes. Use hot-key detection, adaptive splitting, capacity-aware placement, bounded fan-out, and dual-read/write migration with reconciliation.

## Scaling and production choices

PostgreSQL/MySQL application sharding, DynamoDB/Cassandra-style managed partitioning, Kafka partitions, and search shards have different semantics. Observe per-partition QPS/bytes/latency, storage skew, rebalances, hot keys, and cross-shard operation rate.

## Trade-offs and when not to use

Sharding complicates joins, unique constraints, transactions, migrations, backups, and operations. First optimize schema/indexes, archive data, add replicas for reads, and verify one primary is truly limiting.

## Interview mistakes and follow-ups

“Shard by user” without access patterns; no reshard plan; global secondary index ignored; partition count fixed forever. Follow-ups: largest tenant? range scan? unique email? cross-shard transaction? shard loss?

## Five-minute recall

Access patterns/invariant → key/strategy → routing → hotspot → reshard → cross-shard cost → metrics.

Related: [[Consistent Hashing]], [[Replication]], [[Data Storage Selection]], [[Uber System Design]].

## Source metadata

Generic concepts curated from the sanitized source; examples are illustrative.
