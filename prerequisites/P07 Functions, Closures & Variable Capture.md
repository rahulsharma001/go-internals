# P07 Functions, Closures & Variable Capture

> **Prerequisite note** — complete this before starting [[T13 Goroutine Internals]].
> Estimated time: ~20 min

---

## 1. Concept

A **closure** is a function bundled with the variables from the lexical scope where that function was created.

> **In plain English:** Think of a closure as a function with a **backpack**. The backpack holds live references to outer variables. The function can read and update those variables long after the outer function has returned. The backpack is not a snapshot at birth unless you deliberately copy values into locals or parameters.

---

## 2. Core Insight (TL;DR)

**Functions are values.** You can store them, pass them, and return them like any other value.

**Closures capture outer variables by reference**, not by value. Multiple closures can share the same outer variable. **The loop variable trap** happens when concurrent goroutines all close over one shared loop index. **Go 1.22** changed `for` loop variable semantics so each iteration gets fresh variables, but interviewers still expect you to explain the classic bug and why `go func() { ... }()` makes capture obvious.

---

## 3. Mental Model (Lock this in)

**Backpack, not photograph.** A closure does not freeze outer values when it is created. It keeps **pointers** to the outer storage locations. If the outer variable changes later, the closure sees the new value. If many closures share one outer variable, they all see the same moving target.

MEMORY TRACE:

```
Step 1: Outer function runs; local n is allocated (stack until compiler proves escape).
stack:
  outer_frame @ 0x7ffeaa10
    n @ 0x7ffeaa18  ──→  initial value (e.g. 0)
Step 2: Closure literal is evaluated → one function value is allocated (code pointer + env pointer).
heap:
  closure_env @ 0xc0000a0120
    code_ptr   ──→  anonymous func machine code @ 0x401200
    env_ptr    ──→  (will bind to n’s live storage)
Step 3: Because the closure outlives the outer call / is stored, n escapes; live storage moves to heap.
stack:
  outer_frame @ 0x7ffeaa10
    (n slot dead or forwarded)
heap:
  n_obj @ 0xc0000140a0  ◄──  same logical variable as outer n
  closure_env @ 0xc0000a0120
    env_ptr   ──→  &n_obj @ 0xc0000140a0  ◄──  closure holds pointer, not a copy
**Aha:** The closure does not snapshot n; it holds an address. Reads/writes go through that pointer, so later changes to n are visible inside the closure.
```

**Error-driven picture: loop variable trap.** One variable `i` is reused each iteration. Every goroutine closes over **the same** `i`. By the time goroutines run, the loop may have finished and `i` holds the final value.

```go
for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i) // all see the same i
    }()
}
```

MEMORY TRACE:

```
Step 1: Loop declares one variable i — single storage reused each iteration (classic semantics).
stack:
  main @ 0x7ffecc00
    i @ 0x7ffecc08  ──→  0  (then 1, 2, 3 as loop runs)
heap:
  (often, once goroutines capture i) i_esc @ 0xc0000d00a0  ◄──  one promoted cell all closures use
Step 2: Each `go func()` builds a closure (function value + env). Every env binds to the SAME variable.
heap:
  g0.closure @ 0xc0000e0040
    code_ptr  ──→  fmt.Println(i) body
    env_ptr   ──→  &i_esc @ 0xc0000d00a0
  g1.closure @ 0xc0000e0080
    code_ptr  ──→  same body
    env_ptr   ──→  &i_esc @ 0xc0000d00a0  ◄──  same address as g0
  g2.closure @ 0xc0000e00c0
    env_ptr   ──→  &i_esc @ 0xc0000d00a0
Step 3: Main finishes the loop; i_esc holds the final value; goroutines schedule later.
heap:
  i_esc @ 0xc0000d00a0  ──→  3  ◄──  final value everyone reads
stack:
  main continues; loop’s i may be 3 or dead — goroutines only care about shared i_esc
Step 4: Each goroutine runs fmt.Println(i); load goes through env_ptr → one cell → value 3.
**Aha:** All goroutines share one variable in memory; they all see the final value (e.g. 3, 3, 3), not 0, 1, 2.
```

