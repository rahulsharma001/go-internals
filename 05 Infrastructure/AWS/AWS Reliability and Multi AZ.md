---
type: canonical
domain: infrastructure
topic: aws-reliability
status: learning
---

# AWS Reliability and Multi AZ

## Problem and mental model

Survives instance/node/AZ failures while meeting explicit recovery objectives.

## End-to-end flow and internals

Route/load balancer spans AZs → stateless capacity distributed → data service configured Multi-AZ/replication → backups/PITR protect corruption → tested restore/failover meets RTO/RPO. Multi-region adds routing and data conflict complexity.

## Failure modes and diagnosis

Test node/AZ loss, capacity in remaining AZs, target health, cross-AZ dependencies and restore. A Multi-AZ label does not guarantee application topology or backup correctness.

## Security, scaling and trade-offs

Use fault isolation, topology spread, idempotency, queues, graceful degradation and runbooks. Active-passive is simpler; active-active needs write ownership/conflict rules and cost.

## Interview questions and five-minute revision

Availability versus durability; failover versus restore; RTO versus RPO. Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[Pod Disruption Budgets]] · [[Disaster Recovery]] · [[Multi Region Architecture]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
