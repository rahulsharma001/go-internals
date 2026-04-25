# T07 Pointers & Pointer Semantics — Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[T07 Pointers & Pointer Semantics]].

---

## Tier 2: Fix the Bug — Solution

A **value receiver** means `db` is a *copy* of the `DB` struct. Assigning to `db.conn` only updates the copy; the original `db` in `main` is unchanged, so `db.conn` stays `""`.

Use a **pointer receiver** so the method mutates the *same* struct the caller has.

**Before (bug):**

```go
func (db DB) Connect(dsn string) {
    db.conn = dsn // mutates a temporary copy, not the caller's db
}
```

**After (fix):**

```go
func (db *DB) Connect(dsn string) {
    db.conn = dsn // *db is the original struct, shared with the caller
}
```

**Runnable example:**

```go
package main

import "fmt"

type DB struct {
	conn string
}

func (db *DB) Connect(dsn string) {
	db.conn = dsn
}

func main() {
	db := DB{}
	db.Connect("postgres://localhost/mydb")
	fmt.Println(db.conn) // now prints the DSN
}
```

Go will pass `&db` automatically when you call `db.Connect(...)` on a `DB` value, because `Connect` has a pointer receiver—no change required in `main`. If you only had a `*DB` from somewhere, `db.Connect` still works the same.

---

## Tier 3: Build It — Solution

### Task

Build a `LinkedList` with `Push`, `Pop`, and `Print` methods. The list should use pointer semantics correctly — `Push` and `Pop` must modify the list, `Print` can use a value receiver. Use `*Node` pointers to chain elements.

### Solution

`Push` and `Pop` reassign or advance `Head`; that changes the *list header* the caller is holding, so the receiver must be a pointer. `Print` only reads the chain via `Head` and follows `Next`; a value receiver still sees the same nodes because `Head` in the copy points to the same first node (only the `LinkedList` wrapper is copied, not the nodes).

`Pop` returns `(value int, ok bool)` so you can tell an empty list from a legitimate `0` value if you use zero as data later.

```go
package main

import "fmt"

// Node is one element. Next chains to the rest of the list or nil.
type Node struct {
	Value int
	Next  *Node
}

// LinkedList is the "container": only Head matters for where the list starts.
// Empty list: Head == nil.
type LinkedList struct {
	Head *Node
}

// Push prepends: new head, old list hangs off Next. Must use pointer receiver
// so we update the caller's Head, not a copy of LinkedList.
func (l *LinkedList) Push(v int) {
	l.Head = &Node{Value: v, Next: l.Head}
}

// Pop removes the head and returns its value. Pointer receiver: we nil out
// or advance Head on the real list, not a copy.
func (l *LinkedList) Pop() (int, bool) {
	if l.Head == nil {
		return 0, false
	}
	v := l.Head.Value
	l.Head = l.Head.Next // list shrinks; old first node is no longer referenced
	return v, true
}

// Print walks the chain. Value receiver is enough: the copy's Head is the
// same *Node address as the original's, so we traverse the real list.
func (l LinkedList) Print() {
	for n := l.Head; n != nil; n = n.Next {
		fmt.Printf("%d -> ", n.Value)
	}
	fmt.Println("nil")
}

func main() {
	var list LinkedList

	list.Print()
	list.Push(10)
	list.Push(20)
	list.Push(30)
	list.Print()

	if v, ok := list.Pop(); ok {
		fmt.Println("Popped:", v)
	}
	list.Print()

	list.Push(5)
	list.Print()
}
```

### Output

```
nil
30 -> 20 -> 10 -> nil
Popped: 30
20 -> 10 -> nil
5 -> 20 -> 10 -> nil
```

### What to observe

- **Why `Push` / `Pop` need a pointer receiver:** A value receiver would copy the whole `LinkedList` struct. That copy would get a new `Head` while the caller’s `list` in `main` would still have the old `Head` — the list would never “stick.” With `*LinkedList`, the method updates the *same* `Head` field the caller uses.

- **Why `Print` can use a value receiver:** The copy still contains the same `Head` pointer (same address). You only read and follow `Next` pointers; you don’t reassign `Head` on the `LinkedList` itself, so a shallow copy of the struct is enough. (If the list were huge, you’d still only copy the small `LinkedList` header, not every node — another reason the pointer in `Head` is the right design.)

- **`Head` and `*Node`:** The *chain* is built from pointers; the list is empty when `Head` is `nil`, and you never need to reallocate the whole list to prepend — just a new `Node` and one pointer update.

---
