# T10 Defer, Panic & Recover Internals

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T10 Defer, Panic & Recover Internals - Interview Questions]]
> Something not clicking? → [[simplified/T10 Defer, Panic & Recover Internals - Simplified]]

---

## 0. Prerequisites

Complete these before starting this topic:

- [[prerequisites/P06 Function Call Stack]]

---

## 1. Concept

A **`defer` statement** schedules a function to run when the **surrounding function** returns, every `return` path, or a **panic** starts unwinding. The scheduled work is **not** the next line. It is "later, on the way out."

A **`panic`** stops normal control flow. It **unwinds** the stack, runs **deferred** functions in that **goroutine**, and if nothing **recovers**, the program reports a panic and may exit that goroutine or the whole process, depending on context.

A **`recover`** is a **built-in** that **returns the panic value** and **stops the panic** if it is called **while a deferred function from that same goroutine is still running** on the way out. Otherwise it returns **`nil`**.

> **In plain English:** `defer` is a sticky note you put on the door on your way in: you promise to do one more chore when you leave. `panic` is a fire alarm: everyone stops their normal work and runs for the exit. `recover` is a fire extinguisher you mounted **on that same door** — it only works if you already put the mount there with `defer`.

---

## 2. Core Insight (TL;DR)

**Three rules lock most interview answers.** **First,** arguments to a deferred function are **fully evaluated and copied at the `defer` line**, not when the deferred work runs. **Second,** deferred work runs in **LIFO** order. The **last** `defer` you wrote in that function is the **first** to run on exit. **Third,** if the function has **named result parameters**, deferred functions can **read and write** those names on the way out, which is how the famous "double return" works.

**`recover` is goroutine-scoped and defer-scoped.** It does **not** cross goroutines. A parent function cannot "catch" a **panic in a child goroutine** the way a server might "catch" an error in a worker. That panic crashes that child unless **that** goroutine’s own `defer` + `recover` handles it.

> **In plain English:** You schedule chores with `defer` when you can still read the **labels on the boxes** for arguments, even if the room changes before you do the chore. The cleanup line is **LIFO** because you pile sticky notes, then peel from the top. A panic in another **worker thread** in your company is not your sticky pile — you never see the alarm.

---

## 3. Mental Model (Lock this in)

### The Sticky-Note Stack

Each **`defer` in a function** adds one **frame of work** to a **per-function stack of deferred calls** for that activation. The stack is a **LIFO** stack. The **newest** note is on top. On **any** return or panic, Go **peels from the top** first.

```
defer A   ── pushes  [ A ]           stack:  top → A
defer B   ── pushes  [ B ]           stack:  top → B, A
defer C   ── pushes  [ C ]           stack:  top → C, B, A

function ends (return or panic unwind):
  run C  (first)
  run B
  run A  (last)
```

**Panic as fire alarm, recover as mounted extinguisher:** A **panic** starts an **emergency walk toward the door**. The **door** is where you hung **deferred** work. A **`recover` call** only "puts out" the panic if you already placed it in the **deferred** path. If the panic is in another **goroutine** (another room), your extinguisher in **this** room does nothing.

> **In plain English:** Sticky notes stack on a desk. You add new notes on top. When you stand up to leave, you read from the top down. A panic in another room is not on your desk.

### Mistake That Teaches: `defer` in a Loop

```go
// BUG: N files stay open until the *outer* function returns
func processAll(paths []string) error {
	for _, p := range paths {
		f, err := os.Open(p)
		if err != nil {
			return err
		}
		defer f.Close() // <- schedules one Close per path; LIFO; all at once at end
		// ... read f ...
	}
	return nil
}
```

```
Iteration 0:  defer #1: Close file₀   [stack: Close₀]
Iteration 1:  defer #2: Close file₁   [stack: Close₁, Close₀]
...
Iteration n:  FDs 0..n-1 are ALL still open
              until the whole function returns

       └── every iteration pushed another "Close later" note
           but "later" is ONE moment: outer function end
       └── file descriptor exhaustion risk  <-- OOPS
```

**Fix pattern:** do **one** `defer` per **loop body scope** that ends **before the next** iteration, or use a function literal per iteration.

```go
for _, p := range paths {
	func() { // or extract to a named function
		f, err := os.Open(p)
		if err != nil { /* handle */; return }
		defer f.Close()
		// work
	}()
}
```

> **In plain English:** A `defer` in a loop is like writing "I will clean every dish at midnight" a hundred times. You still have a hundred dishes on the table until midnight. The sink stays full. Put each meal in a **small** room, clean on the way out of **that** room, then start the next meal.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

