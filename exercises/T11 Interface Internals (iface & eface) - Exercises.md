# T11: Interface Internals (iface & eface) — Exercises

> Practice for [[T11 Interface Internals (iface & eface)]]. Try without peeking at solutions first.

---

## Tier 2 — Fix the typed `nil` error return through an interface

### Problem

A function is supposed to return `nil` when there is no error, but callers using `if err == nil` never see “no error.” The bug involves returning a **typed nil pointer** through an **`error` interface value**.

**Broken starter code (do not run as-is; find the issue):**

```go
package main

import "fmt"

type appError struct{ msg string }

func (e *appError) Error() string { return e.msg }

func doWork() error {
	var e *appError = nil
	return e
}

func main() {
	if err := doWork(); err == nil {
		fmt.Println("ok")
	} else {
		fmt.Println("surprise:", err) // you may land here incorrectly
	}
}
```

### Your tasks

1. Explain **why** `err == nil` can be false when `e` is a typed `nil` `*appError` returned as `error`.
2. **Fix** `doWork` so a “no error” path returns a **true** nil `error` (no spurious non-nil `error` interface value).
3. Optional: show a second acceptable pattern if your API must sometimes return a **nil concrete pointer** with a *different* method (e.g. explicit sentinel or separate bool).

### Solution sketch (reveal after attempt)

**Cause:** the returned `error` is an **interface value** with type `*appError` and data `nil` — the **type half** of the interface is not nil, so the whole `error` is not `== nil`.

**Fix:** return **untyped** nil for the `error` interface, e.g. `return nil` (not `return e` where `e` is a typed `*appError` variable), or assign to `error` first in a way that produces a true nil interface (often simply `return nil`).

```go
func doWork() error {
	return nil
}
```

---

## Tier 3 — Mini plugin system

### Requirements

1. Define a `Plugin` **interface** (e.g. `Name() string`, `Run() string` — adjust names if you prefer, but keep **two** methods so it is a non-**empty** interface).
2. **Register** concrete types by a **string name** in a **map** or **registry** (e.g. `map[string]func() Plugin` or `map[string]Plugin` factories).
3. **Load** by name, then use **type assertion** (comma-ok) to treat a plugin as a **more specific** type when needed (e.g. a `Greeter` sub-interface or concrete type for extra methods).
4. **Demonstrate** with **2–3** small plugins (e.g. `Hello`, `Echo`, `Counter`) and a `main` that runs them in a loop.

### Starter outline (fill in)

```go
package main

import "fmt"

// TODO: define Plugin (non-empty interface).

// TODO: 2-3 concrete types implementing Plugin.

// TODO: registry: register by name, build by name.

// TODO: runPlugin(name string) that loads, asserts if needed, runs.

func main() {
	// register plugins
	// run a few by name; show type assertion to a concrete *EchoPlugin or extra iface
}
```

### Acceptance checks

- [ ] Returning a `Plugin` from a map lookup and calling methods works.
- [ ] At least one call site uses `p, ok := somePlugin.(ConcreteType)` or an interface with **extra** methods and documents **why** assertion was needed.
- [ ] No panics in the happy path; failed lookup or wrong type is handled (comma-ok or `ok` from map).

### Example solution (one possible shape — compare after you write yours)

```go
package main

import "fmt"

type Plugin interface {
	Name() string
	Run() string
}

type hello struct{}

func (hello) Name() string { return "hello" }
func (hello) Run() string  { return "Hello from plugin" }

type echo struct{ s string }

func (e *echo) Name() string { return "echo" }
func (e *echo) Run() string  { return e.s }

type counter int

func (c *counter) Name() string { return "counter" }
func (c *counter) Run() string  { return fmt.Sprintf("n=%d", *c) }

// EchoAsSetter — optional: extra behavior only on *echo
type PhraseSetter interface {
	Plugin
	SetPhrase(string)
}

func (e *echo) SetPhrase(s string) { e.s = s }

var registry = map[string]func() Plugin{
	"hello": func() Plugin { return hello{} },
	"echo": func() Plugin {
		e := &echo{s: "default"}
		return e
	},
	"counter": func() Plugin {
		c := counter(0)
		return &c
	},
}

func runNamed(name string) {
	p, ok := registry[name]
	if !ok {
		fmt.Println("unknown:", name)
		return
	}
	pl := p()
	fmt.Println(pl.Name(), "->", pl.Run())

	// Type assertion: only *echo can set phrase
	if s, ok := pl.(PhraseSetter); ok {
		s.SetPhrase("asserted and set")
		if e2, ok2 := pl.(*echo); ok2 { // pointer assertion to concrete
			fmt.Println("echo after set:", e2.Run())
		}
	}
}

func main() {
	for _, n := range []string{"hello", "echo", "counter", "missing"} {
		runNamed(n)
	}
}
```

Tie this back to **iface** (your `Plugin` has methods → **iface** + `itab` for dispatch) and **type assertions** as **peeking** at the real concrete type. See [[T11 Interface Internals (iface & eface) - Simplified]].
