# Engineering OS Vault Inventory

> Audit date: 2026-07-16  
> Scope: content-level audit of every Markdown note and every relevant folder in the vault.  
> Mode: audit only. No existing note was edited, moved, renamed, merged, split, deleted, or archived.

## Executive finding

The vault is currently a **large Go-internals study pack**, not yet a complete Engineering Operating System. It contains strong explanations and many interview assets, but retrieval and implementation are undermined by repetition and scale:

- **121 user/content notes** (122 Markdown files including `AGENTS.md`), approximately **255,612 words**.
- **49 notes exceed 1,800 words**; several core notes are 6,000–10,000 words.
- The same topic is commonly represented in a main note, simplified note, visual map, revision card, question bank, exercise solution, `Daily Revision.md`, `Glossary.md`, and `Connections.md`.
- Go internals and concurrency receive far more space than basic cold implementation, DSA in Go, system design, infrastructure, projects, and mistake/re-test evidence.
- Existing exercises are useful, but most are titled or structured as **solutions** and therefore do not provide a clean blank-editor attempt surface or re-test history.
- The vault contains plans for many topics that do not yet exist. Missing-note wikilinks make roadmaps look more complete than the underlying material.
- The user-described project names and most system-design patterns are **not present as substantive notes**. They must not be inferred from generic behavioral claims.

The migration should therefore reduce the number of places one concept is explained, preserve specialized revision/drill/question assets only where they serve a distinct learning action, and make implementation evidence—not reading completion—the readiness gate.

## Scope and counting rules

- Count includes `.md` content notes and excludes `AGENTS.md` from the 121-note user-content total.
- `.obsidian/` configuration and plugin code were inspected as vault infrastructure, not counted as notes.
- `.agents/`, `.codex/`, and `Behavioural/` are empty.
- No exact duplicate Markdown files were found by file hash. “Duplicate” below means semantic overlap, not byte-identical content.
- Word counts are approximate shell token counts and are used only as triage signals.

## Current directory tree

```text
engineering-os/
├── AGENTS.md
├── .obsidian/                         # Obsidian settings + obsidian-git plugin
├── .agents/                           # empty
├── .codex/                            # empty
├── Behavioural/                       # empty; behavioral note is at root
├── Coding Problems/
│   └── Worker Pool (fixed workers).md
├── apis/
│   └── _index.md
├── cloud/
│   └── _index.md
├── databases/
│   ├── _index.md
│   └── T06 MongoDB.md
├── devops/
│   └── _index.md
├── exercises/                         # 14 solution-oriented topic exercise notes
│   ├── T01–T12 topic exercises (except T13–T15)
│   └── T16–T17 topic exercises
├── frameworks/
│   ├── _index.md
│   └── T05 GIN Framework.md
├── messaging/
│   └── _index.md
├── prerequisites/                     # 10 long prerequisite notes
│   ├── P01 Structs & Struct Memory Layout.md
│   ├── P02 Methods & Receivers.md
│   ├── P03 Mutex & Concurrency Safety Basics.md
│   ├── P04 Hash Functions & Hashing Basics.md
│   ├── P05 Interfaces Basics.md
│   ├── P06 Function Call Stack.md
│   ├── P07 Functions, Closures & Variable Capture.md
│   ├── P08 OS Threads vs Green Threads.md
│   ├── P09 GC Basics & Why It Matters.md
│   └── P10 OS Threads, Processes, and Go Scheduling Basics.md
├── questions/                         # 18 interview/MCQ notes
│   ├── T01–T12 topic question banks (except T13)
│   ├── T14–T17 topic question banks
│   └── Week 1 / Week 2 MCQ notes
├── revision/                          # 13 quick-revision cards
│   └── T01–T12 cards (except T13–T16) + T17
├── security/
│   └── _index.md
├── simplified/                        # 14 simplified restatements
│   └── T01–T12 (except T13–T15) + T16–T17
├── testing/
│   └── _index.md
├── visuals/                           # 13 visual maps
│   └── T01–T12 (except T13–T16) + T17
├── Application Targets.md
├── Connections.md
├── Daily Revision.md
├── Day 1 — Interview Preparation Plan.md
├── Gap Tracker.md
├── Glossary.md
├── Go Memory Model (Happens-Before).md # empty
├── INTERVIEW_PREP_STATUS.md
├── README.md                          # only old vault name
├── RAHUL SHARMA — BEHAVIORAL INTERVIEW COMPILATION MASTERCLASS.md
├── Roadmap.md
├── Study Plan.md
├── T01–T04.md                         # core Go notes
├── T07–T17.md                         # core Go notes; no root T05/T06
└── Welcome.md                         # untouched Obsidian starter note
```

