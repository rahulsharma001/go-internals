---
type: canonical
domain: system-design
topic: database-and-storage-selection
status: active
last_verified: 2026-07-17
---
# Database and Storage Selection

## 1. Problem it solves

Different state has different invariants and access patterns. One fashionable database rarely fits transactional records, blobs, search, cache, and analytics simultaneously.

## 2. Simple mental model

Choose the authoritative model first, then add derived stores. Ask invariant, access path, key/index, rate/skew, consistency/region, retention, and operations before a product name.

## 3. How it works

Relational stores enforce transactions/constraints; key-value serves exact keys; wide-column supports high partitioned writes/ranges; document stores aggregate documents; search indexes text/geo; object stores large immutable bytes; TSDBs compress time series; caches accelerate.

## 4. Concrete example

Video metadata and processing state use relational/strong records; source/renditions use object storage; search index is derived; CDN caches immutable segments; analytics uses columnar storage.

## 5. Detailed success flow

01. Write commits to one authoritative owner.
11. Outbox/CDC updates derived search/cache/analytics with versions.
21. Queries route to the store designed for their access pattern
31. derived data can rebuild.

## 6. Detailed failure flow

01. Derived search is unavailable.
11. Authoritative create/update still works
21. search degrades explicitly.
31. Rebuild consumes versioned changes/snapshot without becoming a second writer.

## 7. Scaling behaviour

Partition by an access-aligned key; avoid cross-partition invariants; tier hot/cold retention; estimate indexes/replicas/amplification. Operational limits—connections, compaction, repair, shard count—matter.

## 8. Data consistency implications

State which store is truth and each derived view’s freshness. Transaction isolation and conditional updates protect invariants; multi-store dual writes require outbox/repair.

## 9. Real implementation choices

PostgreSQL/MySQL; DynamoDB-like KV; Cassandra-like wide-column; MongoDB document; OpenSearch; S3/GCS; ClickHouse/BigQuery; Redis. These are candidates, not mandatory.

## 10. Trade-offs

Transactions/query flexibility versus distributed write scale; denormalized read speed versus write amplification; managed operations versus control/cost; specialized stores versus system complexity.

## 11. When not to use it

Do not introduce polyglot persistence before a distinct requirement. Do not use cache/search/event log as automatic source of truth.

## 12. Common interview mistakes

“NoSQL scales”; no PK/partition/index; blobs in DB by default; sharding before access paths; no retention/migration/restore; shared ownership; product guarantee assumed.

## 13. How it appears inside larger systems

Every system’s data model and technology choices. See [[Choosing Databases and Storage]] for the interview decision narrative.

## 14. Likely interviewer follow-ups

Which query dominates? What invariant spans rows? Hot key? Cross-shard query? Schema evolution? Delete/backfill? Backup/restore? Region semantics? When switch technologies?

## 15. Five-minute revision

Invariant → access path → authoritative owner → PK/partition/index → rate/skew → consistency/region → retention/operations → derived stores → switch condition.

## 16. Related notes

[[Choosing Databases and Storage]] · [[Blob Object and File Storage]] · [[Search and Geospatial Indexes]] · [[Consistency Models]]

## 17. Verified further reading

- [PostgreSQL concurrency control](https://www.postgresql.org/docs/current/mvcc.html) — official transactional behavior.
- [Amazon S3 user guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/) — official object storage consistency and concepts.

