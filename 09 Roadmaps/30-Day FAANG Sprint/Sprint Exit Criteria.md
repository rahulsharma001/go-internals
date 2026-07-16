---
type: sprint-exit-gate
domain: interview-preparation
status: not-started
---

# Sprint Exit Criteria

Readiness is supported by recorded performance, not confidence alone.

## Go implementation

- [ ] Balanced slice partitioning, frequency counting, `map[string][]T`, and nested maps can be written without help.
- [ ] Constructors, pointer/value receivers, two interface implementations, correct interface invocation from `main()`, and embedding can be written without help.
- [ ] A map-backed CRUD program has errors, tests, complete wiring, and a later hint-free rewrite.
- [ ] Each core program can be explained, tested at edges, given a complexity, and modified under time pressure.
- [ ] The concurrency integration passes `go test -race ./...`.

## DSA in Go

- [ ] Easy problems are consistently correct in about 15–20 minutes.
- [ ] Common mediums are generally correct in about 30–40 minutes.
- [ ] No recurring slice, map, struct, or pointer syntax failure remains unresolved.
- [ ] Pattern is explained before coding; edges and complexity are tested manually.
- [ ] Solutions start in Go rather than being translated from Java.
- [ ] At least one later re-attempt exists for weak patterns; a first success alone is not readiness.

## System design and project evidence

- [ ] One complete design is delivered in 40–45 minutes with requirements, estimates, entities, APIs, data, architecture, success/failure flows, bottlenecks, reliability, security, trade-offs, and technology choices.
- [ ] Four scheduled systems have attempt evidence; at least one has a successful later re-test.
- [ ] Three project stories are backed by verified facts and can be explained in two minutes.
- [ ] No unverified metric or claim from [[Behavioural Interview Compilation - Needs Verification]] is used as fact.

## Behavioural, mocks, and applications

- [ ] “Tell me about yourself,” challenging project, failure, and disagreement answers survive timed mock follow-ups.
- [ ] Every mock records score, mistakes, root causes, correction drills, and re-test date.
- [ ] Priority applications are based on mock evidence; outreach and secondary applications began before the final week.
- [ ] Application pipeline has a concrete next action for every active role.

## Final decision

- **Ready:** exit criteria are evidenced and priority applications continue.
- **Targeted extension:** only failed gates remain active for another 7–14 days.
- **Not ready:** return to the smallest failing drills; do not expand the curriculum.

