---
type: quick-revision
domain: system-design
review_time: 5-minutes
---
# Common Interview Traps

| Trap | Recovery sentence |
| --- | --- |
| ten minutes of clarification | “I’ll lock these assumptions and start the critical path; please redirect me if needed.” |
| memorized giant architecture | “Let me remove derived components and show the smallest working design first.” |
| requirements without priority | “The primary journey is ___; the other feature is a non-goal for this interview.” |
| numbers without consequence | “This estimate forces ___ because one node/store can handle roughly ___.” |
| vague database box | “This store owns ___; key ___ supports access pattern ___ and protects invariant ___.” |
| cache with no truth/miss | “The cache holds ___ under key ___; ___ remains authority and miss does ___.” |
| exactly-once claim | “Across this external boundary I can provide at-least-once plus idempotency/reconciliation.” |
| retry storm | “Retries share a deadline/budget; overload is shed, not retried indefinitely.” |
| horizontal-scale hand wave | “The partition unit is ___, routed by ___; hotspot ___ is handled by ___.” |
| no complete flow | “I’ll pause components and trace caller, read/write, commit, event, failure, response.” |
| no summary | “The final design guarantees ___, relaxes ___, and its largest remaining risk is ___.” |

After the mock, record only observed traps in [[Common Mistakes and Re-test Queue]].
