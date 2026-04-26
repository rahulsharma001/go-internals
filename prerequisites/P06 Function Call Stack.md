# P06 Function Call Stack

> **Prerequisite note** — complete this before starting **T10 Defer, Panic & Recover Internals** or **T13 Goroutine Internals**.
> Estimated time: ~15 min

---

## 1. Concept

The **call stack** is a last-in-first-out pile of **stack frames**. Each frame belongs to one function call that has started but not finished yet.

> **In plain English:** Picture a spring-loaded stack of cafeteria trays. Each new tray you add sits on top. When you need a tray, you take the top one off first. A function call is like placing a tray. Returning from the function is like removing that tray. The tray on top is always the call that is currently running.

---

## 2. Core Insight (TL;DR)

**Each active call gets one frame.** The CPU follows **return addresses** to know where to resume after a call finishes. **Defer** schedules cleanup that runs while the frame still exists but **after** the function body completes, so deferred calls unwind in **reverse order** like nested trays coming off the stack. **Named results** live in the caller-visible result slots that **defer** can still touch before the function truly returns.

---

## 3. Mental Model (Lock this in)

**Cafeteria tray stack.** Outer function places the bottom tray. Inner calls add trays on top. Returns peel trays from the top down. **Defer** attaches little sticky notes: "do this before you throw away my tray," and those notes are processed **top tray first** when the function ends.

**Three nested calls, then unwind with defers:**

```
CALLING DOWN (push frames):

  frame for C  ← top, C is running
  frame for B
  frame for A
  frame for main
```

```
INSIDE C, BEFORE RETURN:

  C's locals live only in C's frame
  defers registered in C wait in a LIFO list attached to C's frame
```

```
AFTER C RETURNS (pop C, resume B):

  frame for B  ← top
  frame for A
  frame for main
```

**Defer fits LIFO:**

```
func outer() {
    defer fmt.Println("1st registered, runs 2nd")
    defer fmt.Println("2nd registered, runs 1st")
    fmt.Println("body")
}
```

Execution order: body prints, then second defer, then first defer. The **last** `defer` you write is the **first** to run at return time.

```
defer list for outer's frame (conceptual):

  push: defer A  →  [A]
  push: defer B  →  [A, B]   // B is on the "top"

at return, run top-first  →  B runs, then A
```

> **In plain English:** Defers are not a queue at the deli counter. They are a stack of chores you assigned yourself. The last chore you wrote down is the first one you actually do when you clean up and leave the room.

---

## 4. How It Works

### 4.1 What lives in a stack frame

A frame is the bookkeeping for **one** invocation. Typical contents:

- **Parameters** passed into this call
- **Local variables** declared in this function
- **Return address**: instruction pointer where execution resumes in the **caller** after this call returns
- Space for **return values** the caller will read
- Compiler temporaries and spill slots you rarely name in Go source

The exact layout is ABI and compiler dependent. For interviews, the durable idea is **scoped lifetime**: anything tied to this call dies when the frame is popped, unless the compiler moves it elsewhere for correctness.

**Tiny example:**

```go
func add(a, b int) int {
    sum := a + b
    return sum
}
```

```
frame for add while running:

  +------------------+
  | return address   |  → back into caller
  | a, b  (params)   |
  | sum   (local)    |
  | slot for result  |
  +------------------+
```

### 4.2 Push on call, pop on return

**Call:** the runtime prepares a new frame, copies or registers parameters, stores where to resume, then jumps into the callee.

**Return:** the callee writes results, execution jumps to the saved return address, and the callee frame is reclaimed.

Order is strictly **LIFO**. If `main` calls `f` calls `g`, finishes `g`, then `f`, then `main`, frames appear and disappear like nested parentheses.

```go
func g() { }
func f() { g() }
func main() { f() }
```

```
main calls f:

  [main][f]

f calls g:

  [main][f][g]

g returns:

  [main][f]

f returns:

  [main]

main eventually returns:

  []
```

### 4.3 Locals and parameters live in the frame

```go
func counter() func() int {
    n := 0
    return func() int {
        n++
        return n
    }
}
```

Here `n` must outlive `counter`'s return. The compiler does **not** keep `n` on `counter`'s stack frame in the naive sense. It escapes to the heap inside a closure object. That is the bridge to **stack versus heap**: the language lets you write locals, but the compiler decides where they actually live.

**Contrast with plain locals:**

```go
func bump(x int) int {
    y := x + 1
    return y
}
```

While `bump` runs, `x` and `y` are tied to `bump`'s frame. When `bump` returns, that frame conceptually vanishes. Holding a pointer to `y` after return would be a bug; Go's escape analysis and types usually prevent that at compile time.

```
frame for bump:

  x
  y
  return address
  result slot
```

### 4.4 Return path and named return values