### Notes per location

| Location | Notes | Observation |
|---|---:|---|
| Root | 28 | Core Go notes, dashboards, plans, behavioral content, and stale starter files are mixed together. |
| `prerequisites/` | 10 | Mostly long foundation notes; several should become canonical rather than “prerequisite” appendices. |
| `questions/` | 18 | Strong inventory, but many banks are themselves 2,000–6,600 words and repeat main notes. |
| `exercises/` | 14 | Predominantly answer/solution documents, not cold drill records. |
| `revision/` | 13 | Best-aligned five-minute assets; generally 372–568 words. |
| `simplified/` | 14 | Often repeats canonical content; one map note is 3,860 words and is not simplified. |
| `visuals/` | 13 | Useful but usually attached to the same small set of topics. |
| `databases/` | 2 | Only MongoDB plus an index. |
| `frameworks/` | 2 | Only Gin plus an index. |
| `apis/`, `cloud/`, `devops/`, `messaging/`, `security/`, `testing/` | 1 each | Empty index/table shells; no substantive topic notes. |
| `Coding Problems/` | 1 | One worker-pool prompt/outline; code is incomplete and has no `main()`. |

## Major topic areas actually present

| Area | Depth | Evidence and assessment |
|---|---|---|
| Go language/value semantics | Very deep | Types, pointers, strings, slices, maps, structs, methods, interfaces, errors, defer/panic. Strong theory; overly distributed. |
| Go runtime/memory | Very deep | Allocation, GC basics, goroutines, scheduler, channels, select, interface/map/slice internals. Advanced material dominates. |
| Go concurrency | Deep but incomplete lifecycle | Mutex basics, goroutines, GMP, channels, select, one worker-pool note. Context, graceful shutdown, leak prevention, fan-in/out are links/plans, not notes. |
| Frameworks/APIs | Narrow | Gin only. API index mentions GraphQL, gRPC, WebSocket; no corresponding technical notes. |
| Databases | Narrow | MongoDB only; generic indexing/transactions appear only incidentally. |
| DSA | Plan-only | Study schedules mention arrays, hashing, two pointers, sliding window, stack, heap, graphs, DP. No DSA problem corpus, Go templates, timed mock logs, or DSA mistake notes exist. |
| System design | Fragmentary | Generic mentions and behavioral stories, plus a Day-1 prompt. No canonical system-design framework or complete real-system design note. |
| Messaging | Placeholder | Kafka and consumer groups are mentioned in a gap/index context only; no substantive Kafka note. |
| Infrastructure/cloud | Placeholder | AWS/Kubernetes/Docker/CI/CD appear in indexes or behavioral claims; no canonical technical notes. |
| Security/networking | Fragmentary | OAuth/JWT/API Gateway/WebSocket occur in behavioral or incidental examples. No focused technical notes. |
| Behavioral/interview prep | Substantive but risky | One 3,565-word compilation with 18 answers, plans, application targets, and status notes. Claims require manual factual verification. |
| Projects | Absent as project records | No NCS, CEE, CoMarketer, or PulseCheck canonical project note. |

## Existing MOCs, indexes, dashboards, and plans

### MOCs and indexes

- `Connections.md`: the closest existing technical MOC; useful dependency/cross-topic map, but tied to T/P numbering and includes missing future notes.
- `Roadmap.md`: broad Go internals dependency roadmap; useful scope map, but creates many unresolved placeholder links and centers advanced internals.
- `Glossary.md`: 3,258-word Go glossary; retrieval value exists, but it repeats definitions already in canonical-topic candidates.
- `_index.md` files in `apis/`, `cloud/`, `databases/`, `devops/`, `frameworks/`, `messaging/`, `security/`, and `testing/`: category shells. Only database and framework indexes link to substantive content.

### Dashboards and preparation plans

