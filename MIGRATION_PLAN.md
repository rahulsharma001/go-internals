# Engineering OS Migration Plan

> Prepared: 2026-07-16
> Updated: 2026-07-17 after ChatGPT audit and deterministic source extraction
> Status: **structural cleanup and source extraction executed**; permanent ChatGPT knowledge migration remains intentionally deferred.
> Controls retained: preserve every source, use `99 Archive` for superseded originals, maintain source traceability, and do not claim readiness without evidence.

## ChatGPT extraction update — 2026-07-17

- [x] Validated all seven expected export files as JSON without changing the source directory.
- [x] Processed `conversations-000.json` through `conversations-004.json` as one history: 487 primary records and 487 unique conversation IDs.
- [x] Checked 13 shared records; all overlap primary history and produced no duplicates.
- [x] Reconstructed selected parent-linked branches and preserved alternative branch suffixes for 78 forked conversations.
- [x] Classified message content (not titles alone) and created 213 Inbox extracts for technical, potential, or mixed records.
- [x] Kept 213 excluded conversations out of Markdown source notes and queued 61 ambiguous records for manual review.
- [x] Generated deterministic machine indexes, schema/manifest reports, and a category migration plan.
- [ ] Review the Inbox by category and false-positive disposition before any permanent promotion.
- [ ] Verify confidential/project content and all personal claims before reuse.
- [ ] Execute future permanent migration one category at a time under [[CHATGPT_MIGRATION_PLAN]].

The export changes the source assessment: NCS and CEE have concrete project
candidate conversations; PulseCheck has at least one substantive candidate;
CoMarketer is still supported mainly by incidental/name mentions. The confirmed
implementation failures are explicitly present in conversation
`6a5778fc-3758-83ee-9998-cba2bb1b0577`. These findings supersede earlier
statements that no project-specific source existed, but they do not verify the
claims or authorize promotion into project canonicals.

## Execution update — full vault cleanup

- [x] Stage 1 usage-first Go foundations, quick revisions, and ten blank-editor drills completed; see [[MIGRATION_REPORT_STAGE_1]].
- [x] Complete numbered target directory structure created, including `01 Inbox` and project/interview/infrastructure placeholders.
- [x] Root technical/study/behavioural noise relocated; visible root now contains repository instructions, README, audit/migration plans, inventories, and migration reports only.
- [x] Legacy root directories migrated and removed; empty index shells and starter content preserved under `99 Archive/Legacy Structure`.
- [x] Remaining substantive Go foundations, concurrency, runtime/memory, Gin, MongoDB, and worker-pool sources assigned canonical owners.
- [x] Superseded technical packs preserved under `99 Archive/Superseded Originals` with canonical backlinks.
- [x] Fundamentals-first Go learning path, MOCs, dashboard, current-week focus, quick-revision index, drill/mistake indexes, and Google roadmap created.
- [x] Behavioural compilation relocated and marked as unverified personal evidence.
- [x] Active-link validation completed for numbered directories; the final scan found no unresolved active wikilink targets.
- [ ] DSA problem attempts, timed mocks, and mistake records require real practice evidence and were not fabricated.
- [ ] Kafka, caching, Kubernetes, AWS, general database, reliability, security, networking, and observability canonicals require substantive traceable sources.
- [ ] NCS, CEE, CoMarketer, and PulseCheck project notes require verified user-provided evidence.
- [ ] Behavioural claims require line-by-line verification before canonical STAR/project reuse.

Detailed results and remaining work: [[MIGRATION_REPORT_FULL_VAULT_CLEANUP]].

## Migration objective

Transform the vault from a repeated Go-internals curriculum into an implementation-driven Engineering Operating System where:

1. every concept has one canonical explanation;
2. revision, coding, interview, mistake, and project assets have distinct jobs;
3. interview readiness requires explain + cold code + modify + production application evidence;
4. dashboards retrieve current work instead of copying content;
5. foundational Go and DSA-in-Go execution precede advanced runtime expansion;
6. personal project and behavioral claims remain explicitly unverified until supported by the user.

## Non-negotiable execution controls

- Do not migrate all stages at once. Approve and execute one category/stage, verify it, then continue.
- Before each stage, capture a file/link manifest and a stage-specific move/merge/split ledger.
- Never delete an original. After verifying the replacement, move superseded sources to `99 Archive/Superseded Originals/` with source traceability.
- Use `99 Archive/Exact Duplicates/` only after byte/content equivalence is proven; the audit found no current exact duplicates.
- Preserve source URLs, imported-conversation identifiers, dates, and author context wherever present.
- Do not promote inferred metrics, scale, ownership, production outcomes, interview history, or project details into canonical notes.
- Verify version-sensitive Go/runtime claims against the intended Go version during the relevant stage.
- Keep aliases or update all wikilinks atomically when a note is renamed/moved.
- A checkbox saying “read” is not completion evidence.

## Proposed target structure

The execution phase should create this structure later, not during this audit:

