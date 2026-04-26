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
MEMORY TRACE:

Step 1: main() calls A() — push A's frame
  call stack:
    ┌─────────────────────────────┐  ◄── top (current)  SP ≈ 0x7fff_c0a0
    │ A() frame                    │
    │   return addr: main +0x18     │ ──→ after A returns
    │   locals: (A's)              │
    ├─────────────────────────────┤
    │ main() frame                 │
    │   return addr: runtime       │
    └─────────────────────────────┘

Step 2: A() calls B() — push B
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_c040
    │ B() frame                    │
    │   return addr: A +0x24        │ ──→ after B returns
    ├─────────────────────────────┤
    │ A() frame                    │
    ├─────────────────────────────┤
    │ main() frame                 │
    └─────────────────────────────┘

Step 3: B() calls C() — C is running
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_bfe0
    │ C() frame                    │
    │   return addr: B +0x30        │ ──→ after C returns
    ├─────────────────────────────┤
    │ B() frame                    │
    ├─────────────────────────────┤
    │ A() frame                    │
    ├─────────────────────────────┤
    │ main() frame                 │
    └─────────────────────────────┘

Step 4: INSIDE C, before return — locals and defer list on C's frame only
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ C() frame                    │
    │   locals: only visible here  │
    │   defer stack (LIFO):        │
    │     [defer₁][defer₂]…        │ ◄── last registered runs first at exit
    │   return addr: B +0x30        │
    ├─────────────────────────────┤
    │ B() frame                    │
    ├─────────────────────────────┤
    │ A() frame                    │
    ├─────────────────────────────┤
    │ main() frame                 │
    └─────────────────────────────┘

Step 5: C returns — C's frame popped; B resumes
  call stack:
    ┌─────────────────────────────┐  ◄── top  C's frame gone; C's locals gone
    │ B() frame                    │
    ├─────────────────────────────┤
    │ A() frame                    │
    ├─────────────────────────────┤
    │ main() frame                 │
    └─────────────────────────────┘

  **Aha:** Only the top frame is “live” for your variables; popping C is what makes C’s locals disappear for good.
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
MEMORY TRACE (defer stack lives inside outer's frame):

Step 1: Enter outer() — frame pushed; defer A registered
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ outer() frame                │
    │   defer stack (LIFO):        │
    │     bottom ──→ [ A ] ◄── top │
    │   return addr: caller        │
    └─────────────────────────────┘

Step 2: Register defer B — pushed on defer stack (on top of A)
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ outer() frame                │
    │   defer stack (LIFO):        │
    │     bottom ──→ [ A ][ B ] ◄── top │  ◄── B runs first at exit
    │   return addr: caller        │
    └─────────────────────────────┘

Step 3: Run body — fmt.Println("body")

Step 4: Function exit — unwind defers top-first: B runs, then A, then frame pops

  **Aha:** Defer is a stack attached to the frame, not a queue — LIFO matches “last chore registered, first done at cleanup.”
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
MEMORY TRACE:

Step 1: Caller invokes add(a, b) — callee frame allocated at SP ≈ 0x7fff_d100
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ add() frame                  │
    │   return addr: caller +0x1C   │ ──→ instruction after call
    │   params: a, b               │
    │   local: sum = a + b         │
    │   result slot: int (to caller)│
    ├─────────────────────────────┤
    │ caller frame                 │
    └─────────────────────────────┘

Step 2: add returns sum — value written to result slot; frame popped; caller resumes

  **Aha:** Params, locals, return address, and result space are one bundle — the frame — tied to this one invocation.
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
MEMORY TRACE:

Step 1: main() calls f() — push f's frame
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_e080
    │ f() frame                    │
    │   return addr: main +0x14     │ ──→ after f returns
    ├─────────────────────────────┤
    │ main() frame                 │
    │   return addr: runtime       │
    └─────────────────────────────┘

Step 2: f() calls g() — push g
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_e020
    │ g() frame                    │
    │   return addr: f +0x0C        │ ──→ after g returns
    ├─────────────────────────────┤
    │ f() frame                    │
    ├─────────────────────────────┤
    │ main() frame                 │
    └─────────────────────────────┘

Step 3: g() returns — pop g; resume f
    ┌─────────────────────────────┐  ◄── top
    │ f() frame                    │
    ├─────────────────────────────┤
    │ main() frame                 │
    └─────────────────────────────┘

Step 4: f() returns — pop f; resume main
    ┌─────────────────────────────┐  ◄── top
    │ main() frame                 │
    └─────────────────────────────┘

Step 5: main() returns — stack empty for this goroutine's root return path

  **Aha:** Nesting depth equals frame count; every return peels exactly one frame — strict LIFO.
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
MEMORY TRACE:

Step 1: bump(x) running — e.g. caller passed x = 7, frame at SP ≈ 0x7fff_f060
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ bump() frame                 │
    │   return addr: caller +0x20   │ ──→ after bump returns
    │   param: x = 7               │
    │   local: y = x + 1  (= 8)    │
    │   result slot: int           │
    ├─────────────────────────────┤
    │ caller frame                 │
    └─────────────────────────────┘

Step 2: bump returns y — result slot = 8; frame popped; x and y no longer exist as stack locals

  **Aha:** `y` only “exists” while this frame exists; no hidden second life on the stack after pop.
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
MEMORY TRACE:

Step 1: split(sum) entered — named results are frame locals from the first instruction (zero-initialized)
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_9040
    │ split() frame                │
    │   return addr: caller +0x28   │ ──→ after split returns
    │   param: sum                 │
    │   named results (caller slots):│
    │     x = 0, y = 0  ──→ live whole function │
    │   defer list: (any defers see x, y)      │
    ├─────────────────────────────┤
    │ caller frame                 │
    └─────────────────────────────┘

Step 2: Body assigns x, y; bare `return` copies final x,y to outgoing result protocol; defer may still mutate x,y before caller reads

  **Aha:** Named results are not “created at return” — they are real variables in the frame, which is why defer can rewrite what the caller gets.
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
MEMORY TRACE:

Step 1: a() calls first b() — new frame for this invocation
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_8100
    │ b() frame  (call #1)       │
    │   return addr: a +0x10        │ ──→ between the two b() calls
    ├─────────────────────────────┤
    │ a() frame                    │
    └─────────────────────────────┘

Step 2: first b() returns — that frame popped
    ┌─────────────────────────────┐  ◄── top
    │ a() frame                    │
    └─────────────────────────────┘

Step 3: a() calls second b() — fresh b frame (different locals lifetime from call #1)
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_8100  (new frame, same depth)
    │ b() frame  (call #2)       │
    │   return addr: a +0x1C        │ ──→ after second b returns
    ├─────────────────────────────┤
    │ a() frame                    │
    └─────────────────────────────┘

  **Aha:** Same function text, different frame each time — two calls ⇒ two workspaces, not one reused bowl.
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
MEMORY TRACE (pattern applies to safeEscape once return runs; v itself may live on heap if escaped):

Step 1: While g() [or any callee] is still executing
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ g() frame                    │
    │   locals: …                  │
    │   return addr: caller +0x??   │
    ├─────────────────────────────┤
    │ … caller chain …             │
    └─────────────────────────────┘

Step 2: After g() returns — g's frame popped
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ caller frame                 │  ◄── g's locals are gone; stack storage reused
    └─────────────────────────────┘

  **Aha:** “After return” means the frame is gone — stack locals are not yours anymore unless the compiler moved them (escape).
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
MEMORY TRACE:

Step 1: Enter demo() — frame at SP ≈ 0x7fff_7000
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ demo() frame                 │
    │   return addr: caller        │
    │   defer stack: [ println defer ] │
    └─────────────────────────────┘

Step 2: Run body — fmt.Println("body") while frame still active

Step 3: Exit sequence — run deferred calls (LIFO), still in demo's frame; then return protocol

Step 4: Pop demo's frame — defers done; locals gone

  **Aha:** Defer runs after the body but before the frame is fully torn down — same frame, later phase.
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
MEMORY TRACE:

Step 1: Enter trick() — named result n in frame (0)
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ trick() frame                │
    │   return addr: caller +0x40   │
    │   named result: n = 0        │ ◄── slot caller will read
    │   defer stack: [ closure: n++ ] │
    └─────────────────────────────┘

Step 2: `return 1` — assigns 1 into named slot n (n = 1)

Step 3: Defer runs — closure increments n in same frame (n = 2)

Step 4: Return completes — caller receives n = 2; then frame pops

  **Aha:** The “envelope” n lives in the frame; defer mutates it after the return expression assigned into it but before the caller truly gets control.
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
MEMORY TRACE:

Step 1: G1 runs work(1), G2 runs work(2) — separate stacks, same function text
  goroutine G1 stack (base ≈ 0xc000000000):     goroutine G2 stack (base ≈ 0xc000001000):
    ┌─────────────────────────┐                  ┌─────────────────────────┐
    │ work() frame            │ ◄── top          │ work() frame            │ ◄── top
    │   param: id = 1         │                  │   param: id = 2         │
    │   return addr: G1 sched │                  │   return addr: G2 sched │
    └─────────────────────────┘                  └─────────────────────────┘

Step 2: New goroutine — tiny initial stack (e.g. ~2 KiB); depth stays small until recursion/deep calls

Step 3: Stack growth — runtime allocates larger block (e.g. 0xc000002000..), copies live frames, fixes internal pointers; old stack abandoned

  **Aha:** Stacks don't share memory between goroutines; growth is copy/relocate, not unbounded in place.
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
MEMORY TRACE:

Step 1: blow() calls blow() — each call pushes a new frame, no return ever unwinds
  call stack (conceptual addresses climbing SP):
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_0100
    │ blow() frame  depth N      │
    │   return addr: blow +0x08   │ ──→ immediate re-call
    ├─────────────────────────────┤
    │ blow() frame  depth N-1    │
    ├─────────────────────────────┤
    │ … more blow frames …       │
    ├─────────────────────────────┤
    │ blow() frame  depth 1      │
    ├─────────────────────────────┤
    │ main() frame               │
    └─────────────────────────────┘

Step 2: Stack limit — no room for another frame; runtime aborts (stack overflow)

  **Aha:** Recursion without a base case is pure push — frames pile up until the goroutine stack cap is hit.
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
MEMORY TRACE:

Step 1: Inside c() while fmt.Println runs — deepest callee on top
  call stack (top ◄── current SP ≈ 0x7fff_a200):
    ┌─────────────────────────────┐  ◄── top
    │ fmt.Println frame (callee)   │  (or runtime/print path)
    │   return addr: c +0x??        │ ──→ back into c
    ├─────────────────────────────┤
    │ c() frame                    │
    │   return addr: b +0x??        │ ──→ after c returns
    ├─────────────────────────────┤
    │ b() frame                    │
    │   return addr: a +0x??        │
    ├─────────────────────────────┤
    │ a() frame                    │
    │   return addr: main +0x??     │
    ├─────────────────────────────┤
    │ main() frame                 │
    │   locals: (after "in main")  │
    └─────────────────────────────┘

  **Aha:** The function printing "in c" is not floating alone — the whole chain of frames still exists underneath.
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
MEMORY TRACE:

Step 1: Enter main — first defer registered (third runs first among defers)
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_b000
    │ main() frame                 │
    │   defer stack: [ D3 ]        │  ◄── D3 = third registered
    │   return addr: runtime       │
    └─────────────────────────────┘

Step 2: Second defer — D2 pushed on top of D3
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ main() frame                 │
    │   defer stack: [ D3 ][ D2 ]  │  ◄── D2 on top
    │   return addr: runtime       │
    └─────────────────────────────┘

Step 3: Third defer — D1 on top (first registered string runs last among defers)
  call stack:
    ┌─────────────────────────────┐  ◄── top
    │ main() frame                 │
    │   defer stack:               │
    │     bottom ──→ [ D3 ][ D2 ][ D1 ] ◄── top
    │   return addr: runtime       │
    └─────────────────────────────┘

Step 4: Run body — fmt.Println("main body")

Step 5: Exit — unwind LIFO: run D1, then D2, then D3; then pop main's frame

  **Aha:** Registration order builds bottom→top; exit order peels top→bottom — last registered defer runs first.
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
MEMORY TRACE:

Step 1: Enter total() — named sum in frame; defer registered
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_c100
    │ total() frame                │
    │   return addr: main +0x??     │
    │   named result: sum = 0      │ ◄── caller-visible slot
    │   defer stack: [ closure: sum += 10 ] │
    └─────────────────────────────┘

Step 2: sum = 5 — named slot updated in frame

Step 3: return sum — assigns 5 into named sum (still 5); defer runs next

Step 4: Defer — sum += 10 → sum = 15 in same frame

Step 5: Return completes — caller reads 15; frame pops

  **Aha:** Named `sum` never left the frame; defer ran after the return expression but still saw the same slot.
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
MEMORY TRACE:

Step 1: main calls recurse(0) — first frame
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_d200
    │ recurse(n) frame             │
    │   param: n = 0               │
    │   return addr: main +0x??     │ ──→ never reached
    ├─────────────────────────────┤
    │ main() frame                 │
    └─────────────────────────────┘

Step 2: recurse returns recurse(n+1) — each call pushes another frame before any return unwinds
  call stack:
    ┌─────────────────────────────┐  ◄── top  param n = K
    │ recurse frame               │
    │   return addr: recurse +0x?  │ ──→ parent recurse (still waiting)
    ├─────────────────────────────┤
    │ … K more recurse frames …    │
    ├─────────────────────────────┤
    │ recurse(0)                  │
    ├─────────────────────────────┤
    │ main()                      │
    └─────────────────────────────┘

Step 3: Stack overflow — unbounded growth, no pop; runtime stops the goroutine

  **Aha:** Tail-call shape in source does not magically recycle the frame here — each call is a new push until the cap.
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
MEMORY TRACE:

Step 1: i = 0 — defer fmt.Println(i) executes: arguments evaluated **now** (i is 0); defer record pushed
  call stack:
    ┌─────────────────────────────┐  ◄── top  SP ≈ 0x7fff_e300
    │ enclosing frame              │
    │   local: i = 0               │
    │   defer stack: [ Println(0) ]  │  ◄── value 0 captured in defer record
    └─────────────────────────────┘

Step 2: i++ — local i becomes 1; defer record still holds **0**

Step 3: Function exit — deferred Println runs with saved arg 0 → prints 0; then frame pops

  **Aha:** For `defer f(args)`, args are fixed at registration; only `defer func(){ ... i ... }` sees the variable later.
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
