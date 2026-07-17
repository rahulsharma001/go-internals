---
type: research-queue
domain: system-design
status: clear
last_checked: 2026-07-17
---
# External Research Queue

Use this queue only when a useful external claim or link cannot be verified. Internal canonical links remain usable while an item is open; never invent a URL.

## Open verification-needed items

None as of 2026-07-17.

## Validation corrections made during this rebuild

| Original problem | Resolution | Verification result |
| --- | --- | --- |
| generic AWS interaction-failure page did not resolve reliably | replaced with the specific AWS Well-Architected fail-fast and retry-control pages | official pages opened and matched the cited topic |
| Microsoft Architecture Center links omitted the locale and intermittently failed | replaced with current `en-us` pattern URLs; Saga uses the current `/patterns/saga` path | official pages opened for Bulkhead, Circuit Breaker, CQRS, Event Sourcing, and Saga |
| Redis caching-pattern path had moved | replaced with the current Redis client coding-patterns page | official page opened and described the pattern catalog |

## Add an item

| Date | Note/claim | Intended authority | Why verification failed | Safe internal fallback | Status |
| --- | --- | --- | --- | --- | --- |

Allowed status: `verification-needed`, `verified`, `removed`, `replaced`.

Reference policy: prefer official product documentation, RFCs/standards, public engineering publications, and reputable architecture references. Do not use random SEO summaries as authority.

Related: [[System Design Dashboard]] · [[FINAL SYSTEM DESIGN READINESS AUDIT]].