```text
00 Home/
    Engineering Dashboard/
    Current Focus/
    Quick Revision Index/
    Interview Readiness/

01 Inbox/
    ChatGPT Export/
    Articles/
    PDFs/
    Unprocessed/

02 Go/
    Fundamentals/
    Collections/
    Structs Methods and Interfaces/
    Error Handling/
    Concurrency/
    Runtime and Memory/
    Standard Library/
    Networking/
    Testing/
    Design Patterns/
    Coding Drills/
    Production Scenarios/
    Interview Questions/

03 DSA/
    Patterns/
    Problems/
    Templates/
    Revision/
    Timed Mocks/
    Mistakes/

04 System Design/
    Interview Framework/
    Foundations/
    Patterns/
    Systems/
    Databases/
    Messaging/
    Caching/
    Reliability/
    Security/
    Observability/
    Quick Revision/

05 Infrastructure/
    Kubernetes/
    AWS/
    Docker/
    Linux/
    Networking/
    Terraform/
    Observability/

06 Interviews/
    Interview Experiences/
    Mistakes/
    Mock Interviews/
    Behavioural/
    Leadership/
    Company Preparation/

07 Projects/
    NCS/
    CEE/
    CoMarketer/
    PulseCheck/

08 Quick Revision/
    Go/
    DSA/
    System Design/
    Databases/
    Kafka and Messaging/
    Kubernetes/
    Networking/
    Security/
    Projects/

09 Roadmaps/
    Google/
    Current Week/
    Current Month/
    Applications/

10 Templates/

99 Archive/
    Superseded Originals/
    Exact Duplicates/
    Unclassified/
```

### Folder ownership rules

- `02 Go/...` owns durable Go knowledge and Go-specific drills/questions.
- `03 DSA/...` owns language-independent problem-solving patterns and attempt records; solutions default to Go.
- `04 System Design/...` owns reusable distributed-system concepts and complete real-system designs.
- `05 Infrastructure/...` owns operational technology mechanics. A Kubernetes system-design flow may live here and be linked from System Design; choose one canonical owner, never copies.
- `08 Quick Revision/...` contains short companions only. It must not become a second canonical library.
- `00 Home/...` and `09 Roadmaps/...` contain indexes, queries, and readiness state—not repeated explanations.
- `07 Projects/...` contains only verified personal/project evidence; generic architecture belongs in technical canonicals.

## Canonical-note architecture

### Canonical technical note contract

A normal canonical should be about 800–1,800 words and include, where relevant:

- problem and mental model;
- essential behavior and minimum syntax;
- one minimum executable example with complete `main()` usage;
- dry run plus success and failure paths;
- production use and trade-offs;
- common mistakes;
- links to the separate revision card, coding drill, interview questions, and related mistakes.

Internals should be included only when they change implementation, debugging, performance reasoning, or interview answers. A large runtime deep dive can be a separately linked canonical, but it cannot be the entry point for a foundation topic.

### Proposed Go canonical notes

Legend: **M** = merge multiple sources; **S** = split a source; **QR/CD/IQ** = quick revision/coding drill/interview-question companion needed.

