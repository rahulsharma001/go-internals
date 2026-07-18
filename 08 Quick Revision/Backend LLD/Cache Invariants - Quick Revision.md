---
type: quick-revision
domain: backend-lld
topic: cache-invariants
review_time: under-5-minutes
---

# Cache Invariants — Quick Revision

## Mental Model

A cache is defined by lookup, update, eviction, expiry, and concurrency semantics. For LRU, a map and doubly linked list contain exactly the same entries; the front is most recent, the back is the eviction victim, and every map pointer targets one list node. For TTL, an entry is valid only while now < expiresAt. Lazy expiration avoids a cleanup goroutine but may retain cold expired entries until an operation scans them. Capacity is a hard bound after every successful write.

## Go / Design Checklist

Specify whether Get updates recency, whether Put updates existing entries, whether zero/negative TTL is rejected, and whether expired reads count as misses. container/list stores any, so type assertions must remain internal. Keep the map and list mutation under one lock. A background janitor needs clock/timer ownership and graceful shutdown; do not add it automatically. Tests cover update without growth, eviction after access, capacity one, expiry boundary, concurrent Get/Put, and invariant consistency. Follow-ups include sharding, admission policies, stampede prevention, persistence, and hit/miss/eviction metrics.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[TTL Cache]], [[LRU Cache]], [[LFU Cache]], [[Expiring Priority Queue]], [[In-Memory Key-Value Store]], [[Cache Invariants - Quick Revision]]

