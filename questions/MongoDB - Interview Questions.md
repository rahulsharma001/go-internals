# MongoDB -- Interview Questions

> Comprehensive interview Q&A bank for [[databases/MongoDB]].
> Sorted by frequency at top tech companies. Tags: [COMMON] [ADVANCED] [TRICKY]

---

## Q1: Explain embedding vs referencing in MongoDB. When do you use each? [COMMON]

**Answer:**

**In one line:** Use embedding when related data is small, bounded, and always read together, and use referencing when the relationship is 1:many, independent access, or unbounded growth would threaten the 16MB document cap.

**Visualize it:**

```
EMBED (1:few, "always together")
┌─────────────────────────────────────┐
│ User document                        │
│  _id, name,                        │
│  shippingAddresses: [               │  ← nested array, bounded
│    { street, city, zip },         │
│    { ... }                          │
│  ]                                  │
└─────────────────────────────────────┘

REFER (1:many, independent access)
┌──────────────┐         ┌────────────────────┐
│ User         │  userId │ Order              │
│  _id         │────────>│  _id, userId, ...   │
│  name        │  (FK)   │  (many rows)       │
└──────────────┘         └────────────────────┘
```

**Key facts:**
- Embedding places related data inside a single document; referencing stores the relationship as an ID pointing to another collection.
- Embed when data is always read together (1:few), you need atomic writes on the group, and the embedded array is bounded.
- Reference when data is accessed independently, the relationship is 1:many or many:many, related data is shared across documents, or the array could grow unboundedly and risk the 16MB limit.
- The decision is driven by query patterns, not entity relationships.

**Interview tip:** The interviewer wants to hear you reason about access patterns, not just recite rules. Give a concrete example: "For a user's shipping addresses (1:few, always loaded with user) I'd embed. For a user's order history (1:many, accessed independently, grows forever) I'd reference."

> [!example]- Full Story: Embedding vs referencing
>
> **The problem:** Relational thinking maps poorly to document stores: a single "correct" ER model does not tell you where data should live, because read/write paths and growth characteristics differ per product.
>
> **How it works:** Embedding places related data inside a single document. Referencing stores the relationship as an ID pointing to another collection. Embed when: data is always read together (1:few relationship), you need atomic writes on the group, and the embedded array is bounded. Reference when: data is accessed independently, the relationship is 1:many or many:many, the related data is shared across documents, or the array could grow unboundedly (risk hitting 16MB limit). The decision is driven by query patterns, not entity relationships.
>
> **What to watch out for:** Unbounded arrays embedded in a parent document: they can bloat the document, increase replication and cache pressure, and eventually hit the 16MB per-document cap. Shifting from embed to ref later can be a heavy migration, so you size and access-pattern the relationship up front.

---

## Q2: How does the mongo-go-driver handle connection pooling? [COMMON]

**Answer:**

**In one line:** A single `mongo.Client` is thread-safe, builds a per-server connection pool (default 100, lazy, reused by goroutines), and you should create it once at startup rather than per request.

**Visualize it:**

```
Application startup
        │
        ▼
   mongo.Connect()  ──►  ONE mongo.Client (long-lived)
        │
        ├─► server A in topology ──► pool (max 100 conns, lazy)
        └─► server B in topology ──► pool (max 100 conns, lazy)

Per operation:  checkout conn ──► op ──► return to pool
If pool full:  block until waitQueueTimeoutMS
(Compare mentally to sql.DB pool: same idea.)
```

**Key facts:**
- The `mongo.Client` maintains a connection pool per server in the topology.
- Default `maxPoolSize` is 100 connections per server; connections are created lazily on demand and reused across goroutines.
- The client is thread-safe and should be created once at startup; each operation checks out a connection, runs, and returns it to the pool.
- If the pool is exhausted, operations block until `waitQueueTimeoutMS` expires. This is architecturally similar to Go's `sql.DB` pool.

**Interview tip:** Mention the anti-pattern: creating a new client per HTTP request. This is the #1 production issue in Go+MongoDB services.

