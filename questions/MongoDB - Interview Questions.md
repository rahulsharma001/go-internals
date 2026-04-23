# MongoDB -- Interview Questions

> Comprehensive interview Q&A bank for [[databases/MongoDB]].
> Sorted by frequency at top tech companies. Tags: [COMMON] [ADVANCED] [TRICKY]

---

## Q1: Explain embedding vs referencing in MongoDB. When do you use each? [COMMON]

**Answer:**
Embedding places related data inside a single document. Referencing stores the relationship as an ID pointing to another collection. Embed when: data is always read together (1:few relationship), you need atomic writes on the group, and the embedded array is bounded. Reference when: data is accessed independently, the relationship is 1:many or many:many, the related data is shared across documents, or the array could grow unboundedly (risk hitting 16MB limit). The decision is driven by query patterns, not entity relationships.

**Interview tip:** The interviewer wants to hear you reason about access patterns, not just recite rules. Give a concrete example: "For a user's shipping addresses (1:few, always loaded with user) I'd embed. For a user's order history (1:many, accessed independently, grows forever) I'd reference."

---

## Q2: How does the mongo-go-driver handle connection pooling? [COMMON]

**Answer:**
The `mongo.Client` maintains a connection pool per server in the topology. Default `maxPoolSize` is 100 connections per server. Connections are created lazily on demand and reused across goroutines. The client is thread-safe and should be created once at startup. Each operation checks out a connection, performs the operation, and returns it to the pool. If the pool is exhausted, operations block until `waitQueueTimeoutMS` expires. This is architecturally identical to Go's `sql.DB` pool.

**Interview tip:** Mention the anti-pattern: creating a new client per HTTP request. This is the #1 production issue in Go+MongoDB services.

---

## Q3: What is the aggregation pipeline? Walk through a real example. [COMMON]

**Answer:**
The aggregation pipeline is MongoDB's data processing framework. Documents enter the pipeline and are transformed through stages sequentially, like a Unix pipe. Key stages: `$match` (filter, like WHERE), `$group` (aggregate, like GROUP BY), `$project` (reshape, like SELECT), `$sort`, `$lookup` (join), `$unwind` (flatten arrays). Example: "Find the top 5 product categories by revenue" would be: `$match` orders from last month, `$group` by category summing price, `$sort` by total descending, `$limit` 5.

**Interview tip:** Draw the pipeline as boxes with arrows. Mention that `$match` early is critical for performance (it can use indexes, reducing documents for later stages).

---

## Q4: How does indexing work in MongoDB? Explain compound index prefix rules. [COMMON]

**Answer:**
MongoDB uses B-tree indexes. A compound index on `{a: 1, b: 1, c: 1}` supports queries on `{a}`, `{a, b}`, or `{a, b, c}` but NOT `{b}`, `{c}`, or `{b, c}` alone. This is the leftmost prefix rule -- the index can only be used starting from the leftmost field. For sort operations, the index direction matters: an index on `{a: 1, b: -1}` supports `sort({a: 1, b: -1})` and `sort({a: -1, b: 1})` (exact reverse) but NOT `sort({a: 1, b: 1})`. Use `explain("executionStats")` to verify `IXSCAN` vs `COLLSCAN`.

**Interview tip:** Interviewers often follow up with "how would you design indexes for these 5 queries?" Think about the ESR rule: Equality fields first, Sort fields next, Range fields last.

---

## Q5: How do you handle the 16MB document size limit? [COMMON]

**Answer:**
Three strategies: (1) Schema design: use referencing instead of embedding for unbounded arrays; (2) Bucketing Pattern: group items into fixed-size sub-documents (e.g., 200 events per bucket document); (3) GridFS: for large binary files, MongoDB chunks them into 255KB pieces across two collections (`fs.files` and `fs.chunks`). The real answer: if you're approaching 16MB, your schema needs redesign -- this limit is intentional to keep operations fast.

**Interview tip:** Mention that the 16MB limit includes BSON overhead, so the actual usable space is slightly less. Show awareness that this limit exists for performance reasons (WiredTiger cache, replication oplog).

---

## Q6: Explain write concerns and read preferences. [ADVANCED]

**Answer:**
Write concern controls durability: `w:1` (acknowledged by primary), `w:majority` (acknowledged by majority of replica set), `w:0` (fire-and-forget). Higher write concern = more durable but slower. Read preference controls where reads go: `primary` (always primary, strongest consistency), `primaryPreferred` (primary if available), `secondary` (read from secondaries, may be stale), `secondaryPreferred`, `nearest` (lowest latency). For FinTech: use `w:majority` for financial transactions and `readPreference:secondaryPreferred` for analytics queries.

**Interview tip:** This is a consistency vs availability tradeoff question. Connect it to CAP theorem.

---

## Q7: How do MongoDB transactions work? When should you avoid them? [ADVANCED]

**Answer:**
Multi-document ACID transactions were introduced in v4.0 (replica sets) and v4.2 (sharded clusters). They use snapshot isolation with WiredTiger's MVCC. Usage: start a session, start a transaction, perform operations, commit or abort. However, transactions have performance overhead: they hold locks, consume WiredTiger cache, and have a 60-second default timeout. Design to avoid them: use document embedding for atomic operations on related data. Only use transactions when you genuinely need atomic writes across multiple collections.

**Interview tip:** Show that you know transactions exist but prefer schema design that avoids needing them. This demonstrates real MongoDB expertise.