| Proposed canonical | Existing source notes | Destination | Work | QR | CD | IQ | Manual conflicts/review |
|---|---|---|---|---:|---:|---:|---|
| Go Types and Value Semantics | T01; relevant T02; P01; Glossary | `02 Go/Fundamentals/Go Types and Value Semantics.md` | M+S | Yes | Yes | Yes | Remove embedding/method/interface ownership; verify absolute rules. |
| Strings, Bytes, Runes and UTF-8 | T03 + derivative pack | `02 Go/Fundamentals/Strings Bytes Runes and UTF-8.md` | M+S | Existing card to refine | Existing drill to refactor | Existing bank to trim | Separate runtime string layout from usage if still oversized. |
| Pointers in Go | T07; relevant T02 | `02 Go/Fundamentals/Pointers in Go.md` | M+S | Existing card to refocus | Existing drill | Existing bank | Move receivers, method sets, mutex-copying, and escape analysis to their owners. |
| Go Slices | T04; relevant T01/T02/T07; derivative pack | `02 Go/Collections/Go Slices.md` | M+S | Existing card to rewrite usage-first | Yes—new blank-editor set | Existing bank to trim | Runtime growth/version claims; arrays may be a section or separate small note. |
| Go Maps | T08; relevant P04/T01/T02; derivative pack | `02 Go/Collections/Go Maps.md` | M+S | Existing card to rewrite usage-first | Yes—new blank-editor set | Existing bank to trim | Separate hash fundamentals/map internals if canonical exceeds target. |
| Collection Transformations in Go | T04 §filter/reverse/rotate; T08 counting; exercises | `02 Go/Collections/Collection Transformations in Go.md` | M+S | Yes | Yes, primary asset | Yes | Avoid turning this into DSA pattern theory; focus on Go fluency. |
| Go Structs and Constructors | P01; T01; examples in P02/P05 | `02 Go/Structs Methods and Interfaces/Go Structs and Constructors.md` | M+S | Yes | Yes | Yes | Go has constructor functions by convention, not language constructors; clarify literal variants and validation. |
| Go Methods and Receivers | P02; T07/T01 overlaps | `02 Go/Structs Methods and Interfaces/Go Methods and Receivers.md` | M+S | Yes | Yes | Yes | Replace rigid pointer/value thresholds with decision factors. |
| Go Method Sets | P02; P05; T01; T07; T11 | `02 Go/Structs Methods and Interfaces/Go Method Sets.md` | M+S | Yes | Yes | Yes | Decide whether it remains its own canonical or a tightly scoped section; high retrieval value favors separate note. |
| Go Interfaces | P05; T11 fundamentals; T12 usage/design; T01/T09 typed-nil links | `02 Go/Structs Methods and Interfaces/Go Interfaces.md` | M+S | Yes | Yes | Yes | Keep `iface`/`eface` internals out of entry-level note; typed nil gets one authoritative explanation. |
| Interface Design in Go | T12; P05 small-interface material | `02 Go/Structs Methods and Interfaces/Interface Design in Go.md` | M+S | Existing card to refine | Existing exercise to refactor | Existing bank to trim | Distinguish test seam/design guidance from runtime implementation. |
| Struct Embedding and Composition | P01; T01; T12 examples | `02 Go/Structs Methods and Interfaces/Struct Embedding and Composition.md` | M+S | Yes | Yes | Yes | Must show promotion, ambiguity, receiver behavior, and “not inheritance” with complete `main()`. |
| Go Error Handling | T09; P05 error sections; relevant T10 | `02 Go/Error Handling/Go Error Handling.md` | M+S | Existing card to refocus | Yes—layered cold drill | Existing bank to trim | Move distributed retry policy out; keep errors.Is/As/wrapping and typed nil. |
| Defer, Panic and Recover | T10 + derivative pack | `02 Go/Error Handling/Defer Panic and Recover.md` | M+S | Existing card | Existing drill | Existing bank | Consider separate `defer` resource-management and panic-boundary sections, not multiple canonicals unless size demands. |
| Goroutines and Lifecycle | T13; P08; P10; relevant T15 | `02 Go/Concurrency/Goroutines and Lifecycle.md` | M+S | Yes | Yes | Yes | Usage/ownership before scheduler internals; loop-capture advice must be Go-version aware. |
| Mutexes and Data Race Safety | P03; mutex portions of T07/T13/T15 | `02 Go/Concurrency/Mutexes and Data Race Safety.md` | M+S | Yes | Yes | Yes | T18 is currently only a placeholder; do not invent its content. |
| Go Channels | T15; T16; derivative material | `02 Go/Concurrency/Go Channels.md` | M+S | Yes | Yes | Yes | Split `hchan` runtime implementation into advanced note; emphasize ownership/close rules. |
| Select in Go | T17 + derivative pack | `02 Go/Concurrency/Select in Go.md` | M+S | Existing card | Existing drill to make attempt-first | Existing bank | Preserve nil-channel and cancellation patterns; runtime selection internals optional. |
| Worker Pool | `Coding Problems/Worker Pool (fixed workers)`; T13/T15 examples | `02 Go/Design Patterns/Worker Pool.md` | M+S | Yes | Yes—complete runnable variant | Yes | Existing code is incomplete. Define bounded queue, cancellation, error, shutdown, and modification variants. |
| Context Cancellation | Mentions/placeholders in plans and channel/interface notes | `02 Go/Concurrency/Context Cancellation.md` | New from verified/curated sources later | Yes | Yes | Yes | No source canonical exists; requires future authoring with traceability. |
| Graceful Shutdown | Plan links; T13 lifecycle and T10 panic-boundary fragments | `02 Go/Production Scenarios/Graceful Shutdown.md` | New + small source extraction | Yes | Yes | Yes | Must not pretend missing T22 exists. |
| Go Scheduler | T14; T13; P08; P10; Glossary/Connections | `02 Go/Runtime and Memory/Go Scheduler.md` | M+S | Yes | Optional diagnostic drill | Existing T14 bank | Resolve repeated GMP descriptions and version-sensitive runtime detail. |
| Go Memory Allocation and Escape Analysis | T02; T07; P06; P09 | `02 Go/Runtime and Memory/Go Memory Allocation and Escape Analysis.md` | M+S | Existing T02 card to refocus | Existing exercise | Existing bank | Remove unsupported fixed latency/size claims or cite/version them. |
| Go Garbage Collector | P09; T02; roadmap placeholder T24 | `02 Go/Runtime and Memory/Go Garbage Collector.md` | M+S | Yes | Diagnostic drill | Yes | No T24 content exists; retain only verified current material. |
| Go Memory Model | empty root note; P03/T13/T15/T17 fragments | `02 Go/Runtime and Memory/Go Memory Model.md` | New from verified sources later | Yes | Race/happens-before drill | Yes | Current named note is empty; requires authoritative sourcing and Go-version context. |
| Go Map Internals | advanced T08; P04 | `02 Go/Runtime and Memory/Go Map Internals.md` | S+M | Existing internals card may point here | Optional | Existing advanced questions | Create only if map fundamentals remain concise; otherwise keep an advanced section. |
| Go Interface Internals | advanced T11/T02 | `02 Go/Runtime and Memory/Go Interface Internals.md` | M+S | Existing T11 card | Optional typed-nil diagnostic | Existing bank | Runtime terminology is version-sensitive; do not duplicate interface usage. |
| Go Testing Fundamentals | current `testing/_index`; examples elsewhere | `02 Go/Testing/Go Testing Fundamentals.md` | New later | Yes | Yes | Yes | No substantive current source. Stage 2 only. |
| Gin HTTP Services | frameworks/T05 + derivative pack | `02 Go/Networking/Gin HTTP Services.md` | M+S | Existing card | Existing exercise | Existing bank | Manual decision: current priority vs archive; prefer standard `net/http` foundation before framework depth. |
| MongoDB with Go | databases/T06 plus driver examples | `02 Go/Production Scenarios/MongoDB with Go.md` or link to DB canonical | S | Optional | Existing exercise | Existing bank | Separate Go-driver mechanics from MongoDB/database design; ownership decision needed. |

### Proposed DSA canonicals

No substantive DSA notes exist, so these are **execution-stage creations**, not migrations from hidden content.