> **In plain English:** The runtime does not "magically" remember your wishes. It keeps a small chain of "do this on exit" records per goroutine. A panic is a flag that tells the walk-out logic to run those records while a stack walk is in progress.

### 4.1 The `_defer` struct and the per-goroutine defer chain

The runtime uses a **linked list** of **defer records** attached to the **current goroutine** or fast path storage. A conceptual struct name you will see in **runtime** code is **`_defer`**. It holds a pointer to the **function**, **captured argument slots**, a link to the **next** record, and information about **open-coded** vs **heap** records.

**Mental shape:**

```
Goroutine G
  _defer* chain:   newest ──▶ _defer → _defer → _defer ──▶ (nil)
                    │           fn + args, link to next
                    └── LIFO: walk "newest" first
```

> **In plain English:** The runtime keeps a **clothesline of hooks** on the **line that belongs to this worker** only. You clip the newest tag next to your hand. When you back out, you unclip from the hand side first.

```go
// You never write _defer; this is read-the-runtime intuition only.
// (Names/sizes vary across Go versions; idea is stable.)
// type _defer struct { fn, args, link, ... }
```

```
your function frame
   │
   └── defer chain head on G:  d3 → d2 → d1
```

### 4.2 Open-coded defers (Go 1.14+)

Before **go1.14**, many defers always built **heap**-backed **records**. From **1.14** onward, the **compiler** can **open-code** many `defer` patterns. **If** a function **cannot** panic, or the compiler can prove a **cheap** path, it may **inline** the "run defers" epilogue. **If** a **panic** might happen, the runtime still needs a path that can **unwind** and find **ordered** work.

**Interview line:** "Open coding removes **allocation** in the **common no-panic** path, but the **panic** path still has to consult a correct ordering story."

> **In plain English:** The factory pre-writes your checkout steps on a **one-page checklist** you carry in your pocket, instead of making you fetch a new card from the **warehouse** for every errand, unless a real fire drill forces the old long path.

#### Tiny example + mental picture of "no work until epilogue"

```go
func f() {
	x := 1
	defer func() { println(x) }()
	x = 2
}
// prints 2: args captured, body runs at exit; see Key Rules
```

```
compile-time split (not exact, but the idea):
  - fast path: write straight-line code + a tiny "finish" block
  - slow path: panic/unwind has full defer chain
```

### 4.3 Panic mechanics — the `_panic` struct and stack unwind

A **panic** builds a **runtime** record often represented by **`_panic`**. The runtime **stops the normal** forward execution of that **goroutine**. It **unwinds** **stack frames** and **executes** **deferred** functions in the right **LIFO** order. If a **defers** a **`recover`**, the unwind can **stop** at that frame.

**Checklist: what happens on panic, high level**
1. Build panic value and mark **G** "panicking".
2. Walk back frames; run **deferred** work in **LIFO** order.
3. If **recover** succeeds in a valid place, return to normal flow at that `recover` site, with maybe adjusted **return** paths.
4. If unwinding **never** recovers, print stack + exit the **goroutine** (default behavior for user goroutines) or the **process** (some **main** cases you should still treat as "never rely on that").

> **In plain English:** A panic is a **flag on one toy train set**. The train **backtracks** along its track, visiting each **station** where you left a `defer` note. A **`recover` station** can fold the **flag** down. A train set in another playroom is separate.

#### Error-driven: panic in inner call

```go
func a() { b() }
func b() { panic(42) } // unwinds through a's defers, then b's, then ...
```

```
call stack (forward):   main → a → b
unwind:                 b →  run defers in b's frame
                        a →  run defers in a's frame
                        main → run defers in main
```

### 4.4 Recover — the goroutine must be panicking, the frame must be right

A **`recover()`** call checks whether **this** **goroutine** is currently **panicking**. **If** yes, and the **`recover` call** is **legally** placed **inside a deferred function execution path** that the runtime recognizes, it **returns the panic value** and **stops the panic** for that stack walk. If **not**—for example, **`recover()`** not **inside** a **deferred** function body, or a **silly** placement like `defer recover()` in some **wrong** form—it often returns **`nil`**.

> **In plain English:** The extinguisher **locks** to **this** **wall bracket** the building code approved. A random can on the floor does not count, even if you stand near it when the alarm blares.

```go
func ok() (re interface{}) {
	defer func() { re = recover() }()
	panic("boom")
	// not reached
}
```

