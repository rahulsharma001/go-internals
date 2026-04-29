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

A **`defer` statement** schedules a function to run when the **surrounding function** returns, on every `return` path, or when a **panic** starts unwinding that goroutine. The scheduled work is **not** the next line. It is "later, on the way out."

A **`panic`** stops normal control flow. It **unwinds** the stack, runs **deferred** functions in that **goroutine**, and if nothing **recovers**, the runtime prints a stack trace. An unrecovered panic in **any** goroutine tears down the **whole program** — not just that goroutine.

A **`recover`** is a **built-in** that **returns the panic value** and **stops the panic** if it is called **while a deferred function from that same goroutine is still running** on the way out. Otherwise it returns **`nil`**.

Think of `defer` as a sticky note you put on the door on your way in — you promise to do one more chore when you leave. `panic` is a fire alarm: everyone stops and runs for the exit. `recover` is a fire extinguisher you mounted on that same door — it only works if you already put the mount there with `defer`.

---

## 2. Core Insight (TL;DR)

**Three rules lock most interview answers.** **First,** arguments to a deferred function are **fully evaluated and copied at the `defer` line**, not when the deferred work runs. **Second,** deferred work runs in **LIFO** order. The **last** `defer` you wrote in that function is the **first** to run on exit. **Third,** if the function has **named result parameters**, deferred functions can **read and write** those names on the way out, which is how the famous "double return" works.

**`recover` is goroutine-scoped and defer-scoped.** It does **not** cross goroutines. A parent function cannot "catch" a **panic in a child goroutine** the way you might catch an error from a function call. The child must run its own `defer` + `recover`, or signal the parent on a channel.

You schedule chores with `defer` when you can still read the labels on the boxes — arguments are snapshotted right then, even if the room changes before you do the chore. The cleanup line is LIFO because you pile sticky notes, then peel from the top. A panic in another worker is not your sticky pile — you never see that alarm unless you wired a separate signal path.

---

## 3. Mental Model (Lock this in)

### The Sticky-Note Stack

Each **`defer` in a function** adds one piece of work to a **per-function stack of deferred calls** for that activation. The stack is **LIFO**. The **newest** note is on top. On **any** return or panic, Go **peels from the top** first.

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

Sticky notes stack on a desk. You add new notes on top. When you stand up to leave, you read from the top down. A panic in another room is not on your desk.

### Mistake That Teaches: `defer` in a Loop (DB Connections)

In real services you see the same bug with **`sql.DB`**, Redis clients, or gRPC conns — not just files. Here, each order was supposed to use its **own** connection, but every iteration schedules **another** `Close` for **one** moment: when the **outer** function returns.

```go
// BUG: N connections stay open until the *outer* function returns
func ProcessBatch(ctx context.Context, db *sql.DB, orders []Order) error {
	for _, ord := range orders {
		conn, err := db.Conn(ctx)
		if err != nil {
			return err
		}
		defer conn.Close() // <- one defer per iteration; all fire at outer return
		if err := applyOrder(ctx, conn, ord); err != nil {
			return err
		}
	}
	return nil
}
```

```
Iteration 0:  defer: Close conn₀   [stack: Close₀]
Iteration 1:  defer: Close conn₁   [stack: Close₁, Close₀]
...
Iteration n:  conns 0..n-1 are ALL still open
              until the whole function returns

       └── every iteration pushed another "Close later" note
           but "later" is ONE moment: outer function end
       └── pool exhaustion / too many open conns  <-- OOPS
```

**Fix pattern:** one `defer` per **scope that ends before the next** iteration — usually an IIFE or a small helper.

```go
for _, ord := range orders {
	err := func() error {
		conn, err := db.Conn(ctx)
		if err != nil {
			return err
		}
		defer conn.Close()
		return applyOrder(ctx, conn, ord)
	}()
	if err != nil {
		return err
	}
}
```

A `defer` in a loop is like writing "I will close every connection at midnight" fifty times. You still have fifty live connections until midnight. Put each order in a small room, close on the way out of that room, then start the next.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

### 4.1 The Defer Chain — A Linked List Per Goroutine

The runtime keeps a **linked list of `_defer` records** attached to the current goroutine (`g`). Each `defer` statement creates a new record and pushes it onto the front of the list. When the function exits (return or panic), the runtime walks the list from front to back — that's why execution is LIFO.

```go
package main

import "fmt"

func main() {
	fmt.Println("start")
	defer fmt.Println("A")
	defer fmt.Println("B")
	defer fmt.Println("C")
	fmt.Println("end")
}
// Output: start, end, C, B, A
```

```
Step 1: fmt.Println("start") → prints "start"

Step 2: defer fmt.Println("A")
  Runtime creates _defer record:
    { fn: fmt.Println, args: ["A"], link: nil }
  Goroutine's defer chain: → [A]

Step 3: defer fmt.Println("B")
  New record pushed to FRONT:
    { fn: fmt.Println, args: ["B"], link: → [A] }
  Chain: → [B] → [A]

Step 4: defer fmt.Println("C")
  New record pushed to FRONT:
    { fn: fmt.Println, args: ["C"], link: → [B] → [A] }
  Chain: → [C] → [B] → [A]

Step 5: fmt.Println("end") → prints "end"

Step 6: main() returns → runtime walks the chain front-to-back:
  [C].fn("C") → prints "C"
  [B].fn("B") → prints "B"
  [A].fn("A") → prints "A"

THE CHAIN IN MEMORY (goroutine g):

  g._defer ──→ ┌────────────────┐    ┌────────────────┐    ┌────────────────┐
                │ fn: Println    │    │ fn: Println    │    │ fn: Println    │
                │ args: ["C"]   │──→ │ args: ["B"]   │──→ │ args: ["A"]   │──→ nil
                │ (newest)      │    │                │    │ (oldest)      │
                └────────────────┘    └────────────────┘    └────────────────┘
                     ran 1st              ran 2nd              ran 3rd
```