> **In plain English:** Ten photocopies of a **single whiteboard** are not ten different numbers. Every goroutine is looking at the same whiteboard. If the teacher keeps erasing and writing the next number, late students might only see the final number.

---

## 4. How It Works

### 4.1 First-class functions

In Go, a function type is a type like `func(int) int`. You can assign functions to variables, pass them to other functions, and return them from functions.

```go
type Op func(int, int) int

func apply(a, b int, f Op) int {
    return f(a, b)
}

func main() {
    var add Op = func(x, y int) int { return x + y }
    _ = apply(2, 3, add)
}
```

MEMORY TRACE:

```
Step 1: `var add Op = func(...) { ... }` — function literal becomes a function value; variable `add` stores a reference to that value.
stack:
  main @ 0x7ffedd20
    add @ 0x7ffedd30  ──→  (pointer-sized slot)
heap:
  funcval_add @ 0xc0000b0010
    code_ptr  ──→  anonymous `x+y` machine code @ 0x4010e0
    env_ptr   ──→  nil  ◄──  no outer locals; not a closure over stack
Step 2: `apply(2, 3, add)` — parameter `f` receives a copy of the same descriptor (same code_ptr target).
stack:
  apply.frame @ 0x7ffedcf0
    a @ 0x7ffedcf8   ──→  2
    b @ 0x7ffedd00   ──→  3
    f @ 0x7ffedd08   ──→  funcval_add @ 0xc0000b0010  ◄──  same heap object as `add`
Step 3: Inside apply, `f(a,b)` loads code_ptr from funcval_add and runs with (2,3).
**Aha:** `add` is a variable holding a small function descriptor (code + optional env); passing it copies that descriptor, not a duplicate of the machine code.
```

The **function value** is a small struct-like thing: code pointer plus optional **environment pointer** for closures.

### 4.2 Anonymous functions (function literals)

A **function literal** is an inline function definition. It can be named with `:=` or passed directly.

```go
nums := []int{1, 2, 3}
transformed := make([]int, len(nums))
for i, v := range nums {
    transformed[i] = func() int {
        return v * 2 // closes over v and i
    }()
}
```

MEMORY TRACE:

```
Step 1: Iteration i=0, v=1 — range binds loop variables (one pair of slots per iteration in this mental model).
stack:
  loop @ 0x7ffeef40
    i @ 0x7ffeef48  ──→  0
    v @ 0x7ffeef50  ──→  1
Step 2: Literal `func() int { return v * 2 }` is created; it closes over `v` (and possibly `i`); then `()` runs it immediately.
heap:
  tmp_closure @ 0xc0000c0200  (lifetime: only for this call)
    code_ptr  ──→  return v*2
    env_ptr   ──→  &v @ 0x7ffeef50  ◄──  reads current v (1)
Step 3: Call returns 2; result stored in transformed[0]; temporary closure can be discarded.
stack:
  transformed[0] @ slice+0  ──→  2
Step 4: Next iteration overwrites i, v (e.g. i=1, v=2); new literal/closure for that row; same pattern.
**Aha:** Because the literal is invoked immediately, capture is short-lived; if you appended the func to a slice instead of calling it, each stored closure would keep `v` alive and they would share one slot — classic trap.
```

If you **store** the function instead of calling it immediately, the closure survives and keeps `v` alive.

### 4.3 Closures capture by reference

The closure does not copy `n` when `n` is captured. It captures **where `n` lives**.

```go
func counter() func() int {
    n := 0
    return func() int {
        n++
        return n
    }
}

func main() {
    c := counter()
    _ = c() // 1
    _ = c() // 2
}
```

MEMORY TRACE:

```
Step 1: counter() enters; n := 0. Returned func closes over n; n must outlive counter’s frame → escape analysis moves n to heap.
stack:
  counter @ 0x7fff0010
    (return slot preparing func value)
heap:
  n @ 0xc000014080  ◄──  value 0  ◄──  captured variable lives here
Step 2: Inner literal becomes function value: code_ptr + env_ptr → &n.
heap:
  funcval @ 0xc0000c0040
    code_ptr  ──→  n++; return n @ 0x401240
    env_ptr   ──→  &n @ 0xc000014080  ◄──  closure holds pointer to heap n
Step 3: counter returns; main assigns that value to c (variable holds reference to funcval).
stack:
  main @ 0x7fffaa20
    c @ 0x7fffaa30  ──→  funcval @ 0xc0000c0040
heap:
  n @ 0xc000014080  ──→  still 0 until first call
Step 4: First c() — body loads env_ptr, increments *(&n), returns 1.
heap:
  n @ 0xc000014080  ──→  1
Step 5: Second c() — SAME env_ptr, SAME address; increment again → 2.
heap:
  n @ 0xc000014080  ──→  2
**Aha:** Each call increments the SAME heap variable; the closure’s “backpack” is one shared counter cell, not a fresh n per call.
```

Each call to `counter()` creates a **fresh** `n` and a **new** closure with its own `&n`.

### 4.4 Heap escape of captured variables

If a variable is referenced by a closure that **outlives** its enclosing stack frame, the compiler **escapes** that variable to the **heap**. The garbage collector tracks it like any other heap object.

```go
func makeClosure(x int) func() int {
    return func() int { return x }
}
```

MEMORY TRACE:

```
Step 1: makeClosure(x int) — argument x lives in callee stack frame (e.g. x = 7).
stack:
  makeClosure @ 0x7ffee100
    x @ 0x7ffee108  ──→  7
Step 2: Literal `func() int { return x }` is built; returned func outlives makeClosure → captured x escapes to heap.
heap:
  x_heap @ 0xc0000160a0  ◄──  7  ◄──  live storage for captured x
  closure @ 0xc0000d0080
    code_ptr  ──→  load-return x_heap
    env_ptr   ──→  &x_heap @ 0xc0000160a0
Step 3: makeClosure returns closure value to caller; its stack frame is popped.
stack:
  (makeClosure frame — reclaimed; 0x7ffee108 invalid)
heap:
  x_heap @ 0xc0000160a0  ◄──  still 7, reachable only via closure
Step 4: Caller invokes returned func; each call reads through env_ptr → x_heap.
**Aha:** Variable escapes to heap; closure holds a pointer to that cell — without the closure, x would die with the stack frame.
```

You do not manage this manually. **Escape analysis** decides. The interview point: closures can keep memory alive longer than you expect if you store them in globals, maps, or long-lived structs.

---

## 5. Key Rules & Behaviors

### Functions are values (assign, pass, return)

```go
func twice(f func(int) int) func(int) int {
    return func(x int) int {
        return f(f(x))
    }
}
```

MEMORY TRACE:

```
Step 1: Caller passes function value `f` into `twice` — `f` is a variable whose value is a function descriptor.
stack:
  twice @ 0x7ffee200
    f @ 0x7ffee210  ──→  funcval_f @ 0xc0000e0010
heap:
  funcval_f @ 0xc0000e0010
    code_ptr  ──→  caller’s passed func (e.g. inc)
    env_ptr   ──→  … or nil
Step 2: `return func(x int) int { return f(f(x)) }` — inner literal captures the binding of `f`. Returned closure outlives `twice` → compiler places captured `f` in heap cell.
heap:
  f_cell @ 0xc0000e0180  ──→  funcval_f @ 0xc0000e0010  ◄──  pointer to SAME descriptor as parameter
  returned @ 0xc0000e0200
    code_ptr  ──→  body: call f twice
    env_ptr   ──→  &f_cell @ 0xc0000e0180
Step 3: `twice` returns; caller holds `returned`. `twice`’s stack slot for `f` is gone; `f_cell` keeps the func value reachable.
stack:
  (twice frame — reclaimed)
heap:
  f_cell @ 0xc0000e0180  ──→  funcval_f @ 0xc0000e0010
Step 4: Caller invokes returned closure with some x; each inner `f(...)` dereferences env → f_cell → funcval_f.
**Aha:** The returned function is a closure: its environment is “where `f` lives,” not a frozen copy of `f`’s behavior at return time — invocations still go through that binding.
```