```
panic "boom" registered on G
defer runs anonymous func
  recover()  →  returns "boom"  ✓
```

---

## 5. Key Rules & Behaviors

### Rule 1: Defer arguments are evaluated at the `defer` line, not at exit time

```go
func main() {
	i := 0
	defer fmt.Println("defer prints:", i) // argument list evaluated NOW
	i++
	fmt.Println("after:", i) // 1
}
// prints: after: 1, then "defer prints: 0" (evaluated 0)
```

```
Step: hit `defer fmt.Println("defer prints:", i)`
  evaluate fmt.Println, string constant, and **current i**  → 0
  those values are **stored in the defer record** (conceptually)

Step: i++  →  i is 1 in the frame

Step: on return
  run deferred call with **captured 0**  <-- aha: not "re-read" i
```

> **In plain English:** A **phone order** is taken the moment you say `defer` — the kitchen writes down **"no onions"** from **today’s** list. You can change the whiteboard after that. The old ticket does not rewrite itself.

---

### Rule 2: LIFO — last `defer` registered runs first

```go
func main() {
	defer fmt.Print("1 ")
	defer fmt.Print("2 ")
	defer fmt.Print("3 ")
}
// prints: 3 2 1
```

```
registration order: 1, then 2, then 3
stack:   top   3
              2
              1
execution: 3 → 2 → 1
```

> **In plain English:** The last **Post-it** you stack on the pile is the first one you peel when you clean the desk. That is **LIFO** order.

---

### Rule 3: Named return values can be written by deferred functions (the "double return")

```go
func f() (n int) { // n is a **named** result; addressable on the way out
	defer func() { n++ }()
	return 42  // 1) n := 42  2) defers: n++  3) RET with n=43
	// the famous: return sets n, then defers, then the **final** n goes to caller
}
```

```
without naming (different topic):  you copy into a nameless return slot
with naming:  `n` is one shared box

sequence:
1) `return 42` assigns **n = 42**
2) defers: **n++**  →  n = 43
3) the **final** n is 43
```

> **In plain English:** A **name tag** is stuck on a box the whole office shares for **this** shipment. A cleanup crew on the way out can still **relabel** the box, because the label is a **shared** physical slot.

**Trap:** the trick needs **named** result parameters and a correct mental model. Do not "clever" this in real APIs unless a reviewer loves Easter eggs.

> **In plain English:** A shared **in/out tray** is dangerous if three people "fix" the tag on the way out. Only use the tray on purpose, not to surprise readers.

---

### Rule 4: `recover` must be called **inside a deferred function**; awkward placements return `nil`

**Broken pattern 1: `recover()` not in a deferred function**

```go
func bad() {
	recover() // not inside defer → always useless here
}
```

**Broken pattern 2: `defer recover()` — not the usual safe shape**

For interviews, the **safe, readable** idiom is a **`defer` function literal** that calls `recover` **inside the literal** and checks the return value. Do not rely on cute one-liners in production.

```go
func good() (caught string) {
	defer func() {
		if v := recover(); v != nil {
			caught = fmt.Sprint(v)
		}
	}()
	panic("oops")
	// not reached, but the defer runs during panic unwind
	return ""
}
```

```
panic: "oops" on this goroutine
  unwind hits defer literal
  inside literal:  recover()  returns "oops"  ✓
```

> **In plain English:** The extinguisher’s **bracket** is the **`func() { ... }`**. You do not balance the can on the floor, say "trust me", and read the **manual** the wrong page.

**Deep spec edge:** the runtime tracks whether **recover** is **legal** in the current **deferred** activation. If you add **extra** layers that violate the spec’s rules about **where** the **call** to **recover** sits, you can get **`nil`**. The interview-safe rule: use the **`func() { v := recover(); ... }` pattern. Full depth lives in the spec and release notes, not a flashcard.

> **In plain English:** The building inspector checks **one** **approved** mounting plate. You cannot bolt through three random drywall patches and hope the stamp still counts.

---

### Rule 5: Panics are **goroutine-isolated**; parent cannot "catch" child

```go
func main() {
	defer func() { // this recover **never** sees the child's panic
		if v := recover(); v != nil {
			fmt.Println("parent caught:", v)
		}
	}()
	go func() { panic("child") }()
	time.Sleep(100 * time.Millisecond) // no guarantee this saves you
	// the child goroutine dies with its own panic; main's recover does not catch it
}
```