> [!example]- Full Story: mongo-go-driver connection pooling
>
> **The problem:** Short-lived clients explode connection churn, increase latency, and can destabilize the server and the app under load; pooling exists so a small set of connections is shared efficiently across concurrent work.
>
> **How it works:** The `mongo.Client` maintains a connection pool per server in the topology. Default `maxPoolSize` is 100 connections per server. Connections are created lazily on demand and reused across goroutines. The client is thread-safe and should be created once at startup. Each operation checks out a connection, performs the operation, and returns it to the pool. If the pool is exhausted, operations block until `waitQueueTimeoutMS` expires. This is architecturally identical to Go's `sql.DB` pool.
>
> **What to watch out for:** New client per request; ignoring `waitQueueTimeoutMS` and pool sizing so bursty load blocks forever; and assuming one global pool for the whole process without reusing a single `mongo.Client` instance.

---

## Q3: What is the aggregation pipeline? Walk through a real example. [COMMON]

**Answer:**

**In one line:** The aggregation pipeline is a stage-by-stage transform (like a Unix pipe) where early `$match` on indexed fields is critical to shrink work for `$group`, `$project`, `$lookup`, and the rest.

**Visualize it:**

```
docs in
   │
   ▼
┌──────────┐   ┌──────────┐   ┌───────────┐   ┌────────┐
│ $match   │ → │ $group   │ → │ $sort     │ → │ $limit │
│ (filter) │   │ (agg)    │   │ (order)   │   │  (top) │
└──────────┘   └──────────┘   └───────────┘   └────────┘
   "WHERE"         "GROUP BY"      "ORDER BY"      cap

Example: "top 5 product categories by revenue (last month)"
$match: orders in range → $group: sum by category → $sort: total desc → $limit: 5
```

**Key facts:**
- The aggregation pipeline is MongoDB's data processing framework: documents are transformed through stages sequentially, like a Unix pipe.
- Key stages: `$match` (filter, like WHERE), `$group` (aggregate, like GROUP BY), `$project` (reshape, like SELECT), `$sort`, `$lookup` (join), `$unwind` (flatten arrays).
- Example: "Find the top 5 product categories by revenue" would be: `$match` orders from last month, `$group` by category summing price, `$sort` by total descending, `$limit` 5.
- Placing `$match` early is critical for performance: it can use indexes and reduces documents flowing into later stages.

**Interview tip:** Draw the pipeline as boxes with arrows. Mention that `$match` early is critical for performance (it can use indexes, reducing documents for later stages).

> [!example]- Full Story: Aggregation pipeline
>
> **The problem:** You need to filter, join, group, and reshape data server-side without shipping huge result sets to the application and without ad hoc map-reduce in app code.
>
> **How it works:** The aggregation pipeline is MongoDB's data processing framework. Documents enter the pipeline and are transformed through stages sequentially, like a Unix pipe. Key stages: `$match` (filter, like WHERE), `$group` (aggregate, like GROUP BY), `$project` (reshape, like SELECT), `$sort`, `$lookup` (join), `$unwind` (flatten arrays). Example: "Find the top 5 product categories by revenue" would be: `$match` orders from last month, `$group` by category summing price, `$sort` by total descending, `$limit` 5.
>
> **What to watch out for:** Late `$match` after expensive stages, `$lookup` fan-out, and unbounded sort/large in-memory sort when sort keys are not well supported; always validate with `explain` on real data volumes.

---

## Q4: How does indexing work in MongoDB? Explain compound index prefix rules. [COMMON]

**Answer:**

**In one line:** B-tree compound indexes support the leftmost-prefix rule for both filter and many sort plans, and `explain("executionStats")` confirms `IXSCAN` versus a full `COLLSCAN`.

**Visualize it:**

```
Compound index: { a: 1, b: 1, c: 1 }   (B-tree, left-to-right)

Supported query shapes on PREFIX:
  { a }           [ yes ]
  { a, b }        [ yes ]
  { a, b, c }     [ yes ]

NOT supported on prefix alone:
  { b }  { c }  { b, c }  [ need different index or COLLSCAN ]

Sort direction: index {a:1, b:-1} matches sort {a:1, b:-1} or exact reverse pairings;
mismatching sort (e.g. a:1, b:1) may not use the index for sort.
```

