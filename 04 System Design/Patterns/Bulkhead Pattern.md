---
type: canonical
domain: system-design
topic: bulkhead
status: learning
source_conversations:
  - "Scalable Approach Feedback | 2026-06-25 | 6a3d54ea-471c-83e8-953d-e26213c70a94"
---
# Bulkhead Pattern

## Problem it solves

Bulkheads isolate finite resources so one dependency, tenant, or workload cannot exhaust everything.

## Mental model and how it works

Partition concurrency, queues, connection pools, threads/goroutines, and rate budgets by failure domain. Each compartment has a cap and rejection/degradation policy. Shared spare capacity may be borrowed carefully without removing guaranteed minimums.

## Concrete example and dry run

An aggregator calls profile, preferences, and recommendations. Give each downstream a separate concurrency semaphore and timeout; reserve the main request pool for core profile work. Recommendation latency spikes: its 50 slots fill and further optional calls are skipped, while profile requests continue. The response marks recommendations unavailable.

## Success and failure scenarios

Success: optional dependency saturation does not starve core traffic. Failure: one shared HTTP pool or unbounded goroutines cause global connection/CPU exhaustion; fixed partitions waste capacity. Size from latency/QPS, expose rejections, and tune borrowing.

## Scaling and production choices

Per-dependency pools, worker queues, tenant quotas, Kubernetes resource limits, and separate processes/clusters provide increasing isolation. Observe occupancy, wait time, reject rate, borrowed capacity, saturation, and downstream latency.

## Trade-offs and when not to use

Isolation lowers utilization and adds configuration. Too many tiny pools create starvation. Do not partition resources without identifying a real blast-radius boundary.

## Interview mistakes and follow-ups

Confusing bulkhead with circuit breaker; only CPU limits while DB pool is shared; no overload response. Follow-ups: noisy tenant? pool sizing? priority traffic? spare borrowing? queue or reject?

## Five-minute recall

Finite resource → failure domain → separate cap/queue → reject/degrade → reserved core capacity → saturation metrics.

Related: [[Circuit Breaker Pattern]], [[Backpressure Pattern]], [[Load Balancing]].

## Source metadata

Generic principle extracted from the source; no project outcome retained.
