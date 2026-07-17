---
type: canonical
domain: system-design
topic: bottlenecks
status: active
---
# Finding Bottlenecks

## Mental model

A bottleneck is a saturated resource or coordination point on the critical path—not a component that might someday be slow. Use estimates, skew, and service-time distributions to predict the first one; then verify with signals.

## Scan in this order

1. **Amplification:** fan-out, retries, multiple renditions, indexes, replication.
2. **Serialisation:** locks, leader, single allocator, per-key sequence, transaction contention.
3. **Partition skew:** celebrity, hot SKU, city, tenant, conversation, time bucket.
4. **Finite pools:** CPU, memory, DB connections, sockets/file descriptors, provider quota.
5. **Network/bytes:** large objects, cross-region traffic, origin egress.
6. **Queues:** arrival exceeds service rate, oldest age rises, poison work blocks partitions.
7. **Derived reads:** cache miss storms, search fan-out, replica lag.

## Bottleneck statement

“At peak P, component C can safely process Q and key K receives S% of traffic, so C/K saturates first. I will introduce change X, route by partition unit Y, and bound the new risk Z. I expect metric M to improve and will stop scaling when target T holds.”

## Remedies with costs

- cache: lower origin reads; adds staleness, invalidation, memory, stampede;
- shard: more write/storage capacity; adds routing, rebalancing, cross-shard work;
- queue/batch: absorbs bursts and improves throughput; adds lag, duplicates, backlog;
- replica: read/failure capacity; adds lag and failover semantics;
- CDN/object storage: lower origin/egress latency; adds purge/security concerns;
- isolate pools/bulkheads: contains noisy neighbours; fragments capacity;
- shed/admit: protects core work; denies or degrades users;
- precompute: lowers read latency; increases write amplification and freshness lag.

## Hot partitions

Changing to consistent hashing does not fix a single hot key. Options include request coalescing, replicated hot reads, bounded fan-out, sub-sharding with aggregation, splitting by additional dimension, reserved capacity, and product-specific limits. Preserve ordering/invariants during split.

## Queue diagnosis

Depth alone lacks arrival/service context. Observe oldest age, arrival rate, completion rate, retries, expiry, per-key lag, poison count, and time-to-drain. Scaling consumers fails when the downstream dependency is saturated; apply admission/load shedding instead.

## Five-minute revision

Amplification → serial point → skew → finite pools → bytes → backlog → cache/replica lag → first quantified limit → targeted fix → new cost → signal.

Related: [[Latency Throughput and Capacity]] · [[Partitioning and Sharding]] · [[Backpressure and Load Shedding]] · [[Cache Invalidation and Stampede]].