> **In plain English:** The runtime keeps a clothesline of hooks on each worker (goroutine). You clip the newest tag next to your hand. When you back out, you unclip from the hand side first — that's LIFO.

### 4.2 Argument Evaluation — Snapshot at the `defer` Line

When Go hits a `defer` statement, it evaluates ALL arguments **right then** and stores copies in the `_defer` record. The deferred function sees the snapshotted values, not whatever the variables hold at exit time.

```go
package main

import "fmt"

func main() {
	x := 10
	defer fmt.Println("deferred x =", x) // x is evaluated NOW → 10 stored
	x = 20
	defer fmt.Println("deferred x =", x) // x is evaluated NOW → 20 stored
	x = 30
	fmt.Println("live x =", x) // 30
}
// Output:
// live x = 30
// deferred x = 20    ← LIFO: second defer runs first, with snapshot of 20
// deferred x = 10    ← first defer runs second, with snapshot of 10
```

```
Step 1: x := 10

Step 2: defer fmt.Println("deferred x =", x)
  Runtime evaluates args: "deferred x =", 10   ← snapshot of x RIGHT NOW
  _defer record A: { fn: Println, args: ["deferred x =", 10], link: nil }
  Chain: → [A: x=10]

Step 3: x = 20

Step 4: defer fmt.Println("deferred x =", x)
  Runtime evaluates args: "deferred x =", 20   ← snapshot of x RIGHT NOW
  _defer record B: { fn: Println, args: ["deferred x =", 20], link: → A }
  Chain: → [B: x=20] → [A: x=10]

Step 5: x = 30

Step 6: fmt.Println("live x =", x) → prints "live x = 30"

Step 7: return → walk chain:
  B runs: Println("deferred x =", 20)   ← stored snapshot, not current x=30!
  A runs: Println("deferred x =", 10)   ← stored snapshot from earlier

CONTRAST WITH CLOSURE (no argument snapshot):

  defer func() { fmt.Println("closure x =", x) }()
  ← closure captures the VARIABLE x, not its value
  ← at exit time, x = 30, so prints "closure x = 30"
```

> **In plain English:** A `defer` with arguments is like placing a phone order — the kitchen writes down "no onions" from the current menu. If you change the menu board later, the ticket doesn't update. A closure is like a waiter who checks the menu board at serving time — they always read the latest version.

### 4.3 Named Returns — Why Defer Can Modify the Return Value

When a function has named return parameters, `return expr` is a two-step process:
1. Assign `expr` to the named variable
2. Run deferred functions (which can read/write the named variable)
3. Return the current value of the named variable

```go
package main

import "fmt"

func double() (result int) {
	defer func() {
		result = result * 2 // modifies the named return variable
	}()
	return 21 // Step 1: result = 21, Step 2: defer runs: result = 42
}

func main() {
	fmt.Println(double()) // 42
}
```

```
Step 1: double() starts executing
  stack frame:
    result: 0   ← named return, zero-initialized, lives in the stack frame

Step 2: defer func() { result = result * 2 }()
  Registers a closure. The closure captures `result` — the VARIABLE, not a copy.
  _defer chain: → [closure that reads/writes &result]

Step 3: return 21
  Go splits this into:
    3a: result = 21          ← assign to named variable
    stack frame: result: 21

    3b: run deferred functions
    closure runs: result = result * 2 = 21 * 2 = 42
    stack frame: result: 42

    3c: actually return → caller receives result = 42

WHY this works:
  Named return `result` is a real variable in the stack frame.
  The closure has a reference to that variable (not a copy).
  Between step 3a and 3c, the defer can modify it.

WITHOUT named return (anonymous return):
  func double() int {
      x := 21
      defer func() { x = x * 2 }()
      return x  // copies x into an anonymous return slot
                // defer changes x, but the anonymous slot is already set
  }
  → returns 21, not 42. The defer modified x, but x is NOT the return slot.
```

> **In plain English:** A named return is a labeled mailbox on your desk. `return 21` drops a letter (21) into the mailbox. On the way out, the defer opens the mailbox, reads the letter, doubles it, and puts 42 back. The mailman picks up whatever is in the mailbox at that point. Without a named return, the letter goes into a sealed anonymous dropbox that defer can't reach.

### 4.4 Panic and Unwind — What Happens Step by Step

When `panic(v)` is called, the runtime:
1. Stops normal execution
2. Walks the current goroutine's defer chain, running each deferred function
3. If a deferred function calls `recover()`, the panic stops and execution resumes after the `recover` call
4. If no `recover` is called, after all defers run, the runtime prints the panic value and stack trace, then kills the entire program

