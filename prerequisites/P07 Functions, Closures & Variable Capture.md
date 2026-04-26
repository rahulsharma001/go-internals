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

```
Outer frame (stack or heap after escape)
+------------------+
| n  ----------+   |     Closure value
+------------------+          |
        ^                     |
        |                     v
        |              +-------------+
        +------------> | code ptr    |
                       | captured: &n|
                       +-------------+
                              |
                              v
                       reads/writes n
```

**Error-driven picture: loop variable trap.** One variable `i` is reused each iteration. Every goroutine closes over **the same** `i`. By the time goroutines run, the loop may have finished and `i` holds the final value.

```go
for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i) // all see the same i
    }()
}
```

```
time ---->

main thread:  i=0  i=1  i=2  i=3 (loop done)
                    \   \   \
goroutines wake up:  all read SAME i -> often prints 3,3,3
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

```
values in memory
+-------+     +------------------+
| add   | --> | func object      |
+-------+     | (code + env ptr) |
              +------------------+
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

```
each iteration:
  new v on stack (or register)
  literal executes immediately () 
  unless deferred or stored, closure may be short-lived
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

```
counter frame after return:
  n lives on heap (escaped)
       ^
       |
  +----+----+
  | c closure |
  +-----------+
  env: &n
```

Each call to `counter()` creates a **fresh** `n` and a **new** closure with its own `&n`.

### 4.4 Heap escape of captured variables

If a variable is referenced by a closure that **outlives** its enclosing stack frame, the compiler **escapes** that variable to the **heap**. The garbage collector tracks it like any other heap object.

```go
func makeClosure(x int) func() int {
    return func() int { return x }
}
```

```
stack frame of makeClosure would die after return
but x is still reachable via closure
        => x moved/allocated on heap
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

```
twice receives f ----+
                     v
              +---------------+
returned fn   | env: &f      |
              +---------------+
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

```
one v slot reused:
v: | 10 | -> | 20 | -> | 30 | -> (final 30)
all closures point to final v => three prints of 30
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

```
secret -----+
            v
         [heap]
            ^
Job.run closure holds reference
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

```
single i in enclosing scope
all three goroutines: env -> &i
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

```
go func(n int) { ... }(i)
              ^       ^
           new n   copy of current i
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

```
each iteration:
  outer i (loop)
  inner i (new var) distinct per iteration
closure captures inner i
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

```
greet variable
+------+
| ptr  | ---> function value (code)
+------+
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

```
heap:
  n: 0 -> 1 -> 2

c closure
+--------+
| &n     |
+--------+
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

```
all goroutines: capture &i
i races to 3 before prints
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

```
iteration 0: n=0  iteration 1: n=1  iteration 2: n=2
each closure has its own n (parameter slot)
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
