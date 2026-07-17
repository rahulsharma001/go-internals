> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Database Selection Guide]].

---
type: quick-revision
domain: system-design
canonical: "[[Data Storage Selection]]"
---

# Database Selection Guide

## Ask first

Access paths and indexes; transaction/invariant boundary; consistency/read-after-write; write/read rate and hot keys; data size/growth; retention; query flexibility; availability/region; operational maturity.

## Fast mapping

- Relational (PostgreSQL/MySQL): transactions, constraints, joins, evolving business queries. Default for orders/payments/metadata until proven otherwise.
- Key-value: exact-key reads/writes, simple values, predictable horizontal access. Model secondary access explicitly.
- Wide-column: very high key/range write/read workloads with query-first denormalization; avoid ad-hoc joins.
- Document: aggregate-shaped evolving documents; verify transactions/indexes and avoid unbounded documents.
- Search engine: text/relevance/facets; derived index, usually not financial/source-of-truth state.
- Time-series: timestamped metrics with retention/compression and label/tag queries; control cardinality.
- Graph: repeated relationship traversals where relational joins/materialized paths are inadequate.
- Object storage: large immutable blobs, backups, media, lake/archive; metadata belongs elsewhere.
- Cache: acceleration, not automatically truth; define miss and loss behavior.

## Interview answer

“The authoritative invariant is __ and access paths are __, so I choose __. I need indexes __. At scale the first limit is __; I would shard by __ only after __. Derived __ is eventually consistent and rebuildable.”

Traps: choosing by popularity, “NoSQL scales,” missing key/index, storing blobs in row store by default, search/cache as sole truth, sharding before access patterns, no migration/backup.

