---
type: canonical
domain: infrastructure
topic: aws-data
status: learning
---

# RDS Aurora and DynamoDB

## Problem and mental model

Selects managed relational or key-value persistence from transaction and access-pattern needs.

## End-to-end flow and internals

Service in private subnet → bounded TLS connection pool → RDS/Aurora writer/readers for SQL transaction; or signed DynamoDB request using partition/sort key and conditional operation. Cache may sit ahead only with invalidation semantics.

## Failure modes and diagnosis

RDS: pool wait, sessions, locks, slow queries, CPU/IO/storage, failover. DynamoDB: throttling, consumed capacity, hot partitions, conditional failures and item/access pattern. Retries require idempotency.

## Security, scaling and trade-offs

RDS/Aurora supports joins/transactions and mature SQL at connection/vertical/replica constraints. DynamoDB scales known key access with denormalization and capacity/cost trade-offs. Multi-AZ is not multi-region.

## Interview questions and five-minute revision

Choose for an order ledger versus session lookup and defend consistency. Recall the request/event path, security boundary, bottleneck, recovery and rejected alternative.

## Related notes

[[Database Selection Guide]] · [[ElastiCache Redis]] · [[AWS Reliability and Multi AZ]]

## Source metadata

Curated from the infrastructure source conversations and existing system-design canonicals. AWS feature, quota, price, region and integration details are `needs-verification` against current official documentation.