- `Study Plan.md`: current declared single source of truth. It correctly says “if you are not coding, you are not preparing,” adds DSA in Go, mocks, cold builds, and failure scenarios. Its readiness definition still treats Wave A as already strong without stored implementation evidence.
- `Daily Revision.md`: active-recall dashboard, but at **10,576 words** it is too large for daily retrieval and duplicates question/answer content from topic assets.
- `INTERVIEW_PREP_STATUS.md`: concise meta-dashboard, last updated 2026-05-02. It links to local Cursor skill/rule paths outside this vault, which are not portable vault knowledge.
- `Day 1 — Interview Preparation Plan.md`: good implementation-first day template; includes a one-day system-design prompt and DSA block, but is a dated plan rather than a reusable template or completion record.
- `Application Targets.md`: phased application strategy with examples and an instruction to refresh openings. Company-specific lists are inherently time-sensitive.
- `Gap Tracker.md`: job-description gap tracker for one Kissht role dated 2026-04-23; valuable seed for a gap system but narrow and partly time-sensitive.
- `Roadmap.md`: Go-internals curriculum, not a Google engineering readiness roadmap.

## Note-size and quality triage

### Oversized notes

The highest-priority oversized notes are:

| Note | Approx. words | Problem |
|---|---:|---|
| `Daily Revision.md` | 10,576 | Daily surface is longer than many books’ chapters; duplicates topic cards and future placeholders. |
| `T15 Channel Internals.md` | 10,119 | Combines behavior, runtime internals, patterns, drills, rate limiting, interview Q&A, and production guidance. |
| `T09 Error Handling Patterns.md` | 8,736 | Contains language basics, internals, layered API policy, retry classification, many programs, and interview bank. |
| `T10 Defer, Panic & Recover Internals.md` | 7,379 | Multiple concepts and extensive examples in one note. |
| `T07 Pointers & Pointer Semantics.md` | 7,333 | Mixes pointer fundamentals, escape analysis, receivers, interfaces, mutex-copying, slices, and internals. |
| `T04 Arrays & Slice Internals.md` | 7,126 | Arrays, slice usage, runtime growth, GC retention, algorithms, drills, and Q&A. |
| `T08 Map Internals.md` | 7,078 | Map fundamentals, runtime internals, concurrency, cache design, exercises, and Q&A. |
| T01/T02 | 6,124 / 6,340 | Each covers several future canonical concepts and repeats foundation material. |
| Large T01–T08 question banks | 3,640–6,684 | Often function as alternate textbooks rather than question-only retrieval assets. |
| P02/P05/P06 and other prerequisites | 2,679–4,824 | Strong material, but far above concise foundation-note target. |
| `simplified/T08 Map Internals - Simplified.md` | 3,860 | Too long to be “simplified” or five-minute revision. |
| Behavioral compilation | 3,565 | Eighteen stories/answers in one file; hard to retrieve and verify story-by-story. |

There are **49 notes over 1,800 words**. Not every one must be split: question banks, roadmaps, and archives have different purposes. Each must nonetheless be challenged on retrieval time and repeated exposition.

### Very short, empty, or incomplete notes

| Note/group | Finding |
|---|---|
| `Go Memory Model (Happens-Before).md` | Empty (0 words). |
| `README.md` | Two words: old name `go-internals`. |
| `Welcome.md` | Default Obsidian starter content and a deliberately nonexistent `[[create a link]]`. |
| Six category `_index.md` notes | About 70 words each and contain empty topic tables. |
| `frameworks/_index.md`, `databases/_index.md` | About 80 words; populated with one topic each but contain suspicious escaped wikilink syntax. |
| T14/T15 question notes | 422 and 334 words; concise, but no answer depth or linked drill evidence compared with older question packs. |
| `simplified/T16...` | 295 words; useful short reminder but not linked to a revision card or implementation record. |
| `exercises/T17...` | 376 words; contains solutions but no attempt/re-test history. |
| Worker Pool | 1,500 words but implementation section is a partial outline, has no complete executable `main()`, no recorded run, and no re-test history. |

## Duplicate and overlapping information

No exact duplicate files exist. Semantic duplication is systematic:

