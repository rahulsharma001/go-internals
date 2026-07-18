---
type: dashboard
domain: backend-lld
language: go
status: active
---

# Backend LLD Dashboard

Execution plan: [[Backend LLD - 50 Problem Plan]] · evidence tracker: [[Backend LLD Practice Tracker]] · mock: [[LLD Machine Coding Mock Template]]

## Progress Snapshot

Practice readiness stays at zero until a timed user attempt is recorded. Repository reference health is shown separately.

| Metric | Current state |
| --- | ---: |
| Problems | 50 |
| Running reference implementations | 5 |
| Reference implementations with tests passing | 5 |
| Reference implementations with race tests passing | pending final validation |
| Interview-ready practice rows | 0 |
| Reviews due | 0 scheduled |
| Weakest Go concepts | Not measurable until attempts are recorded |

## Next Recommended Work

1. Due reviews: none scheduled.
2. Incomplete P0 practice problem: [[Thread-Safe Bounded Queue]] from a blank editor.
3. Next new P0 after the enriched references: [[Priority Worker Pool]].
4. Weekly mock: create a 90-minute run in [[02 Go/Backend LLD/Mocks|LLD Mocks]] using [[LLD Machine Coding Mock Template]].

## Enriched Reference Packages

- [[Thread-Safe Bounded Queue]] — bounded FIFO, cancellation, drain-after-close ownership.
- [[Worker Pool]] — bounded admission, worker ownership, graceful drain, close deadline.
- [[TTL Cache]] — generic cache, injected clock, lazy expiry.
- [[LRU Cache]] — map/list invariant and synchronized recency.
- [[Token-Bucket Rate Limiter]] — continuous refill, cancellation-aware wait, explicit fairness trade-off.

These packages support reconstruction and comparison. They do not advance the practice tracker by themselves.

## Five-Minute Revision

[[Go Interface Design - Quick Revision]] · [[Slice and Map Pitfalls - Quick Revision]] · [[Mutex and Channel Ownership - Quick Revision]] · [[Context and Cancellation - Quick Revision]] · [[Graceful Shutdown - Quick Revision]] · [[Timers and Tickers - Quick Revision]] · [[State Machines - Quick Revision]] · [[Idempotency - Quick Revision]] · [[Retry and Backoff - Quick Revision]] · [[Cache Invariants - Quick Revision]]