```go
package main

import "fmt"

func riskyWork() {
	fmt.Println("step 1")
	panic("something broke")
	fmt.Println("step 2") // never runs
}

func main() {
	defer fmt.Println("main: defer A")
	defer fmt.Println("main: defer B")

	defer func() {
		if v := recover(); v != nil {
			fmt.Println("recovered:", v)
		}
	}()

	riskyWork()
	fmt.Println("after riskyWork") // never runs — panic unwound past here
}
// Output:
// step 1
// recovered: something broke
// main: defer B
// main: defer A
```

```
Step 1: main starts, registers 3 defers on goroutine G1's chain
  G1._defer chain at 0xC000050000:
    → [_defer at 0x50020: fn=recover-closure, args=none]
    → [_defer at 0x50010: fn=Println, args=["main: defer B"]]
    → [_defer at 0x50000: fn=Println, args=["main: defer A"]]

Step 2: riskyWork() called — new stack frame at SP 0xC000070000
  Prints "step 1"
  panic("something broke") → runtime sets G1.panic = {value: "something broke"}

Step 3: Runtime unwinds riskyWork's stack frame (SP 0xC000070000)
  riskyWork has no defers (no _defer records for this frame)
  Pop frame → back to main's frame at SP 0xC000060000

Step 4: Runtime walks main's defer chain (LIFO from 0x50020):
  _defer at 0x50020: recover-closure runs
    recover() reads G1.panic.value → returns "something broke"
    v != nil → prints "recovered: something broke"
    recover() clears G1.panic → panic stopped

  _defer at 0x50010: Println("main: defer B") → prints
  _defer at 0x50000: Println("main: defer A") → prints

Step 5: main returns normally (G1.panic was cleared by recover)

WITHOUT the recover:
  Step 4: Chain runs, no recover() clears G1.panic
  Step 5: All defers done, G1.panic still set
  Step 6: Runtime prints stack trace + "something broke"
  Step 7: os.Exit(2) — entire program dies
```

> **In plain English:** Panic is the fire alarm. Everyone stops what they're doing and heads for the exit. On the way out, you execute every sticky note (defer) you posted on the door. If one of those notes says "check if the fire extinguisher works" (recover), and it does, the alarm stops and the building stays open. If nobody has an extinguisher, the building is evacuated (program dies).

### 4.5 Goroutine Isolation — Why Parent Can't Catch Child's Panic

Each goroutine has its own defer chain. When a child goroutine panics, the runtime walks THAT goroutine's chain. The parent's defer chain is on a completely separate goroutine — it never sees the child's panic.

```go
package main

import (
	"fmt"
	"time"
)

func main() {
	defer func() {
		if v := recover(); v != nil {
			fmt.Println("parent recovered:", v) // NEVER prints
		}
	}()

	go func() {
		panic("child panic") // crashes the WHOLE program
	}()

	time.Sleep(100 * time.Millisecond)
	fmt.Println("parent continues") // never reaches here
}
// Output: panic: child panic (then stack trace, then program exits)
```

```
Two separate goroutine structs in memory:

  G1 (main) at 0xC000001000:
    _defer chain: → [_defer at 0xA0: fn=recover-closure]
    panic: nil

  G2 (child) at 0xC000001080:
    _defer chain: → nil (empty — no defers registered)
    panic: nil

Step 1: G2 panics with "child panic"
  G2.panic = {value: "child panic"}
  Runtime walks G2._defer chain → nil → nothing to run
  No recover() cleared G2.panic → panic is unrecovered
  Runtime calls fatalpanic() → kills ENTIRE program (not just G2)

Step 2: G1's recover-closure NEVER executes for G2's panic
  G1._defer chain at 0xA0 belongs to G1 only
  The runtime looked at G2._defer (nil), not G1._defer

  G1 at 0x1000: _defer → [recover-closure]   ← only runs when G1 panics/returns
  G2 at 0x1080: _defer → nil                  ← G2's panic walks THIS, not G1's

FIX: child must recover itself:
  go func() {
      defer func() {
          if v := recover(); v != nil {
              fmt.Println("child recovered:", v)
              // send error on channel to parent
          }
      }()
      panic("child panic") // now caught by child's own recover
  }()
```

> **In plain English:** A smoke alarm in your apartment does not silence a fire in the neighbor's unit. Each goroutine has its own apartment with its own alarm system. If the neighbor's fire isn't handled by their own extinguisher, the whole building (program) is evacuated.

### 4.6 Backend Scenario: Transaction Rollback With Defer

The most common production use of defer — guaranteeing a database transaction is always cleaned up:

```go
package main

import (
	"errors"
	"fmt"
)

func transferFunds(shouldFail bool) (err error) {
	fmt.Println("  begin tx")
	defer func() {
		if err != nil {
			fmt.Println("  defer: err != nil → ROLLBACK")
		} else {
			fmt.Println("  defer: err is nil → skip rollback")
		}
	}()

	fmt.Println("  debit account A")
	if shouldFail {
		return fmt.Errorf("debit: %w", errors.New("connection reset"))
	}

	fmt.Println("  credit account B")
	fmt.Println("  commit")
	return nil
}

func main() {
	fmt.Println("=== SUCCESS path ===")
	err := transferFunds(false)
	fmt.Println("result:", err)

	fmt.Println("\n=== ERROR path ===")
	err = transferFunds(true)
	fmt.Println("result:", err)
}
// Output:
// === SUCCESS path ===
//   begin tx
//   debit account A
//   credit account B
//   commit
//   defer: err is nil → skip rollback
// result: <nil>
//
// === ERROR path ===
//   begin tx
//   debit account A
//   defer: err != nil → ROLLBACK
// result: debit: connection reset
```

