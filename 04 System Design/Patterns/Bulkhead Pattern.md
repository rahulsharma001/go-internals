---
type: canonical
domain: system-design
topic: bulkhead-pattern
status: active
last_verified: 2026-07-17
---
# Bulkhead Pattern

## 1. Problem it solves

One dependency, tenant, priority class, or workload can exhaust a shared pool and take unrelated work down.

## 2. Simple mental model

Ship compartments contain flooding. Split finite concurrency, threads, connections, queues, or worker pools so one failure domain cannot consume all capacity.

## 3. How it works

Identify contention boundary; allocate separate bounded pools/queues/quotas; reserve critical capacity; reject/shed when a compartment fills; allow controlled borrowing only with safeguards; observe utilization and starvation.

## 4. Concrete example

Notification urgent transactional messages use reserved workers/provider quota separate from bulk marketing. Bulk backlog cannot delay password reset.

## 5. Detailed success flow

01. Each class uses its pool
11. spare capacity may be shared within policy
21. critical SLO holds under ordinary burst.

## 6. Detailed failure flow

01. Provider/tenant hangs and fills its pool.
11. Its requests time out/reject while other pools continue.
21. Circuit opens and backlog/admission prevents memory growth.

## 7. Scaling behaviour

More partitions improve isolation but fragment capacity and operations. Choose by tenant tier, dependency, priority, or resource cost; resize from demand/SLO.

## 8. Data consistency implications

Isolation may reorder work across pools; per-entity ordering needs one owner. Reject behavior must not silently lose durable accepted work.

## 9. Real implementation choices

Separate connection pools, semaphores, worker pools, topics/queues, Kubernetes node pools/namespaces, tenant quotas.

## 10. Trade-offs

Failure containment versus lower utilization/idle reserves. Fine isolation improves protection but increases configuration and fairness complexity.

## 11. When not to use it

Tiny uniform workloads where a single bounded pool is simpler. Do not use bulkheads to hide an under-capacity authoritative store.

## 12. Common interview mistakes

Queues separated but same DB pool; unbounded compartment; no priority starvation policy; dynamic tenants create pool explosion; accepted work dropped without state.

## 13. How it appears inside larger systems

API gateway tenants, notification priorities, crawler hosts, job classes, payment providers, query versus ingest planes.

## 14. Likely interviewer follow-ups

Isolation key? reserved capacity? borrowing? starvation? ordering? accepted backlog? what shared dependency remains?

## 15. Five-minute revision

Find shared finite pool → isolate by failure/cost/priority → bound each → reserve critical → define reject/borrow → observe utilization/starvation and hidden shared bottlenecks.

## 16. Related notes

[[Circuit Breaker Pattern]] · [[Backpressure and Load Shedding]] · [[Rate Limiting Pattern]]

## 17. Verified further reading

- [Microsoft bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead) — vendor architecture guidance.
- [Google Cloud reliability framework](https://cloud.google.com/architecture/framework/reliability) — official failure-domain and overload guidance.
