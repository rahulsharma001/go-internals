> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Load Balancing]].

---
type: canonical
domain: system-design
topic: load-balancing
status: learning
source_conversations:
  - "API Gateway Load Balancing | 2026-06-01 | 6a1db9c6-91d4-8323-9bf3-84285f920e7d"
---
# Load Balancing

## Problem it solves

Load balancing distributes requests/connections across healthy capacity while supporting failover, rollout, and overload control.

## Mental model and how it works

A balancer chooses an eligible backend using round-robin, least-connections, weighted, latency-aware, or hash/affinity rules. Health checks remove bad targets. L4 balances connections; L7 understands HTTP routes/headers and can terminate TLS. Long-lived connections balance at connection creation, so equal connections may still mean unequal work.

## Concrete example and dry run

Four WebSocket pods receive connections through an L7 gateway. Round-robin gives 1,000 connections each, but one tenant sends most messages through pod A. CPU/backlog skews. Least-connections still misses message rate; rebalance new connections using weighted health/saturation, partition tenants, and apply per-connection backpressure. Existing sockets remain until reconnect/drain.

## Success and failure scenarios

Success: healthy targets receive bounded work and deploys drain gracefully. Failure: sticky sessions pin hot users, health checks only test process liveness, or retries multiply load. Use readiness for dependencies, passive failure signals, retry budgets, connection draining, and circuit/bulkhead limits.

## Scaling and production choices

Examples: cloud L4/L7 load balancers, Envoy/HAProxy/Nginx, DNS/global traffic managers. Observe backend distribution, active connections, request rate, p95/p99, retry rate, queue depth, rejected work, and health flapping.

## Trade-offs and when not to use

Affinity helps stateful protocols but reduces flexibility; L7 offers routing/observability but costs CPU/latency; global routing improves locality but complicates consistency. One process may not need a separate balancer.

## Interview mistakes and follow-ups

Assuming round-robin equals even load; ignoring long-lived sockets; one health check; no drain. Follow-ups: zone loss? slow target? sticky session? TLS termination? connection mapping?

## Five-minute recall

Eligibility → algorithm → connection/request unit → health → retries → drain → overload → metrics.

Related: [[Stateless and Stateful Services]], [[Bulkhead Pattern]], [[WebSocket Chat or Realtime System]].

## Source metadata

Sanitized source listed above; personal architecture context excluded.
