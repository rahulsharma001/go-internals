---
type: canonical
domain: go
topic: garbage-collector
status: learning
aliases:
  - T24 Garbage Collector Deep Dive
  - T25 GC Tuning (GOGC & GOMEMLIMIT)
  - T25 GC Tuning & Memory Limits
source_notes:
  - "[[99 Archive/Superseded Originals/prerequisites/P09 GC Basics & Why It Matters]]"
  - "[[99 Archive/Superseded Originals/root/T02 Go Memory Allocation & Value Semantics]]"
---

# Go Garbage Collector

## Why this matters

Go automatically reclaims unreachable heap objects. Application allocation rate, live heap size, pointer density, and retention influence GC CPU and latency; tuning cannot compensate for an ownership leak.

## Mental model and core concepts

The collector traces reachable heap objects from roots, marks live objects, and makes unreachable space reusable. Much work runs concurrently with the application, while short stop-the-world phases and write barriers support correctness.

- Allocation creates future collection work; retained reachable objects remain live.
- A memory leak in a garbage-collected language means unintended reachability or unbounded caches/queues/goroutines.
- `GOGC` changes the target growth ratio and trades collection frequency against memory.
- A memory limit can guide runtime behavior, but the process still needs headroom and load validation.
- `sync.Pool` is an opportunistic reuse tool whose contents may disappear; it is not a durable cache.

## Minimum observable example

```go
package main

import (
	"fmt"
	"runtime"
)

func main() {
	values := make([][]byte, 1000)
	for i := range values { values[i] = make([]byte, 1024) }
	var stats runtime.MemStats
	runtime.ReadMemStats(&stats)
	fmt.Println("heap allocated bytes:", stats.HeapAlloc)
	runtime.KeepAlive(values)
}
```

This is an observation example, not a benchmark. Exact output varies by build and runtime.

## Production success and failure

Success: heap and allocation profiles identify retained objects or hot allocation sites; queue/cache bounds are fixed first; benchmarks and load tests validate any representation, reuse, or tuning change.

Failure: forcing GC frequently, using pools as caches, retaining large buffers for small results, increasing a memory limit without understanding live data, or quoting universal pause-time claims.

Observe process RSS, heap goal/live heap, allocation rate, collection CPU, goroutine growth, and application latency together. Profiles explain where memory comes from; time series explain when it grows.

## Trade-offs and interview lens

Reducing allocation can reduce GC work but may introduce aliasing or complex pooling. Increasing GC headroom can reduce CPU while increasing memory. The senior answer links workload, measurements, change, and validation rather than tuning one environment variable blindly.

## Active recall

Given a service whose RSS rises while heap live data stays bounded, list hypotheses. Then handle a case where a cache and goroutine count both grow without bound.

## Related notes

- [[Go Memory Allocation and Escape Analysis]]
- [[Go Scheduler]]
- [[Go Memory Model]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