```
G_main:   defer+recover  ←  watches G_main’s panics only
G_child:  panic          ←  a **different** clothesline of notes

G_main’s recover:  not on G_child’s stack  →  does not help
```

> **In plain English:** A smoke alarm in **your** apartment does not silence a fire in **the neighbor’s** unit. You each have **separate** alarm loops.

---

## 6. Code Examples (Show, Don't Tell)

### LIFO ordering demo and the "value changes" surprise

**A: plain LIFO — three defers, no tricks**

```go
package main

import "fmt"

func main() {
	defer fmt.Print("1 ")
	defer fmt.Print("2 ")
	defer fmt.Print("3 ")
} // prints: 3 2 1
```

```
registration order: 1, 2, 3
execution order:      3, 2, 1   (same story as Key Rule 2)
```

**B: closure + mutating `i` after `defer` — predict before you run**

```go
package main

import "fmt"

func main() {
	i := 0
	defer func() { fmt.Println("defer:", i) }() // closure sees **variable** i, not a copy
	i = 1
	fmt.Println("before return:", i)
}
// before return: 1, then "defer: 1"
```

```
Step: defer records **closure** that reads **i** from the frame, not `i`’s value at defer time
Step: i = 1
Step: on exit, closure runs → prints **1**
```

> **In plain English:** A **name tag** you **read at dinner** is the **name on the person**, not a **photo** from breakfast. A **closure** **follows** the **box**; a **stamped** **argument** in `defer f(i)` is a **breakfast** **photo** — different rule.

**C: loop + closure — the classic fix, always `i := i` if unsure**

```go
for i := 0; i < 3; i++ {
	i := i // shadow copy per iter — safe, boring, right
	defer func() { fmt.Print(i) }()
}
// Go 1.22+ also gives new `i` per iteration, but the copy pattern still reads in old code reviews
```

```
each iteration, **you choose** a **separate** int box **i** to close over
  vs: one big shared `i` everyone reads last (language-version and pattern dependent)
```

> **In plain English:** A row of **stamped** name badges, one per **turn** in line, beats one **loudspeaker** that only shouts the **last** number **called**.

---

### Named return modification (the "double return" trick)

```go
func readTwice() (n int, err error) {
	defer func() {
		if err != nil {
			return
		}
		n = n * 2 // runs **after** the return expression assigned `n`
	}()
	return 21, nil
}
// caller sees n=42, err=nil
```

```
Step: `return 21, nil` sets **n = 21**, err = nil
Step: defers: **n = n*2**  →  n=42; err still nil
Step: return to caller with final n, err
```

> **In plain English:** The **out tray** is labeled **"final count"**. Accounting walks out last and **doubles the slip** in the **final** out tray if nobody flagged an error. If you return **anonymously**, that tray is not always the same object — **naming** matters.

---

### Panic and recover: HTTP **middleware** shape

**Pattern: recover at **handler** **boundary**, return **500**

```go
package main

import (
	"fmt"
	"net/http"
)

func withRecover(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if v := recover(); v != nil {
				w.WriteHeader(http.StatusInternalServerError)
				fmt.Fprint(w, "internal error")
				// log, metrics, request id (not shown)
			}
		}()
		next.ServeHTTP(w, r)
	})
}
```

```
request → middleware defer installed → **handler** runs
  if panic in handler:
     unwind → middleware’s defer
        recover() gets value, write 500, no process crash
  else:
     defers run on normal return
```

> **In plain English:** A **reception** desk puts a **net** at the **door** to your office suite. A tantrum in the **hall** still hits the **net** in **this** suite, not a **different** company branch.

> **In plain English:** In production, you still add **context deadlines**, **logging**, and **metrics** — a net does not write the apology letter, it **stops the vase** from shattering the lobby floor.

---

## 6.5. Practice Checkpoint

All runnable in the Go Playground: https://go.dev/play/

### Tier 1: Predict the output (2 min)

```go
package main
import "fmt"
func f() (x int) {
	defer func() { x += 1 }()
	return 10
}
func main() { fmt.Println(f()) }
```

**Before you run:** what prints?

```
hint row:
  name tag `x`?  return path?  defer order?  (see Key Rules 2–3)
```

> [!success]- Answer
> Prints `11`. Here's why:
> 1. `return 10` sets the named return value `x = 10`
> 2. Before the function actually returns, the deferred closure runs
> 3. The closure does `x += 1`, changing `x` from 10 to 11
> 4. The function returns the current value of `x`, which is now 11
>
> This works because `x` is a **named return value** -- it lives in the stack frame and defer can modify it after `return` sets it but before the function exits.

