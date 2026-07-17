---
type: canonical
domain: system-design
topic: trade-off-communication
status: learning
---
# Trade-off Communication

## Problem it solves

Senior interviews evaluate judgment under constraints, not whether a component list matches a reference answer.

## Mental model and method

Use a four-part sentence: requirement → choice → cost/risk → mitigation or reversal trigger. Example: “Because order ownership needs atomic uniqueness, I start with PostgreSQL; this limits write scaling by one primary, so I partition only when measured contention or capacity requires it.”

## Concrete example and dry run

For Uber driver locations: choose an in-memory geospatial store for fresh nearby lookup, accepting possible loss/staleness because durable ride ownership remains in a transactional store. Replicate location partitions and fall back to slightly stale candidates. Do not claim the same consistency for driver assignment; acceptance uses a conditional write on the ride/driver state.

Dry run competing alternatives: broadcast offers reduce pickup latency but increase double-accept races and driver spam; sequential offers are simpler but slower; small batches balance latency and contention. State the chosen batch size is tuned from measured acceptance latency, not invented as universal.

## Success and failure scenarios

Success: every major choice maps to a requirement and has a failure consequence. Failure: absolutes such as “NoSQL is faster,” “Kafka guarantees exactly once,” or “active-active is always available.” Replace with scoped semantics and operational costs.

## Scaling and production choices

Useful axes: latency/throughput, availability/consistency, durability/cost, freshness/complexity, isolation/utilization, synchronous coupling/eventual consistency, build/buy, managed/self-hosted, single-region/multi-region.

## When not to over-qualify

Do not list every possible alternative. Choose one, defend it, and name the signal that would cause a change.

## Interview mistakes and follow-ups

Technology-first answers; no rejected alternative; ignoring migration/operations; hiding user-visible degradation. Follow-ups: what fails first at 10×? what would you simplify for launch? how do you reverse the decision? which metric validates it?

## Five-minute recall

“Given ___, choose ___; cost is ___; mitigate with ___; revisit when ___.”

Related: [[System Design Trade-off Cheatsheet]], [[Data Storage Selection]], [[Multi Region Architecture]].

## Source metadata

Curated from the existing framework and interview-focused extracts; no personal decision is asserted.