> **In plain English:** A function is a **thing you can hand to someone else**, like handing over a tool. `twice` hands back a **new** tool that uses the original tool twice.

### Closures capture by reference, not by value

```go
var fs []func()
for _, v := range []int{10, 20, 30} {
    fs = append(fs, func() { fmt.Println(v) })
}
for _, f := range fs {
    f()
}
```

MEMORY TRACE:

```
Step 1: `for _, v := range ...` — one variable `v`; its slot is reused: 10 → 20 → 30.
stack:
  loop @ 0x7ffee300
    v @ 0x7ffee308  ──→  10  (then 20, then 30)
heap:
  (if range value escapes into goroutines/closures) v_esc @ 0xc0000f00a0  ◄──  single logical cell all funcs share
Step 2: Each `append(fs, func() { fmt.Println(v) })` allocates a new function value; each env_ptr points at the SAME `v`.
heap:
  closure[0] @ 0xc0000f0000
    code_ptr  ──→  print v
    env_ptr   ──→  &v_esc @ 0xc0000f00a0
  closure[1] @ 0xc0000f0040
    env_ptr   ──→  &v_esc @ 0xc0000f00a0  ◄──  same address
  closure[2] @ 0xc0000f0080
    env_ptr   ──→  &v_esc @ 0xc0000f00a0
Step 3: Loop ends; `v` / `v_esc` holds final value 30.
heap:
  v_esc @ 0xc0000f00a0  ──→  30
Step 4: Second loop runs `fs[0]()`, `fs[1]()`, `fs[2]()`; each closure loads through env_ptr → prints current v (30).
**Aha:** Three closures, one captured slot — everyone prints the last value (30), not 10, 20, 30.
```

> **In plain English:** Everyone shares **one cup**. The last drink poured is what everyone tastes.

### Captured variables escape to heap (GC managed)

```go
type Job struct{ run func() }

func factory() Job {
    secret := 42
    return Job{run: func() { fmt.Println(secret) }}
}
```

MEMORY TRACE:

```
Step 1: factory() — `secret := 42` on stack; struct literal `Job{ run: func(){ ... secret } }` closes over `secret`.
stack:
  factory @ 0x7ffee400
    secret @ 0x7ffee408  ──→  42
Step 2: Closure outlives frame / is stored in returned struct → `secret` escapes to heap.
heap:
  secret_heap @ 0xc0000180b0  ◄──  42
  closure_run @ 0xc000100200
    code_ptr  ──→  fmt.Println(secret)
    env_ptr   ──→  &secret_heap @ 0xc0000180b0
Step 3: Returned `Job` value (possibly on stack of caller) holds field `run` pointing at closure_run.
stack:
  caller receives Job
    .run ──→  closure_run @ 0xc000100200
heap:
  secret_heap @ 0xc0000180b0  ◄──  reachable from Job.run
Step 4: factory stack popped; stack slot 0x7ffee408 dead; only heap copy matters.
**Aha:** Capture + return forces `secret` to the heap; GC keeps it until `Job` and its `run` func are unreachable.
```

> **In plain English:** If a function needs to **remember** something after its creator returns, that memory cannot live on the short-term stack shelf. It moves to the **long-term heap warehouse** until nothing points at it.

### Loop variable trap: goroutines share one variable

```go
var wg sync.WaitGroup
for i := 0; i < 3; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        fmt.Println(i)
    }()
}
wg.Wait()
```

MEMORY TRACE:

```
Step 1: `for i := 0; i < 3; i++` — one `i` for the whole loop (pre–Go 1.22 mental model).
stack:
  main @ 0x7ffee500
    i @ 0x7ffee508  ──→  0 → 1 → 2 → 3
heap:
  i_shared @ 0xc0001100a0  ◄──  promoted cell when goroutines capture `i` (one address for all)
Step 2: Three `go func(){ ... fmt.Println(i) }()` — each closure: function value + env → &i_shared.
heap:
  go#0.closure @ 0xc000111000
    env_ptr   ──→  &i_shared @ 0xc0001100a0
  go#1.closure @ 0xc000111040
    env_ptr   ──→  &i_shared @ 0xc0001100a0
  go#2.closure @ 0xc000111080
    env_ptr   ──→  &i_shared @ 0xc0001100a0
Step 3: Main advances loop and may reach `wg.Wait()`; `i_shared` ends at 3 before goroutines often print.
heap:
  i_shared @ 0xc0001100a0  ──→  3
Step 4: Each goroutine runs deferred `Done`, then `Println(i)` — all dereference same cell → 3.
**Aha:** All goroutines share one variable’s storage; they all see the final `i`, not 0, 1, 2.
```

Typical wrong output: three lines of `3`.

> **In plain English:** Three people each get a **ticket** that says "look at the variable called i." They do not get **copies** of i from when they started. They read whatever i is **right now**.

### Fix: pass as function argument (copy) or shadow locally

**Argument copy: each goroutine gets its own parameter slot.**

```go
for i := 0; i < 3; i++ {
    wg.Add(1)
    go func(n int) {
        defer wg.Done()
        fmt.Println(n)
    }(i)
}
```

MEMORY TRACE:

```
Step 1: Iteration i=1 (example) — main stack holds loop variable `i`.
stack:
  main @ 0x7ffee600
    i @ 0x7ffee608  ──→  1
Step 2: `go func(n int) { ... }(i)` — goroutine spawn evaluates `i` and passes **by value** into new stack frame.
stack:
  g_for_i=1 @ 0x7fff4000
    n @ 0x7fff4008  ──→  1  ◄──  copy made at launch; address ≠ `i` on main
  main.i @ 0x7ffee608  ──→  1  (later becomes 2, 3 on main only)
Step 3: Closure body uses parameter `n` (each goroutine’s own slot), not `&main.i`.
heap:
  closure may only need code_ptr + env to `n` on **that** goroutine’s stack — no shared loop slot
Step 4: Repeat for i=0,2 — three goroutines with n @ 0x7fff5008→0, 0x7fff4008→1, 0x7fff6008→2 (illustrative stacks).
**Aha:** Passing `i` as an argument creates a per-goroutine copy on each goroutine’s stack — no shared loop variable; prints 0, 1, 2 (order may vary).
```

**Local shadow: copy into a new variable each iteration.**

```go
for i := 0; i < 3; i++ {
    i := i
    wg.Add(1)
    go func() {
        defer wg.Done()
        fmt.Println(i)
    }()
}
```

MEMORY TRACE:

```
Step 1: Outer loop `i` advances; inside iteration, `i := i` creates a **new** inner `i` (shadow) copied from outer.
stack:
  main @ 0x7ffee700
    i_outer @ 0x7ffee708  ──→  1
    i_inner @ 0x7ffee718  ──→  1  ◄──  fresh slot per iteration body
Step 2: `go func() { ... fmt.Println(i) }()` — closure captures **inner** `i` only for this iteration.
heap:
  closure_iter1 @ 0xc000112000
    env_ptr   ──→  &i_inner @ 0x7ffee718  ◄──  or escaped copy @ heap if compiler promotes
Step 3: Next iteration: new `i_inner` @ 0x7ffee728 (illustrative); previous goroutine’s closure still points at 0x7ffee718.
stack:
  i_outer @ 0x7ffee708  ──→  2
  i_inner @ 0x7ffee728  ──→  2  ◄──  different address from iteration 1
Step 4: After three spawns, three closures → three distinct captured cells → prints 0,1,2.
**Aha:** Each iteration pins a different storage for the value — same effect as passing `i` as a parameter; no sharing of the single loop variable slot.
```