| Canonical | Source | Destination | QR | CD/problems | IQ/manual review |
|---|---|---|---:|---:|---|
| Go DSA Template | Study Plan/Day 1 requirements only | `03 DSA/Templates/Go DSA Template.md` | Yes | It is the coding scaffold | Keep minimal: input/example invocation, helpers, tests, complexity. |
| Arrays and Hashing Pattern | Plan mentions only | `03 DSA/Patterns/Arrays and Hashing.md` | Yes | Required | Do not copy Go Maps internals; link to Go syntax canonical. |
| Two Pointers | Plan mentions only | `03 DSA/Patterns/Two Pointers.md` | Yes | Required | Add only after real problem attempts provide examples. |
| Sliding Window | Plan mentions only | `03 DSA/Patterns/Sliding Window.md` | Yes | Required | Track fixed/variable window failure modes. |
| Stack and Monotonic Stack | Plan mentions stack only | `03 DSA/Patterns/Stack and Monotonic Stack.md` | Yes | Required | Split if actual coverage grows. |
| Heap and Top-K | Plan mentions heap only | `03 DSA/Patterns/Heap and Top-K.md` | Yes | Required | Go `container/heap` fluency drill needed. |
| BFS and DFS | Plan mentions graphs only | `03 DSA/Patterns/BFS and DFS.md` | Yes | Required | Include Go adjacency/queue/visited templates. |
| Binary Search | No current source | `03 DSA/Patterns/Binary Search.md` | Yes | Required | Add only in Stage 3. |
| Dynamic Programming | Plan says defer until basics stable | `03 DSA/Patterns/Dynamic Programming.md` | Yes | Required | Explicitly later priority. |

Problem notes should be one problem/attempt record each and link to a pattern canonical; they should not repeat the entire pattern explanation.

## Go foundation execution blueprint (Stage 1)

Stage 1 is an **implementation gate**, not merely a content rewrite. Advanced runtime cards remain accessible but do not enter Current Focus until the foundation gate passes.

| Priority | Canonical | Five-minute revision | Blank-editor drill | Mistake capture | Re-test exercise |
|---|---|---|---|---|---|
| 1. Slices | Go Slices | Header, len/cap, append, aliasing, nil/empty, one production trap | Build copy/filter/map/dedupe/delete/reverse; every solution has `main()` and edge cases | Append result ignored; alias overwrite; pointer retention; len/cap confusion | Re-code two transformations after 2/7/21 days; modify to generic/in-place/non-mutating variant. |
| 2. Maps | Go Maps | make/literal, comma-ok, delete, iteration, zero value, synchronization | Frequency map, grouping, set, invert, nested map, map-of-struct update | Nil-map write; missing vs zero; addressability; unstable order; concurrent write | Re-code frequency/grouping under timer; change key/value types and constraints. |
| 3. Struct literals/constructors | Go Structs and Constructors | positional vs keyed literals, zero values, validation constructor | Model a request/domain object; keyed literal; constructor returning `(T,error)`; invoke from `main()` | Positional fragility; invalid zero state; pointer/value return without reason | Add optional field, validation rule, nested struct, and backward-compatible constructor. |
| 4. Receivers | Go Methods and Receivers | mutation/copy mental model and selection checklist | Implement a counter/value object/service with both receiver styles; predict mutation | Mixed receiver sets; copied mutex; value receiver losing slice-header update | Convert design under changed requirement; explain method-set impact. |
| 5. Interfaces | Go Interfaces + Method Sets | implicit satisfaction, consumer-defined interface, typed nil | Define consumer interface, two implementations, constructor injection, compile-time assertion, `main()` | Pointer type mismatch; fat interface; premature interface; typed nil | Add method/implementation; move interface to consumer; test substitution without mocks framework. |
| 6. Embedding | Struct Embedding and Composition | promotion, ambiguity, delegation, not inheritance | Embed logger/base component; resolve name collision; override with wrapper method | Assuming dynamic dispatch/inheritance; ambiguous promotion | Replace embedding with named composition and explain trade-off. |
| 7. Complete execution | Contract applied to all above | “Can I run it?” checklist | Every drill includes package/imports/types/functions/`main()`/expected output | Fragment compiles only in imagination; unused imports; no invocation | Cold-create file and run; then alter signature/behavior under timer. |
| 8. Error handling | Go Error Handling | wrap/Is/As, boundary mapping, success/failure | Repo→service→handler miniature with sentinel/custom/wrapped error and complete main | `%v` losing chain; compare after wrapping; log every layer; typed nil | Add retryable classification and new error while preserving API mapping. |
| 9. Collection transformations | Collection Transformations in Go | transformation decision table | Slices→map, map→slice, filter/group/dedupe/sort, nested structures | Java-shaped code, needless globals, alias mutation, missing capacity planning | Same tasks with structs, generics, stable order, memory constraint. |
| 10. DSA in Go | DSA pattern notes + Go template | One card per active pattern | At most two timed problems/session; first attempt hidden from solution | Log syntax, pattern, edge case, complexity, communication, timer failures separately | Re-code next morning, then 7/21-day unseen variant; modify constraints live. |

### Stage 1 completion gate

A foundation topic moves to `interview-ready` only when there is evidence that the user can:

1. explain it in 60–90 seconds without notes;
2. write the minimum executable example from a blank editor;
3. pass normal and edge-case tests;
4. modify the solution after a requirement change;
5. state one production success path, failure path, and trade-off;
6. pass a scheduled re-test with related mistakes resolved.