**Key facts:**
- MongoDB uses B-tree indexes. A compound index on `{a: 1, b: 1, c: 1}` supports queries on `{a}`, `{a, b}`, or `{a, b, c}` but not `{b}`, `{c}`, or `{b, c}` alone: the leftmost prefix rule.
- The index is used starting from the leftmost field. For sort operations, the index direction matters: an index on `{a: 1, b: -1}` supports `sort({a: 1, b: -1})` and `sort({a: -1, b: 1})` (exact reverse) but not `sort({a: 1, b: 1})`.
- Use `explain("executionStats")` to verify `IXSCAN` vs `COLLSCAN` and to validate the plan.
- ESR design guideline: Equality fields first, Sort fields next, Range fields last when designing compound indexes for mixed queries.

**Interview tip:** Interviewers often follow up with "how would you design indexes for these 5 queries?" Think about the ESR rule: Equality fields first, Sort fields next, Range fields last.

> [!example]- Full Story: Indexing and compound prefix rules
>
> **The problem:** Without the right index shape, the database scans entire collections; compound indexes are powerful but only help queries that share a leftmost prefix of the index fields.
>
> **How it works:** MongoDB uses B-tree indexes. A compound index on `{a: 1, b: 1, c: 1}` supports queries on `{a}`, `{a, b}`, or `{a, b, c}` but NOT `{b}`, `{c}`, or `{b, c}` alone. This is the leftmost prefix rule: the index can only be used starting from the leftmost field. For sort operations, the index direction matters: an index on `{a: 1, b: -1}` supports `sort({a: 1, b: -1})` and `sort({a: -1, b: 1})` (exact reverse) but NOT `sort({a: 1, b: 1})`. Use `explain("executionStats")` to verify `IXSCAN` vs `COLLSCAN`.
>
> **What to watch out for:** Multiple single-field indexes that cannot combine into one compound plan the way you expect; regex and negation can defeat indexes; and sorts that do not line up with index direction, forcing in-memory or blocking sorts.

---

## Q5: How do you handle the 16MB document size limit? [COMMON]

**Answer:**

**In one line:** You avoid unbounded growth in one document by referencing, bucketing into fixed-size sub-documents, or GridFS for large binaries, and hitting this limit is a strong signal to revisit schema design.

**Visualize it:**

```
16MB cap per document (BSON)
│
├─► Reference unbounded "child" data    ──► separate collection + IDs
├─► Bucketing (e.g. 200 events/bucket)  ──► many smaller docs, stable size
└─► GridFS (large files)                ──► fs.files + fs.chunks (~255KB chunks)
```

**Key facts:**
- Three strategies: (1) schema design with referencing instead of embedding for unbounded arrays; (2) bucketing: group items into fixed-size sub-documents (e.g. 200 events per bucket document); (3) GridFS: for large binary files, MongoDB chunks them into 255KB pieces across `fs.files` and `fs.chunks`.
- If you are approaching 16MB, the schema needs redesign: the limit exists in part to keep individual document operations, cache use, and replication efficient.
- The 16MB limit includes BSON overhead, so the usable space is slightly less than the raw cap.

**Interview tip:** Mention that the 16MB limit includes BSON overhead, so the actual usable space is slightly less. Show awareness that this limit exists for performance reasons (WiredTiger cache, replication oplog).

> [!example]- Full Story: 16MB document limit
>
> **The problem:** Documents that grow without bound bloat the working set, increase replication and I/O, and can eventually break writes when they exceed MongoDB's maximum BSON document size.
>
> **How it works:** Three strategies: (1) Schema design: use referencing instead of embedding for unbounded arrays; (2) Bucketing pattern: group items into fixed-size sub-documents (e.g. 200 events per bucket document); (3) GridFS: for large binary files, MongoDB chunks them into 255KB pieces across two collections (`fs.files` and `fs.chunks`). The real answer: if you're approaching 16MB, your schema needs redesign -- this limit is intentional to keep operations fast.
>
> **What to watch out for:** "Just embed everything" for append-only event streams, binary payloads stored inline, and unbounded user-generated arrays without migration or split strategies.

---

## Q6: Explain write concerns and read preferences. [ADVANCED]

**Answer:**

**In one line:** Write concern is how many nodes must acknowledge a write, and read preference is which replica (primary vs secondary) you read from, trading latency and read scaling against how stale a read you accept.

**Visualize it:**

```
WRITE CONCERN (durability)          READ PREFERENCE (where to read)
w:0   fire-and-forget               primary: always primary (strong)
w:1   primary ack                   primaryPreferred / secondaryPreferred
w:     majority: majority of RS    secondary: may be stale, scales reads
         (FinTech: often "majority")  nearest: lowest latency
              │
              └── CAP/operational: stronger writes & primary reads cost latency
```