> **In plain English:** Give each goroutine **its own piece of paper** with the number written on it. Parameters and inner `i := i` both create **fresh** storage.

### Go 1.22 loopvar change (still asked in interviews)

Starting in **Go 1.22**, each iteration of a `for` loop creates **new** variables for the loop index and value. The classic `go func() { fmt.Println(i) }()` bug inside `for i := ...` is **fixed** for that pattern without extra ceremony.

You must still know the old behavior because:

- Codebases and blogs pre-1.22 still show the trap.
- Interviews test whether you understand **capture** and **shared mutable outer state**, not just syntax.
- Not every loop-like construct is magically safe; **shared outer variables** you mutate yourself still bite.

> **In plain English:** The language stopped reusing one sticky note per iteration for `for` loops, but **your** sticky notes and **your** closures can still point at the same board.

---

## 6. Code Examples

### Example A: Function as value

```go
package main

import "fmt"

func main() {
	var greet func(string)
	greet = func(name string) {
		fmt.Println("Hello,", name)
	}
	greet("Ada")
}
```

MEMORY TRACE:

```
Step 1: `var greet func(string)` — stack slot for a function-typed variable, initially nil.
stack:
  main @ 0x7ffee800
    greet @ 0x7ffee810  ──→  nil
Step 2: `greet = func(name string) { ... }` — literal becomes heap-allocated function value; variable now references it.
heap:
  funcval_greet @ 0xc000110100
    code_ptr  ──→  fmt.Println("Hello,", name) @ 0x401300
    env_ptr   ──→  nil  ◄──  no outer locals captured
stack:
  greet @ 0x7ffee810  ──→  funcval_greet @ 0xc000110100  ◄──  function assigned to variable
Step 3: `greet("Ada")` — load code_ptr from funcval_greet; `name` is a parameter on the call frame only.
stack:
  greet.call @ 0x7ffee7e0
    name @ 0x7ffee7e8  ──→  "Ada" (string header/data)
**Aha:** `greet` holds a descriptor (code + env); with no captures, env is empty — still a first-class function value in memory.
```

**Snapshot:** `greet` holds a function value. No outer locals are captured; environment pointer may be nil or empty.

### Example B: Simple closure with counter

```go
package main

import "fmt"

func makeCounter() func() {
	n := 0
	return func() {
		n++
		fmt.Println(n)
	}
}

func main() {
	c := makeCounter()
	c() // 1
	c() // 2
}
```

MEMORY TRACE:

```
Step 1: makeCounter — `n := 0`; inner `return func(){ n++; fmt.Println(n) }` captures `n` → `n` escapes to heap.
heap:
  n @ 0xc0001200a0  ──→  0
  closure_c @ 0xc000120100
    code_ptr  ──→  n++; print
    env_ptr   ──→  &n @ 0xc0001200a0  ◄──  closure capture: pointer to heap `n`
Step 2: Return to main; `c` is a variable whose value is the function descriptor.
stack:
  main @ 0x7ffee900
    c @ 0x7ffee910  ──→  closure_c @ 0xc000120100
Step 3: First `c()` — through env_ptr, `n++` mutates heap cell.
heap:
  n @ 0xc0001200a0  ──→  1  ◄──  SAME cell as step 1
Step 4: Second `c()` — again same env_ptr, same address.
heap:
  n @ 0xc0001200a0  ──→  2
**Aha:** Every call uses the same env_ptr → the SAME heap `n`; the counter closure is shared mutable state across calls.
```

**Snapshot after `makeCounter` returns:** `n` escaped to heap; closure holds `&n`. Each `c()` mutates the same `n`.

### Example C: Loop variable trap with goroutines (wrong)

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			time.Sleep(10 * time.Millisecond)
			fmt.Println("wrong:", i)
		}()
	}
	wg.Wait()
}
```

MEMORY TRACE:

```
Step 1: One loop variable `i`; loop fires three goroutines before `i` finishes at 3.
stack:
  main @ 0x7ffeea00
    i @ 0x7ffeea08  ──→  0 → 1 → 2 → 3