---

## Q8: What is the difference between `bson.D` and `bson.M` in the Go driver? [COMMON]

**Answer:**
`bson.D` is an ordered representation of a BSON document (slice of key-value pairs). `bson.M` is an unordered map. Use `bson.D` for: pipeline stages, sort specifications, index definitions, and any context where field order matters. Use `bson.M` for simple filters where order doesn't matter. The gotcha: Go map iteration is random, so `bson.M{"a": 1, "b": -1}` might send fields in any order to the server.

**Interview tip:** This is a Go-specific question that shows you've actually used the driver, not just read about MongoDB.

---

## Q9: How would you design a schema for a real-time chat application? [ADVANCED]

**Answer:**
Messages collection: `{_id, chatRoomId, senderId, text, timestamp, type}` with compound index on `{chatRoomId: 1, timestamp: -1}` for chronological retrieval. Chat rooms: `{_id, participants: [userId], lastMessage, updatedAt}`. Users referenced, not embedded. For unread counts, use a separate `readReceipts` collection or a `lastReadTimestamp` per user per room. Bucketing pattern for message archives (group 200 messages per bucket doc). TTL index for message expiration if needed. Capped collection is NOT suitable because you can't delete individual messages.

**Interview tip:** Walk through the access patterns first: "fetch last 50 messages for a room", "get all rooms for a user sorted by last activity", "mark messages as read". Then derive the schema from those patterns.

---

## Q10: What causes slow queries in MongoDB? How do you diagnose them? [COMMON]

**Answer:**
Top causes: (1) Missing indexes causing COLLSCAN; (2) Queries that can't use index prefix; (3) Large document scans (scanning millions of docs); (4) Unoptimized aggregation pipelines ($match not at the beginning); (5) Network latency (reading from distant secondaries). Diagnosis: enable `db.setProfilingLevel(1, {slowms: 100})` to log slow queries, use `explain("executionStats")` to check `totalDocsExamined` vs `nReturned` ratio (should be close to 1:1), check `rejectedPlans`, and monitor with MongoDB Atlas or New Relic.

**Interview tip:** Show that you have a systematic approach: profiler first, then explain, then fix.

---

## Q11: How does MongoDB handle sharding? [ADVANCED]

**Answer:**
Sharding distributes data across multiple servers (shards) based on a shard key. The mongos router directs queries to the correct shard(s). Shard key selection is critical: choose a key with high cardinality, even distribution, and that matches your query patterns. Hashed shard keys provide even distribution but don't support range queries. Range shard keys support range queries but can create hotspots. Once set, the shard key cannot be changed (until v5.0 which allows resharding). Chunks are split when they exceed 128MB and migrated by the balancer.

**Interview tip:** Focus on shard key selection -- bad shard key choice is the #1 cause of sharding problems and is very hard to fix.

---

## Q12: How do you handle schema migrations in MongoDB? [TRICKY]

**Answer:**
Unlike SQL with ALTER TABLE, MongoDB schema changes happen at the application level. Strategies: (1) Lazy migration: update documents to new schema on read/write; old documents coexist with new ones; (2) Background migration: batch job updates all documents; (3) Versioned documents: add a `schemaVersion` field, application code handles multiple versions. For breaking changes, use a staged approach: deploy code that reads both old and new format, migrate data, then remove old-format handling. JSON Schema validation can enforce the new schema for new writes.

**Interview tip:** This shows production experience. Mention that "schemaless" doesn't mean "schema-free" -- you need a migration strategy.

---

## Q13: What are capped collections? When would you use them? [TRICKY]

**Answer:**
Capped collections have a fixed size and maintain insertion order. When the collection reaches its size limit, the oldest documents are automatically overwritten (circular buffer). Use cases: application logs, event streams, recent activity feeds. Limitations: you can't delete individual documents, can't shard them, and updates that increase document size fail. They guarantee insertion-order retrieval without needing an index on the time field.

**Interview tip:** Mention that for most logging use cases, a regular collection with a TTL index is more flexible than a capped collection.

---

## Q14: How does MongoDB ensure high availability? [COMMON]

**Answer:**
Replica sets: a primary node handles writes, secondaries replicate asynchronously. If the primary fails, secondaries hold an election to choose a new primary (typically completes in 10-12 seconds). Write concern `majority` ensures writes are replicated before acknowledgment. Reads can be directed to secondaries for load distribution. An arbiter node can participate in elections without holding data. For zero-downtime deployments, use rolling upgrades across replica set members.

**Interview tip:** Connect this to your experience with Redis or MySQL replication. The concepts transfer.

---

## Q15: How do you optimize MongoDB for a FinTech application like Kissht? [ADVANCED]

**Answer:**
Data integrity: use `writeConcern: majority` and `readConcern: majority` for financial transactions. Encryption: enable encryption at rest (WiredTiger encryption) and TLS for data in transit. Audit logging: enable MongoDB's audit log for compliance. Indexing: compound indexes on frequently queried fields (userId + transactionDate). Schema: embed loan details within user documents for atomic reads, reference transaction history for scalability. Backup: use continuous backup with point-in-time recovery (PITR). Performance: use connection pooling, read preference `secondaryPreferred` for analytics, and monitor with New Relic.

**Interview tip:** This is tailored for your Kissht application. Show awareness of compliance, security, and durability requirements specific to FinTech.

---
