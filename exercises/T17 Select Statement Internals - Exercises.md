# T17 Select Statement Internals — Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[T17 Select Statement Internals]].

---

## Tier 3: Build It — TryEnqueue

### Task

Implement `TryEnqueue(job Job, jobs chan<- Job) bool` returning **false** when the send cannot complete without blocking.

### Solution

```go
package main

import "fmt"

type Job struct{ ID int }

func TryEnqueue(job Job, jobs chan<- Job) bool {
	select {
	case jobs <- job:
		return true
	default:
		return false
	}
}

func main() {
	q := make(chan Job, 1)
	fmt.Println(TryEnqueue(Job{1}, q))
	fmt.Println(TryEnqueue(Job{2}, q))
	fmt.Println(TryEnqueue(Job{3}, q))
}
```

### Output

```
true
false
false
```

### What to observe

After the first successful send, a capacity-1 buffer is full. The next `TryEnqueue` hits **`default`** — the runtime never parks on `sendq` because `block=false` for that `select` shape (via `default`).

---

## Tier 3: Build It — MergeOrders

### Task

Merge `a <-chan Order` and `b <-chan Order` into `out chan<- Order` until both inputs close. Use the **nil channel disable** pattern from Section 4.8 of the main note.

### Solution

```go
package main

import "fmt"

type Order struct{ ID int }

func MergeOrders(out chan<- Order, a, b <-chan Order) {
	for a != nil || b != nil {
		select {
		case v, ok := <-a:
			if !ok {
				a = nil
				continue
			}
			out <- v
		case v, ok := <-b:
			if !ok {
				b = nil
				continue
			}
			out <- v
		}
	}
	close(out)
}

func main() {
	a := make(chan Order)
	b := make(chan Order)
	out := make(chan Order, 4)
	go func() {
		a <- Order{1}
		close(a)
	}()
	go func() {
		b <- Order{2}
		close(b)
	}()
	MergeOrders(out, a, b)
	for o := range out {
		fmt.Println(o.ID)
	}
}
```

### Output (order of 1 and 2 may vary by scheduling)

```
1
2
```

or

```
2
1
```

### What to observe

Setting **`a = nil`** removes the first `case` from the next `select` — the compiler still emits a `scase` for the local variable channel, but at source level you **stop receiving** from a closed input by nil-ing the handle; the closed branch fires once with `ok == false`, then you detach.

---

> Exercise from [[T17 Select Statement Internals]] — Section 6.4