heap:
  i_one @ 0xc0001300a0  ◄──  single shared cell (promoted when captured)
Step 2: Each `go func(){ ... Sleep; Println(i) }()` builds closure; all env_ptr → &i_one.
heap:
  g0.closure @ 0xc000131000  env_ptr ──→  &i_one @ 0xc0001300a0
  g1.closure @ 0xc000131040  env_ptr ──→  &i_one @ 0xc0001300a0
  g2.closure @ 0xc000131080  env_ptr ──→  &i_one @ 0xc0001300a0
Step 3: Main hits `wg.Wait()`; loop complete; `i_one` is 3.
heap:
  i_one @ 0xc0001300a0  ──→  3
Step 4: After Sleep, each goroutine reads `i` through shared pointer → 3.
**Aha:** All goroutines share one variable; delayed reads still see the final value — classic trap; fix: pass `i` as arg or `i := i` per iteration.
```

**Typical output:**

```
wrong: 3
wrong: 3
wrong: 3
```

### Example D: Fixed version (correct on all Go versions)

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			time.Sleep(10 * time.Millisecond)
			fmt.Println("right:", n)
		}(i)
	}
	wg.Wait()
}
```

MEMORY TRACE:

```
Step 1: i=0 — `go func(n int){ ... }(0)` evaluates `0` and starts goroutine g0 with its own frame.
stack:
  main @ 0x7ffeeb00
    i @ 0x7ffeeb08  ──→  0  (will advance)
  g0 @ 0x7fff5000
    n @ 0x7fff5008  ──→  0  ◄──  copy on g0’s stack, not a pointer to main’s i
Step 2: i=1 — second spawn; g1’s parameter slot holds copy 1 at distinct address.
stack:
  g1 @ 0x7fff6000
    n @ 0x7fff6008  ──→  1
Step 3: i=2 — third spawn; g2’s n → 2.
stack:
  g2 @ 0x7fff7000
    n @ 0x7fff7008  ──→  2
heap:
  each closure (if any env) may point at **that** goroutine’s `n` slot — not a shared loop index
Step 4: After Sleep, each Println uses its own `n` → 0, 1, 2 (order may vary).
**Aha:** Passing `i` as an argument creates a per-goroutine copy on each goroutine’s stack — no shared loop variable.
```

**Typical output (order may vary):**

```
right: 0
right: 1
right: 2
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

What does this program print?

```go
package main

import "fmt"

func main() {
	x := 1
	f := func() {
		fmt.Println(x)
	}
	x = 2
	f()
}
```

MEMORY TRACE:

```
Step 1: `x := 1` — allocate `x`; literal `func(){ fmt.Println(x) }` closes over `x`.
stack:
  main @ 0x7ffeac00
    x @ 0x7ffeac08  ──→  1
heap:
  (if x escapes) x_heap @ 0xc0001400a0  ◄──  1
  funcval_f @ 0xc000140100
    code_ptr  ──→  Println(x)
    env_ptr   ──→  &x_heap @ 0xc0001400a0  ◄──  closure holds pointer to `x`
Step 2: `f :=` assigns function value to variable `f`.
stack:
  f @ 0x7ffeac18  ──→  funcval_f @ 0xc000140100
Step 3: `x = 2` mutates the **same** captured storage (not a snapshot from step 1).
heap:
  x_heap @ 0xc0001400a0  ──→  2  ◄──  same cell as step 1
Step 4: `f()` runs; closure loads `x` through env_ptr → prints current value 2.
**Aha:** Capture is by reference — `f` sees live `x`, so output is `2`, not `1`.
```

> [!success]- Answer
> It prints `2`.
>
> The closure captures `x` by reference. `f` runs after `x` is updated, so it observes the current value `2`.

### Tier 2: Fix the Bug (5 min)

This code intends to print `0 1 2` from three goroutines. It often prints `3` three times on Go versions before 1.22. Rewrite it so it is correct on **Go 1.21 and older** without relying on new loop semantics.

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var wg sync.WaitGroup
	for i := 0; i < 3; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			fmt.Println(i)
		}()
	}
	wg.Wait()
}
```

