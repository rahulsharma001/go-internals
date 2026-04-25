# T10 Defer, Panic & Recover Internals — Exercises
#exercises #go #defer #panic

Back to: [[T10 Defer, Panic & Recover Internals]]

---

## Tier 2 — Fix the `defer`–in–loop file descriptor leak

**Problem:** The following code opens many files in a loop and defers `Close` in the same function body. **Explain** why this is bad and **fix** it in **two** acceptable ways: (1) an **anonymous function** that scopes the defer per iteration, and (2) an **explicit** `Close` without relying on that defer pattern.

> **Context:** In production, the same mistake appears with `Open`, network connections, `Rows` from databases, and any **close the handle** call—always watch **what** outlives the **iteration**.

```go
package main

import (
	"fmt"
	"os"
)

// Broken: N defers, all run when ReadMany returns — N open FDs until then.
func ReadManyBroken(paths []string) error {
	for _, p := range paths {
		f, err := os.Open(p)
		if err != nil {
			return err
		}
		defer f.Close() // BUG: defers stack for entire function, not per path
		// ... read f ...
		_, _ = f.Read(make([]byte, 1))
	}
	return nil
}

func main() {
	_ = ReadManyBroken([]string{"/etc/hostname", "/etc/hosts"})
	fmt.Println("done")
}
```

**Your tasks**

1. **In two sentences**, state the bug: *when* do the deferred `Close` calls run, and *how many* files stay open as the loop runs?
2. **Fix A — per-iteration closure:** Refactor the loop body so each `defer` is tied to a **function** that **returns** before the next iteration (anonymous func or a named helper).
3. **Fix B — explicit close:** No `defer` in the loop; `Close` in the success path and handle errors in a `defer`-free way (you may use a small inner block and `if err := ...; err != nil { return err }`).

**Acceptance:** After either fix, **at most one** `Open` is **without** a matching `Close` for at most a **short** window per iteration, not **O(n)** held until the outer function returns.

**Self-check wikis:** See the loop material in [[T10 Defer, Panic & Recover Internals]] and [[T10 Defer, Panic & Recover Internals - Revision]].

---

## Tier 3 — `SafeGo`: panic-safe goroutine wrapper

**Goal:** Build **`SafeGo(fn func())`** that:

- launches **`fn` in a new goroutine**;
- if **`fn` panics**, the panic is **recovered** (same goroutine as `fn`), **logged** (use `log.Printf` or `fmt.Println` for the message), and the **parent** goroutine and **other** children **are not** killed;
- if **`fn` returns normally**, nothing special is printed.

**Requirements**

1. Implement **`func SafeGo(fn func())`** in a small `package main` (or `safego` if you prefer).
2. Use **`defer` + `recover()`** in the **same** goroutine that runs `fn` (this is the only model that can catch that panic).
3. **Demo `main`:** start **3** `SafeGo` calls; one `fn` should `panic("boom")`, two should complete quietly. The process must **exit 0** and print a **single** panic line for the bad child (or your chosen log format), not crash the whole program.

**Starter sketch (you complete and correct)**

```go
package main

import (
	"log"
	"runtime/debug"
	"sync"
)

func SafeGo(fn func()) {
	go func() {
		defer func() {
			if r := recover(); r != nil {
				log.Printf("SafeGo: panic: %v\n%s", r, debug.Stack())
			}
		}()
		fn()
	}()
}

func main() {
	var wg sync.WaitGroup
	// 3 workers — one panics, two return normally; use Done() per goroutine (e.g. wrap SafeGo to call wg.Done in a defer) or a channel — do not use Sleep as the only sync in real code
	wg.Add(3)
	// TODO: SafeGo three times, one with panic("boom"), two quiet; wg.Wait() then exit 0
	_ = wg
}
```

**Stretch (optional):** pass a `context.Context` and stop early on cancel, still keeping panic recovery; keep recovery in the child goroutine.

**Links:** [[T10 Defer, Panic & Recover Internals - Interview Questions]] Q3, Q5, Q12 · [[T10 Defer, Panic & Recover Internals - Visual Map]]