```
SUCCESS path (no errors):

  Step 1: BeginTx → tx created
  Step 2: defer registers: func() { if err != nil { tx.Rollback() } }
    Chain: → [rollback-if-err closure]
    Closure captures `err` — the NAMED return variable
  Step 3: Debit exec → success
  Step 4: Credit exec → success
  Step 5: Commit → success, err = nil
  Step 6: return nil
    Deferred closure runs: err == nil → skip rollback ✓
    Transaction committed, money transferred.

ERROR path (debit fails):

  Step 1: BeginTx → tx created
  Step 2: defer registers closure (captures &err)
  Step 3: Debit exec → fails! err = "debit: connection reset"
  Step 4: return fmt.Errorf("debit: %w", err)
    3a: named return `err` = "debit: connection reset"
    3b: deferred closure runs: err != nil → tx.Rollback()
        Both debit and any partial writes are undone ✓
    3c: return the error to caller

  Without defer, you'd need tx.Rollback() before EVERY return statement.
  With 5 possible error points, that's 5 Rollback calls to maintain.
  Defer handles ALL of them with ONE line.

PANIC path (something truly broke):

  Step 3: Debit exec → triggers a panic deep in the driver
  Runtime enters panic mode → walks defer chain
  Closure runs: err is whatever was set → tx.Rollback()
  Transaction cleaned up even during a panic ✓
```

`defer tx.Rollback()` is insurance — it pays out on every bad exit (error, panic, early return). On the happy path where you committed, the rollback is a no-op. You write the insurance policy once and forget about it, instead of remembering to cancel at every possible failure point.

---

## 5. Key Rules & Behaviors

### Rule 1: Defer Arguments Are Evaluated at the `defer` Line, Not at Exit Time

**WHY (Section 4.2):** From Section 4.2, the runtime creates a `_defer` record with snapshotted argument values. The record stores copies of the evaluated expressions, not references to variables.

```go
func main() {
	i := 0
	defer fmt.Println("defer prints:", i) // evaluates i NOW → stores 0
	i++
	fmt.Println("after:", i) // 1
}
// prints: after: 1, then "defer prints: 0"
```

```
defer fmt.Println("defer prints:", i):
  _defer record: { fn: Println, args: ["defer prints:", 0] }
                                                        ↑ snapshot

i++ → i is 1 in the frame, but the _defer record still says 0

On return:
  Println("defer prints:", 0)  ← reads from the record, not from i
```

A phone order is taken the moment you say `defer` — the kitchen writes down "no onions" from today's list. Changing the whiteboard after doesn't update the ticket.

### Rule 2: LIFO — Last `defer` Registered Runs First

**WHY (Section 4.1):** From Section 4.1, each `defer` pushes to the FRONT of the linked list. Walking the list from front to back means the newest runs first.

```go
func main() {
	defer fmt.Print("1 ")
	defer fmt.Print("2 ")
	defer fmt.Print("3 ")
}
// prints: 3 2 1
```

```
After all defers registered:
  Chain: → [3] → [2] → [1]
              ↑ newest          ↑ oldest

Walk front-to-back:
  [3] → print "3 "
  [2] → print "2 "
  [1] → print "1 "
```

The last Post-It you stack on the pile is the first one you peel when you clean the desk.

### Rule 3: Named Return Values Can Be Written by Deferred Functions

**WHY (Section 4.3):** From Section 4.3, `return expr` assigns to the named variable first, then defers run. The closure captures the named variable by reference, so it can read and write the current value.

```go
func addErrorContext() (err error) {
	defer func() {
		if err != nil {
			err = fmt.Errorf("addErrorContext: %w", err)
		}
	}()
	return doWork() // if doWork fails, defer wraps the error
}
```

```
Stack frame of addErrorContext():
  ┌──────────────────────────────────────────┐
  │  named return:  err  at 0xC000060010     │  ← shared slot
  │  _defer chain: → [closure capturing &err] │
  └──────────────────────────────────────────┘

If doWork() returns an error:
  Step 1: return doWork() → Go assigns: err = "connection refused"
    stack 0x60010: [ err = "connection refused" ]

  Step 2: walk _defer chain → closure runs
    closure reads &err → err != nil → wraps:
    err = fmt.Errorf("addErrorContext: %w", err)
    stack 0x60010: [ err = "addErrorContext: connection refused" ]

  Step 3: function returns → caller reads 0x60010 → gets wrapped error

If doWork() succeeds:
  Step 1: return doWork() → err = nil
  Step 2: closure: err == nil → skip wrapping
  Step 3: caller gets nil
```

A named return is a labeled mailbox. The defer can open it and relabel the contents before the mailman picks it up.

### Rule 4: `recover` Must Be Called Inside a Deferred Function

**WHY (Section 4.4):** From Section 4.4, `recover()` only works during panic unwinding when called from a deferred function. Called anywhere else, it returns `nil`. The runtime checks: "am I currently executing a deferred function during a panic unwind?" If not, recover is a no-op.