MEMORY TRACE:

```
Step 1: One loop variable `i` for `i := 0; i < 3; i++` (behavior before Go 1.22 fix).
stack:
  main @ 0x7ffead00
    i @ 0x7ffead08  ──→  0 → 1 → 2 → 3
heap:
  i_shared @ 0xc0001500a0  ◄──  single cell all goroutines observe when they capture `i`
Step 2: Three `go func(){ defer Done(); Println(i) }()` — each closure’s env_ptr → &i_shared.
heap:
  g0.closure @ 0xc000151000  env_ptr ──→  &i_shared @ 0xc0001500a0
  g1.closure @ 0xc000151040  env_ptr ──→  &i_shared @ 0xc0001500a0
  g2.closure @ 0xc000151080  env_ptr ──→  &i_shared @ 0xc0001500a0
Step 3: Loop completes; `i_shared` is 3; goroutines run and read through shared pointer.
heap:
  i_shared @ 0xc0001500a0  ──→  3
Step 4: Typical output: three lines of `3` — not `0 1 2`.
**Aha:** All goroutines share one variable; each sees the final value unless you copy per goroutine (parameter or `i := i`).
```

> [!success]- Answer
> Pass `i` as a parameter:
>
> ```go
> for i := 0; i < 3; i++ {
> 	wg.Add(1)
> 	go func(n int) {
> 		defer wg.Done()
> 		fmt.Println(n)
> 	}(i)
> }
> ```
>
> Or use a per-iteration copy:
>
> ```go
> for i := 0; i < 3; i++ {
> 	i := i
> 	wg.Add(1)
> 	go func() {
> 		defer wg.Done()
> 		fmt.Println(i)
> 	}()
> }
> ```
>
> Both approaches give each goroutine its **own** `int` slot instead of sharing the loop variable's single slot.

---

## 7. Gotchas & Interview Traps

**Defer inside loops with closures.** A deferred function captures outer variables by reference. Combining `defer` with loop indices can surprise you if you expected a per-iteration snapshot.

**Accidental sharing in `range` over pointers or structs.** If you capture a loop variable that aliases mutable state, you can mutate the wrong element after the loop advances.

**Closures in benchmarks.** Capturing variables can defeat compiler optimizations or change escape behavior; microbenchmarks can lie if closure allocation dominates.

**"I fixed it with `go 1.22`" as a complete answer.** Interviewers want the **model**: shared outer storage, reference capture, and explicit copying when needed.

**Heavy closures in hot paths.** Each distinct closure value may allocate. Not always wrong, but know there is a cost.

---

## 8. Interview Gold Questions (Top 3)

1. **What does it mean that Go closures capture variables by reference?** Expect you to explain a single outer slot shared by multiple closures, contrast with copying via parameters or local `v := v`, and connect to heap escape when the closure outlives the frame.

2. **Why do concurrent goroutines inside a `for` loop sometimes all print the same index?** Expect the loop variable reuse story, a diagram of one `i`, and fixes: parameter, inner copy, or Go 1.22 loop scoping with the caveat that understanding capture still matters.

3. **What is the difference between a function value and a closure?** Expect: every function value has code; a closure adds an environment binding captured variables so the code can close over outer state.

---

## 9. 30-Second Verbal Answer

Functions in Go are **first-class values**. A **closure** is a function value that **captures outer variables by reference**, so it sees live updates and shares one outer slot with other closures from the same scope. That is why **`go func() { ... }()` in a loop** famously captured a **single** loop variable; fixes copy into a parameter or a per-iteration local, and Go 1.22 changed loop variable scoping but the **concept** still shows up in interviews. Captured variables that must outlive the stack frame **escape to the heap** and stay alive until the closure is unreachable.

---

> See [[Glossary]] for term definitions.
