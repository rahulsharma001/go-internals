# Day 1 — Interview preparation plan

> **Wave focus:** B (Days 1–3) · **Deep-work topic:** [[Go Error Handling]]
> **DSA week:** 1 (Arrays, Hashing, Two Pointers) · **Total:** ~2.75 h execution  
> **Historical one-day plan. Current execution is [[Current Week]] and [[Engineering Study Plan]].**

---

## 1. Morning — Active Recall (20–30 min)

**Deliver:** answer **before** opening any `<details>`.

Topics from **Wave A / maintenance** (not today’s deep-work topic):

1. You append with `s = append(s, x)` where `s` was sliced from a larger backing array — **which callers see the new length**, and what’s the classic alias trap?

2. When does `==` on two structs **compile**, and when does it **not**?

3. For `map[string]User`, can you take `&m["foo"].Name` directly? Why or why not?

4. Name **one** way **struct copy** vs **pointer** bites you in an HTTP handler.

5. **Bonus:** What changes between two `range` loops over the same map?

**Definition of done:** every prompt answered aloud or written **before** opening `<details>`.

<details>
<summary>Show Answer</summary>

Only callers holding the **updated** slice header after assignment see the new len/cap. Others keep the old header — if append **reallocates**, they may still point at **stale** backing storage. Trap: append-growth without returning the new slice to every alias.

</details>

<details>
<summary>Show Answer</summary>

Compiles when **every field is comparable**. Does **not** compile if any field is a slice, map, or func (non-comparable).

</details>

<details>
<summary>Show Answer</summary>

**No** — map index expressions are not addressable; use a local variable or store pointers in the map.

</details>

<details>
<summary>Show Answer</summary>

**Examples:** copying a struct that holds a **mutex** / **sync.Once**; value receivers that still mutate **shared** pointer fields; copying large structs on every request.

</details>

<details>
<summary>Show Answer</summary>

**Iteration order is unspecified** — two passes can visit keys in different orders. Never rely on map order.

</details>

---

## 2. Go Deep Work (60–90 min)

**Topic today:** [[Go Error Handling]]

> **Do NOT refer to vault notes while implementing. Close Obsidian or any pane with answers. Only open notes after a failed compile, failing test, or expired timer — then fix and retry.**

### Core Idea (max 6 lines)

Errors are values: return them, wrap with `fmt.Errorf("…: %w", err)`, branch with `errors.Is` / `errors.As`. Plain `==` breaks across wraps. Typed-nil concrete errors still produce **non-nil** `error` interfaces — return untyped `nil` on success. `%v` / string concat **cuts** the unwrap chain.

### Interview Traps

- **Trap:** `%v` or string concat when wrapping — loses unwrap chain.

<details>
<summary>Show Answer</summary>

**Why it loses offers:** Callers can’t use `errors.Is` / `errors.As`; HTTP/status mapping and retries break. **Fix:** use `%w` (or structured wrapping that preserves `Unwrap()`).

</details>

- **Trap:** `return err` when `err` is a typed nil pointer — `err != nil` on success.

<details>
<summary>Show Answer</summary>

**Why it loses offers:** Interface holds `(type, nil)` → non-nil `error`. **Fix:** `return nil, nil` or `return nil, nil` with explicit `error` zero; avoid `var e *MyErr; return e`.

</details>

- **Trap:** `err == ErrSentinel` after a `%w` wrap — always false.

<details>
<summary>Show Answer</summary>

**Why it loses offers:** Wrap allocates a new wrapper; `==` compares top-level identity. **Fix:** `errors.Is(err, ErrSentinel)`.

</details>

### Implementation Task (MANDATORY)

**Build** (~25–35 min timer): package `users`.

- `var ErrNotFound = errors.New("not found")`, `type User struct { ID int64; Name string }`.
- `UserRepo` interface: `FindByID(ctx context.Context, id int64) (*User, error)` — fake impl returns `ErrNotFound` for unknown IDs.
- `GetUser(ctx, repo, id)` wraps repo errors: `fmt.Errorf("get user %d: %w", id, err)`.
- `HTTPStatus(err error) int` → **404** if `errors.Is(err, ErrNotFound)`, else **500**.
- `_test.go`: prove `errors.Is` works through `GetUser`’s wrap; table-test status mapping.