**Key facts:**
- Write concern controls durability: `w:1` (acknowledged by primary), `w:majority` (acknowledged by majority of replica set), `w:0` (fire-and-forget). Higher write concern = more durable but slower.
- Read preference controls where reads go: `primary` (always primary, strongest consistency), `primaryPreferred` (primary if available), `secondary` (read from secondaries, may be stale), `secondaryPreferred`, `nearest` (lowest latency).
- For FinTech: use `w:majority` for financial transactions and `readPreference: secondaryPreferred` for analytics queries. This is fundamentally a consistency, durability, and availability tradeoff: connect to CAP in discussion.

**Interview tip:** This is a consistency vs availability tradeoff question. Connect it to CAP theorem.

> [!example]- Full Story: Write concerns and read preferences
>
> **The problem:** Different features need different safety: payments need durability; dashboards may accept eventually consistent reads; misconfigured read/write rules cause lost writes, stale reads, or avoidable load on the primary.
>
> **How it works:** Write concern controls durability: `w:1` (acknowledged by primary), `w:majority` (acknowledged by majority of replica set), `w:0` (fire-and-forget). Higher write concern = more durable but slower. Read preference controls where reads go: `primary` (always primary, strongest consistency), `primaryPreferred` (primary if available), `secondary` (read from secondaries, may be stale), `secondaryPreferred`, `nearest` (lowest latency). For FinTech: use `w:majority` for financial transactions and `readPreference: secondaryPreferred` for analytics queries.
>
> **What to watch out for:** `w:0` for anything that must not disappear; `secondary` reads for workflows that read-your-writes; and ignoring `readConcern` (not just preference) when you need monotonic or causally consistent reads across operations.

---

## Q7: How do MongoDB transactions work? When should you avoid them? [ADVANCED]

**Answer:**

**In one line:** Multi-document ACID transactions (4.0+ on replica sets, 4.2+ sharded) use snapshot isolation and WiredTiger MVCC, but you still prefer document atomicity and good schema design to avoid lock/cache pressure and time limits.

**Visualize it:**

```
Session.startTransaction()
        │
   snapshot isolation (WiredTiger MVCC)
        │
   [ ops on multiple docs / collections ]
        │
   commit  ──►  locks + cache + default timeout (e.g. 60s) considered
   abort

Prefer: single-doc atomic updates (embed) when possible
Use transactions: only when you truly need atomicity across multiple docs
```

**Key facts:**
- Multi-document ACID transactions: v4.0 (replica sets) and v4.2 (sharded clusters). They use snapshot isolation with WiredTiger's MVCC. Usage: start a session, start a transaction, perform operations, commit or abort.
- Transactions add overhead: locks, WiredTiger cache use, and a 60-second default timeout.
- Design to avoid when possible: use document embedding for atomic operations on related data. Use transactions when you genuinely need atomic writes across multiple collections.

**Interview tip:** Show that you know transactions exist but prefer schema design that avoids needing them. This demonstrates real MongoDB expertise.

> [!example]- Full Story: MongoDB transactions
>
> **The problem:** You sometimes need to move money between two balance documents or update multiple collections as one unit; single-document updates already give you atomicity within that document, but multi-doc invariants need more.
>
> **How it works:** Multi-document ACID transactions were introduced in v4.0 (replica sets) and v4.2 (sharded clusters). They use snapshot isolation with WiredTiger's MVCC. Usage: start a session, start a transaction, perform operations, commit or abort. However, transactions have performance overhead: they hold locks, consume WiredTiger cache, and have a 60-second default timeout. Design to avoid them: use document embedding for atomic operations on related data. Only use transactions when you genuinely need atomic writes across multiple collections.
>
> **What to watch out for:** Long-running transactions under load, unbounded work inside a session, and reaching for SQL-style transactions for patterns that a better document model would collapse into one atomic update.

---

## Q8: What is the difference between `bson.D` and `bson.M` in the Go driver? [COMMON]

**Answer:**

**In one line:** `bson.D` preserves key order and is the right type for ordered constructs (pipeline, sort, index keys); `bson.M` is a map and is fine for unordered filters where iteration order does not matter.

**Visualize it:**