Reading the old long note, completing an MCQ, or recognizing a solution does not satisfy this gate.

## Proposed system-design canonicals

The table distinguishes **source-backed migration** from **future creation**. “No substantive source” means do not fabricate a note during migration; author it later from traceable technical sources or verified experience.

### Foundations and reusable patterns

| Canonical | Existing sources | Destination | Merge/split | QR | Coding/design drill | IQ | Manual conflict |
|---|---|---|---|---:|---:|---:|---|
| System Design Interview Framework | Day 1 prompt; Study Plan SD block; AGENTS standard | `04 System Design/Interview Framework/System Design Interview Framework.md` | M+new structure | Yes | Timed outline drill | Yes | Current sources are plans, not complete framework content. |
| API Design | Gin/API index fragments | `04 System Design/Foundations/API Design.md` | New later | Yes | Yes | Yes | Separate HTTP implementation from system API decisions. |
| Database Indexes | MongoDB note/questions; unverified behavioral mentions | `04 System Design/Databases/Database Indexes.md` | Extract+new verified content | Yes | Query/index case drill | Yes | Do not convert behavioral metrics into technical evidence. |
| Transactions and Isolation | Incidental behavioral/Go examples only | `04 System Design/Databases/Transactions and Isolation.md` | New later | Yes | Yes | Yes | No substantive source. |
| Replication and Failover | MongoDB note + behavioral failover claim | `04 System Design/Databases/Replication and Failover.md` | Extract technical parts | Yes | Failure-flow drill | Yes | Personal failover story remains separate/unverified. |
| Sharding and Partitioning | MongoDB/questions fragments | `04 System Design/Databases/Sharding and Partitioning.md` | Extract+new | Yes | Yes | Yes | Avoid MongoDB-only framing. |
| Caching | Generic map/cache examples; MongoDB; behavioral claims | `04 System Design/Caching/Caching.md` | Extract+new | Yes | Cache design drill | Yes | Separate in-process Go map cache from distributed cache design. |
| Cache Invalidation | Scattered behavioral mention | `04 System Design/Caching/Cache Invalidation.md` | New later | Yes | Yes | Yes | No verified technical source. |
| Idempotency | T09 classification and behavioral claim | `04 System Design/Reliability/Idempotency.md` | Extract+new | Yes | Request-flow drill | Yes | Keep personal Redis result unverified. |
| Retry | T09 retryable/non-retryable section | `04 System Design/Reliability/Retry.md` | Split+expand later | Yes | Backoff/jitter drill | Yes | Distinguish retry policy from Go error taxonomy. |
| Circuit Breaker | Channel/worker and behavioral mentions | `04 System Design/Reliability/Circuit Breaker.md` | New later | Yes | State-machine drill | Yes | No complete source. |
| Bulkhead | Mentions only | `04 System Design/Reliability/Bulkhead.md` | New later | Yes | Design drill | Yes | No substantive source. |
| Backpressure | T15, Worker Pool, behavioral story | `04 System Design/Reliability/Backpressure.md` | Extract+new | Yes | Queue-overload drill | Yes | Keep channel mechanics linked, not copied. |
| Rate Limiting | T15 token-bucket exercise; roadmap placeholder | `04 System Design/Reliability/Rate Limiting.md` | Extract+new | Yes | Algorithm/design drill | Yes | Clarify local vs distributed limiter. |
| Distributed Locking | Behavioral claim only | `04 System Design/Patterns/Distributed Locking.md` | New later | Yes | Failure-mode drill | Yes | No technical source; personal use unverified. |
| Leader Election | No substantive source | `04 System Design/Patterns/Leader Election.md` | New later | Yes | Failure-mode drill | Yes | Must cover leases/fencing, not generic locks. |
| Saga | Day 1 name only | `04 System Design/Patterns/Saga.md` | New later | Yes | Flow drill | Yes | No source content. |
| Transactional Outbox | Day 1 name only | `04 System Design/Patterns/Transactional Outbox.md` | New later | Yes | Success/failure flow | Yes | No source content. |
| Change Data Capture | Day 1 name only | `04 System Design/Patterns/Change Data Capture.md` | New later | Yes | Pipeline drill | Yes | No source content. |
| CQRS | Day 1 name only | `04 System Design/Patterns/CQRS.md` | New later | Yes | Trade-off drill | Yes | No source content. |
| Event-Driven Architecture | Index/roadmap and behavioral mentions | `04 System Design/Patterns/Event-Driven Architecture.md` | Extract generic parts+new | Yes | Design drill | Yes | Separate verified technology from behavioral claims. |
| Kafka Fundamentals | Messaging index/gap mentions | `04 System Design/Messaging/Kafka Fundamentals.md` | New later | Yes | Partition-flow drill | Yes | No substantive source. |
| Kafka Consumer Groups | Mentions only | `04 System Design/Messaging/Kafka Consumer Groups.md` | New later | Yes | Rebalance/failure drill | Yes | No substantive source. |
| Observability | Go notes/plan fragments; behavioral claim | `04 System Design/Observability/Observability.md` | Extract+new | Yes | Instrumentation/design drill | Yes | Infrastructure implementation may link from `05`; no duplicated theory. |
| OAuth 2.0 and OIDC | Behavioral/incidental mentions | `04 System Design/Security/OAuth 2.0 and OIDC.md` | New later | Yes | Flow drill | Yes | No substantive source. |
| JWT | Incidental mentions | `04 System Design/Security/JWT.md` | New later | Yes | Threat/failure drill | Yes | No substantive source. |
| mTLS | Requested scope only | `04 System Design/Security/mTLS.md` | New later | Yes | Handshake/trust drill | Yes | No current source. |
| API Gateway | Behavioral mention | `04 System Design/Foundations/API Gateway.md` | New later | Yes | Routing/failure drill | Yes | Personal architecture claim unverified. |
| WebSocket | Gin/API/P08 references + behavioral story | `04 System Design/Foundations/WebSocket.md` | Extract generic parts+new | Yes | Connection lifecycle drill | Yes | Do not label as CoMarketer without proof. |

