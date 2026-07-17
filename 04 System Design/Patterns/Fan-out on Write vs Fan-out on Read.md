---
type: canonical
domain: system-design
topic: fan-out-on-write-vs-fan-out-on-read
status: active
last_verified: 2026-07-17
---
# Fan-out on Write vs Fan-out on Read

## 1. Problem it solves

One event must reach many recipients. Systems choose whether to precompute recipient inboxes when writing or merge sources when reading.

## 2. Simple mental model

Push work early for fast reads; pull work late to avoid huge write amplification. Hybrid selects by audience size/activity.

## 3. How it works

Write fan-out emits post/event then workers append references to follower inboxes idempotently. Read fan-out fetches followed sources and ranks/merges at query. Hybrid pushes normal accounts and pulls celebrity/high-fan-out content.

## 4. Concrete example

News feed pushes ordinary posts to active followers’ inboxes; celebrity posts stay in author timeline. Read merges user inbox with celebrity sources, deduplicates and ranks.

## 5. Detailed success flow

Post commits+outbox; fan-out tasks partition follower ranges; inbox insert unique `(user,post)`; feed read cursor-merges and caches first page.

## 6. Detailed failure flow

Fan-out backlog delays posts; feed exposes bounded stale and pull fallback for missing recent source. Duplicate tasks are idempotent. Celebrity surge does not create millions of writes.

## 7. Scaling behaviour

Write amplification = posts × followers; read amplification = followed sources queried/merged. Active-user filtering, batching, partition by recipient, hot-author isolation, and cursor pagination.

## 8. Data consistency implications

Feeds are usually eventual; deletion/privacy/block changes need tombstones/filter at read and async cleanup. Ordering/ranking may be approximate; source post remains truth.

## 9. Real implementation choices

Kafka fan-out tasks; Cassandra/DynamoDB/Redis inbox; author timeline store; ranking service; cache. Thresholds based on fan-out cost and user activity.

## 10. Trade-offs

Write fan-out fast reads but storage/write/backlog; read fan-out fresh and cheap writes but high tail/query cost. Hybrid adds merge/threshold complexity.

## 11. When not to use it

Small bounded groups may choose either simplest. Strict broadcast completion needs explicit acknowledgement, not a feed pattern.

## 12. Common interview mistakes

Celebrity ignored; full post copied into every inbox; no deletion/block handling; offset pagination; global rank; cache considered feed truth; duplicate fan-out.

## 13. How it appears inside larger systems

News feeds, notifications, chat groups, activity streams, subscription delivery.

## 14. Likely interviewer follow-ups

Celebrity? inactive followers? delete/block? ranking? fan-out lag? cursor? storage? hybrid threshold? region?

## 15. Five-minute revision

Push=write amplification/fast read; pull=cheap write/read fan-out. Hybrid normal push + celebrity pull, idempotent inbox refs, cursor merge, delete/privacy filter, lag metrics.

## 16. Related notes

[[News Feed System]] · [[Queues Streams and Pub Sub]] · [[Caching Pattern]] · [[CQRS]]

## 17. Verified further reading

- [Apache Kafka documentation](https://kafka.apache.org/documentation/) — partitioned fan-out transport.\n- [Redis client-side caching](https://redis.io/docs/latest/develop/reference/client-side-caching/) — official hot/read cache considerations.

