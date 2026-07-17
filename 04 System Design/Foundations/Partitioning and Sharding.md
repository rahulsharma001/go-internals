---
type: canonical
domain: system-design
topic: partitioning-and-sharding
status: active
last_verified: 2026-07-17
---
# Partitioning and Sharding

## 1. Problem it solves

One node cannot own unlimited writes, data, connections, or per-key computation. Partitioning divides ownership so work and state can scale independently.

## 2. Simple mental model

Choose a partition unit, key-to-owner routing, and movement protocol. A good key distributes load while keeping invariant-bound operations together. Sharding is horizontal data partitioning; every shard is a failure and operations boundary.

## 3. How it works

Hash partitioning spreads keys; range partitioning supports ordered scans but can hotspot; directory routing maps keys explicitly; composite keys balance and preserve query locality. Maintain metadata, replicas, and rebalancing with versioned routing.

## 4. Concrete example

Chat messages partition by `conversation_id` so per-conversation ordering stays local. A time-series system partitions by tenant plus series hash; time alone would hotspot the newest range.

## 5. Detailed success flow

01. Router derives the logical shard from the operation's ownership key and reads its current routing epoch.
11. The current owner performs the key-local read or invariant-changing write and replicates according to policy.
21. During movement, a new owner copies a snapshot and catches up the shard change log without accepting stale-epoch writes.
31. Routing switches atomically by version
41. only after validation and a grace period is old state removed.

## 6. Detailed failure flow

01. A hot celebrity key overloads one shard while fleet average is low.
11. Add hot-read replicas, request coalescing, key sub-shards with aggregation, or product limits
21. adding ordinary shards alone does not split that key.

## 7. Scaling behaviour

Account for skew, per-shard overhead, rebalancing bandwidth, cross-shard queries, indexes, and operational limits. Pre-split/bucket monotonic keys. Plan shard count larger than node count so ownership can move.

## 8. Data consistency implications

Single-partition transactions/order are simpler. Cross-partition invariants require coordination, saga, or remodel. Stale routing must be rejected/redirected with versions/epochs.

## 9. Real implementation choices

Application sharding on PostgreSQL; DynamoDB/Cassandra native partitions; Kafka topic partitions; consistent/rendezvous hashing for cache ownership; range partitions for ordered/time data.

## 10. Trade-offs

Hash balances but loses range locality; range preserves scans but hotspots; more shards improve balance/mobility but add metadata/connection/repair cost; denormalization avoids joins but amplifies writes.

## 11. When not to use it

Do not shard before a measured/estimated single-owner limit. Vertical scale and indexing may be simpler.

## 12. Common interview mistakes

No access paths; random key breaking invariants; assuming uniform hash fixes hot key; no rebalance; cross-shard list query; shard count tied one-to-one to machines.

## 13. How it appears inside larger systems

Feeds by user, chat by conversation, events by aggregate, geo by region/cell, TSDB by tenant/series, cache by key.

## 14. Likely interviewer follow-ups

What is the partition unit? Which queries cross shards? What is hottest key? How rebalance without double writes? How recover one shard? How split a key?

## 15. Five-minute revision

Unit/key → routing → local invariant → skew → replica → rebalance with version → cross-shard cost. More nodes do not solve one hot key.

## 16. Related notes

[[Consistent Hashing]] · [[Replication]] · [[Finding Bottlenecks]] · [[Consistent Hashing Pattern]]

## 17. Verified further reading

- [DynamoDB condition expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.OperatorsAndFunctions.html) — official per-item conditional update mechanics.
- [Apache Kafka design](https://kafka.apache.org/documentation/#design) — official partitioned-log concepts.
