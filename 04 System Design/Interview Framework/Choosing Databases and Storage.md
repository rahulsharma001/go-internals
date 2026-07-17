---
type: canonical
domain: system-design
topic: storage-choice
status: active
---
# Choosing Databases and Storage

## Decision order

Choose semantics before product: invariant/transaction boundary → access patterns → key/index → growth/write rate/skew → consistency/regions → retention → operational capability. Start with the simplest store that satisfies the invariant.

## Fast comparison

| Need | Candidate | Why | Main cost |
| --- | --- | --- | --- |
| multi-row constraints, evolving queries | PostgreSQL/MySQL | transactions, uniqueness, joins | write scaling/connection coordination |
| exact-key access at large scale | DynamoDB-like key-value | predictable partitioned access | query rigidity/hot keys |
| high write and key/range scans | Cassandra-like wide-column | partitioned throughput | denormalization/repair/consistency choices |
| aggregate documents | document store | flexible aggregate shape | unbounded documents/cross-aggregate constraints |
| text, facets, geospatial retrieval | OpenSearch/Elasticsearch | inverted and geo indexes | derived index lag/operations |
| large immutable bytes | S3/GCS-like object store | durability, cheap scale, multipart | not relational query/low-latency small mutation |
| hot ephemeral values | Redis/Memcached | low-latency in-memory access | memory cost, eviction, consistency |
| metrics/time windows | TSDB | compression and time-range queries | cardinality and specialized operations |

The exact product is optional; the key, source of truth, and failure behavior are not.

## Decision narrative

“Booking confirmation needs a uniqueness constraint across `(event_id,seat_id)` and a transaction with the booking state, so PostgreSQL is the initial source of truth. Search uses OpenSearch as a derived index and may lag. At write scale, I partition events by `event_id`; a key-value alternative wins when access is exact-key, joins disappear, and operational scale justifies it.”

## Replication, sharding, and migration

Do not treat them as properties automatically supplied by a database. Define leader/follower or leaderless behavior, read consistency, failover, partition key, hot-key mitigation, resharding, backups, restore, schema migration, and reconciliation.

## When technologies change

- global strict transactions may justify a distributed SQL system and higher latency/cost;
- predictable exact-key access may justify DynamoDB over relational sharding;
- long retention with rare access moves to object/archive tiers;
- flexible text/geo queries add a derived search index, not replace truth;
- operational team maturity may outweigh theoretical fit.

## Mistakes and follow-ups

“NoSQL scales,” blobs in a row store by default, cache/search as truth, no index, random shard key, ignoring skew/retention, and multi-region without write semantics. Follow-ups: replica lag, hot tenant, cross-shard transaction, backup restore, data deletion, schema evolution, and cost.

## Five-minute revision

Invariant → transactions → access paths → PK/partition/index → size/rate/skew → consistency/region → retention → operations → alternative and switch condition.

Canonical depth: [[Database and Storage Selection]] · [[Blob Object and File Storage]] · [[Search and Geospatial Indexes]] · [[Database Selection Guide]].

