# Full Vault Cleanup Audit Plan

> Frozen: 2026-07-16  
> Scope: all remaining existing vault content except raw ChatGPT export history  
> Authorization: the full-vault cleanup request dated 2026-07-16

## Safety boundary

- Preserve every existing note; relocate obsolete or superseded sources to `99 Archive`.
- Do not read, transform, or import `01 Inbox/ChatGPT Export` content.
- Do not infer project facts, personal achievements, production metrics, or interview results.
- Keep `.obsidian` unchanged; the pre-existing user change to `.obsidian/workspace.json` is out of scope.
- Establish one canonical owner per migrated concept and retain source traceability.

## Frozen remaining source clusters

| Cluster | Primary sources | Canonical destination |
|---|---|---|
| Strings and Unicode | T03 plus exercise/question/revision/simplified/visual pack | `02 Go/Fundamentals/Strings Bytes Runes and UTF-8.md` |
| Pointers | T07 plus derivative pack | `02 Go/Fundamentals/Pointers in Go.md` |
| Functions and closures | P07 | `02 Go/Fundamentals/Functions and Closures.md` |
| Defer and panic boundaries | T10, P06, derivative pack | `02 Go/Error Handling/Defer Panic and Recover.md` |
| Goroutine lifecycle | T13, P08, P10 | `02 Go/Concurrency/Goroutines and Lifecycle.md` |
| Mutex safety | P03 | `02 Go/Concurrency/Mutexes and Data Race Safety.md` |
| Channels | T15, T16 and T16 derivative pack | `02 Go/Concurrency/Go Channels.md` |
| Select | T17 plus derivative pack | `02 Go/Concurrency/Select in Go.md` |
| Worker pools | existing worker-pool problem and channel/goroutine examples | `02 Go/Design Patterns/Worker Pool.md` plus a drill |
| Scheduler | T14, P08, P10 and scheduler question pack | `02 Go/Runtime and Memory/Go Scheduler.md` |
| Allocation and GC | T02, P06, P09 and T02 derivative pack | allocation/escape and GC canonicals under `02 Go/Runtime and Memory` |
| Interface internals | T11 plus derivative pack | `02 Go/Runtime and Memory/Go Interface Internals.md` |
| Map internals | preserved Stage 1 T08 sources plus P04 | `02 Go/Runtime and Memory/Go Map Internals.md` |
| Memory model | empty root placeholder plus concurrency source fragments | `02 Go/Runtime and Memory/Go Memory Model.md` |
| Gin | T05 plus derivative pack | `02 Go/Networking/Gin HTTP Services.md` |
| MongoDB | T06 plus derivative pack | `04 System Design/Databases/MongoDB with Go.md` |
| Behavioural | root compilation | `06 Interviews/Behavioural/Behavioural Interview Compilation - Needs Verification.md` |
| Plans and indexes | root plans, roadmap, status, glossary and connections | Home/Roadmaps indexes or `99 Archive/Legacy Structure` |

## Merge and archive rules

1. Create or improve the canonical and its learning companion before archiving a source cluster.
2. Move old main notes and derivative textbooks to the archive with a visible canonical link.
3. Preserve compact revision cards by converting them into under-five-minute companions when useful.
4. Preserve question banks and solution packs in the archive; the canonical/drill surfaces become the active path.
5. Empty category indexes and starter content move to `99 Archive/Legacy Structure`.

## Validation gates

- Compare pre/post note counts and confirm no tracked or untracked note vanished.
- Check root allowlist and absence of legacy root directories.
- Scan active wikilinks by basename and explicit path; report ambiguous or unresolved targets.
- Verify YAML frontmatter in newly created notes.
- Compile representative executable Go examples and the worker-pool reference solution.
- Confirm the fundamentals-first MOCs and Google roadmap do not claim unrecorded readiness.