```go
// BROKEN: recover not in defer
func bad() {
	recover() // returns nil — useless outside defer during panic
}

// BROKEN: recover in a nested function called from defer
func alsoBad() {
	defer func() {
		innerRecover() // recover inside innerRecover doesn't count
	}()
}
func innerRecover() { recover() } // wrong depth — must be directly in the defer

// CORRECT: recover directly in the deferred function
func good() (caught string) {
	defer func() {
		if v := recover(); v != nil {
			caught = fmt.Sprint(v)
		}
	}()
	panic("oops")
}
```

```
WHY the nesting matters:

  The runtime checks the call depth when recover() is called:
    defer func() {
        recover()  ← called at depth 1 from the deferred function → WORKS
    }()

    defer func() {
        helper()   ← helper is at depth 2
    }()
    func helper() { recover() }  ← depth 2 → runtime says "not directly in defer" → nil

  The rule: recover() must be called DIRECTLY inside the deferred function body,
  not inside a function called by the deferred function.
```

The fire extinguisher must be mounted ON the door (directly in the defer). If you hide it in a closet behind the door (nested function), the fire inspector (runtime) won't count it.

### Rule 5: Panics Are Goroutine-Isolated — Parent Cannot Catch Child

**WHY (Section 4.5):** From Section 4.5, each goroutine has its own defer chain. The runtime walks only the panicking goroutine's chain. The parent goroutine's chain is on a separate linked list that is never consulted during the child's panic.

```go
func main() {
	defer func() {
		recover() // only catches panics in main's goroutine
	}()
	go func() {
		panic("child") // main's recover NEVER sees this
	}()
	time.Sleep(time.Second)
}
// program crashes — child's panic is unrecovered
```

```
G1 (main):   defer chain → [recover-closure]
G2 (child):  defer chain → (empty)

G2 panics → runtime walks G2's chain → empty → no recover → PROGRAM DIES

G1's recover-closure was never consulted because it's on G1's chain, not G2's.
```

The fix is always: the child goroutine must carry its own `defer + recover`, then signal the parent through a channel or `errgroup`.

A smoke alarm in your apartment does not silence a fire in the neighbor's unit. Each goroutine is a separate apartment.

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: Defer Execution Order — Traced Through the Chain

The foundation: see how the linked list determines execution order.

```go
package main

import "fmt"

func cleanup() {
	fmt.Println("step 1")
	defer fmt.Println("defer A")

	fmt.Println("step 2")
	defer fmt.Println("defer B")

	fmt.Println("step 3")
	defer fmt.Println("defer C")

	fmt.Println("step 4 (last)")
}

func main() {
	cleanup()
}
// Output: step 1, step 2, step 3, step 4 (last), defer C, defer B, defer A
```

```
Execution trace:

  Println("step 1") → output
  defer Println("A") → chain: → [A]

  Println("step 2") → output
  defer Println("B") → chain: → [B] → [A]

  Println("step 3") → output
  defer Println("C") → chain: → [C] → [B] → [A]

  Println("step 4") → output

  Function returns → walk chain:
    [C] → prints "defer C"
    [B] → prints "defer B"
    [A] → prints "defer A"
```

### Example 2: Argument Snapshot vs Closure Capture

The difference that trips up everyone in interviews.

```go
package main

import "fmt"

func main() {
	x := 0

	defer fmt.Println("arg snapshot:", x)          // copies x=0 into _defer record
	defer func() { fmt.Println("closure sees:", x) }() // captures &x, reads at exit

	x = 100
	fmt.Println("live x:", x) // 100
}
// Output:
// live x: 100
// closure sees: 100    ← closure reads current x
// arg snapshot: 0      ← _defer record stored x=0
```

```
Step 1: x := 0

Step 2: defer fmt.Println("arg snapshot:", x)
  _defer record A: { args: ["arg snapshot:", 0] }   ← 0 stored NOW
  Chain: → [A: snapshot 0]

Step 3: defer func() { ... }()
  _defer record B: { fn: closure referencing &x }   ← no snapshot, reads x later
  Chain: → [B: closure(&x)] → [A: snapshot 0]

Step 4: x = 100

Step 5: return → walk chain:
  B runs: closure reads x → x is 100 → prints "closure sees: 100"
  A runs: Println("arg snapshot:", 0) → prints "arg snapshot: 0"
```

### Example 3: `defer rows.Close()` — The Pattern You Type Daily

The most common production defer: ensuring database rows are closed on every exit path.

```go
func ListUsers(ctx context.Context, db *sql.DB) ([]User, error) {
	rows, err := db.QueryContext(ctx, "SELECT id, name FROM users")
	if err != nil {
		return nil, fmt.Errorf("query: %w", err)
	}
	defer rows.Close() // runs on EVERY return path below

	var users []User
	for rows.Next() {
		var u User
		if err := rows.Scan(&u.ID, &u.Name); err != nil {
			return nil, fmt.Errorf("scan: %w", err) // rows.Close() still runs!
		}
		users = append(users, u)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("rows: %w", err) // rows.Close() still runs!
	}
	return users, nil // rows.Close() runs on success too
}
```