### Tier 2: Fix the bug (5 min)

You have a `defer` **inside a `for` loop** over files. The process **runs out of file** descriptors. Rewrite so each file is **closed** before the next file opens, without changing the **outer** `function`’s return behavior more than you must.

> **Hint:** a **function literal** per iteration, or a **named** helper, both build a small **room** the function returns from **each** time, so the **defers** run **per** room, not **once** at the end of the world.

> [!success]- Answer
> Wrap the body of the loop in an immediately-invoked function literal so defer runs per iteration:
> ```go
> for _, path := range files {
>     func() {
>         f, err := os.Open(path)
>         if err != nil { return }
>         defer f.Close()  // runs when THIS anonymous func returns, not the outer func
>         // process f...
>     }()
> }
> ```
> Or extract a named helper: `func processFile(path string) { f, _ := os.Open(path); defer f.Close(); ... }` and call it in the loop. Either way, each iteration gets its own function scope, so `defer f.Close()` fires before the next file opens.

### Tier 3: Build it (15 min)

Build a small **`StartWorker(fn func())` helper** that **starts `fn` in a new goroutine** and **converts a panic in that child** into a **return** on a **result channel** or **err** to the **caller** — the **parent** must **not** **crash** or **leak** the panic. **You may not** **recover** in the **parent** from the child’s work **directly** — design the child so **it** **recovers** and **sends** a value.