| Concept cluster | Overlapping sources | Recommendation signal |
|---|---|---|
| Go type system, method sets, embedding | T01, P01, P02, P05, T07, T11, T12, their simplified/revision/visual/question/exercise notes, Daily Revision, Glossary | Establish separate concise canonicals for types, structs, methods/method sets, embedding/composition, and interfaces. Link instead of re-explaining. |
| Slices | T04, T01/T02/T07 excerpts, simplified/revision/visual/question/exercise assets, Daily Revision, Glossary | Keep one usage-first Slice canonical; split runtime growth details only if needed. |
| Maps | T08, P04, T01/T02 excerpts, simplified/revision/visual/question/exercise assets, Daily Revision, Glossary | Keep one usage-first Map canonical and one advanced internals section/note; do not maintain eight explanations. |
| Interfaces and typed nil | P05, T11, T12, T01/T02/T09, multiple derivative assets | Fundamentals/design, method sets, and runtime representation are distinct; typed-nil explanation should have one primary home and backlinks. |
| Receivers/pointers | P02, T07, T01/T02, P01/P05 | P02 is the best usage-first source; T07 should not own receivers and method sets. |
| Errors | T09, T10, P05, simplified/revision/visual/question/exercise, Daily Revision | One Error Handling canonical; keep panic/recover separate. Retry belongs to distributed-systems reliability, with a link from error classification. |
| Goroutine scheduler | P08, P10, T13, T14, T15 excerpts, Connections/Glossary | Merge repeated GMP explanations; preserve a usage-first goroutine note and a scheduler-internals canonical. |
| Channels | T15, T16, T17 plus derivative assets | Split channel usage/ownership from `hchan` internals; keep select distinct; fold buffer comparison into usage canonical. |
| MongoDB/Gin | Main + simplified + visual + revision + questions + exercises + Daily Revision | Decide whether these remain current interview priorities. If retained, use one canonical plus small revision/drill assets. |
| Active recall | Main-note “Practice Checkpoint,” question banks, revision cards, Daily Revision, MCQ weeks | Too many recall surfaces. Dashboard should index current cards/drills, not contain all answers. |

## Notes mixing unrelated or separately retrievable concepts

- `T01 Go Type System & Value Semantics.md`: defined types, aliases, zero values, method sets, interfaces, embedding, comparability, map keys.
- `T02 Go Memory Allocation & Value Semantics.md`: stack/heap, escape analysis, GC, pass-by-value, slices, maps, interfaces, receivers, cache layout and performance claims.
- `T07 Pointers & Pointer Semantics.md`: pointers, receiver choice, interface method sets, escape analysis, loop semantics, mutex copying, pointer-to-slice usage.
- `T09 Error Handling Patterns.md`: error language mechanics, sentinel/custom errors, wrapping, API-layer mapping, middleware logging, retry classification, typed nil.
- `T10 Defer, Panic & Recover Internals.md`: `defer`, panic/recover, resource management, goroutine boundaries, runtime internals.
- `T15 Channel Internals.md`: channel behavior, runtime layout, buffered/unbuffered choices, closing, select-related behavior, worker patterns, rate limiter, backpressure.
- `Daily Revision.md`: every completed and planned topic plus answers; a dashboard and content repository combined.
- Behavioral compilation: 18 different behavioral stories/approaches and interviewer questions; each should eventually be independently verifiable/retrievable.
- `Glossary.md`: definitions across almost every Go category; duplicates canonical explanations and can become an index of short definitions/backlinks.

## Unclear filenames and naming problems

- T/P numeric prefixes (`T01`, `P05`) encode curriculum order rather than durable retrieval terms.
- `T01 Go Type System & Value Semantics` and `T02 Go Memory Allocation & Value Semantics` overlap by title and content.
- `T14 GMP Scheduler` uses a Go-specific acronym that is poor for novice retrieval; “Go Scheduler” is clearer.
- `T11 Interface Internals (iface & eface)` is runtime-implementation terminology, while most interview needs start with “Go Interfaces.”
- `RAHUL SHARMA — BEHAVIORAL INTERVIEW COMPILATION MASTERCLASS.md` is promotional/verbose, has an empty H1, and does not reveal story/project names.
- `Day 1 — Interview Preparation Plan.md` is time-bound but has no date, completion state, or relationship to subsequent days.
- `_index.md` is clear inside a folder but ambiguous in global search.
- “Simplified,” “Revision,” “Visual Map,” “Interview Questions,” and “Exercises” are consistent suffixes, but create five parallel navigation systems.
- `Worker Pool (fixed workers).md` names only one variant and hides that it is a drill/outline rather than a canonical pattern note.

