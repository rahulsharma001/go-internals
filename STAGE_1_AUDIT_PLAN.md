# Stage 1 Migration Audit Plan

> Audit frozen: 2026-07-16  
> Scope: Go foundations and current implementation weaknesses only  
> Status: approved for execution by the Stage 1 migration request

## Scope boundary

Stage 1 will establish usage-first canonical ownership for:

- Go types and value semantics needed by the foundation topics;
- slices, maps, and collection transformations;
- structs and constructor functions;
- methods, value/pointer receivers, and method sets;
- interfaces, interface design, and typed-nil behavior;
- struct embedding and composition;
- error values, wrapping, `errors.Is`, `errors.As`, and boundary mapping;
- complete executable `main()` programs;
- blank-editor drills and source-backed implementation-weakness records.

Stage 1 explicitly excludes standalone migration of strings/UTF-8, pointers, memory allocation, escape analysis, garbage collection, map/interface/runtime internals, defer/panic/recover, concurrency, DSA, Gin, MongoDB, system design, infrastructure, behavioral content, projects, and imported ChatGPT history.

## Canonical ownership decisions

| Concept | Canonical owner |
|---|---|
| Types and value semantics | `02 Go/Fundamentals/Go Types and Value Semantics.md` |
| Complete executable program structure | `02 Go/Fundamentals/Complete Go Programs.md` |
| Slices and arrays needed to use slices | `02 Go/Collections/Go Slices.md` |
| Maps | `02 Go/Collections/Go Maps.md` |
| Collection transformations | `02 Go/Collections/Collection Transformations in Go.md` |
| Structs and constructor functions | `02 Go/Structs Methods and Interfaces/Go Structs and Constructors.md` |
| Methods and receivers | `02 Go/Structs Methods and Interfaces/Go Methods and Receivers.md` |
| Method sets | `02 Go/Structs Methods and Interfaces/Go Method Sets.md` |
| Interface mechanics and typed nil | `02 Go/Structs Methods and Interfaces/Go Interfaces.md` |
| Interface placement and size | `02 Go/Structs Methods and Interfaces/Interface Design in Go.md` |
| Embedding and composition | `02 Go/Structs Methods and Interfaces/Struct Embedding and Composition.md` |
| Error handling | `02 Go/Error Handling/Go Error Handling.md` |

Arrays remain a concise section of `Go Slices`; method sets remain a separate canonical because they are a frequent implementation failure. Typed nil is owned by `Go Interfaces` and linked from `Go Error Handling`. Map and interface runtime representations stay deferred to Stage 2 sources. Gin and MongoDB remain excluded.

## Frozen source manifest

The following 33 originals are superseded by the canonical/companion set and will be moved intact to `99 Archive/Superseded Originals/`, preserving their former relative directory in the archive:

- `T01 Go Type System & Value Semantics.md`
- `T04 Arrays & Slice Internals.md`
- `T08 Map Internals.md`
- `T09 Error Handling Patterns.md`
- `T12 Interface Design Principles.md`
- `prerequisites/P01 Structs & Struct Memory Layout.md`
- `prerequisites/P02 Methods & Receivers.md`
- `prerequisites/P05 Interfaces Basics.md`
- the T01, T04, T08, T09, and T12 notes in each of `exercises/`, `questions/`, `revision/`, `simplified/`, and `visuals/`

Mixed or later-stage sources remain active: T02, T03, T07, T10, T11, T13-T17, P03, P04, and P06-P10 and all of their companions.

## Merge and split ledger

| Source | Merge/split decision |
|---|---|
| T01 | Split type/value semantics, method sets, interfaces, embedding, and map comparability into their canonical owners. |
| T04 pack | Merge usage material into Slices and Collection Transformations; retain the complete original for deferred runtime detail. |
| T08 pack | Merge usage material into Maps and Collection Transformations; retain the complete original for deferred internals/concurrency detail. |
| T09 pack | Merge language-level error handling into Go Error Handling; defer distributed retry policy to a later stage. |
| T12 pack | Merge interface mechanics into Go Interfaces and design guidance into Interface Design in Go. |
| P01 | Split structs/constructors and embedding; retain memory-layout detail in the archived source for later runtime treatment. |
| P02 | Split receivers and method sets. |
| P05 | Split interfaces, method sets, and error/typed-nil behavior. |

## Link-repair strategy

1. Add a visible archive notice to every moved original, linking to its canonical replacement(s).
2. Replace active wikilinks to moved T/P names with canonical names.
3. Retain legacy titles in canonical `aliases` so plain old wikilinks still resolve when practical.
4. Validate explicit wikilink targets after moves; unresolved future-roadmap placeholders are outside Stage 1 and will be reported, not changed.

## Verification plan

- confirm every original exists under the archive and none was deleted;
- verify every canonical contains source traceability and a complete executable example;
- verify quick-revision notes are 250-600 words where practical and under five minutes;
- verify the ten requested drills are blank-editor-first and contain complete runnable solutions below a collapsed section;
- compile every Go solution block marked `go verify` in the new Stage 1 notes;
- scan active Markdown for links to moved paths/titles and repair them;
- ensure no later-stage content file was moved or rewritten beyond necessary link repair;
- document all counts, deferred conflicts, and recommendations in `MIGRATION_REPORT_STAGE_1.md`.