```
bson.D  (ordered slice of ELEMents)
  [ {Key:"$match", Value:...}, {Key:"$group", Value:...} ]  -- stage ORDER matters

bson.M  (unordered map)
  {"$match": ...}   -- for filter doc; key order usually irrelevant

GOTCHA:  bson.M{"a":1,"b":-1}  + random map iteration  -- field order to server = undefined
         Use bson.D for sort {{"a",1},{"b",-1}} when order must be exact
```

**Key facts:**
- `bson.D` is an ordered representation of a BSON document (slice of key-value pairs). `bson.M` is an unordered map.
- Use `bson.D` for pipeline stages, sort specifications, index definitions, and any context where field order matters.
- Use `bson.M` for simple filters where order does not matter. The gotcha: Go map iteration is random, so `bson.M{"a": 1, "b": -1}` might send fields in any order to the server.

**Interview tip:** This is a Go-specific question that shows you've actually used the driver, not just read about MongoDB.

> [!example]- Full Story: bson.D vs bson.M
>
> **The problem:** BSON documents are ordered sequences of key-value pairs, but Go maps are unordered; some server-side constructs are sensitive to the order of keys (especially aggregation and sort).
>
> **How it works:** `bson.D` is an ordered representation of a BSON document (slice of key-value pairs). `bson.M` is an unordered map. Use `bson.D` for: pipeline stages, sort specifications, index definitions, and any context where field order matters. Use `bson.M` for simple filters where order doesn't matter. The gotcha: Go map iteration is random, so `bson.M{"a": 1, "b": -1}` might send fields in any order to the server.
>
> **What to watch out for:** Using `bson.M` for aggregation pipelines and sorts; and assuming two maps with the same keys serialize identically for debugging.

---

## Q9: How would you design a schema for a real-time chat application? [ADVANCED]

**Answer:**

**In one line:** You model messages and rooms for room-scoped timelines with a compound index on `chatRoomId` and `timestamp`, then layer read state (receipts or per-user cursors) and optional bucketing for history at scale, avoiding capped collections when you need deletes.

**Visualize it:**

```
messages: { _id, chatRoomId, senderId, text, timestamp, type }
   INDEX: { chatRoomId: 1, timestamp: -1 }   -- "last N in room" cheaply

chatRooms: { _id, participants: [userId], lastMessage, updatedAt }
users: referenced by id (not embedded in every message for duplication)

read path:  lastRead per user per room OR readReceipts collection
scale:  bucket old messages (e.g. 200 per bucket doc)

NOT: capped for chat if you need delete / moderation / sharding
```

**Key facts:**
- Messages collection: `{_id, chatRoomId, senderId, text, timestamp, type}` with compound index on `{chatRoomId: 1, timestamp: -1}` for chronological retrieval.
- Chat rooms: `{_id, participants: [userId], lastMessage, updatedAt}`. Users are referenced, not embedded.
- Unread: separate `readReceipts` or `lastReadTimestamp` per user per room. Bucketing for message archives (e.g. 200 messages per bucket doc). TTL index for message expiration if needed.
- Capped collection is not suitable for typical chat: you cannot delete individual messages, which blocks moderation and many product requirements.

**Interview tip:** Walk through the access patterns first: "fetch last 50 messages for a room", "get all rooms for a user sorted by last activity", "mark messages as read". Then derive the schema from those patterns.

> [!example]- Full Story: Chat app schema
>
> **The problem:** Chat needs fast, ordered reads per room, presence of participants, and read/unread state, without unbounded document growth in a single parent document and without wrong tool choices (e.g. capped when you need deletes).
>
> **How it works:** Messages collection: `{_id, chatRoomId, senderId, text, timestamp, type}` with compound index on `{chatRoomId: 1, timestamp: -1}` for chronological retrieval. Chat rooms: `{_id, participants: [userId], lastMessage, updatedAt}`. Users referenced, not embedded. For unread counts, use a separate `readReceipts` collection or a `lastReadTimestamp` per user per room. Bucketing pattern for message archives (group 200 messages per bucket doc). TTL index for message expiration if needed. Capped collection is NOT suitable because you can't delete individual messages.
>
> **What to watch out for:** Embedding full user profiles on every message, huge room lists without denormalized `lastMessage`/`updatedAt` for list views, and using capped collections when compliance or deletion is required.

---

## Q10: What causes slow queries in MongoDB? How do you diagnose them? [COMMON]