**Named results** are special in Go: they are **variables in the outer function's frame**, initialized to zero values, visible to the whole function body **and** to deferred functions.

```go
func split(sum int) (x, y int) {
    x = sum * 4 / 9
    y = sum - x
    return
}
```

Conceptually, `x` and `y` are not ephemeral names invented only at the `return` statement. They are real slots the caller will read after this function completes.

```
frame for split:

  sum
  x  (named result, lives whole function)
  y  (named result, lives whole function)
  defers can see x, y
```

That is why a `defer` can assign to named results and change what the caller receives.

---

## 5. Key Rules & Behaviors

### Every function call pushes a frame

```go
func a() { b(); b() }
func b() { }
```

Each `b()` is a **new** frame, even though the function code is shared.

```
first b():

  [a][b]

back to a:

  [a]

second b():

  [a][b]
```

> **In plain English:** Reusing the same recipe does not reuse the same mixing bowl mid-bake. Each call gets its own workspace.

### Return pops the frame; locals are gone

```go
func safeEscape() *int {
    v := 42
    return &v
}
```

The address of `v` outlives the call. The compiler **escapes** `v` to the heap so the pointer stays valid after `safeEscape`'s frame is gone. If the storage truly lived only in the frame you just popped, the pointer would dangle. Go does not let that happen for code like this.

**Contrast in spirit:** a language without escape analysis might let you build a pointer into a dead frame. Go refuses that failure mode for ordinary code paths by moving `v` elsewhere when its address escapes.

**Mental picture after return:**

```
before return from g:

  ... [g-frame with locals]

after return:

  g-frame reclaimed; those locals are not yours anymore
```

> **In plain English:** When you leave a hotel room, you do not get to keep using the nightstand drawer. The next guest might overwrite it.

### Defer runs after the function body but before the frame is fully torn down

```go
func demo() {
    defer fmt.Println("defer")
    fmt.Println("body")
}
```

Output:

```
body
defer
```

The deferred call executes as part of the **function exit sequence**, still in the context of `demo`'s frame.

```
timeline for demo():

  enter demo → push frame
  register defer
  run body
  run deferred calls (LIFO among defers)
  finish return protocol → pop frame
```

> **In plain English:** You finish your homework first. Then you do the chores you pinned to the door on the way in. Then you actually leave the house.

### Named return values live in the frame; defer can modify them

```go
func trick() (n int) {
    defer func() { n++ }()
    return 1
}
```

What the caller receives is **2**, not **1**. The bare `return 1` assigns to `n`. The deferred closure runs afterward and increments `n`.

```
order:

  n starts at 0
  return 1  →  n = 1
  defer runs →  n = 2
  caller reads n → 2
```

> **In plain English:** The envelope is labeled before you walk out. A defer can still scribble on the label before you hand it over.

### Goroutines have their own stack

Each **goroutine** begins with a **small** stack that grows as needed. Stacks do not overlap between goroutines. Two goroutines calling the same function still have **separate** frames.

```go
func work(id int) {
    // this frame belongs to whichever goroutine called work
}

func main() {
    go work(1)
    work(2)
}
```

```
goroutine G1 stack:     goroutine G2 stack:

  ...                     ...
  [work frame id=1]       [work frame id=2]
```

> **In plain English:** Two cooks can follow the same recipe at the same time. Each one still needs a separate cutting board.

### Stack overflow means too many nested frames

**Infinite recursion** keeps pushing frames until the stack limit trips.

```go
func blow() { blow() }

func main() {
    blow()
}
```

Runtime error: stack overflow.

```
conceptual:

  [blow][blow][blow]... until no room left
```

> **In plain English:** You keep opening new Russian nesting dolls forever. Eventually the table is not big enough.

---

## 6. Code Examples (Show, Don't Tell)

### Simple call chain with ASCII stack trace

```go
package main

import "fmt"

func c() { fmt.Println("in c") }
func b() { fmt.Println("in b"); c() }
func a() { fmt.Println("in a"); b() }

func main() {
    fmt.Println("in main")
    a()
    fmt.Println("back in main")
}
```

While `fmt.Println` inside `c` runs:

```
top → bottom:

  [c's frame]
  [b's frame]
  [a's frame]
  [main's frame]
```

### Defer order explained via stack

```go
package main

import "fmt"

func main() {
    defer fmt.Println("third runs first among defers")
    defer fmt.Println("second")
    defer fmt.Println("first registered runs last among defers")
    fmt.Println("main body")
}
```

```
defer stack after three defers:

  bottom: third registered
          second
  top:    first registered   ← runs first at exit
```

### Named return modified by defer

```go
package main

import "fmt"

func total() (sum int) {
    defer func() {
        sum += 10
    }()
    sum = 5
    return sum // sum is 5, then defer adds 10
}

func main() {
    fmt.Println(total()) // 15
}
```

