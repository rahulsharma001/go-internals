# Week 2 MCQ - Foundations (T10-T12)

> Coverage: [[T10 Defer, Panic & Recover Internals]], [[T11 Interface Internals (iface & eface)]], [[T12 Interface Design Principles]]
> Use as daily interview drill (10-15 min).
> Try answering first, then expand each hidden answer.

---

## Defer, Panic, Recover (T10)

1) Deferred calls in one function execute:
- A. FIFO order
- B. random order
- C. LIFO order
- D. only on panic  
> [!success]- Answer
> **C** — defer stack unwinds in last-in-first-out order.

2) Defer arguments are evaluated:
- A. when deferred function executes
- B. at defer statement time
- C. after function returns
- D. only if panic occurs  
> [!success]- Answer
> **B** — arguments are bound when `defer` is registered.

3) `recover()` works when called:
- A. anywhere in same package
- B. only in deferred function on panicking goroutine
- C. from another goroutine
- D. in normal execution path  
> [!success]- Answer
> **B** — recover is effective only in deferred call on same panicking goroutine.

4) Panic in goroutine without recover:
- A. crashes only that goroutine always safely
- B. may crash whole process if unhandled
- C. is automatically converted to error
- D. ignored by runtime  
> [!success]- Answer
> **B** — unhandled panic can terminate process.

5) Best pattern in HTTP services:
- A. recover in every repo method
- B. no recover anywhere
- C. top-level middleware recover and map to 500 safely
- D. panic for expected validation failures  
> [!success]- Answer
> **C** — centralized boundary recover is operationally safest.

6) Defer is commonly used for:
- A. map growth
- B. guaranteed cleanup (unlock/close)
- C. changing `GOMAXPROCS`
- D. forcing stack allocation  
> [!success]- Answer
> **B** — defer is standard cleanup guard.

---

## Interface Internals (T11)

7) `eface` runtime representation refers to:
- A. interface with method set
- B. empty interface (`interface{}` / `any`)
- C. error interface only
- D. map internal bucket header  
> [!success]- Answer
> **B** — `eface` is empty-interface runtime representation.

8) `iface` runtime representation refers to:
- A. non-empty interface with method table info
- B. empty interface only
- C. channel descriptor
- D. goroutine descriptor  
> [!success]- Answer
> **A** — `iface` tracks method-bearing interface metadata.

9) Interface value is `nil` only when:
- A. dynamic value is nil even if dynamic type exists
- B. dynamic type is non-nil
- C. both dynamic type and dynamic value are nil
- D. pointed object equals zero value  
> [!success]- Answer
> **C** — both type and value slots must be nil.

10) Why `var err error = (*MyErr)(nil)` can be non-nil?
- A. compiler bug
- B. interface holds non-nil dynamic type metadata
- C. recover changed error
- D. map hash collision  
> [!success]- Answer
> **B** — typed-nil still carries dynamic type, so interface is non-nil.

11) Type assertion `v, ok := i.(T)`:
- A. panics always on mismatch
- B. returns `ok=false` on mismatch
- C. only works for pointers
- D. mutates interface dynamic type  
> [!success]- Answer
> **B** — comma-ok assertion handles mismatch safely.

12) Type switch helps:
- A. avoid all allocations
- B. branch on dynamic concrete type
- C. force map key ordering
- D. change method set of type  
> [!success]- Answer
> **B** — dynamic type-based branching.

13) Boxing into interface can add cost because:
- A. scheduler pauses all threads
- B. value metadata + possible allocation/escape paths
- C. map rehash always triggered
- D. it disables inlining globally  
> [!success]- Answer
> **B** — boxing can involve metadata work and allocation/escape tradeoffs.

---

## Interface Design Principles (T12)

14) Preferred Go API design principle:
- A. accept structs, return interfaces
- B. accept interfaces, return structs
- C. always return `any`
- D. expose only empty interfaces  
> [!success]- Answer
> **B** — keeps API concrete outputs while allowing flexible inputs.

15) Why keep interfaces small?
- A. runtime cannot handle large interfaces
- B. improves substitution and testability
- C. compiler requires <=2 methods
- D. avoids goroutine leaks  
> [!success]- Answer
> **B** — narrow contracts are easier to implement and mock.

16) Where should interface usually live?
- A. provider package always
- B. consumer side where behavior is needed
- C. global shared package always
- D. runtime package  
> [!success]- Answer
> **B** — consumer-defined interfaces avoid over-coupled provider APIs.

17) "Fat interface" risk:
- A. easier mocking
- B. tighter coupling and brittle implementations
- C. better cache locality guaranteed
- D. smaller API surface  
> [!success]- Answer
> **B** — wider interfaces force unnecessary implementation burden.

18) Returning interface from constructors everywhere is bad because:
- A. impossible in Go
- B. hides concrete capabilities and complicates evolution
- C. causes panic automatically
- D. breaks garbage collector  
> [!success]- Answer
> **B** — over-abstraction can reduce clarity and flexibility.

19) Best mock-friendly design in services:
- A. define narrow behavior interfaces at call site
- B. expose all concrete dependencies globally
- C. avoid interfaces entirely
- D. use only reflection-based mocks  
> [!success]- Answer
> **A** — focused consumer-side interfaces are easiest to test.

20) Most asked interview design tradeoff:
- A. number of tabs in editor
- B. flexibility vs over-abstraction in interface boundaries
- C. choosing shortest variable names
- D. avoiding packages  
> [!success]- Answer
> **B** — interviewers care about boundary design quality.

---