**Answer:**

**In one line:** Slow queries usually come from full collection scans, bad index use, or heavy pipelines, and you triage with the profiler, then `explain("executionStats")` to compare `totalDocsExamined` to `nReturned` and the winning plan.

**Visualize it:**

```
Healthy:   docsExamined : nReturned  ≈  1 : 1   (tight index use)

Sick:     COLLSCAN  OR  index scans millions but returns few
              │
              ▼
   profiler (slowms)  →  find bad query shape
   explain("executionStats")  →  IXSCAN vs COLLSCAN, rejected plans
   Atlas / APM: trends
```

**Key facts:**
- Top causes: (1) missing indexes causing `COLLSCAN`; (2) queries that cannot use the index prefix; (3) large document scans; (4) unoptimized aggregation pipelines (e.g. `$match` not at the beginning); (5) network latency when reading from distant secondaries.
- Diagnosis: `db.setProfilingLevel(1, {slowms: 100})` to log slow queries; `explain("executionStats")` for `totalDocsExamined` vs `nReturned` (should be near 1:1); check `rejectedPlans`; monitor with MongoDB Atlas or New Relic.
- A systematic order helps: profile or logs first, `explain` second, then index or query shape fixes.

**Interview tip:** Show that you have a systematic approach: profiler first, then explain, then fix.

> [!example]- Full Story: Slow query diagnosis
>
> **The problem:** A query that "worked" in dev explodes in prod when data grows, usually because the planner falls back to collection scans or examines orders of magnitude more documents than it returns.
>
> **How it works:** Top causes: (1) Missing indexes causing COLLSCAN; (2) Queries that can't use index prefix; (3) Large document scans (scanning millions of docs); (4) Unoptimized aggregation pipelines ($match not at the beginning); (5) Network latency (reading from distant secondaries). Diagnosis: enable `db.setProfilingLevel(1, {slowms: 100})` to log slow queries, use `explain("executionStats")` to check `totalDocsExamined` vs `nReturned` ratio (should be close to 1:1), check `rejectedPlans`, and monitor with MongoDB Atlas or New Relic.
>
> **What to watch out for:** Hidden `$where`, case-insensitive regex on unanchored fields, and aggregation stages that block index use even when an index exists for the data you think you are filtering.

---

## Q11: How does MongoDB handle sharding? [ADVANCED]

**Answer:**

**In one line:** Sharding partitions data by a shard key across shards, with `mongos` routing, chunk splits around size thresholds, and balancer-driven migrations, and bad shard key choice is the main long-term pain because it is hard to change.

**Visualize it:**

```
[ clients ]
     │
     ▼
  mongos  (query router)  ──► shard1  (chunk ranges or hashed)
     │                    ──► shard2
     │                    ──► shardN
     │
  shard key: high cardinality, even spread, matches hot queries
  hashed: even spread, range queries harder; range: range-friendly, hotspot risk
  chunks split (~128MB); balancer migrates chunks between shards
  (Resharding/change constraints: version-specific; "immutable" historically mattered in interviews)
```

**Key facts:**
- Sharding distributes data across multiple servers (shards) based on a shard key. The `mongos` router directs queries to the correct shard(s).
- Shard key: high cardinality, even distribution, alignment with common query patterns. Hashed keys spread load but complicate range-style access; range keys help range queries but can hotspot. Chunk splits when large; balancer migrates chunks.
- Once set, the shard key could not be changed in older versions; v5.0+ introduces resharding capabilities, but interviews still stress that poor early choices were historically very costly.

**Interview tip:** Focus on shard key selection: bad shard key choice is the #1 cause of sharding problems and is very hard to fix.

> [!example]- Full Story: Sharding
>
> **The problem:** A single replica set runs out of CPU, disk, or I/O for a working set; you need horizontal scale and isolation of hot ranges without rewriting the whole application, but the shard key is a one-way door for years of production pain if chosen poorly.
>
> **How it works:** Sharding distributes data across multiple servers (shards) based on a shard key. The mongos router directs queries to the correct shard(s). Shard key selection is critical: choose a key with high cardinality, even distribution, and that matches your query patterns. Hashed shard keys provide even distribution but don't support range queries. Range shard keys support range queries but can create hotspots. Once set, the shard key cannot be changed (until v5.0 which allows resharding). Chunks are split when they exceed 128MB and migrated by the balancer.
>
> **What to watch out for:** Monotonic insert keys (hot shard), low-cardinality keys (few chunks, poor parallelism), and scatter-gather queries that must hit every shard on every read.

