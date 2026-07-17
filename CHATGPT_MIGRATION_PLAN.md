# ChatGPT Migration Plan

> Prepared: 2026-07-17
> Status: extraction complete; permanent knowledge migration not started

## Migration boundary

The 213 extracts are immutable-style source evidence in Inbox, not a new knowledge base. Migrate one category at a time into existing canonical owners. Every promoted passage must retain its conversation ID/source link. Mixed records must be split during review, and unsupported claims remain unverified.

## Ordered execution plan

1. **Foundation implementation failures** — review the flagged conversations, especially `6a5778fc-3758-83ee-9998-cba2bb1b0577`, then improve existing slice/map/struct/method/interface/embedding/error canonicals and drills only where the source adds unique evidence. Create personal mistake and re-test records only from the user-confirmed failures.
2. **DSA in Go** — separate reusable Go syntax from language-independent patterns; historical Java solutions become a queue for fresh Go attempts, not copied solution notes.
3. **Verified project evidence** — triage NCS and CEE first because source candidates are concrete; then PulseCheck; leave CoMarketer blocked unless direct evidence is found/confirmed.
4. **System-design patterns** — promote reusable concepts one at a time, linking systems to patterns instead of copying explanations.
5. **Databases/messaging/cache/reliability/security** — select source-backed concepts by interview priority and verify version-sensitive claims.
6. **Kubernetes/AWS/Linux/networking/observability** — separate operational mechanics from system-design decisions and project claims.
7. **Interview/behavioural evidence** — verify all personal claims and metrics before producing STAR/project notes.

## High-priority source candidates

The following shortlist combines classifier failure signals with manually audited adjacent Go/interview conversations. Heuristics can over-match; the review decision remains manual.

| Conversation ID | Title | Priority flags | Extract |
| --- | --- | --- | --- |
| 6974ed44-b94c-8322-8f3c-0b684c7e8bba | DSA Focus vs Go | maps, methods and receivers, embedding and composition, error handling, Java DSA for Go interviews | 2026-01-24 - DSA Focus vs Go - 6974ed44.md |
| 69f0f564-696c-8321-96a9-42d209cc4862 | Go Structs and Pointers | maps, methods and receivers, interfaces | 2026-04-28 - Go Structs and Pointers - 69f0f564.md |
| 69f646ad-f5d8-8320-a796-ea63cab363ed | DSA Prep with Go | DSA implementation in Go, Java DSA for Go interviews | 2026-05-02 - DSA Prep with Go - 69f646ad.md |
| 69f8c79f-0024-8323-8c2a-13a02404bc79 | Go Backend Interview Prep | theory stronger than implementation | 2026-05-04 - Go Backend Interview Prep - 69f8c79f.md |
| 6a0880d8-e788-83a3-887b-78916efd303e | Go Program Correction | manually shortlisted adjacent source | 2026-05-16 - Go Program Correction - 6a0880d8.md |
| 6a11f5e6-8020-8321-8234-5e3661848716 | 45-Day Backend Interview Plan | DSA implementation in Go, Java DSA for Go interviews | 2026-05-23 - 45-Day Backend Interview Plan - 6a11f5e6.md |
| 6a33ff36-963c-83ee-92df-8e6684d5aedd | Go Developer Feedback | methods and receivers, embedding and composition | 2026-06-18 - Go Developer Feedback - 6a33ff36.md |
| 6a3b81c9-7418-83e8-85d6-683e381ed9ab | Senior Go Interview Prep | slices, maps, methods and receivers, error handling, theory stronger than implementation | 2026-06-24 - Senior Go Interview Prep - 6a3b81c9.md |
| 6a44bb84-6f10-83ee-917a-0d957485f633 | Senior Golang Interview Q&A | slices, maps, struct construction and constructors, methods and receivers, interfaces, error handling | 2026-07-01 - Senior Golang Interview Q&A - 6a44bb84.md |
| 6a5778fc-3758-83ee-9998-cba2bb1b0577 | Golang Implementation Fluency Issues | slices, maps, struct construction and constructors, methods and receivers, interfaces, embedding and composition, complete main invocation, balanced four-part slice failure, map and slice syntax failure, theory stronger than implementation, Java DSA for Go interviews | 2026-07-15 - Golang Implementation Fluency Issues - 6a5778fc.md |

The strongest single source is **Golang Implementation Fluency Issues** (`6a5778fc…`): it explicitly records the balanced four-part slice failure, map/slice syntax failure, theory/implementation gap, Java NeetCode practice for Go roles, interface invocation difficulty, and embedding/construction concerns. It should seed one verified interview-mistake cluster and scheduled re-tests—not duplicate all existing Go canonicals.

## System-design source map

Counts are conversation mentions/content matches, not proof that each deserves a note.

| Concept | Candidate conversations |
| --- | --- |
| caching | 96 |
| networking | 91 |
| AWS | 74 |
| Redis | 68 |
| Kafka | 67 |
| retry | 66 |
| rate limiting | 58 |
| Kubernetes | 56 |
| observability | 49 |
| YouTube | 47 |
| idempotency | 38 |
| Uber | 35 |
| WebSockets | 33 |
| PostgreSQL | 31 |
| backpressure | 28 |
| replication | 26 |
| circuit breaker | 23 |
| sharding | 22 |
| JWT | 21 |
| distributed locking | 19 |
| OAuth | 18 |
| leader election | 13 |
| Saga | 9 |
| event pipelines | 9 |
| mTLS | 9 |
| OIDC | 7 |
| bulkhead | 7 |
| CQRS | 6 |
| transactional outbox | 6 |
| CDC | 5 |

For every real-system design, use the vault standard plus a separate under-five-minute revision. Reusable Saga/outbox/CDC/CQRS/cache/idempotency/retry/circuit-breaker/bulkhead/backpressure/rate-limit/sharding/replication/locking material must have one canonical owner and be linked from Uber/YouTube/project designs.

## Project evidence assessment

| Project | Matched conversations | Audit assessment |
| --- | --- | --- |
| CEE Conductor Migration | 8 | Multiple code/architecture candidates exist around DALM, GetContacts, Conductor networking, and refactoring; exact migration boundary and personal ownership remain unverified. |
| CoMarketer WebSocket Architecture | 3 | Matches are incidental/name mentions; no clearly substantive project-specific conversation was established automatically. |
| NCS Permission Versioning | 7 | Substantive candidates exist, especially Permission Version Analysis and Versioned Permissions Planning; ownership and metrics still require verification. |
| PulseCheck Monitoring System | 14 | The Pulsecheck conversation is a substantive candidate, but other matches are mostly reused name/context; verify which material describes the actual project. |

Before updating a project canonical, create a claim ledger with: exact source passage, business problem, previous limitation, ownership, architecture, implementation, trade-off, failure/lesson, measurable impact source, redesign idea, STAR phrasing, and follow-up questions. Unknowns remain explicit.

## Per-category migration checklist

- Freeze the category's extract list from `classification_index.json`.
- Review mixed/manual false positives before content work.
- Map each useful passage to an existing canonical owner or a justified future canonical.
- Record source conversation ID and date.
- Verify technical/version-sensitive claims and all personal claims.
- Improve the canonical; do not create a parallel explanation.
- Add/update revision/drill/question assets only when they support a distinct learning action.
- Run executable examples/tests and link observed mistakes to scheduled re-tests.
- Archive superseded originals only in a later, separately approved execution stage.

## Explicitly deferred

No permanent note was reorganized, merged, rewritten from the export, or archived in this run. No readiness status, drill result, project metric, or personal achievement was inferred from ChatGPT text.