```
sum timeline:

  after assignment: 5
  at return assign: still 5 into named sum
  defer: sum = 5 + 10 → 15
  caller sees: 15
```

### Stack overflow

```go
package main

func recurse(n int) int {
    return recurse(n + 1)
}

func main() {
    _ = recurse(0)
}
```

```
each call adds a frame without ever returning:

  [recurse][recurse][recurse]...
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

```go
package main

import "fmt"

func f() (r int) {
    defer func() {
        r += 2
    }()
    if r == 0 {
        return 5
    }
    return 1
}

func main() {
    fmt.Println(f())
}
```

> [!success]- Answer
> Prints **7**.
>
> Named result `r` starts at **0**. The condition `r == 0` is true, so the branch executes `return 5`, which assigns **5** to `r`. The deferred function then runs and does `r += 2`, yielding **7**. There is only one return path taken, and the defer always runs after that assignment.

### Tier 2: Fix the Bug (5 min)

The program should print pairs lines in an **unbuffered** way, but the author tried to micro-optimize with a deferred `Close` on `os.Stdout`. Explain why this is wrong and show a correct pattern.

```go
package main

import (
    "fmt"
    "os"
)

func main() {
    f, err := os.OpenFile("out.txt", os.O_CREATE|os.O_WRONLY, 0o644)
    if err != nil {
        panic(err)
    }
    defer f.Close()

    os.Stdout = f
    defer func() { _ = os.Stdout.Close() }()

    fmt.Println("hello")
}
```

> [!success]- Answer
> **Bug:** Reassigning `os.Stdout` to a file handle and then deferring `Close` on `os.Stdout` closes whatever `os.Stdout` points to **at defer execution time**. If other code mutates `os.Stdout` before main returns, you may close the wrong thing. More importantly, closing the process's standard output handle while the runtime may still write errors is a design smell. For this exercise, the core trap is treating a **global** like `os.Stdout` as if it were a simple local file variable.
>
> **Correct pattern:** Keep a **local** `*os.File` variable, write through it, defer `Close` on **that** local only, and never rebind `os.Stdout` unless you really intend to redirect the whole process and manage lifetime carefully.
>
> ```go
> package main
>
> import (
>     "fmt"
>     "os"
> )
>
> func main() {
>     f, err := os.OpenFile("out.txt", os.O_CREATE|os.O_WRONLY, 0o644)
>     if err != nil {
>         panic(err)
>     }
>     defer f.Close()
>
>     fmt.Fprintln(f, "hello")
> }
> ```
>
> This ties the defer to the **frame-local** `f`, which matches the mental model: defers run while the frame exists, against stable locals, not moving global handles.

---

## 7. Gotchas & Interview Traps

**Defer argument evaluation happens when the `defer` statement executes, not when the deferred call runs.**

```go
i := 0
defer fmt.Println(i) // prints 0
i++
```

The `fmt.Println` closure captures the value of `i` at defer registration time for this form. Interviewers love variants with `defer func() { fmt.Println(i) }()` where the closure sees the **variable** later.

```
register defer: evaluate arguments now
later at return: run the call
```

**Named return confusion.** Mixing bare `return` and expressions, or multiple returns with defers that assign to named results, produces puzzles. Draw the **single** named slots in the frame.

**Stack growth.** Goroutine stacks **grow** by allocating a larger block and **copying** the old stack. Pointers into the stack are updated by the runtime during copy. Do not assume a `uintptr` to a stack address stays valid across a growth event. In normal Go code you rarely observes this; interviews mention it to test whether you know stacks move.

**Stack versus heap.** Locals start life as **locals** in the source. The compiler places them on the stack **if they can die with the frame**. If pointers leak upward or outward, they **escape** to the heap. That is not a performance moral story in the interview; it is a **lifetime** story.

---

## 8. Interview Gold Questions (Top 3)

1. **What is a stack frame, and what is pushed or popped across a function call?** Expect you to mention parameters, locals, return address, return values, and LIFO ordering.

2. **Why do defers run in reverse order, and when are deferred arguments evaluated?** Expect LIFO defer lists plus the distinction between evaluated arguments and closure capture.

3. **How can a defer change what a caller receives from a function?** Walk through named return values living in the outer frame, assignment on `return`, then defer mutating those slots before the function completes.

---

## 9. 30-Second Verbal Answer

The call stack is a LIFO pile of frames, one per active call. Each frame holds parameters, locals, where to resume in the caller, and space for results. Calling pushes, returning pops. **Defer** registers cleanup that runs after the body as the function exits, in reverse registration order. **Named results** are real variables in that function's frame, so **defer** can still update what the caller reads. Each **goroutine** has its own growing stack; infinite recursion exhausts that stack and overflows.

---

> See the **Glossary** for term definitions.