---

## Q12: How do you handle schema migrations in MongoDB? [TRICKY]

**Answer:**

**In one line:** There is no `ALTER TABLE`; you evolve at the application and jobs layer with lazy or background rewrites, often multi-version code paths, and optional JSON Schema validation for new writes, because schemaless storage still needs an intentional schema and migration plan.

**Visualize it:**

```
Deploy code reads v1 + v2  ──►  backfill / lazy migrate  ──►  drop v1 only after safe

Patterns:
  lazy:      fix document shape on read/write
  background: batch cursor update all docs
  versioned:  schemaVersion field, branches in code

"Schemaless" != "no migration"  (operational + compatibility discipline)
```

**Key facts:**
- Unlike SQL with `ALTER TABLE`, MongoDB schema changes happen at the application level.
- Strategies: (1) lazy migration: update documents on read/write; old and new shapes coexist; (2) background migration: batch job updates all documents; (3) versioned documents: add `schemaVersion`, application code handles multiple versions.
- For breaking changes: deploy code that reads both old and new format, migrate data, then remove old-format handling. JSON Schema validation can enforce the new schema for new writes.
- "Schemaless" does not mean "schema-free": you need a migration strategy and compatibility discipline.

**Interview tip:** This shows production experience. Mention that "schemaless" doesn't mean "schema-free" -- you need a migration strategy.

> [!example]- Full Story: Schema migrations
>
> **The problem:** Documents with mixed shapes in one collection, rolling deploys, and long-lived mobile clients all mean a single "big bang" column migration is not how MongoDB teams ship safely; you coordinate code and data over time.
>
> **How it works:** Unlike SQL with ALTER TABLE, MongoDB schema changes happen at the application level. Strategies: (1) Lazy migration: update documents to new schema on read/write; old documents coexist with new ones; (2) Background migration: batch job updates all documents; (3) Versioned documents: add a `schemaVersion` field, application code handles multiple versions. For breaking changes, use a staged approach: deploy code that reads both old and new format, migrate data, then remove old-format handling. JSON Schema validation can enforce the new schema for new writes.
>
> **What to watch out for:** Assuming readers always see the newest shape, dropping support for old versions too early, and running unbounded backfills without throttling and resume tokens.

---

## Q13: What are capped collections? When would you use them? [TRICKY]

**Answer:**

**In one line:** Capped collections are fixed-size, insertion-order ring buffers in the collection namespace, which are simple for high-throughput tailing but limit deletes, growth, and sharding, so many teams prefer TTL on normal collections.

**Visualize it:**

```
fixed max bytes / max docs
[ oldest ... newest ]  "wrap" overwrites tail when full  (circular)

NO individual deletes (except drop whole col). NO shard.
insertion order cheap without a time index

vs TTL on normal collection: flexible deletes, more typical for logs/telemetry
```

**Key facts:**
- Capped collections have a fixed size and maintain insertion order; when full, oldest documents are overwritten (circular buffer).
- Use cases: application logs, event streams, recent activity feeds. Limitations: cannot delete individual documents, cannot shard, updates that grow document size fail. Insertion-order retrieval is available without a separate index on the time field.
- For most logging, a regular collection with a TTL index is more flexible than capped.

**Interview tip:** Mention that for most logging use cases, a regular collection with a TTL index is more flexible than a capped collection.

> [!example]- Full Story: Capped collections
>
> **The problem:** You need a bounded, fast FIFO-like stream in the database for consumers that "tailed" a cursor, without growing disk forever, but you still need the right feature for regulations and data lifecycle.
>
> **How it works:** Capped collections have a fixed size and maintain insertion order. When the collection reaches its size limit, the oldest documents are automatically overwritten (circular buffer). Use cases: application logs, event streams, recent activity feeds. Limitations: you can't delete individual documents, can't shard them, and updates that increase document size fail. They guarantee insertion-order retrieval without needing an index on the time field.
>
> **What to watch out for:** Need to purge PII, legal hold, or per-record deletion; sharded clusters; and variable-size records that need growth updates.

---

## Q14: How does MongoDB ensure high availability? [COMMON]

**Answer:**