## Misplaced notes

- All root T-notes should eventually live under Go categories.
- Root dashboards/plans (`Daily Revision`, `Study Plan`, status) belong under Home/Roadmaps after canonical roles are decided.
- Root behavioral compilation belongs under `06 Interviews/Behavioural/`, not beside Go internals.
- Root `Application Targets.md` belongs under `09 Roadmaps/Applications/`.
- Root `Gap Tracker.md` belongs under Current Focus or interview mistakes/gaps, depending on whether it tracks job requirements or demonstrated failures.
- `Coding Problems/Worker Pool...` is a Go concurrency coding drill, not a generic coding-problem/DSA note.
- Gin is under `frameworks/` while the target structure has Go Networking/Production Scenarios; destination needs manual choice.
- MongoDB currently lives under `databases/`; target distinguishes system-design Databases and quick revision. Canonical technical ownership should be `04 System Design/Databases/`, with Go-driver examples linked rather than mixed.
- Empty `Behavioural/` conflicts with the actual root location of behavioral content.

## Potentially stale or unverified material

- `README.md` still names the vault `go-internals`.
- `Welcome.md` is untouched starter content.
- `INTERVIEW_PREP_STATUS.md` is dated 2026-05-02 and declares no pending tasks despite major missing planned notes.
- `Gap Tracker.md` is tied to a Kissht job description dated 2026-04-23; requirements and openings may have changed.
- `Application Targets.md` explicitly contains employer examples that require refreshing at application time.
- `Roadmap.md`, `Study Plan.md`, `Daily Revision.md`, and `Connections.md` link to many not-yet-created T18–T29 topics, so their apparent progress model is ahead of the corpus.
- Runtime implementation details and numerical heuristics in long Go notes (growth formulas, struct layouts, performance nanoseconds, size thresholds, runtime-field descriptions) are version-sensitive and need source/version verification during migration.
- Several statements use absolute production guidance (“always,” fixed byte thresholds, “sub-millisecond,” etc.). They should be reviewed as heuristics, not retained as universal rules.
- The behavioral compilation contains many specific employers, responsibilities, scales, metrics, uptime values, incident outcomes, and leadership claims. The audit does **not** validate them. Every claim must be confirmed by the user against real evidence before becoming a project or STAR canonical.

## Broken or suspicious internal links

### Clearly broken or missing companions

- `Welcome.md` → `[[create a link]]` (starter placeholder).
- `T13 Goroutine Internals.md` → missing simplified, exercise, and interview-question companions.
- `T14 GMP Scheduler.md` → missing exercise companion.
- `T15 Channel Internals.md` → missing simplified companion.
- Roadmap/planning links to missing `T18`–`T29` notes, including Mutex/RWMutex Internals, Context, Worker Pool, Fan-Out/Fan-In, Graceful Shutdown, Goroutine Leak Prevention, GC Deep Dive/Tuning, `net/http`, gRPC, `database/sql`, and Observability.

### Unresolved roadmap-topic links

`Roadmap.md` also links to nonexistent notes for atomic operations, race detector, `sync`/`sync.Pool`, memory ordering, stack/allocator/compiler internals, reflection, `unsafe`, generics, testing/fuzzing, benchmarking, build tags/CGO, code generation, configuration, dependency injection, networking/netpoll, rate limiting, pipelines, pub-sub/event-driven patterns, and microservices patterns.

These are not all errors: many are intentional future-topic placeholders. They are nevertheless suspicious in an operational dashboard because an unresolved link is indistinguishable from a missing note.

### Naming/syntax mismatches

- `Daily Revision.md` uses `T21 Fan-Out Fan-In Pattern`; other plans use `T21 Fan-Out / Fan-In Pattern`.
- `P09` references `T25 GC Tuning & Memory Limits`, while plans use `T25 GC Tuning (GOGC & GOMEMLIMIT)`.
- `databases/_index.md` and `frameworks/_index.md` contain backslash-escaped pipe syntax inside wikilinks; verify in Obsidian because the parsed target appears to include a trailing backslash.
- Portable-link concern: `INTERVIEW_PREP_STATUS.md` refers to `~/.cursor/...` files outside the vault.

