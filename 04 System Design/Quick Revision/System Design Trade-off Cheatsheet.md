---
type: quick-revision
domain: system-design
---

# System Design Trade-off Cheatsheet

| Choice | Gains | Costs / question to answer |
|---|---|---|
| synchronous call | immediate answer, simple flow | temporal coupling, tail latency |
| asynchronous queue | buffering, decoupling, retries | eventual state, duplicates, backlog |
| cache | latency and origin relief | invalidation, stale data, hot keys |
| replication | read scale and failure tolerance | lag, conflicts, failover semantics |
| sharding | write/data scale | routing, rebalancing, cross-shard work |
| strong consistency | simpler invariants/read-after-write | latency/quorum availability |
| eventual consistency | availability/locality | stale views and reconciliation |
| SQL | transactions, constraints, relational access | horizontal-write/shape trade-offs |
| key-value/wide-column | key-based scale | limited joins/ad-hoc queries |
| orchestration saga | visible workflow/repair | coordinator/state-machine complexity |
| choreography saga | loose coupling | hidden flow, loops, observability |
| polling outbox | simpler operations | database scans/latency |
| CDC outbox | low-latency log relay | connector/log/schema operations |
| active-passive region | simpler authority | failover delay, idle/warm capacity |
| active-active region | locality/availability | conflicts, fencing, cost |

Strong phrasing: “I choose X because requirement Y needs semantic Z. The cost is C; I contain it with M and measure N.”

Weak phrasing: “X is scalable,” “NoSQL is faster,” “Kafka gives exactly once,” “microservices are best.”

Related: [[Trade-off Communication]] · [[System Design Trade-off Vocabulary and Interview Traps]]