**In one line:** Replica sets use a primary for writes, replicated secondaries, automatic failover elections (on the order of 10-12 seconds), and `w:majority` plus rolling upgrades to keep the service up during change.

**Visualize it:**

```
        [ clients ]
            │
            ▼
        ┌─────────┐
        │ Primary │  writes, replication oplog
        └────┬────┘
     rep   │   │ rep
     ┌────┘   └────┐
┌────▼───┐     ┌───▼────┐
│ Sec 1  │     │ Sec 2  │   (async replication typical)
└────────┘     └────────┘

primary fails  ──►  election (often ~10-12s)  ──►  new primary
arbiter: votes in election, no data
```

**Key facts:**
- Replica sets: a primary handles writes, secondaries replicate (often asynchronously). If the primary fails, secondaries hold an election; typical completion 10-12 seconds.
- Write concern `majority` ensures writes are replicated to a majority before acknowledgment. Reads can go to secondaries for load distribution when stale reads are acceptable. An arbiter can participate in elections without holding data.
- Rolling upgrades across replica set members support zero- or low-downtime version upgrades in production.

**Interview tip:** Connect this to your experience with Redis or MySQL replication. The concepts transfer.

> [!example]- Full Story: High availability
>
> **The problem:** A single `mongod` is a single point of failure; production clusters need automated failover, replication for durability, and safe upgrade paths.
>
> **How it works:** Replica sets: a primary node handles writes, secondaries replicate asynchronously. If the primary fails, secondaries hold an election to choose a new primary (typically completes in 10-12 seconds). Write concern `majority` ensures writes are replicated before acknowledgment. Reads can be directed to secondaries for load distribution. An arbiter node can participate in elections without holding data. For zero-downtime deployments, use rolling upgrades across replica set members.
>
> **What to watch out for:** Reading from secondaries for workflows that need read-your-writes, split-brain misconfiguration, and elections during network partitions without proper majority rules.

---

## Q15: How do you optimize MongoDB for a FinTech application like Kissht? [ADVANCED]

**Answer:**

**In one line:** You combine `writeConcern`/`readConcern` majority for money-moving paths, transport and storage encryption, audit and compliance logging, index and schema choices for idempotent, queryable money trails, and PITR-capable backup with observability.

**Visualize it:**

```
Durability:     writeConcern/majority, readConcern/majority on critical paths
Security:        TLS in transit, encryption at rest (WiredTiger)
Compliance:     audit log, app-level audit, least-privilege users
Data model:     compound indexes (userId + txnDate), embed when atomic read, ref history
Ops:            PITR backup, New Relic (or similar), connection pooling, secondary reads for analytics
                    │
                    ▼
              FinTech: consistency + provability + security over raw speed
```

**Key facts:**
- Data integrity: `writeConcern: majority` and `readConcern: majority` for financial transactions.
- Encryption: encryption at rest (WiredTiger encryption) and TLS in transit. Audit logging: MongoDB's audit log for compliance.
- Indexing: compound indexes on frequently queried fields (e.g. `userId` + `transactionDate`). Schema: embed loan details within user documents for atomic reads; reference transaction history for scale.
- Backup: continuous backup with point-in-time recovery (PITR). Performance: connection pooling, `readPreference: secondaryPreferred` for analytics, monitoring with New Relic.

**Interview tip:** This is tailored for your Kissht application. Show awareness of compliance, security, and durability requirements specific to FinTech.

> [!example]- Full Story: FinTech optimization
>
> **The problem:** Regulated money and lending need durable writes, provable history, and defensible access controls, not just low p99 on happy-path reads; outages and data loss are existential.
>
> **How it works:** Data integrity: use `writeConcern: majority` and `readConcern: majority` for financial transactions. Encryption: enable encryption at rest (WiredTiger encryption) and TLS for data in transit. Audit logging: enable MongoDB's audit log for compliance. Indexing: compound indexes on frequently queried fields (userId + transactionDate). Schema: embed loan details within user documents for atomic reads, reference transaction history for scalability. Backup: use continuous backup with point-in-time recovery (PITR). Performance: use connection pooling, read preference `secondaryPreferred` for analytics, and monitor with New Relic.
>
> **What to watch out for:** Secondary reads for post-payment verification without matching read concern, weak handling of idempotency keys for payments, and backups that are not restorable in your RPO/RTO tests.

---