## Existing quick-revision material

Strongest assets:

- 13 `revision/` cards, normally **372–568 words**, with recall grids, a core visual, quick-fire questions, and a verbal answer. These are closest to the target five-minute format.
- 13 `visuals/` maps, normally 319–649 words. Keep only when the diagram materially aids recall; otherwise fold into the canonical or revision card.
- 14 `simplified/` notes. Quality/length is inconsistent: T16 is 295 words; T08 is 3,860 words. Many are alternate explanations rather than revision tools.
- `Daily Revision.md` contains collapsible blurts and answers, but its size makes it an index failure. Its content should eventually be linked/queried from topic records rather than copied.
- Several prerequisite notes embed “Quick Visual Recap” or verbal answers.

Coverage gaps: no revision cards for structs, methods/receivers, interface basics as a usage-first topic, T13–T16 concurrency sequence (except simplified T16), worker pool, context, Go Memory Model, DSA patterns, system design, infrastructure, projects, or behavioral stories.

## Existing interview questions

- 16 topic-specific interview-question notes covering T01–T12 (except T13) and T14–T17.
- Two weekly MCQ packs covering T07–T12.
- Every major main T-note includes “Interview Gold Questions” and/or a comprehensive question section, creating duplication with `questions/`.
- Revision cards also contain quick-fire questions.
- Behavioral compilation contains 18 behavioral prompts and strategic interviewer questions.
- `Day 1` includes Go, DSA, system-design, and behavioral prompts.

The vault has ample **question quantity** for existing Go topics. The gap is recorded performance: attempt date, answer quality, timing, failure category, correction drill, and re-test.

## Existing coding drills

- 14 exercise notes for T01–T12 (except T13–T15) and T16–T17.
- Main T-notes typically contain Tier 1 predict-output, Tier 2 fix-bug, and Tier 3 build-it checkpoints.
- `T04` includes slice algorithms such as filter/reverse/rotate and full executable examples.
- `T08` includes map basics, copy-edit-write, safe concurrent access, and a TTL-cache build prompt.
- `P01`, `P02`, and `P05` contain executable struct/method/interface examples.
- `Coding Problems/Worker Pool (fixed workers).md` provides requirements, traps, debug scenarios, and a solution outline, but not a complete executable solution.
- `Study Plan.md` requires DSA in Go and a cold build, but no actual DSA problem note or timed result exists.

Critical drill weaknesses:

- Exercise filenames often say “Exercise Solutions,” and answers are in the same note; this encourages recognition instead of recall.
- No common drill schema for constraints, attempt status, `main()` invocation, modifications, test result, failure cause, or re-test history.
- Many long canonical notes have numerous snippets but few complete `main()` examples relative to their volume. Notably T12 has 16 Go fences and no `func main()`.
- No evidence that examples compile against a recorded Go version.
- No DSA-in-Go implementation corpus despite the explicit plan.

## Existing mistake and gap trackers

- `Gap Tracker.md`: job-description gaps, not demonstrated interview/coding mistakes.
- `Study Plan.md` contains an interview-log section and tells the user to feed misses into future focus, but it is not a dedicated mistake record system.
- Main notes include “Mistake That Teaches” and gotcha sections; these are generic teaching examples, not the user’s observed failures.
- Worker Pool contains a debug scenario but no personal attempt result.
- No dedicated DSA mistakes folder/note, Go implementation mistake log, mock-interview log, re-test schedule, or per-topic related-mistakes field exists.

## Go foundation material audit