**Acceptance:** `go test ./...` passes for this package.

### Debug drills (MANDATORY — exactly two)

#### Drill A — Missing context cancellation

**Failure:** `FindByID` **ignores `ctx`** (e.g. hard-coded sleep or blocks without `ctx.Done()`). Under test timeout or `context.WithTimeout`, call hangs; tests flake or hang forever.

**Repro:** In fake repo, `time.Sleep(30 * time.Second)` or block on a channel; call `GetUser` with a **2s deadline** context — observe hang / test timeout.

<details>
<summary>Show Answer</summary>

**Root cause:** Downstream work doesn’t respect cancellation — no `select` on `ctx.Done()`, no passing `ctx` to I/O that supports it.

**Correct fix:** Short-circuit when `ctx.Err() != nil`; use `select` with `ctx.Done()` around blocking work; in real code pass `ctx` into `QueryContext` / `http.NewRequestWithContext`, etc.

</details>

#### Drill B — Race on shared resource

**Failure:** Concurrent `GetUser` calls increment **`package-level map[string]int` error metrics** (key = error kind) **without synchronization**. `go test -race` reports data race.

**Repro:** Test runs `GetUser` from **many goroutines** with random IDs; race detector fires on map writes.

<details>
<summary>Show Answer</summary>

**Root cause:** Unsynchronized writes (and reads during write) to a shared `map` from multiple goroutines.

**Correct fix:** guard with `sync.Mutex`, use `sync.Map`, or channel-serialize updates; for metrics prefer `atomic` counters or a dedicated metrics lib — never bare map from concurrent handlers.

</details>

**Definition of done (Go):** `go test` passes; **no hang** on canceled context in Drill A; **`go test -race` clean** on the scenario tests for Drill B; **`context` honored** on the hot path after fixes.

---

## 3. DSA Block (60 min)

> **Do NOT refer to vault notes while implementing. Close Obsidian or any pane with answers. Only open notes after a failed compile, failing test, or expired timer — then fix and retry.**

**Two Medium problems · ~30 min each · Go · Week 1 patterns (hashing, two pointers)**

