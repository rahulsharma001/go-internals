---
type: quick-revision
domain: system-design
review_time: 4-minutes
---
# API and Data Model Checklist

## API

- interview-sized critical operations only
- method/RPC and path/name
- request and response identifiers
- caller authentication and resource authorization owner
- idempotency key for retryable mutations
- cursor pagination for mutable large collections
- conflict, validation, quota, dependency, and ambiguous errors
- end-to-end deadline for synchronous calls

## State

For every table/store say:

- source of truth or derived/rebuildable?
- owner service and lifecycle?
- primary key and partition key?
- indexes derived from exact access patterns?
- conditional/transactional update protecting which invariant?
- retention and deletion?
- consistency/read freshness?

Avoid a generic `status` field without legal transitions and versioning. See [[API and Data Model Design]].