| Priority | Existing material | Current gap |
|---|---|---|
| Slices | T04 plus revision, visual, simplified, questions, exercise; related T01/T02/T07 content | Excellent theory. Needs usage-first canonical, cold transformations, complete `main()`, modification challenges, and recorded re-tests. |
| Maps | T08 + P04 plus all derivative layers | Excellent internals. Needs basic construction/lookup/update/count/group transformations under timer before internals. |
| Struct literals/constructors | P01; parts of T01/P02/P05 | P01 covers declaration forms and examples, but there is no dedicated revision card or blank-editor constructor drill. |
| Value/pointer receivers | P02; T07/T01/P05 overlaps | Strong explanations and many `main()` examples. Needs one concise canonical and timed choose/fix/modify drills. |
| Interfaces | P05 usage, T11 internals, T12 design, overlaps elsewhere | Three useful depth levels but excessive repetition. Usage and implementation should gate runtime internals. |
| Embedding/composition | P01 and T01; scattered interface/design references | No dedicated canonical, revision card, or cold implementation drill. |
| Complete `main()` | Present in many T/P/exercise notes | Uneven: snippets dominate some topics; no vault-wide proof that minimum examples compile. |
| Error handling | T09/T10/P05 plus derivative layers | Very deep. Needs a concise usage-first canonical and blank repo→service→handler drills before runtime details. |
| Collection transformations | T04 filter/reverse/rotate; T08 counting; scattered exercises | No focused Go collection-transform drill set tied to interview timing. |
| DSA in Go | Plans only | No problem notes, templates, timed mocks, attempt history, or re-tests. This is the largest execution gap. |

## System-design knowledge audit

Substantive, canonical system-design notes do **not** currently exist. Coverage is incidental:

- Worker pools/backpressure/rate limiting: examples in channel/worker notes.
- Retry classification: section in T09; not a distributed retry design.
- Redis caching/idempotency/distributed locking, DLQ/circuit breaker, observability, Kubernetes, AWS, API Gateway, WebSocket, replication/failover, and event-driven orchestration: primarily claims or anecdotes in the behavioral compilation.
- MongoDB: a technology note and associated learning pack, not a database/system-design foundations set.
- Saga/outbox/CDC/CQRS: mentioned only in the audit instructions/Day-1 prompt, not explained.
- Kafka/consumer groups: index/gap mentions only.
- Uber/YouTube: mentions, not complete system designs.
- OAuth/JWT/mTLS, leader election, sharding, generic transactions/isolation, database indexes, API design, security, and Kubernetes request-to-pod flow: no focused canonical notes.

Behavioral anecdotes must not be converted into technical canonicals without separating verified personal evidence from generic architectural explanation.

## Project evidence audit

| Requested project | Exact named content found | Related but insufficient content | Audit conclusion |
|---|---|---|---|
| NCS Permission Versioning | None | Generic permission/token/security and map-version wording only | No source note; require user-supplied evidence. |
| CEE Conductor Migration | None | Generic migration/orchestration stories; “conductor” search matches ordinary words such as “concurrent”/“exceeded,” not the project | No source note; require user-supplied evidence. |
| CoMarketer WebSocket Architecture | None by project name | Behavioral WebSocket connection-broker and goroutine-leak claims at Netcore; generic Gin/WebSocket references | Do not equate these with CoMarketer. Require project-specific confirmation. |
| PulseCheck Monitoring System | None | Generic observability/Prometheus/dashboard claims | No source note; require user-supplied evidence. |

The behavioral compilation may contain reusable interview evidence, but none of the four requested project identities is established. Ownership, architecture, trade-offs, failures, metrics, and STAR answers must remain “unknown” until verified.

## Highest-risk findings for migration

1. **Accidental invention:** converting behavioral prose or generic examples into personal project evidence.
2. **Information loss through aggressive merging:** derivative notes sometimes contain unique diagrams, questions, or executable solutions.
3. **Canonical bloat:** simply renaming 7,000-word main notes would preserve the core retrieval problem.
4. **False readiness:** checkboxes or “already strong” labels without cold-code, modify, and re-test evidence.
5. **Advanced-topic gravity:** scheduler/channel/map internals can continue displacing slices, maps, structs, methods, interfaces, and DSA implementation.
6. **Link breakage:** T/P names are heavily cross-linked; moves/renames require an alias/link-rewrite ledger during execution.
7. **Version-sensitive Go details:** runtime claims need verification before becoming durable canonical content.

## Audit conclusion

The vault’s strongest reusable assets are its Go explanations, compact revision cards, executable examples, interview prompts, and implementation-first language in the study plan. Its weakest areas are canonical ownership, retrieval speed, cold implementation evidence, DSA in Go, mistake/re-test tracking, system-design depth, and verified project records.

The first migration stage should therefore **pause advanced expansion**, establish usage-first Go foundation canonicals and drills, turn the dashboard into an index rather than a content dump, and require evidence across explain → code → modify → production before a topic becomes interview-ready.