> Full solutions with explanations → [[exercises/T10 Defer, Panic & Recover Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

| Gotcha | Why it burns | Fix |
|--------|-------------|-----|
| **`defer` in a `for` loop** | N defers, **LIFO** at **end**; **N** open resources | per-**iteration** `func(){ ...; defer ... }` or a named inner function |
| **`recover` not in `defer`** | **no valid frame**; returns **`nil`** | **`defer func(){ v:=recover()...}()` |
| **goroutine panic isolation** | **other** G’s **panic** is invisible to **this** G’s `recover` | **recover inside** the **child**; **signal** to parent on **error** |
| **`os.Exit` bypasses defers** | `os.Exit` **stops the process** now | **return** and **teardown** first, or a single **place** for shutdown |
| **`defer` in `init`** | `init` **runs** at package startup; defers to **end of `init`**, not **`main`**, not **program** the way you imagine | do **not** build **one-time** "program cleanup" in **`init` defers**; use **`main`**, `sync.Once`, or `runtime` hooks very carefully and rarely |

> **In plain English:** A **buzzer** to leave the **building** is not a **buzzer** to leave **a single room** inside it. A **red phone** that **kills the city power** is not a **room light switch**. **Init**-time is like **wiring the lobby** at **6am**—your **"before I lock today"** notes still only fire at **6am** **shift change**, not when you **turn off the whole city** at 9pm with **`os.Exit`**.

**Mini step-through: `os.Exit` vs `return`**

```go
import "os"

func main() {
	defer println("deferred in main")
	os.Exit(0) // **no** "deferred in main" from this
}
```

```
os.Exit(0) — **immediate** process stop
  └── **defer in main** does not run
```

> **In plain English:** A **main breaker** does not wait for you to **close** each **window**; the building goes dark.

---

## 8. Performance & Tradeoffs

| Path | What you pay | When it wins | When to worry |
|------|-------------|-------------|--------------|
| **Open-coded** defers, **go1.14+** | **~zero** extra **alloc** on **no-panic** path | **hot** `defer` in **tight** loops of **I/O** **wrappers** | **any** `defer` in **tight** **numeric** inner loops: **measure**; **sometimes** **manual** `cleanup` is clearer and faster than cleverness |
| **Heap-backed** defers (historical / some shapes) | **alloc** of **record**; **LIFO** **walk** on exit | default **safety** | **pprof** if **defer**-heavy **on** a **p99** path |
| **Panic** path | full **unwind**; **stacks**; **worse** than **return error** in **steady** work | **truly** **exceptional** (programmer bug) | **do not** `panic` for **normal** error returns |

**Guidance for interviews:** "Normal errors are **values**. **Panic** is for **bugs** or **APIs** you cannot change **as fast** in **tight** time. `defer` is for **readability** and **pairing** `Close` and **unlock**; on **hottest** code, **data beats faith** with **pprof** and **one** tiny benchmark if someone asks for **micro** proof.

---

## 9. Common Misconceptions

| Misconception | Reality |
|---------------|---------|
| "`defer` runs when I `return` from a **child** `func`" | **`defer` binds to** the **function** you wrote it in, not **who** you **call** while inside, unless a **new** `func` **scope** **owns** a **separate** **defer** |
| "I can **recover** a child **goroutine** from **parent**" | **Parent** and **child** are **separate** **goroutine** **panic** universes. **Child** must **recover** or the **child** **dies** |
| "`recover` in **any** function **saves** the **day**" | must be a **deferred** **execution** the **spec** and **runtime** both accept, usually **`func(){ recover() }`**, not a **naked** `recover()` **in** **the** main line |
| "arguments **rebind** to **latest** values at `defer` time" | **no**; **arguments** were **stamped** at the **`defer` line**; **closures** are a **separate** story about which **box** the **name** `i` is |
| "panic is a **faster** error" | **slower** than **return**; **worse** for **control** **flow** in **API** **design** |

---

## 10. Related Tooling & Debugging

| Tool / idea | How it helps with **defer** / **panic** |
|------------|----------------------------------------|
| `go test -race` | finds **races** where **defers** and **concurrent** writes mix badly |
| `GOTRACEBACK=single|all` | controls **stack** print detail on **panic** |
| `runtime/debug` **Stack** / **PrintStack** | get **stacks** in **middleware** and **logs** |
| `pprof` **alloc** / **alloc_space** (long note elsewhere) | see if **defers** are still **alloc**-**heavy** in a **version** and **codepath** you care about |

---

## 11. Interview Gold Questions

**Q1: What is the **evaluation** order of **deferred** calls, and when are the **arguments** fixed?**  
**Answer idea:** **LIFO** for **order**; **arguments** are **fixed** at the **`defer` line**. If they want a **nibble**: **open-coded** defers, **1.14+**, **reduced** **alloc** on **no** **panic** **path** — for **trivia** with **caution**. **Tradeoff:** still **readability** and **safety** first.

**Q2: How does a **named** **return** interact with a **`defer` that** **mutates** the **name**?**  
**Answer idea:** the **one** **result** **variable** is **live**; **`return` expression** may **set** it; then **defers** run, then the **value** is **truly** **returned**. This is a **concrete** **memory** of **"double return"** (not a **recommendation** in **all** code).

**Q3: **Why** is **`recover`** **useful** in **HTTP** **middleware**, and **can** a **server** `recover` a **client**'s **bug**?**  
**Answer idea:** **one** `defer` **at** a **server** **boundary** can **turn** a **handler** **panic** into **500** + **log**, **saving the process** for **one** request’s **catastrophe** — **if** the **panic** is in **this** **request’s** **stack**, **not in** some **arbitrary** **goroutine** the **handler** **spawned** **without** its **own** **guard** **rails**.

> **Verbal 15-second nugget for Q3:** A **reception** **net** in **one** **room**; **neighbors** still need their **own** **nets** if you **outsource** the **chore** to a **separate** **worker** **thread**.

---

## 12. Final Verbal Answer

> **`defer`** schedules a **callee** to run when **this** **function** **leaves** — on **return** or **panic** on **this** **goroutine**. The **args** are **stamped** at the **`defer` line**. The **LIFO** order means the **most** **recent** **`defer` runs first**. A **panic** **unwinds** **this** **goroutine**; **`recover`** only **works** in a **deferred** **function** for **this** same **goroutine** and **turns a panic into a value** if the **place** is **legal** — you **do not** **magically** **catch** **another** **goroutine**'s **panic** from the **parent**. In **servers**, **middleware** uses **`recover`** to **shield** a **request**'s **bug**; **child** **workers** or **spawns** need **their** **own** **discipline** or a **separate** **signal** **path** back. **On** **performance**: **1.14+** **open**-**coded** **defers** make the **common** **no**-**panic** path **lean**, but you still **treat** **panic** as **rare** and **errors** as **values** in **public** **APIs**.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (see companion file) → [[questions/T10 Defer, Panic & Recover Internals - Interview Questions]]

**Preview questions (answer in the bank):**
- When are **`defer` arguments** evaluated, and how is that different from a **closure** that captures a **loop** variable on **older** **Go** code?
- **Walk** a **LIFO** **order** of **three** defers, then add a **return** in the **middle** of the **function** — which **deferred** **calls** run?
- **Design** a **HTTP** **server** that **logs** a **request** **id** and **converts** **handler** **panics** to **500** while **leaving** a **separate** **goroutine** **pool** **safe** from **unhandled** **child** **panics**.

---

> See [[Glossary]] for term definitions.