| # | Problem | Pattern | Time |
|---|---------|---------|------|
| **1** | [Group Anagrams](https://leetcode.com/problems/group-anagrams/) | Hash map + canonical key | 30 min |
| **2** | [3Sum](https://leetcode.com/problems/3sum/) | Sort + two pointers + dedup | 30 min |

**Definition of done (DSA):** both finished within **30 min** each; **correct big-O** stated aloud after each; code passes samples; **re-code** Problem 2 once from scratch after a 2-min break (still no notes during the timed attempt).

<details>
<summary>Show Answer — Problem 1 (approach · complexity · Go sketch)</summary>

**Approach:** Canonical key per string — sort chars **or** `[26]int` count vector → map[key]→slice of originals.

**Complexity:** O(N · K log K) if sort per word (K = max len); O(N · K) with count key.

**Go sketch:** `map[string][]string`, key from `sort.StringSlice` copy or `fmt.Sprintf` of counts.

</details>

<details>
<summary>Show Answer — Problem 2 (approach · complexity · Go sketch)</summary>

**Approach:** Sort nums; fix `i`, two-pointer `lo/hi` for target `-nums[i]`; skip duplicates on `i`, `lo`, `hi`.

**Complexity:** O(n²) time, O(1) extra if sorting in-place (excluding sort O(n log n)).

**Go sketch:** sort `[]int`, nested loop with skip `if i > 0 && nums[i]==nums[i-1]`.

</details>

---

## 4. Verbal Task (10–15 min)

**Question (visible):** When do you use `errors.Is`, when `errors.As`, and why doesn’t `==` work after `fmt.Errorf` with `%w`?

**Definition of done (Verbal):** **≤90 s** live answer; **≥3** named concepts (`Unwrap`, sentinel, typed assertion); no drift.

<details>
<summary>Show Answer (example script)</summary>

**Is** walks the unwrap chain for **sentinel equality** — “is this error *this* `ErrNotFound` anywhere inside?” **As** finds a **typed error** in the chain — “give me a `*ValidationError` to read fields.” **`==`** compares the **top wrapper’s identity**; `%w` allocates a new wrapper, so the outer box isn’t the same pointer as the sentinel — use **Is**, not `==`. Mention **`%v` drops Unwrap** — then neither Is nor As can see inside.

</details>

---

## 5. System Design (15–20 min)

**Mini-problem (visible):** Inbound **webhooks** from partners — POST JSON events; side effects (charge user, ship order) **must run exactly once** even if partners retry.

**Scale constraint:** **10k successful webhook writes/min** at peak (~**167 RPS** sustained), with **24h retry storms** doubling traffic briefly.

**Failure scenario:** **Redis idempotency cache flips unavailable** for 2 minutes during deploy — duplicates may arrive from partners.

**Forced tradeoff:** **latency vs consistency** — synchronous **strong dedupe** ( row-level DB commit before ACK) vs faster ACK with **risk of duplicate side effect** under partition.

**Definition of done (SD):** spoken or bullet walkthrough names **scale**, **failure**, **tradeoff**, and **one mitigation** (e.g. dedupe table + PK, outbox, or partner signing).

<details>
<summary>Show Answer</summary>

**Expected approach:** Stable **idempotency key** in header/body; store `(key, outcome)` in **DB** with unique constraint — source of truth beats Redis alone. ACK only after durable record of “accepted” or after side effect in **transaction**. **Outbox** or **exactly-once-ish** via dedupe + compensation.

**Key tradeoffs:** Redis-only dedupe is fast but **volatile**; DB unique index adds **write latency** but survives Redis loss. Under Redis down: fall back to **DB lookup** only (slower) or **fail closed** (429/503) if partner allows retry — **never** silent double-charge.

**Failure behavior change:** When Redis is down, **p99 rises** but correctness holds if **authoritative dedupe** lives in Postgres; if you only had Redis, you **lose dedupe** → duplicates unless you reject traffic.

</details>

---

## 6. End-of-Day Check

Answer **cold** first — if any blank after honest effort, **treat Day 1 deep work as incomplete** for T09 (repeat block tomorrow).

1. How does `errors.Is` differ from `err == ErrSentinel` after one `%w` wrap?

2. What does `errors.As` give you that `errors.Is` does not?

3. Why can `if err != nil { return err }` return a **non-nil** error on the success path?

4. Where should you **stop** wrapping before the HTTP boundary so clients don’t get internal strings?

5. One reason **wrapped errors** beat substring checks on `err.Error()`?

**Definition of done:** recall **without** `<details>` first — open only to self-grade.

<details>
<summary>Show Answer</summary>

**`Is`** walks `Unwrap()` until a sentinel match; **`==`** compares only the **outer** wrapper’s identity → **false** after `%w` even when the cause matches.

</details>

<details>
<summary>Show Answer</summary>

**`As`** binds a **typed** error value from the chain (`errors.As(err, &target)`). **`Is`** only answers sentinel equality — no typed fields.

</details>

<details>
<summary>Show Answer</summary>

**Typed nil:** e.g. `var e *MyErr = nil` — the **interface** holds `(type *MyErr, data nil)` → `err != nil` is **true**. Fix: `return nil, nil` with explicit nil error on success.

</details>

<details>
<summary>Show Answer</summary>

At the **HTTP boundary**: map to **stable codes/reasons**; **log** full chain server-side. Stop piping opaque wrapped strings to clients.

</details>

<details>
<summary>Show Answer</summary>

**Wrapped errors** keep machine-checkable **`Is`/`As`** and survive refactors; **`Error()`** substring checks break when wording changes and encode leaks.

</details>

---

## Time sanity (~2.75 h)

| Block | Minutes |
|-------|---------|
| Morning | 25 |
| Go + drills | 85 |
| DSA | 60 |
| Verbal | 12 |
| SD | 18 |
| End-of-day | 10 |

---

## Log (optional)

| Done | Notes |
|------|-------|
| [ ] | Record observed gaps through [[Mistake Index]] if useful |