### Real-system design notes

Create these only after the framework and reusable canonicals exist:

| System canonical | Current source | Destination | Required companions/manual review |
|---|---|---|---|
| Design Uber | No complete source | `04 System Design/Systems/Design Uber.md` | QR + interview follow-ups; author later, do not derive from mentions. |
| Design YouTube | No complete source | `04 System Design/Systems/Design YouTube.md` | QR + interview follow-ups; author later. |
| Design an Event-Driven Processing System | Worker/channel fragments + unverified behavioral stories | `04 System Design/Systems/Design an Event-Driven Processing System.md` | QR + failure drill; generic design must stay separate from personal evidence. |
| Kubernetes Request-to-Pod Flow | No substantive source | Prefer `05 Infrastructure/Kubernetes/Kubernetes Request-to-Pod Flow.md`, linked from System Design | QR + troubleshooting drill + IQ; choose one canonical owner. |

Every real-system note must follow: requirements, scale assumptions, entities, API, data model, HLD, complete success flow, complete failure flow, bottlenecks, reliability/observability, security, trade-offs, real technology choices, interview follow-ups, and five-minute revision. Reusable pattern details are links, not copied chapters.

## Learning and readiness property model

Do not add these properties until the templates and query behavior are approved. Proposed frontmatter:

```yaml
---
type: canonical              # canonical | quick-revision | coding-drill | mistake | project | roadmap
domain: go
topic: go-slices
status: implementation-needed
confidence: 2                # 0 unknown, 1 fragile, 2 guided, 3 independent, 4 pressure-tested
can_explain: false
can_code: false
can_modify: false
can_apply_in_production: false
last_reviewed: null          # YYYY-MM-DD; only an actual retrieval attempt updates this
next_review: null            # YYYY-MM-DD
related_mistakes: []         # wikilinks to concrete mistake notes
source_notes: []             # legacy/import traceability
---
```

### Status semantics

| Status | Entry condition | Exit evidence |
|---|---|---|
| `unprocessed` | Imported or audited but not triaged | Canonical owner and next action selected. |
| `learning` | Mental model/essential behavior is being formed | Can explain core behavior and complete guided examples. |
| `implementation-needed` | Theory exists but cold implementation is absent/failed | Working blank-editor implementation plus edge cases recorded. |
| `revision-needed` | Previously implemented but recall is weak/stale | Successful retrieval and scheduled next review. |
| `interview-ready` | All capability gates true and recent evidence exists | Reverts automatically/manually when a mock or re-test exposes a failure. |

### Capability evidence rules

- `can_explain`: dated 60–90 second answer or mock rating, not “read note.”
- `can_code`: dated cold implementation that runs/tests; solution was not visible during attempt.
- `can_modify`: dated requirement-change attempt completed under a timer.
- `can_apply_in_production`: can describe a realistic success path, failure path, observability, and trade-off. It does **not** assert personal production experience.
- `confidence`: subjective forecast only; never overrides evidence booleans.
- `last_reviewed`: last active retrieval attempt, not last file edit.
- `next_review`: explicitly scheduled from performance (suggested initial cadence 1/3/7/21/45 days, adjusted by failures).
- `related_mistakes`: only concrete mistake records, not generic “gotchas.”

### Readiness invariant

`status: interview-ready` requires all four capabilities true, no unresolved high-severity related mistake, and a recent successful re-test. Obsidian queries may flag inconsistent records; they should not silently manufacture readiness.

## Drill, revision, and mistake models

### Quick-revision note (250–600 words)

- definition and mental model;
- minimum syntax or one small diagram;
- common mistake;
- one production example;
- 30–60 second interview answer;
- one active-recall challenge;
- link to canonical and latest drill/mistake.

### Coding drill

- problem and why it matters;
- constraints and examples;
- expected implementation surface (without solution above the fold);
- complete `main()` usage or tests;
- edge cases;
- modification challenge;
- attempt table: date, time, result, hints, failure category;
- re-test history;
- solution in a collapsed/lower section or separate linked solution after attempt.

### Mistake note

- original question and context;
- exact observed failure (code/error/answer);
- root cause category: syntax, concept, pattern selection, edge case, complexity, communication, timer, or production judgment;
- correct pattern;
- smallest correction drill;
- re-test dates/results;
- links to canonical, drill, and mock/interview.

Generic teaching traps remain in canonicals; only actual failures become personal mistake notes.

## Google engineering roadmap proposal

Future file: `09 Roadmaps/Google/Google Engineering Roadmap.md`.

It should be a thin evidence dashboard linking to canonical material, attempts, and readiness queries. Proposed sections:

1. **Current gate and target role** — no fabricated deadline or interview stage.
2. **DSA pattern coverage** — pattern canonical, problems attempted, independent solves, overdue re-tests.
3. **Timed coding performance** — rolling mock duration, correctness, communication, modification success; link to timed mocks.
4. **Go implementation fluency** — slices/maps/structs/methods/interfaces/errors/collections/DSA capability matrix.
5. **System-design readiness** — framework reps, real-system designs, failure-flow quality, follow-up gaps.
6. **Behavioral and leadership stories** — verified STAR notes, evidence status, repeated questions, weak dimensions.
7. **Production project evidence** — links to verified NCS/CEE/CoMarketer/PulseCheck notes; unknowns visibly marked.
8. **Repeated mistakes** — query/link to unresolved and recurring mistake notes.
9. **Mock interviews** — type, date, score/rubric, feedback, corrective actions, re-test.
10. **Applications and stages** — company, role, source, stage, dates, next action; time-sensitive data separated from durable knowledge.
11. **This week’s constraints** — at most three focus outcomes, each with proof required.

It must not copy DSA explanations, Go syntax, system designs, STAR prose, or company research. It links to those canonical/evidence notes.

## Project evidence proposal

The audit found no exact project-name sources. Create no project canonical until the user provides or validates source material.

| Future project canonical | Destination | Current source status | Required manual decision |
|---|---|---|---|
| NCS Permission Versioning | `07 Projects/NCS/NCS Permission Versioning.md` | None found | Provide project identity, problem, role, design, code/artefact references, outcomes, and permitted disclosure boundaries. |
| CEE Conductor Migration | `07 Projects/CEE/CEE Conductor Migration.md` | None found | Clarify what “Conductor” is, migration endpoints, ownership, failure/rollback, and actual evidence. |
| CoMarketer WebSocket Architecture | `07 Projects/CoMarketer/CoMarketer WebSocket Architecture.md` | None found by project name | Confirm whether any behavioral WebSocket story refers to this project; do not assume equivalence. |
| PulseCheck Monitoring System | `07 Projects/PulseCheck/PulseCheck Monitoring System.md` | None found | Provide scope, architecture, signals, alerting, ownership, failures, and actual outcomes. |

Each project note will use:

- business problem;
- previous limitations;
- verified ownership and collaborators;
- architecture and complete request/event flow;
- implementation details linked to relevant technical canonicals;
- trade-offs and alternatives;
- failures, incidents, and recovery only if actually known;
- lessons and redesign ideas;
- measurable impact only where source evidence exists;
- a concise STAR answer derived from the verified record;
- technical follow-up questions and honest unknowns.

The behavioral compilation is a **candidate source requiring line-by-line verification**, not proof. During Stage 6/7, each metric and claim should be labeled `verified`, `needs verification`, or `remove from personal answer` before reuse.

## Merge/split decision rules

### Merge when

- two notes answer the same retrieval question for the same audience;
- the “simplified” note is merely another full explanation;
- glossary/daily-revision text repeats a canonical definition;
- a prerequisite and T-note differ mainly by depth but can fit a layered 800–1,800-word canonical.

### Split when

- a note has two independently searched concepts (for example receivers vs pointer mechanics);
- usage-first material is buried under runtime internals;
- reusable system-design pattern detail is copied inside a real-system design;
- a long note combines teaching, revision, questions, solutions, and personal attempts;
- the resulting canonical cannot meet the retrieval contract without losing useful material.

### Keep as companion when

- it supports a different action: five-minute recall, blank-editor practice, interview questioning, or mistake re-test;
- it is concise and links clearly to one canonical;
- it does not restate the full canonical.

### Archive after verification when

- all unique content has been migrated with source traceability;
- links/aliases resolve;
- executable examples have been retained or superseded by verified ones;
- the original is no longer the canonical or an active companion.

## Controlled migration stages and estimates

Estimates are planning ranges, not commitments. “Moved” counts physical source-note relocations; “merged” counts sources consolidated into a canonical; “split” counts sources whose distinct sections gain separate canonical owners. A source can be both merged and split, so columns do not sum to total notes. New source-backed canonicals may reuse existing names/content; “created” means a canonical identity is established, not that facts are invented.

### Stage 1 — Go foundations and current implementation weaknesses

Scope: slices, maps, structs/constructors, methods/receivers, method sets, interfaces, embedding, errors, collection transformations, executable `main()`, Go coding drills, foundation revision/questions, and initial DSA-in-Go scaffolding.

| Estimate | Count |
|---|---:|
| Files moved | 45–55 |
| Source files merged into canonicals | 24–34 |
| Source files split by concept | 7–10 |
| Canonical notes established | 12–15 |
| Revision notes established/refined | 10–12 |

Risks: losing unique examples while collapsing derivative packs; retaining unverified absolutes; breaking dense T/P links; mistakenly treating solution recognition as coding ability.

Manual decisions: arrays separate or within slices; Method Sets separate or within Methods; interface typed-nil ownership; Gin/MongoDB exclusion from Stage 1 focus; archive vs retain each visual/simplified asset; which foundation drills are attempted before solutions migrate.

Exit check: all ten priority areas have a canonical owner, quick revision, cold drill, mistake/re-test path, and at least one recorded executable attempt. No advanced runtime topic becomes Current Focus to compensate for a failed foundation gate.

### Stage 2 — Go concurrency, runtime, memory, networking, standard library, testing

| Estimate | Count |
|---|---:|
| Files moved | 30–38 |
| Source files merged | 16–24 |
| Source files split | 6–9 |
| Canonical notes established | 12–17 |
| Revision notes established/refined | 9–13 |