```
Step-through (scan error path):

  Step 1: db.QueryContext succeeds
    rows = *sql.Rows at 0xC000080000 (holds network connection, buffers)
    stack: [ rows: 0xC000080000 ]

  Step 2: defer rows.Close() registers
    G._defer chain: → [_defer: fn=(*Rows).Close, receiver=0xC000080000]
    Argument is evaluated NOW: 0xC000080000 is captured

  Step 3: rows.Scan fails → return nil, err
    Function is about to return
    Runtime walks G._defer chain:
      _defer.fn = Close(0xC000080000)
      rows.Close() releases the connection back to pool ✓

  Step 4: Caller gets (nil, "scan: ..."), connection safely returned

Without defer:
  You'd need rows.Close() before EVERY return:
    return nil, fmt.Errorf("scan: %w", err)   ← need Close() before this
    return nil, fmt.Errorf("rows: %w", err)   ← need Close() before this
    return users, nil                           ← need Close() before this
  That's 3 places to remember. Miss one → connection leak under load.

With defer:
  ONE defer after the successful Query. Covers ALL 3 returns + any future returns.
  If someone adds a new error check later, it's already covered.
```

### Example 4: HTTP Middleware Recover — Keeping the Server Alive

The standard pattern for turning handler panics into 500 responses instead of crashing the server.

```go
func withRecover(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if v := recover(); v != nil {
				slog.Error("handler panic",
					"panic", v,
					"path", r.URL.Path,
					"stack", string(debug.Stack()),
				)
				http.Error(w, "internal error", 500)
			}
		}()
		next.ServeHTTP(w, r)
	})
}
```

```
Normal request (no panic):
  Step 1: defer registers recover-closure
  Step 2: next.ServeHTTP handles request normally
  Step 3: handler returns → defer runs → recover() returns nil → skip
  Result: normal response

Panicking request:
  Step 1: defer registers recover-closure
  Step 2: next.ServeHTTP → handler panics deep in the call stack
  Step 3: Runtime unwinds back to this function's defer chain
  Step 4: recover-closure runs:
    recover() returns the panic value (e.g., "nil pointer dereference")
    v != nil → log the error with stack trace
    Write 500 response to client
    Panic is stopped — server continues serving other requests

  Chain: → [recover-closure]
  Panic unwinds FROM handler's stack frame BACK TO this frame
  recover() intercepts → server stays alive

LIMITATION: if the handler spawns a goroutine and THAT panics,
this recover does NOT catch it (Section 4.5 — goroutine isolation).
The spawned goroutine must have its own defer+recover.
```

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

> [!success]- Answer
> Prints `11`. Here's why:
> 1. `return 10` sets the named return value `x = 10`
> 2. Before the function actually returns, the deferred closure runs
> 3. The closure does `x += 1`, changing `x` from 10 to 11
> 4. The function returns the current value of `x`, which is now 11
>
> This works because `x` is a **named return value** — it lives in the stack frame and defer can modify it after `return` sets it but before the function exits (Section 4.3).

### Tier 2: Fix the bug (5 min)

You have a `defer` **inside a `for` loop** over database connections (like `ProcessBatch` above). The service **runs out of pool connections**. Rewrite so each connection is **closed** before the next iteration opens another, without changing the outer function's contract more than necessary.

> **Hint:** a **function literal** per iteration, or a **named** helper, gives a small **room** you return from each time so **defers** run **per** room.

> [!success]- Answer
> Wrap the body of the loop in an immediately-invoked function literal so defer runs per iteration:
> ```go
> for _, ord := range orders {
>     err := func() error {
>         conn, err := db.Conn(ctx)
>         if err != nil { return err }
>         defer conn.Close()
>         return applyOrder(ctx, conn, ord)
>     }()
>     if err != nil { return err }
> }
> ```
> Or extract `func processOneOrder(ctx context.Context, db *sql.DB, ord Order) error` and call it from the loop. The key: defer binds to the enclosing FUNCTION, not the loop iteration (Section 4.1).

### Tier 3: Build it (15 min)

Build a small **`StartWorker(fn func())` helper** that **starts `fn` in a new goroutine** and **converts a panic in that child** into a **return** on a **result channel** or **err** to the **caller** — the **parent** must **not** **crash** or **leak** the panic. **You may not** **recover** in the **parent** from the child's work **directly** — design the child so **it** **recovers** and **sends** a value.

