# Week 1 MCQ - Foundations (T07-T09)

> Coverage: [[T07 Pointers & Pointer Semantics]], [[T08 Map Internals]], [[T09 Error Handling Patterns]]
> Use as daily interview drill (10-15 min).

---

## Pointers & Value Semantics (T07)

1) In Go, passing a struct by value to a function means:
- A. original object is always mutated
- B. function gets a copy of struct value
- C. data moves to global heap automatically
- D. only pointer fields are copied  
**Answer: B**

2) Pointer receiver is typically preferred when:
- A. method does not touch data
- B. struct is large or needs mutation
- C. type has only constants
- D. you want to avoid method sets  
**Answer: B**

3) Which statement is true?
- A. `nil` pointer dereference is compile-time error
- B. pointer arithmetic is encouraged in Go
- C. `*p = x` writes through pointer target
- D. taking address with `&` copies heap object  
**Answer: C**

4) Escape analysis primarily decides:
- A. map hash seed
- B. stack vs heap allocation
- C. goroutine priority
- D. scheduler preemption frequency  
**Answer: B**

5) A common trap with pointer receiver methods is:
- A. method cannot return error
- B. calling on non-addressable temporary values
- C. impossible to satisfy interfaces
- D. pointer receiver methods are never in method set  
**Answer: B**

6) Which is best interview explanation?
- A. pointers are always faster
- B. pointers remove all copies and allocations
- C. pointers control sharing/mutation semantics
- D. pointers bypass Go type safety  
**Answer: C**

---

## Map Internals (T08)

7) Go maps are not safe for concurrent writes because:
- A. hash function is random every op
- B. map internals mutate shared buckets/growth state
- C. runtime forbids any goroutines on maps
- D. map value type lacks locks by default  
**Answer: B**

8) Buckets in map internals are used to:
- A. store goroutine stacks
- B. group key/value slots by hash bits
- C. pin threads to cores
- D. cache interface method sets  
**Answer: B**

9) During map growth, Go may:
- A. migrate all entries in one mandatory stop
- B. incrementally evacuate buckets
- C. disable reads entirely
- D. convert map to slice  
**Answer: B**

10) Best fix for concurrent map writes in hot path:
- A. ignore race detector
- B. use single global mutex always
- C. choose proper sync strategy (mutex/sharding/sync.Map by pattern)
- D. replace map with array blindly  
**Answer: C**

11) Iteration order in Go maps:
- A. insertion order guaranteed
- B. lexical key order guaranteed
- C. intentionally not deterministic
- D. deterministic if map capacity fixed  
**Answer: C**

12) Reading from nil map:
- A. panics
- B. returns zero value and ok=false behavior for lookup form
- C. creates map automatically
- D. blocks until initialized  
**Answer: B**

13) Writing to nil map:
- A. compile error
- B. silently ignored
- C. panics at runtime
- D. converts to empty map  
**Answer: C**

---

## Error Handling Patterns (T09)

14) Preferred modern wrapping pattern:
- A. `panic(err)`
- B. `fmt.Errorf("context: %w", err)`
- C. `errors.New(err.Error())`
- D. global lastError variable  
**Answer: B**

15) `errors.Is(err, target)` is used to:
- A. compare error strings only
- B. detect wrapped sentinel/type chain match
- C. unwrap all errors manually
- D. cast to concrete type directly  
**Answer: B**

16) `errors.As(err, &typedErr)` is used to:
- A. check sentinel equality
- B. extract concrete error type from chain
- C. serialize error
- D. allocate stack frame  
**Answer: B**

17) Interview-friendly error strategy in services is:
- A. hide root errors always
- B. return only string messages
- C. wrap with context at each boundary, preserve cause
- D. use panic for control flow  
**Answer: C**

18) Best practice for HTTP handlers on errors:
- A. leak full internal stack to client
- B. map internal errors to safe API error responses
- C. ignore logging
- D. return 200 with error text always  
**Answer: B**

19) Recovering from panic should generally happen:
- A. inside every helper function
- B. nowhere in server code
- C. at service/HTTP boundary middleware
- D. only in database driver  
**Answer: C**

20) Most interviewers test in error handling:
- A. keyboard shortcuts
- B. syntax memorization only
- C. ability to preserve context and classify failure
- D. how many custom error structs you know  
**Answer: C**

---
