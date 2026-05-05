# Day 1 — Interview preparation plan

> **Wave focus:** B → C start · **Deep-work topic:** [[T09 Error Handling Patterns]]  
> **DSA week:** 1 (Arrays, Hashing, Two Pointers) · **Total:** ~2.75 h execution  
> **Aligned with:** [[Study Plan]] §3 Days 1–3 · §2.5 · §2.6 · §2.7

---

## 1. Morning — Active Recall (20–30 min)

Answer **without** opening notes first. Topics from **Wave A / maintenance** (not today’s deep-work topic):

1. You append to a slice `s = append(s, x)` where `s` was sliced from a larger array — **who sees the new length**, callers holding the old slice header or only after reassignment? What’s the leak/trap?
2. When does comparing two structs with `==` **compile**, and when does it **not**?
3. A `map[string]User` — can you take the address of `m["foo"].Name` directly? Why or why not?
4. Explain **one** situation where a **copy** of a struct bites you in an HTTP handler vs a **pointer**.
5. **Bonus:** What happens to iteration order if you range over a map twice?

---

## 2. Go Deep Work (60–90 min)

**Topic today:** [[T09 Error Handling Patterns]]

### Core Idea (max 6 lines)

In Go, errors are values: you return them, wrap context with `fmt.Errorf("…: %w", err)`, and callers use `errors.Is` / `errors.As` to branch. Plain `==` usually fails on wrapped errors. Typed nil pointers can make `err != nil` true when you meant success — return bare `nil` for `error`. Logging/`%v` vs `%w` changes whether the chain is inspectable.

### Interview Traps

- Wrapping with `%v` or string concat → breaks `errors.Is` / `errors.As`.
- `return err` when `err` is a typed nil → caller sees non-nil `error`.
- Using `==` on wrapped errors instead of `errors.Is`.
- Discarding wrapped cause when mapping to HTTP status.

### Implementation Task (MANDATORY)

**Time:** ~25–35 min · **`go test` must pass**

Build a tiny package:

- Define `var ErrNotFound = errors.New("not found")`.
- `UserRepo` interface: `FindByID(ctx context.Context, id int64) (*User, error)` + fake impl returning `ErrNotFound` for unknown ID.
- `GetUser(ctx, repo, id)` wraps repo errors with `fmt.Errorf("get user %d: %w", id, err)`.
- `HTTPStatus(err error) int` returns **404** if `errors.Is(err, ErrNotFound)`, **500** otherwise.

Deliverable: `_test.go` proving `errors.Is` works through your wrap.

### Debug Scenario

Start from your passing code. **Introduce exactly one** of these bugs (pick A or B):

- **A:** Change `%w` to `%v` in `GetUser` — tests that rely on `errors.Is(..., ErrNotFound)` **fail**. Fix by restoring `%w` and explain why.
- **B:** On “found” path accidentally `return nil, err` where `err` is `var e *MyNotFoundError = nil` — triggers typed-nil interface. Fix by returning `nil, nil` on success.

Run `go test -v` before and after. Document the symptom in one sentence.

---

## 3. DSA Block (60 min)

**Week 1 patterns:** hashing · two pointers · **Medium** · **30 min each** · solve in **Go** · **re-code** the second from scratch after a 2-min break.

| # | Problem | Pattern | Time |
|---|-----------|---------|------|
| **1** | [Group Anagrams](https://leetcode.com/problems/group-anagrams/) | Hash map + canonical key (sorted string or char count) | 30 min |
| **2** | [3Sum](https://leetcode.com/problems/3sum/) | Sort + two pointers + dedup | 30 min |

---

## 4. Verbal Task (10–15 min)

**Question:** “When do you use `errors.Is`, when `errors.As`, and why doesn’t `==` work after `fmt.Errorf` with `%w`?”

**Expect:** 60–90 s · chain/unwrap mental model · sentinel vs type assertion · mention `%v` killing inspectability.

---

## 5. System Design (15–20 min)

**Mini-problem:** Webhook receiver — partner POSTs events; you **must not** double-apply side effects if they retry.

**Cover (tradeoffs, not pretty diagrams):**

- At-least-once delivery vs your **idempotency key** (header/body).
- Store seen IDs (**Redis** vs DB unique constraint) vs cryptographic verification.
- What breaks if Redis loses memory / TTL too short.

---

## 6. End-of-Day Check

Answer cold — if any fail, **Day 1 topic not done** (repeat T09 block tomorrow):

1. Show how `errors.Is` differs from comparing `err == ErrSentinel` after one `%w` wrap.
2. What does `errors.As` give you that `Is` does not?
3. Why might `if err != nil { return err }` return a non-nil error on the success path?
4. When mapping to HTTP, where should you **stop** wrapping so clients don’t leak internals?
5. Name **one** reason to prefer wrapped errors over string matching on `err.Error()`.

---

## Time sanity (~2.75 h)

| Block | Minutes |
|-------|---------|
| Morning | 25 |
| Go + debug | 85 |
| DSA | 60 |
| Verbal | 12 |
| SD | 18 |
| Checks | 15 |

---

## Log (optional)

| Done | Notes |
|------|--------|
| [ ] | Paste what failed in [[Study Plan]] §9 if useful |