> Full solutions with explanations → [[exercises/T10 Defer, Panic & Recover Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

| Gotcha | What Happens | Because (Section 4 link) | Fix |
|--------|-------------|-------------------|-----|
| `defer` in a `for` loop | All N defers fire at outer function return, not per iteration. N connections/files stay open simultaneously | Section 4.1 — defer pushes to the function's chain, not the loop's. The chain only runs when the function exits | Wrap loop body in IIFE or extract to helper function so each iteration is a separate function scope |
| `recover()` outside `defer` | Returns `nil` — no panic is caught | Section 4.4 — runtime only honors recover() when called directly inside a deferred function during panic unwind | Always use `defer func() { if v := recover(); ... }()` pattern |
| `recover()` in nested function inside defer | Returns `nil` — wrong call depth | Section 4.4 — recover must be at depth 1 from the deferred function, not depth 2+ | Call recover() directly in the `defer func()` body, not in a helper |
| Parent tries to catch child goroutine's panic | Unrecovered panic crashes the entire program | Section 4.5 — each goroutine has its own defer chain. Parent's chain is never consulted for child's panic | Child must carry its own defer+recover and send errors on a channel |
| `os.Exit(n)` bypasses all defers | Deferred functions never run — process terminates immediately | Section 4.1 — os.Exit calls the OS exit syscall directly. The runtime doesn't walk the defer chain | Return from main() instead, or do explicit cleanup before os.Exit |
| `defer` in `init()` | Defers run when `init` ends, not at program shutdown | Section 4.1 — defer binds to the enclosing function. `init` is a function that runs once at startup | Don't use init() defers for global cleanup. Use explicit shutdown hooks |
| Closure vs argument in `defer` | Closure reads current value at exit; argument reads snapshot from defer line | Section 4.2 — arguments are evaluated and copied into the _defer record immediately. Closures capture variable references | Use `defer f(x)` for snapshots; use `defer func() { f(x) }()` when you need the latest value |

### Gotcha Deep Dive: `os.Exit` Skips All Defers

```go
package main

import (
	"fmt"
	"os"
)

func main() {
	defer fmt.Println("this never prints")
	fmt.Println("about to exit")
	os.Exit(0)
}
// Output: about to exit
// "this never prints" is NEVER printed
```

```
Step 1: defer registers Println("this never prints")
  Chain: → [Println("this never prints")]

Step 2: fmt.Println("about to exit") → prints

Step 3: os.Exit(0)
  os.Exit calls the OS-level exit syscall directly
  The Go runtime does NOT walk the defer chain
  Process terminates immediately

  Chain → [Println("this never prints")]   ← never walked!

FIX:
  func main() {
      defer fmt.Println("cleanup runs")
      if err := run(); err != nil {
          fmt.Fprintln(os.Stderr, err)
          os.Exit(1)  // only exit after explicit cleanup
      }
      // returning from main() DOES run defers
  }

  Or restructure so main() returns normally and defers run:
  func main() {
      defer fmt.Println("cleanup runs")
      // ... work ...
  }  // defers run when main returns
```

`os.Exit` is pulling the main breaker in a building. It doesn't wait for you to close windows or turn off lights — the building goes dark instantly. Return from main() instead, and the building's automated shutdown sequence (defer chain) runs properly.

### Gotcha Deep Dive: Defer in a Loop — Connection Pool Exhaustion

The most expensive production bug from misunderstanding defer:

```go
func ProcessAllOrders(ctx context.Context, db *sql.DB) error {
	orders := getOrders() // 1000 orders
	for _, ord := range orders {
		conn, err := db.Conn(ctx)
		if err != nil {
			return err
		}
		defer conn.Close() // BUG: all 1000 Close() calls wait until outer function returns
		process(conn, ord)
	}
	return nil
}
```

```
Iteration 0: conn₀ opened. defer chain: → [Close(conn₀)]
Iteration 1: conn₁ opened. defer chain: → [Close(conn₁)] → [Close(conn₀)]
Iteration 2: conn₂ opened. defer chain: → [Close(conn₂)] → [Close(conn₁)] → [Close(conn₀)]
...
Iteration 999: 1000 connections open simultaneously!

  DB pool default: max 25 connections
  Iteration 26: db.Conn(ctx) blocks waiting for a free connection
  All 25 connections are held by THIS function's defer chain
  DEADLOCK: function waits for connection, connections wait for function to end

  The chain in memory:
  g._defer → [Close₉₉₉] → [Close₉₉₈] → ... → [Close₁] → [Close₀]
  ← 1000 _defer records, 1000 open connections

FIX: IIFE per iteration:
  for _, ord := range orders {
      err := func() error {
          conn, err := db.Conn(ctx)
          if err != nil { return err }
          defer conn.Close()  // runs at END OF THIS func(), not the loop
          return process(conn, ord)
      }()
      if err != nil { return err }
  }
  ← each iteration opens 1 connection, processes, closes, then next iteration
```

Writing "close connection at the end" inside a loop is like hiring 1000 people and telling them all "leave at 5 PM." At 3 PM you have 1000 people in a room built for 25. The IIFE pattern is like processing one person at a time — they leave before the next one enters.

---

## 8. Performance & Tradeoffs

### Where this hits you in production

Your order service processes a CSV import of 50k rows per file upload. Each row calls a helper that opens a DB connection, defers `conn.Close()`, runs an INSERT, and returns. At 50k rows, that's 50k `defer` registrations — each one allocates a `_defer` record (~48-64 bytes) and pushes it onto the chain. Your INSERT round-trip is 2ms. Those 50k defer records add maybe 0.3ms total. You'd never notice them next to 100 seconds of DB I/O.

Now picture the same loop, but the `defer conn.Close()` is inside the loop of the *outer* function instead of in a helper. All 50k connections stay open until the outer function returns. Your pool has 25 connections. At iteration 26 the pool blocks, waiting for a free connection that will never come back — deadlock. The cost isn't CPU. It's connection exhaustion.

| Pattern | What it costs | You'd see this in... | Verdict |
|---------|--------------|---------------------|---------|
| `defer rows.Close()` after a query | One `_defer` record (~48B), runs on return | Every handler that does `db.QueryContext` | Noise. The query itself is 1-50ms. Use it every time. |
| `defer mu.Unlock()` in a cache read | One `_defer` record, runs on return | Rate limiter checking the token bucket map | Essentially free — the lock/unlock pair is ~20ns, defer adds ~5ns |
| `defer` in a tight loop (10k+ iterations) | 10k `_defer` records accumulated until function exit | CSV import, batch validation, log replay | Measurable memory, but the real risk is resource leaks (connections, files). Use IIFE or helper. |
| `panic` + `recover` vs `return error` | Panic unwind is 10-50x slower than returning an `error` value | Middleware recovery catching rare handler panics | Worth it as a safety net at the request boundary. Never use panic for normal control flow. |
| `recover` in every handler | One `_defer` + `recover` per request | HTTP middleware wrapping `next.ServeHTTP` | Cheap insurance — the recover path only runs on actual panics, which should be rare. |

### What actually hurts

The anti-pattern that burns you in production: `defer conn.Close()` inside a `for` loop in the outer function. Your batch import opens 50k connections, all held by deferred calls that won't fire until the function ends. At connection 26, `db.Conn(ctx)` blocks on the pool semaphore. The function can't finish because it's waiting for a connection. The connections can't be released because the function hasn't finished. Deadlock. Your p99 goes to infinity and the pod gets OOM-killed because 50k connection buffers eat memory.

The fix is boring: wrap the loop body in an IIFE or extract a helper, so `defer` runs per iteration. Or skip defer entirely and call `conn.Close()` explicitly after the INSERT. Either way, the principle is: defer binds to the *function*, not the *loop iteration*.

### What to measure

```bash
# Benchmark defer overhead in a hot loop
go test -bench=BenchmarkDeferLoop -benchmem ./pkg/batch/

# Compare: defer vs explicit close in a tight loop
go test -bench='BenchmarkExplicit|BenchmarkDeferred' -benchmem ./pkg/batch/

# Profile connection pool exhaustion
GODEBUG=netdns=go go test -run=TestBatchImport -count=1 -v ./service/
# Watch for "driver: bad connection" or context deadline errors

# Find defer-related allocations under load
go tool pprof -alloc_objects http://localhost:6060/debug/pprof/heap
# Then: top 20 -cum | grep "runtime.deferproc\|runtime.newdefer"
```

---

## 9. Common Misconceptions

People say **`defer` runs when the inner function I called returns** — but `defer` binds to the **function you wrote it in**. Only a **new** function scope (literal, method, nested func) gets its own defer stack.

People say **I'll recover the worker from main** — you won't. The child must **`recover` or not panic**, and usually **signals** the parent.

People say **`recover` anywhere saves me** — the spec and runtime expect the **`defer func() { v := recover(); ... }`** shape. Random `recover()` calls are `nil` factories.

People confuse **stamped defer args** with **closures**. `defer fmt.Println(i)` copies `i` at the `defer` line. `defer func() { fmt.Println(i) }()` reads `i` when the closure runs.

People think **panic is a fast error path** — it is slower than returning an `error` and makes control flow hard to reason about in public APIs.

---

## 10. Related Tooling & Debugging

**`go test -race`** — catches races where defers and concurrent writes interact badly.

**`GOTRACEBACK=single|all`** — controls how much stack you see when something does panic during dev.

**`runtime/debug.Stack`** — paste stack bytes into logs inside middleware when you recover; pair with request ID.

**`pprof` (CPU, alloc)** — if someone swears defer is killing a hot loop, prove or disprove it with data.

---

## 11. Interview Gold Questions

**Q1: In what order do deferred calls run, and when are the arguments fixed?**

They run **last-in, first-out**. Arguments are evaluated **at the `defer` statement** — copies happen then, not at function exit. If they want extra color: the runtime keeps defers on a **per-function chain** and walks it **backwards** on return or panic.

**Q2: What happens with a named result and a defer that mutates it?**

The named result is **one live variable**. The `return expr` step assigns into it, then defers run, then the function returns the **final** value. That is the "double return" trick — clever in puzzles, use sparingly in production.

**Q3: Why `recover` in HTTP middleware, and what does it *not* cover?**

Middleware wraps **one request's** call stack. A `defer` + `recover` there can log a panic, return a **500**, and keep the process alive **for panics in that stack**. It does **not** catch panics in goroutines the handler fired **without** their own guard rails — those can still **crash the program**. You fix that with **worker-local** `recover` or structured error returns.

---

## 12. Final Verbal Answer

`defer` schedules a function to run when the enclosing function exits — whether that's a normal return, an early error return, or a panic unwinding. Two things catch people: first, arguments are evaluated at the `defer` line, not at exit time, so if you defer with a variable it captures the value at that moment. Second, defers run in LIFO order — the last one you registered is the first to execute.

`recover` only works if you call it directly inside a deferred function on the same goroutine that's panicking. A parent goroutine cannot catch a child's panic — each goroutine has its own defer chain. If a child panics without its own defer+recover, the whole program crashes.

In production, you see `defer rows.Close()`, `defer tx.Rollback()`, and `defer span.End()` everywhere — they guarantee cleanup on every exit path with a single line. The one trap is defer in a loop: each iteration pushes another deferred call that won't fire until the outer function returns, which can exhaust connection pools. The fix is wrapping the loop body in a small function so defer runs per iteration.

---

## 13. Comprehensive Interview Questions

> Full interview question bank (see companion file) → [[questions/T10 Defer, Panic & Recover Internals - Interview Questions]]

**Preview questions:**

1. When are `defer` arguments evaluated, and how is that different from a closure that captures a loop variable?
2. Walk the LIFO order of three defers, then add a `return` in the middle of the function — which deferred calls run?
3. Design an HTTP server that logs a request ID, converts handler panics to 500 responses, and keeps a separate goroutine pool safe from unhandled child panics.

---

> See [[Glossary]] for term definitions.
