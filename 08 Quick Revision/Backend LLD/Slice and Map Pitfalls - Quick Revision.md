---
type: quick-revision
domain: backend-lld
topic: slice-and-map-pitfalls
review_time: under-5-minutes
---

# Slice and Map Pitfalls — Quick Revision

## Mental Model

Slices are descriptors over backing arrays; append may reuse or replace that array. Reslicing can retain a large backing array, and appending to an aliased slice can mutate data visible elsewhere. Decide whether an API may mutate caller input, copy when it may not, and zero removed pointer elements in long-lived structures. A nil slice and empty non-nil slice both have length zero but can encode different JSON. Maps return zero values for missing keys, so use comma-ok whenever absence differs from a stored zero. Maps are reference-like runtime structures and are unsafe for concurrent writes without synchronization.

## Go / Design Checklist

Initialize maps before assignment; append to a missing map-of-slice entry works, but nested maps need inner allocation. Arrays are comparable and may be map keys; slices are not. Map iteration order is deliberately unspecified, so sort keys for stable output and tests. Removing queue front elements with repeated append/copy is costly; use a head index or ring buffer. For generic containers, return (zero,false) on absence. Test aliasing, nil input, duplicate keys, zero values, capacity growth, deterministic output, and concurrent access under the race detector.

## Explain Aloud

In 60–90 seconds: state the contract, name the invariant and owner, describe success and failure flow, identify cancellation/shutdown behavior, give complexity, and make one Decision → Reason → Cost → Alternative trade-off.

## Reconstruction Drill

Close this note. Sketch the public API and ownership diagram from memory, implement the smallest success path, add one boundary/failure test, then run go test and go test -race where concurrent. Record only observed mistakes and schedule the re-test in [[Backend LLD Practice Tracker]].

## Practice Links

[[Go Slices]], [[Go Maps]], [[Generic Stack]], [[Generic Queue]], [[Circular Deque]], [[Thread-Safe Set]], [[TTL Cache]]

