# T06 MongoDB — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[databases/T06 MongoDB]]
> Q&A bank → [[questions/T06 MongoDB - Interview Questions]]

---

## Recall Grid (answer each, then check)

| # | Prompt | Check |
|---|--------|-------|
| 1 | Embed vs reference (rule of thumb) | Embed: 1:few, read together; reference: 1:many, independent lifecycles |
| 2 | Connection pool (typical) | Per mongod/mongos; e.g. `maxPoolSize` default often 100 |
| 3 | Aggregation pipeline: `$match` | Put `$match` early to use indexes and shrink working set |
| 4 | Compound index | Left-to-right prefix; ESR: equality fields, then sort, then range |
| 5 | 16MB document limit | May require bucketing, arrays with caps, or splitting with references |
| 6 | `bson.D` vs `bson.M` | `D` preserves key order; `M` is unordered map (order can matter in updates/filters) |
| 7 | Write concern | `w: "majority"` for durable replication to majority of data-bearing nodes |
| 8 | Multi-document transactions | Work but add overhead; prefer schema that avoids when possible |
| 9 | Replica set election (ballpark) | Primary loss: failover often on order of ~10–12s (tunable by heartbeat/retry) |

---

## Core Visual

```
  EMBED (1:few, same doc read)                REFERENCE (1:many, own docs)
  ┌─────────────────────────┐                 orders                users
  │ order {                  │                 ┌──────┐              ┌──────┐
  │   _id, userId,           │                 │ _id  │──ObjectId──►│ _id  │
  │   items: [ {...},... ]  │  vs             └──────┘              └──────┘
  │   shipping: { ... }  }  │                 separate collection, join in app
  └─────────────────────────┘
```

---

## Top Interview Questions (quick-fire)

**Q: When do you embed vs reference?**
Embed when data is small, tightly coupled, and always loaded with the parent. Reference when one side is large, unbounded, or queried independently to avoid document bloat and write amplification.

**Q: How do compound index prefix and ESR matter?**
Queries use a left prefix of the index fields. ESR orders fields so equality can prune, one sort can use the index, and range is last. Wrong order can force in-memory sort or full scans on parts of the query.

**Q: When do you avoid multi-document transactions?**
When you can model atomic updates in one document, use idempotent design, or pre-allocate buckets—transactions add latency and require replica set; prefer patterns that keep hot paths single-document or eventually consistent if acceptable.

---

## Verbal Answer (say this out loud)

> "MongoDB schema design is driven by query patterns, not entity relationships. Embed for 1:few always-read-together data; reference for 1:many independent data. Compound indexes follow leftmost prefix rule (ESR: Equality, Sort, Range). Use w:majority for durability. Transactions exist but prefer schema design that avoids them."

---