Includes goroutines, mutex/data races, channels, select, worker pool, scheduler, allocation/escape, GC, Go Memory Model, context, graceful shutdown, Gin/net-http decision, testing, and missing companions where justified.

Risks: version-sensitive runtime claims; giant channel/scheduler canonicals; authoring nonexistent T18–T29 as if sources existed; moving into internals before Stage 1 capability evidence.

Manual decisions: channel usage vs internals split; P08/P10/T13/T14 consolidation; fate of planned-but-empty topics; target Go version; standard `net/http` before Gin; testing scope.

### Stage 3 — DSA patterns, problems, Go implementations, timed mocks, mistakes

| Estimate | Count |
|---|---:|
| Existing files moved | 1–3 (plan fragments/indexes only) |
| Existing files merged | 1–2 |
| Existing files split | 1–2 |
| Canonical pattern/template notes created | 7–10 |
| Revision notes created | 6–9 |

Problem and timed-mock note counts depend on actual practice and are not prefilled. Add them incrementally from real attempts.

Risks: importing a passive NeetCode encyclopedia; writing solutions before attempts; copying Java habits into Go; measuring volume rather than independent/timed success.

Manual decisions: initial pattern set based on demonstrated misses; which historical Java solutions are worth re-solving in Go; timer/rubric; solution reveal convention.

### Stage 4 — System design foundations, patterns, systems, databases, messaging, caching, reliability, security, observability

| Estimate | Count |
|---|---:|
| Existing files moved | 3–6 |
| Existing files merged | 2–5 |
| Existing files split | 2–4 |
| Canonical notes created | 18–28, incrementally |
| Revision notes created | 12–20 |

The upper range assumes future sourced authoring; current vault content alone supports only a small subset.

Risks: inventing depth from keyword mentions; one enormous system-design note; duplicating patterns inside Uber/YouTube; treating behavioral anecdotes as architecture truth; source-free technology claims.

Manual decisions: canonical ownership across DB/messaging/infrastructure; source selection; which real systems match upcoming interviews; MongoDB technical vs Go-driver split; security depth.

### Stage 5 — Infrastructure: Kubernetes, AWS, Docker, Linux, networking, Terraform, observability

| Estimate | Count |
|---|---:|
| Existing files moved | 4–7 (mostly indexes/fragments) |
| Existing files merged | 1–3 |
| Existing files split | 0–2 |
| Canonical notes created | 10–18, only from sourced learning/experience |
| Revision notes created | 8–14 |

Risks: current substantive source is almost absent; cloud product details drift; system-design and infrastructure notes can duplicate each other.

Manual decisions: real interview/JD priority, AWS services actually used, Kubernetes depth, Terraform relevance, one owner for networking and observability concepts.

### Stage 6 — Interviews, mistakes, behavioral, leadership, mocks

| Estimate | Count |
|---|---:|
| Existing files moved | 5–8 |
| Existing files merged | 2–4 |
| Existing files split | 2–4 (behavioral compilation into verified story records) |
| Canonical/framework notes created | 4–8 |
| Revision/story cards created | 6–18, only after verification |

Risks: preserving fabricated/exaggerated claims; losing source wording; multiplying one story per question rather than one canonical story linked to many competencies; exposing confidential data.

Manual decisions: verify every employer/project/metric/ownership statement; story grouping; confidentiality boundaries; mock rubric; distinguish interview mistake from generic study gap.

### Stage 7 — Projects, quick-revision indexes, Google roadmap, dashboards

| Estimate | Count |
|---|---:|
| Existing files moved | 7–12 |
| Existing files merged | 3–6 |
| Existing files split | 1–3 |
| Canonical project/dashboard/roadmap notes created | 6–10 |
| Revision/project cards created | 4–8 |

Risks: dashboards becoming content dumps again; creating empty project shells that imply evidence; duplicated readiness state; stale application data.

Manual decisions: project source availability; verified metrics; dashboard query mechanism; weekly/monthly review cadence; archive old plans vs preserve as dated records.

## Recommended execution order inside each stage

1. Audit the stage sources again and freeze its source ledger.
2. Declare canonical owners and identify unique sections/examples in every source.
3. Build the canonical and companion set for **one topic only**.
4. Verify links, source traceability, note length, and executable examples.
5. Run/record the cold drill before exposing/refining solution content where possible.
6. Move superseded sources to archive; never delete.
7. Update dashboard/index links after the topic is stable.
8. Review stage metrics and manual decisions before the next topic/stage.

## Stage-level acceptance checklist

- [ ] Every migrated concept has exactly one canonical owner.
- [ ] Every archived source is represented in the migration/source ledger.
- [ ] No unique diagram, example, question, story, or source citation was lost.
- [ ] Canonicals meet the concise technical-note contract or have a documented reason not to.
- [ ] Revision companions are readable in five minutes.
- [ ] Coding drills hide solutions during the attempt and include complete invocation/tests.
- [ ] Readiness is supported by dated performance evidence.
- [ ] Broken links and aliases were checked in Obsidian after moves.
- [ ] Runtime/cloud claims were verified for version and source.
- [ ] Personal/project claims were confirmed by the user; unknowns remain unknown.
- [ ] Only the approved stage changed.

## Immediate next action after structural cleanup

Do not expand the folder structure or generate a broad content encyclopedia. Use [[Current Week]] to collect cold implementation, timed modification, mock, mistake, and re-test evidence. Let those observed gaps select the next source-backed DSA, system-design, infrastructure, behavioural, or project stage.
