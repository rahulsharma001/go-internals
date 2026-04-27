# Daily Revision

> Your 8-week master guide: [[Study Plan]]. Check it first to know what to study today.

> **How to use this file:**
> 1. Open every morning. One scroll, top to bottom.
> 2. Cover everything below each "Blurt check" and answer from memory.
> 3. Check yourself against the **5-second answer** (visible).
> 4. Still fuzzy? Open the **two-line answer** accordion.
> 5. Still weak? Click "Drill deeper" at the bottom of the block.
> ~2 min per topic. Skip "maintenance" topics (just read the 5-second answer).

---

## Already Completed (Pre-Plan)

These 6 topics were done before the study plan started. Revise daily.

---

### [[T01 Go Type System & Value Semantics]]

**Blurt check** (cover below, answer from memory):
1. What is structural typing? How does Go decide if a type satisfies an interface?
2. What are the three questions to ask about any Go type?
3. Why can't a value type T satisfy an interface with pointer receiver methods?
4. What is the nil interface trap? What are the two fields?
5. How does embedding differ from inheritance?
6. What's the difference between `type X int` and `type X = int`?
7. What is the zero value of a struct, slice, map, interface?
8. How does Go achieve polymorphism without classes?
9. What does "accept interfaces, return structs" mean?

**5-second answer:**
> Go is statically typed with structural (implicit) interface satisfaction. Every type has an underlying type, zero value, and method set. Value T only has value-receiver methods; *T has both. Interfaces are two-field structs {type, data} -- a typed nil pointer makes a non-nil interface. Embedding is delegation, not inheritance.

> [!info]- Two-line answer (open if you forgot)
> Go uses structural typing: a type satisfies an interface if it has all the methods -- no `implements` keyword. T's method set has value-receiver methods only; *T has both, which is why a value T can't satisfy an interface requiring pointer-receiver methods.
> The nil interface trap: an interface is nil only when BOTH the type and data fields are nil. `var err *MyError = nil; return err` returns a non-nil error because the type field is set. Embedding promotes methods (delegation) but the receiver stays the inner type.

**Key visual:**
```
Interface: [type: *MyError | data: nil] ← NOT nil (type field is set)
           [type: nil       | data: nil] ← nil (both fields nil)
Method set: T → value receivers only.  *T → value + pointer receivers.
```

**Traps to remember:**
- `var err *MyError = nil; return err` -- returns non-nil error interface
- Embedded type's method receiver is always the embedded type, not the outer
- `type X int` (new type, can add methods) vs `type X = int` (alias, cannot)

**Weak? Drill deeper** → [[revision/T01 Go Type System & Value Semantics - Revision]]

---

### [[T02 Go Memory Allocation & Value Semantics]]

**Blurt check** (cover below, answer from memory):
1. What are the 4 triggers that cause escape to heap?
2. Stack alloc cost vs heap alloc cost? (rough numbers)
3. Is Go pass-by-value or pass-by-reference? What about slices and maps?
4. What is mark assist and why is it the real GC bottleneck?
5. How do you reduce GC pressure? (systematic approach)
6. What is the difference between `new()` and `make()`?
7. What does `go build -gcflags="-m"` show you?
8. What is GOGC and what is GOMEMLIMIT?
9. What is sync.Pool and when should you use it?

**5-second answer:**
> Go is strictly pass-by-value. The compiler uses escape analysis to decide stack (~1-2ns, auto-freed) vs heap (~25-50ns, GC-managed). Escape triggers: returned pointer, goroutine/channel, global, unknown size. Mark assist is the real GC bottleneck. Reduce pressure: profile first, sync.Pool, value semantics, pre-allocate, GOMEMLIMIT.

> [!info]- Two-line answer (open if you forgot)
> Escape analysis decides stack vs heap: if the compiler can prove a variable doesn't outlive its function, it stays on stack (cheap). Four escape triggers: returned pointer, sent to goroutine/channel, stored in global, or unknown size. `new()` returns a pointer (may stack-allocate); `make()` initializes slices/maps/channels.
> Mark assist is worse than STW pauses because goroutines that allocate during GC are forced to help mark before their allocation proceeds -- this adds unpredictable latency to hot paths. Reduce GC pressure: profile with pprof, use sync.Pool for reusable objects, prefer value semantics, pre-allocate slices, tune GOMEMLIMIT.

**Key visual:**
```
STACK (per goroutine, ~2KB)     HEAP (shared, GC-managed)
┌──────────────────┐            ┌──────────────────┐
│ x := 42          │            │ User struct       │
│ auto-freed       │            │ (escaped via &)   │
└──────────────────┘            └──────────────────┘
Escape? 1.returned ptr 2.goroutine/chan 3.global 4.unknown size → heap
```

**Traps to remember:**
- `new()` and `&T{}` do NOT guarantee heap -- escape analysis decides
- Slice append beyond capacity: new backing array, caller's header is stale
- "STW pauses are the bottleneck" is outdated -- mark assist is the real killer

**Weak? Drill deeper** → [[revision/T02 Go Memory Allocation & Value Semantics - Revision]]

---

### [[T03 Strings, Runes & UTF-8 Internals]]

**Blurt check** (cover below, answer from memory):
1. What are the two fields in StringHeader? Total size on 64-bit?
2. What does `len("cafe")` return and why?
3. What's the difference between `byte` and `rune`?
4. How does `for range` over a string differ from index-based loop?
5. Why is `+=` in a loop O(n^2)? What replaces it?
6. How does `strings.Builder.String()` avoid allocation?
7. What happens if you copy a Builder value?
8. What is `string(65)` and why is it a trap?
9. How does substring slicing cause memory leaks?

**5-second answer:**
> A string is an immutable 16-byte header (ptr + len) over a UTF-8 byte array. `len()` counts bytes, not characters. `for range` decodes runes. Builder wraps `[]byte` with zero-copy String() via unsafe.String. Substring slicing shares the backing array -- can leak memory.

> [!info]- Two-line answer (open if you forgot)
> StringHeader = pointer + length (16 bytes). Strings are immutable UTF-8 byte sequences. `len()` returns bytes, not runes -- `len("cafe")` = 5 because the accented e is 2 bytes. `byte` = uint8 (one byte), `rune` = int32 (one Unicode code point). `for range` decodes runes; index loop gives raw bytes.
> `strings.Builder` wraps a `[]byte` with amortized O(1) appends and zero-copy `String()` via `unsafe.String`. Copying a Builder panics on write (copy detection). `string(65)` = "A" not "65" (it converts a code point). Substring `s[:5]` shares the backing array -- use `strings.Clone()` to break the reference.

**Key visual:**
```
StringHeader [ptr|len=5] ──▶ [c][a][f][0xC3][0xA9]  ("cafe" = 5 bytes, 4 runes)
Builder: buf [G][o][ ][i][s] → String() points at same buf (zero copy)
```

**Traps to remember:**
- `len("cafe")` = 5 (not 4 -- "e" is 2 bytes in UTF-8)
- `small := huge[:5]` keeps entire huge string alive (use `strings.Clone`)
- `string(65)` = "A" not "65" (Unicode code point, not decimal)

**Weak? Drill deeper** → [[revision/T03 Strings, Runes & UTF-8 Internals - Revision]]

---

### [[T04 Arrays & Slice Internals]]

**Blurt check** (cover below, answer from memory):
1. What are the 3 fields in a slice header? Total size on 64-bit?
2. Array vs slice: what's copied on assignment/pass?
3. What happens when append exceeds capacity?
4. Why doesn't the caller see appended elements? (the append trap)
5. What is the three-index slice expression `a[l:h:m]` for?
6. nil slice vs empty slice: how do they differ?
7. `make([]T, 5)` vs `make([]T, 0, 5)` -- what's the difference?
8. How does sub-slicing cause memory leaks?
9. What's the growth formula for slices in Go 1.18+?
10. `[]Struct` vs `[]*Struct` -- which is more cache-friendly and why?

**5-second answer:**
> A slice is a 24-byte header (ptr + len + cap) describing a window into a backing array. Passing copies the header, sharing the array. Append within capacity writes to the shared array; beyond capacity allocates a new array. Growth doubles below 256, smoothly transitions to ~1.25x for large slices. The caller's header is stale after append -- always return and reassign.

> [!info]- Two-line answer (open if you forgot)
> Slice = {ptr, len, cap} (24 bytes). Passing a slice copies the header (24B), not the backing array. Append within capacity writes to the shared array and updates local len; beyond capacity allocates a new, larger array and copies -- the caller's header is stale because it still points to the old array. Always `s = append(s, x)`.
> Three-index `a[l:h:m]` limits capacity to `m-l`, forcing append to allocate rather than overwrite shared data. nil slice (ptr=nil) vs empty slice (ptr=valid) both work with len/cap/append, but JSON marshals differently (null vs []). Sub-slice keeps entire backing array alive for GC -- use `copy()` or `slices.Clone()`. Growth: 2x below 256, smoothly declining to ~1.25x.

**Key visual:**
```
SliceHeader [ptr|len=3|cap=5] ──▶ [1][2][3][_][_]
Append within cap: writes to [3], len→4, SAME array
Append beyond cap: NEW array, old eligible for GC, caller's header stale
```

**Traps to remember:**
- Append in a function: caller's slice header is stale (return + reassign)
- Sub-slice `s2 := s1[2:5]` keeps entire backing array alive (use copy/Clone)
- nil slice (`var s []int`) vs empty slice (`s := []int{}`): JSON marshals differently

**Weak? Drill deeper** → [[revision/T04 Arrays & Slice Internals - Revision]]

---

### [[frameworks/T05 GIN Framework]]

**Blurt check** (cover below, answer from memory):
1. How does Gin's radix tree routing differ from DefaultServeMux?
2. How does c.Next() create the before/after middleware lifecycle?
3. Why is gin.Context not goroutine-safe? What's the fix?
4. Bind vs ShouldBind vs MustBind -- which to use and why?
5. Why should you NOT use r.Run() in production?
6. How does Gin handle concurrent requests? (goroutine model)
7. How would you structure a production Gin API? (layers)
8. How do you implement graceful shutdown with Gin?

**5-second answer:**
> Gin uses httprouter's radix tree for O(log n) routing with path params. Middleware chains execute via c.Next() (before/after pattern). gin.Context is recycled from sync.Pool -- not goroutine-safe, use c.Copy(). In production: ShouldBind for error control, explicit http.Server for timeouts and graceful shutdown.

> [!info]- Two-line answer (open if you forgot)
> Gin routes via a radix tree (compressed trie) compiled at startup -- O(log n) matching with zero allocation. Middleware chain: `[Recovery → Logger → Auth → Handler]`, each calls `c.Next()` to proceed; code after c.Next() runs in reverse on the response path.
> gin.Context is recycled from sync.Pool after each request -- spawning a goroutine with `c` directly reads stale/recycled data. Use `c.Copy()`. In production: use `c.ShouldBind()` (returns error) not `c.Bind()` (auto-responds 400). Never use `r.Run()` -- create explicit `http.Server` with timeouts + graceful shutdown via signal handling.

**Key visual:**
```
Request → [Recovery] → [Logger] → [Auth] → [Handler]
              ↓ c.Next()   ↓ c.Next()  ↓ c.Next()  ↓ (runs)
              ← after       ← after     ← after     ← return
Context: sync.Pool → per-request → recycled (NOT goroutine-safe)
```

**Traps to remember:**
- gin.Context recycled after handler returns -- goroutine reading it gets stale data
- `r.Run()` has no timeouts and no graceful shutdown
- `c.Bind()` auto-responds 400 -- use `c.ShouldBind()` for control

**Weak? Drill deeper** → [[revision/T05 GIN Framework - Revision]]

---

### [[databases/T06 MongoDB]]

**Blurt check** (cover below, answer from memory):
1. Embedding vs referencing -- when to use each?
2. What is the compound index prefix rule? What's ESR?
3. What is the 16MB document limit and how to handle it?
4. bson.D vs bson.M -- when to use which?
5. Why should you avoid transactions when possible?
6. What is write concern w:majority and when do you use it?
7. Why should you NOT create a new mongo.Client per HTTP request?
8. How do you diagnose slow queries? (explain, profiler)
9. What's the difference between replica set and sharding?

**5-second answer:**
> Schema design is driven by query patterns. Embed for 1:few always-read-together; reference for 1:many independent data. Compound indexes follow leftmost prefix (ESR: Equality, Sort, Range). 16MB limit → bucketing or referencing. Transactions have overhead -- prefer schema design. Use w:majority for durability.

> [!info]- Two-line answer (open if you forgot)
> Schema design is query-driven: embed for 1:few always-read-together (atomic reads), reference for 1:many or independently-accessed data. Compound index {a,b,c} supports queries on {a}, {a,b}, {a,b,c} but NOT {b} or {c} alone. ESR = Equality first, Sort next, Range last for optimal index usage.
> 16MB document limit means unbounded arrays must use bucketing or references. Use a single `mongo.Client` at startup (it manages its own connection pool). `bson.D` preserves field order (use for pipelines, sorts); `bson.M` has random order. Transactions add ~2x latency -- design schemas to avoid them. w:majority ensures writes survive primary failure.

**Key visual:**
```
Embed: { user: { name, addresses: [{...}, {...}] } }  ← 1:few, atomic reads
Reference: { order: { userId: ObjectId("...") } }     ← 1:many, independent

Index {a,b,c}: supports {a}, {a,b}, {a,b,c} -- NOT {b} or {c} alone
```

**Traps to remember:**
- Creating new mongo.Client per HTTP request (use single client at startup)
- `bson.M` has random field order -- use `bson.D` for pipelines, sorts, indexes
- "Schemaless" does NOT mean "schema-free" -- you need a migration strategy

**Weak? Drill deeper** → [[revision/T06 MongoDB - Revision]]

---

## Week 1-2: Foundations

Prerequisites first, then main topics. See [[Study Plan]] for the full schedule.

---

### [[prerequisites/P01 Structs & Struct Memory Layout]]

**Blurt check** (cover below, answer from memory):
1. What is a struct? How does it differ from a class?
2. What is the zero value of a struct?
3. What happens when you assign one struct to another?
4. Why does field ordering affect struct size?
5. Can you compare two structs with `==`?
6. What types of fields make a struct non-comparable?
7. How does embedding work? Is it inheritance?

**5-second answer:**
> A struct is a named bundle of typed fields -- Go's replacement for classes. Structs are value types: assignment copies all fields. The compiler inserts padding for alignment, so field order matters for memory size. Two structs are comparable with `==` only if all fields are comparable. Embedding promotes fields and methods but is NOT inheritance.

> [!info]- Two-line answer (open if you forgot)
> Structs are value types: assigning `b = a` copies every field. The compiler pads fields for memory alignment (e.g., uint8 before int64 gets 7 bytes of padding), so ordering fields from largest to smallest minimizes wasted space.
> Structs are comparable with `==` only if ALL fields are comparable -- slices, maps, and functions are not, so a struct containing them causes a compile error. Embedding promotes the inner type's methods and fields to the outer type (delegation, not inheritance -- the receiver stays the inner type).

**Key visual:**
```
type User struct { Age uint8; Score int64 }
Memory: [Age][pad 7 bytes][Score 8 bytes] = 16 bytes
Reorder: [Score 8 bytes][Age][pad 7 bytes] = 16 bytes (same!)
Better:  struct { Score int64; Age uint8 } = only 16 bytes aligned
```

**Traps to remember:**
- Struct with slice/map/func fields is NOT comparable (compile error with `==`)
- `bump(c Counter)` copies c -- the original is unchanged
- Embedding is delegation, not inheritance -- the embedded type's receiver is still the inner type

**Weak? Drill deeper** → [[prerequisites/P01 Structs & Struct Memory Layout]]

---

### [[prerequisites/P02 Methods & Receivers]]

**Blurt check** (cover below, answer from memory):
1. What is a method in Go? How does it differ from a function?
2. Value receiver vs pointer receiver -- what's the key difference?
3. What is T's method set vs *T's method set?
4. When should you use a pointer receiver? (4 cases)
5. What happens when you call a method on a nil pointer?
6. What happens if you mix value and pointer receivers on the same type?

**5-second answer:**
> A method is a function with a receiver parameter. Value receivers get a copy (can't mutate original), pointer receivers get the address (can mutate). T's method set has value-receiver methods only; *T has both. Use pointer receiver when: need mutation, struct is large, consistency with other methods, contains sync.Mutex. Nil pointer receiver won't panic unless you access a field.

> [!info]- Two-line answer (open if you forgot)
> A method is a function bound to a type via a receiver parameter. Value receiver `func (a Account) Deposit()` gets a copy -- modifications are silently lost. Pointer receiver `func (a *Account) Deposit()` gets the address -- can mutate the original.
> T's method set = value-receiver methods only. *T's method set = value + pointer receiver methods. This asymmetry determines interface satisfaction: a value of T can't satisfy an interface that requires a pointer-receiver method. Use pointer receiver for: mutation, large structs, consistency, types containing sync.Mutex.

**Key visual:**
```
func (a Account) Deposit(n int)  → gets COPY → original unchanged
func (a *Account) Deposit(n int) → gets ADDRESS → original mutated

Method set: T  → { value receiver methods }
            *T → { value + pointer receiver methods }
```

**Traps to remember:**
- Value receiver modification is silently lost (no error, no warning)
- Value of type T can't satisfy interface requiring pointer receiver method
- Mixing value/pointer receivers on same type → inconsistent, confuses interface satisfaction

**Weak? Drill deeper** → [[prerequisites/P02 Methods & Receivers]]

---

### [[prerequisites/P03 Mutex & Concurrency Safety Basics]]

**Blurt check** (cover below, answer from memory):
1. What is a mutex? What problem does it solve?
2. What is a critical section?
3. Why should you always use `defer mu.Unlock()`?
4. What happens if you copy a mutex?
5. RWMutex: how many readers can hold the lock at once?
6. Can you upgrade RLock to Lock without releasing first?

**5-second answer:**
> A mutex provides mutual exclusion -- only one goroutine enters the critical section at a time. Always pair Lock() with defer Unlock() to avoid forgetting unlock on error paths. NEVER copy a mutex (pass by pointer or embed). RWMutex allows multiple concurrent readers OR one exclusive writer. Locking twice without unlock = deadlock.

> [!info]- Two-line answer (open if you forgot)
> A mutex ensures only one goroutine accesses a critical section at a time. Always `mu.Lock(); defer mu.Unlock()` -- forgetting unlock blocks all goroutines waiting for that lock forever (deadlock). Never copy a mutex (pass by pointer or embed in struct with pointer receiver).
> RWMutex allows unlimited concurrent readers OR exactly one writer. You cannot upgrade RLock to Lock without releasing first (would deadlock). Copying a struct that contains a mutex copies the lock state -- the copy might be held/unheld in an inconsistent state.

**Key visual:**
```
goroutine A: Lock() → [critical section] → Unlock()
goroutine B: Lock() → blocked... → unblocked → [critical section] → Unlock()

NEVER: func(mu sync.Mutex) ← copies the lock! Use *sync.Mutex
```

**Traps to remember:**
- Copying a struct with mutex field copies the lock state (use pointer)
- Forgetting Unlock = all other goroutines blocked forever
- RWMutex: can't upgrade RLock to Lock (must release first)

**Weak? Drill deeper** → [[prerequisites/P03 Mutex & Concurrency Safety Basics]]

---

### [[prerequisites/P04 Hash Functions & Hashing Basics]]

**Blurt check** (cover below, answer from memory):
1. What does a hash function do?
2. What is a collision and is it a bug?
3. How does Go handle collisions in maps?
4. What is load factor? What's Go's threshold?
5. Why can't slices be map keys?
6. Why does map iteration order change between runs?

**5-second answer:**
> A hash function maps a key to a fixed-size number deterministically. Collisions (two keys, same hash) are normal, not bugs -- Go handles them with chaining (overflow buckets). Load factor is entries/buckets; Go grows at ~6.5 avg per bucket. Only comparable types can be map keys (no slices, maps, or functions). Each map gets a random hash seed to prevent hash-flooding attacks.

> [!info]- Two-line answer (open if you forgot)
> A hash function deterministically maps any key to a fixed-size number. Collisions are inevitable (pigeonhole principle) -- Go handles them by chaining entries in overflow buckets within the same bucket group.
> Load factor = entries / buckets. Go grows the map when average load exceeds ~6.5 per bucket. Only comparable types can be map keys (slices, maps, functions are not comparable). Each map gets a random hash seed at creation, so iteration order is deliberately randomized to prevent code from depending on it.

**Key visual:**
```
key "alice" → hash(seed, "alice") → 0x4A2B → bucket index: 0x4A2B % 8 = 3
key "bob"   → hash(seed, "bob")   → 0x4A2B → same bucket! → chained after alice
```

**Traps to remember:**
- `map[[]int]string` won't compile (slices aren't comparable)
- Map iteration order is random by design (hash seed)
- Different program runs = different hash seeds = different iteration order

**Weak? Drill deeper** → [[prerequisites/P04 Hash Functions & Hashing Basics]]

---

### [[prerequisites/P05 Interfaces Basics]]

**Blurt check** (cover below, answer from memory):
1. What is an interface in Go?
2. How does a type satisfy an interface? Is there an `implements` keyword?
3. What is the error interface? How many methods?
4. When is an interface value nil?
5. What is a type assertion? What happens without comma-ok?
6. What is the typed nil trap?

**5-second answer:**
> An interface is a contract -- a set of method signatures. Types satisfy interfaces implicitly (no `implements` keyword). The `error` interface has one method: `Error() string`. An interface is nil only when BOTH its type and value fields are nil. A nil pointer inside a non-nil interface is NOT nil. Type assertions extract the concrete type: `v, ok := i.(ConcreteType)`.

> [!info]- Two-line answer (open if you forgot)
> An interface is a set of method signatures. Types satisfy interfaces implicitly -- if a type has all the methods, it satisfies the interface. The `error` interface has exactly one method: `Error() string`. Type assertion `v, ok := i.(T)` extracts the concrete type; without comma-ok it panics on mismatch.
> An interface is nil only when BOTH its type and data fields are nil. The typed nil trap: `var p *MyError = nil; var err error = p` -- err is NOT nil because the type field is set to `*MyError`. Always return bare `nil`, never a typed nil pointer through an interface.

**Key visual:**
```
Interface value: [ type | value ]
nil interface:   [ nil  | nil   ] → i == nil is TRUE
typed nil:       [ *Err | nil   ] → i == nil is FALSE  ← THE TRAP
```

**Traps to remember:**
- Returning a typed nil pointer through error interface → non-nil error
- Type assertion without comma-ok panics if wrong type
- Value T can't satisfy interface with pointer receiver methods

**Weak? Drill deeper** → [[prerequisites/P05 Interfaces Basics]]

---

### [[prerequisites/P06 Function Call Stack]]

**Blurt check** (cover below, answer from memory):
1. What is the call stack?
2. What happens when a function is called? When it returns?
3. Why do deferred calls run in LIFO order?
4. How can defer modify return values?
5. What's special about goroutine stacks in Go vs C stacks?
6. When are defer arguments evaluated?

**5-second answer:**
> The call stack is a LIFO structure of frames, one per active function call. Each frame holds local variables, parameters, and return address. Call pushes a frame, return pops it. Defer runs in reverse (LIFO) because deferred functions sit on a stack within the frame. Named return values live in the caller's frame, so defer can modify them. Go goroutine stacks start small (~2-8 KB) and grow automatically by copying to a larger allocation.

> [!info]- Two-line answer (open if you forgot)
> The call stack is a LIFO of frames -- each function call pushes a frame (locals, params, return addr), return pops it. Defer accumulates in a LIFO list within the frame, so they execute in reverse order when the function returns. Defer arguments are evaluated at the defer statement, not when the deferred function runs.
> Named return values live in the caller's frame, so a deferred function can read and modify them (the frame isn't popped yet when defers run). Go stacks start at ~2-8 KB and grow by copying to a larger contiguous allocation -- unlike C's fixed-size stacks, no stack overflow from deep recursion (until memory runs out).

**Key visual:**
```
main() calls A() calls B():
  ┌──────────┐
  │ B() frame │ ← top (current)
  ├──────────┤
  │ A() frame │
  ├──────────┤
  │ main()   │ ← bottom
  └──────────┘
  Return from B → pop → A is current again
```

**Traps to remember:**
- Defer args evaluated at defer statement time, not when defer executes
- Named return values can be modified by defer (lives in frame, not popped yet)
- Infinite recursion → stack overflow (frames never pop)

**Weak? Drill deeper** → [[prerequisites/P06 Function Call Stack]]

---

### [[T07 Pointers & Pointer Semantics]]

**Blurt check** (cover below, answer from memory):
1. What is a pointer's size on 64-bit? What's its zero value?
2. Is Go pass-by-value or pass-by-reference?
3. Pointer receiver vs value receiver -- what's the difference in mutation?
4. What's the method set of T vs *T? Why does it matter for interfaces?
5. When does a pointer cause heap allocation? How to check?
6. What is the typed nil interface trap?
7. What happens when you dereference a nil pointer?
8. Why should you never copy a struct containing sync.Mutex?
9. What's the difference between `*[]int` and `[]*int`?

**5-second answer:**
> A pointer holds a memory address (8 bytes). Go is always pass-by-value -- passing a pointer copies the address. Pointer receivers can modify the struct; value receivers get a copy. T's method set has only value-receiver methods; *T has both -- this determines interface satisfaction. Returning a pointer escapes data to the heap. Key traps: nil dereference panics, typed-nil interface, never copy mutex.

> [!info]- Two-line answer (open if you forgot)
> A pointer is 8 bytes (64-bit), zero value = nil. Go is strictly pass-by-value -- passing a pointer copies the address (8 bytes), not the pointed-to data. Pointer receivers can mutate the original struct; value receivers get a full copy. T's method set has value-receiver methods only; *T has both -- a value T can't satisfy an interface needing pointer-receiver methods.
> Returning a pointer from a function forces the pointed-to data to escape to the heap (verified with `-gcflags="-m"`). Nil dereference panics at runtime. Typed nil trap: `var p *MyError = nil` stored in an `error` interface makes it non-nil. Never copy a struct with sync.Mutex -- the copy holds a stale lock state.

**Key visual:**
```
stack: [ x = 42 ] at 0xA0
       [ p = 0xA0 ]          ← p holds x's address (8 bytes)
*p = 100 → follows 0xA0 → x becomes 100
```

**Traps to remember:**
- Dereferencing nil pointer → panic (check != nil first)
- Typed nil pointer in interface → non-nil interface (return bare nil)
- Value receiver on mutex-containing type → copies the lock (use pointer receiver)

**Weak? Drill deeper** → [[revision/T07 Pointers & Pointer Semantics - Revision]]

---

### [[T08 Map Internals]]

**Blurt check** (cover below, answer from memory):
1. What struct backs every Go map? How many KV pairs per bucket?
2. What triggers map growth? Is it done all at once?
3. Why is map not safe for concurrent access? What happens?
4. Can you take the address of a map value? Why not?
5. What's the tophash array for?
6. What happens when you write to a nil map?
7. What types can be map keys? What can't?
8. Does a map shrink after mass deletion?
9. How do low hash bits and high hash bits work together?

**5-second answer:**
> A Go map is a hash table backed by hmap. 2^B buckets, each holding 8 KV pairs with tophash filters for fast matching. Low hash bits select bucket, top 8 bits filter within it. Growth at load factor 6.5, incremental evacuation. NOT concurrent-safe -- Go panics on detected races. Map values aren't addressable because growth moves entries. Iteration order deliberately randomized.

> [!info]- Two-line answer (open if you forgot)
> Go map = hmap struct with 2^B buckets. Each bucket (bmap) holds 8 key-value pairs plus an 8-byte tophash array for fast probing. Low hash bits select the bucket index; the top 8 bits of the hash are stored in tophash to quickly filter mismatches without comparing full keys.
> Growth triggers at load factor ~6.5 (avg entries per bucket). Growth is incremental -- old buckets evacuated gradually during inserts/deletes. NOT concurrent-safe -- runtime detects races and panics (fatal, not recoverable). Map values aren't addressable because growth reallocates entries. Maps never shrink -- re-create to reclaim memory after mass deletes.

**Key visual:**
```
Bucket: [tophash: h0..h7][keys: k0..k7][values: v0..v7][overflow: *bmap]
hmap: count + B + hash0 + buckets ptr → [bucket0]...[bucket 2^B-1]
```

**Traps to remember:**
- Concurrent map access → fatal panic (use sync.RWMutex or sync.Map)
- Write to nil map → panic (use make())
- Map never shrinks after mass delete (re-create to reclaim memory)

**Weak? Drill deeper** → [[revision/T08 Map Internals - Revision]]

---

### [[T09 Error Handling Patterns]]

**Blurt check** (cover below, answer from memory):
1. What is the error interface? How many methods?
2. What are the three error patterns? (sentinel, custom, wrapping)
3. What's the difference between errors.Is and errors.As?
4. What does %w do in fmt.Errorf that %v doesn't?
5. What is the typed nil error trap?
6. When should you NOT wrap an error?
7. How do you create a custom error type that works with errors.As?
8. Why shouldn't you use panic for normal error handling?

**5-second answer:**
> Go's error is just an interface with `Error() string`. Three patterns: sentinel errors (predefined values, checked with `errors.Is`), custom error types (struct with extra fields, extracted with `errors.As`), and error wrapping (`fmt.Errorf %w` preserves the chain). `errors.Is` walks the unwrap chain comparing values. `errors.As` walks it looking for a matching type. Never use `==` on wrapped errors. Never return a typed nil pointer through an error interface.

> [!info]- Two-line answer (open if you forgot)
> Go's error is `interface { Error() string }`. Three patterns: sentinel errors (`var ErrNotFound = errors.New("not found")`, checked with `errors.Is`), custom error types (struct implementing Error(), extracted with `errors.As`), and wrapping (`fmt.Errorf("context: %w", err)` preserves the chain for unwrapping).
> `errors.Is(err, target)` walks the Unwrap() chain comparing values. `errors.As(err, &target)` walks it looking for a matching type. `%w` wraps (preserves chain); `%v` formats as string (breaks chain). Don't wrap when: error is from a different package's internal detail, or wrapping leaks implementation. Typed nil trap: never return a typed nil pointer through error interface.

**Key visual:**
```
fmt.Errorf("save: %w", fmt.Errorf("validate: %w", ErrRequired))

Unwrap chain: "save: validate: required" → "validate: required" → ErrRequired
errors.Is(err, ErrRequired) → walks chain → true at depth 2
```

**Traps to remember:**
- `==` breaks after wrapping (use `errors.Is` always)
- `%v` formats but doesn't wrap -- `errors.Is` won't find the original
- Typed nil `*MyError` returned as `error` → non-nil interface

**Weak? Drill deeper** → [[revision/T09 Error Handling Patterns - Revision]]

---

### [[T10 Defer, Panic & Recover Internals]]

**Blurt check** (cover below, answer from memory):
1. When are deferred function arguments evaluated?
2. What order do deferred functions execute in?
3. Can deferred functions modify return values? How?
4. Where must recover() be called to work?
5. Can a parent goroutine catch a child goroutine's panic?
6. What happens to defers when os.Exit() is called?
7. Why should you never defer inside a loop?
8. When should you use panic vs returning an error?

**5-second answer:**
> `defer` schedules cleanup to run when the function returns. Three rules: args evaluated at defer time, LIFO execution, can modify named return values. `panic` unwinds the stack, running defers. `recover` only works inside a directly deferred function in the same goroutine. Panics are goroutine-isolated -- unrecovered panic in any goroutine crashes the whole program. Never defer in loops -- accumulates until function returns.

> [!info]- Two-line answer (open if you forgot)
> Three defer rules: (1) arguments evaluated at the defer statement, not when it runs, (2) execute in LIFO order (last deferred = first to run), (3) can modify named return values because named returns live in the frame (not popped when defers run). `recover()` only works inside a directly deferred function in the same goroutine -- not in a nested call, not in a different goroutine.
> Panics are goroutine-isolated: a parent goroutine CANNOT catch a child goroutine's panic. Unrecovered panic in ANY goroutine crashes the entire program. `os.Exit()` bypasses all defers. Defer in a loop accumulates resources until the function returns -- wrap the loop body in a helper function. Use panic only for truly unrecoverable situations (programmer errors), not for expected failures.

**Key visual:**
```
defer A(); defer B(); defer C()
Execution order: C → B → A (LIFO, like a stack of plates)

panic("boom") → run defers (LIFO) → if recover() in defer → stop unwind
                                   → if no recover → crash program
```

**Traps to remember:**
- defer in loop → accumulates all defers, exhausts resources (wrap in helper func)
- recover() not in a defer → always returns nil, does nothing
- os.Exit() bypasses ALL defers -- use return + defer for cleanup

**Weak? Drill deeper** → [[revision/T10 Defer, Panic & Recover Internals - Revision]]

---

### [[T11 Interface Internals (iface & eface)]]

**Blurt check** (cover below, answer from memory):
1. What are the two internal representations of interfaces?
2. What fields does iface have vs eface?
3. What is the itab and what does it cache?
4. When is an interface nil? Why does the typed nil trap exist?
5. What's the method set of T vs *T for interface satisfaction?
6. What happens when you compare two interfaces with uncomparable dynamic types?
7. Why is *io.Reader (pointer to interface) almost always wrong?
8. How big is an interface value in memory?

**5-second answer:**
> Go interfaces are two-word structs. Empty interfaces (any) use eface: {_type, data}. Non-empty interfaces use iface: {tab, data} where tab points to an itab containing method pointers. itabs are cached globally -- computed once per type-interface pair. An interface is nil only when BOTH words are nil. Assigning a typed nil pointer sets the type word, making the interface non-nil. T's method set has value receivers; *T has both.

> [!info]- Two-line answer (open if you forgot)
> Two representations: eface (empty interface / `any`) = {_type, data} (16 bytes); iface (non-empty interface) = {tab, data} (16 bytes). The itab in iface contains: the interface type descriptor, the concrete type descriptor, a hash for type switches, and an array of method pointers. itabs are computed once per (concrete type, interface) pair and cached globally.
> An interface is nil only when both words are nil. Typed nil trap: assigning a `*MyError(nil)` to an `error` interface sets the type word to `*MyError`, making the interface non-nil. Comparing interfaces with uncomparable dynamic types (e.g., slices) panics at runtime. `*io.Reader` is almost always wrong -- you want `io.Reader` (the interface itself is already a pointer-like wrapper).

**Key visual:**
```
eface (any):  [ _type | data ]     ← 16 bytes
iface (Reader): [ tab | data ]     ← 16 bytes
  tab → itab: [ inter | _type | hash | fun[0] fun[1]... ]

nil interface:  [ nil | nil ]      ← true nil
typed nil:      [ *MyErr | nil ]   ← NOT nil (type is set)
```

**Traps to remember:**
- Typed nil pointer in interface → non-nil interface (return bare nil)
- Comparing interfaces with uncomparable dynamic types → panic
- *io.Reader (pointer to interface) is almost always wrong

**Weak? Drill deeper** → [[revision/T11 Interface Internals (iface & eface) - Revision]]

---

### [[T12 Interface Design Principles]]

**Blurt check** (cover below, answer from memory):
1. What does "accept interfaces, return structs" mean?
2. Why should interfaces be small (1-2 methods)?
3. Where should interfaces be defined -- at the producer or consumer?
4. What is interface pollution? Give an example.
5. When should you NOT create an interface?
6. How does interface composition work? (io.ReadWriter example)
7. What's wrong with exporting interfaces prematurely?
8. Why is using `any` everywhere an anti-pattern?

**5-second answer:**
> Go interface design follows three rules: keep interfaces small (1-2 methods like io.Reader), define them at the consumer (not the producer), and never create them "just in case." Return concrete structs from constructors -- let callers define their own narrow interfaces. Interface composition (io.ReadWriter = Reader + Writer) beats fat interfaces. Interface pollution -- creating interfaces for every type -- is the #1 design mistake from Java/C# backgrounds.

> [!info]- Two-line answer (open if you forgot)
> "Accept interfaces, return structs": function parameters should be narrow interfaces (so callers can pass any implementation), but return concrete structs (so callers get full functionality). Define interfaces at the consumer, not the producer -- the consumer knows what methods it needs. Keep interfaces small: io.Reader (1 method) is ideal; 15-method interfaces force tests to mock everything.
> Interface composition (`type ReadWriter interface { Reader; Writer }`) is preferred over fat interfaces. Interface pollution = creating an interface for every struct "just in case" -- this is the #1 Java/C# mistake in Go. Don't create an interface until you have two implementations or need to mock for testing. `any` everywhere defeats Go's type system.

**Key visual:**
```
WRONG (producer-defined fat interface):
  package user → type UserService interface { 15 methods }
  test needs to mock ALL 15

RIGHT (consumer-defined slim interface):
  package billing → type UserGetter interface { GetUser(id) }
  test mocks only 1 method
```

**Traps to remember:**
- Interface for a single implementation = unnecessary indirection
- Exporting interfaces prematurely locks your API surface
- `any` (empty interface) everywhere = no type safety, defeats Go's type system

**Weak? Drill deeper** → [[revision/T12 Interface Design Principles - Revision]]

---

## Week 3-4: Concurrency Core

The most tested area in Go interviews (30-40% of questions).

---

### [[prerequisites/P07 Functions, Closures & Variable Capture]]

**Blurt check** (cover below, answer from memory):
1. Can you assign a function to a variable in Go?
2. What is a closure?
3. Does a closure capture by value or by reference?
4. What is the loop variable trap with goroutines?
5. How do you fix the loop variable trap? (3 ways)
6. Do captured variables escape to heap?

**5-second answer:**
> Functions are first-class values in Go -- assign, pass, return them. A closure is a function that captures variables from its enclosing scope by REFERENCE (pointer to the variable). The loop variable trap: goroutines in a loop all share one loop variable, so they all see the final value. Fix: pass as argument (copy), shadow locally, or use Go 1.22+ loopvar. Captured variables escape to heap.

> [!info]- Two-line answer (open if you forgot)
> A closure is a function literal that captures variables from its enclosing scope by reference (pointer to the variable, not a copy of its value). This means the closure sees the variable's current value at execution time, not at definition time.
> The loop variable trap: `for i := 0; i < 3; i++ { go func() { fmt.Println(i) }() }` -- all goroutines print 3 because they share the same `i`. Fix: pass `i` as a function argument (creates a copy), shadow with `i := i` inside the loop, or use Go 1.22+ per-iteration loop variables. Captured variables escape to heap.

**Key visual:**
```
for i := 0; i < 3; i++ {
    go func() { fmt.Println(i) }()  // all print 3 (or whatever i ends at)
}
Fix: go func(n int) { fmt.Println(n) }(i)  // each gets its own copy
```

**Traps to remember:**
- Closure captures the VARIABLE, not the value at that moment
- Loop variable trap is still asked in interviews (even after Go 1.22 fix)
- Captured vars escape to heap → GC pressure

**Weak? Drill deeper** → [[prerequisites/P07 Functions, Closures & Variable Capture]]

---

### [[prerequisites/P08 OS Threads vs Green Threads]]

**Blurt check** (cover below, answer from memory):
1. What is an OS thread? How big is its stack?
2. What is a context switch and why is it expensive?
3. What is a green thread / goroutine?
4. What is the M:N threading model?
5. What does GOMAXPROCS control?
6. How much cheaper is a goroutine than an OS thread? (rough numbers)

**5-second answer:**
> OS threads are kernel-managed, ~1-8 MB stack, ~1-10 us context switch. Green threads (goroutines) are runtime-managed, ~2-8 KB stack, ~200 ns switch. Go uses M:N model: M goroutines multiplexed onto N OS threads. GOMAXPROCS controls N (defaults to CPU cores). This lets you spawn millions of goroutines cheaply. Goroutine blocking doesn't block the OS thread -- runtime handles it.

> [!info]- Two-line answer (open if you forgot)
> OS threads: kernel-managed, ~1-8 MB fixed stack, ~1-10 us context switch (involves kernel mode switch, TLB flush, register save/restore). Goroutines: runtime-managed, ~2-8 KB initial stack (grows automatically), ~200 ns switch (user-space, no kernel involvement).
> Go's M:N model: M goroutines (millions possible) multiplexed onto N OS threads (GOMAXPROCS, defaults to CPU core count). When a goroutine blocks (I/O, channel, mutex), the runtime parks it and schedules another on the same OS thread -- the OS thread itself doesn't block. This is why Go can handle 100K+ concurrent connections cheaply.

**Key visual:**
```
OS Thread:   ~1-8 MB stack | ~1-10 us switch | kernel-managed
Goroutine:   ~2-8 KB stack | ~200 ns switch  | runtime-managed

M:N: [G1 G2 G3 ... G1M] → multiplexed onto → [M1 M2 ... MN]
     (millions of goroutines)                  (GOMAXPROCS OS threads)
```

**Traps to remember:**
- "Goroutine = OS thread" is WRONG (M:N model, much cheaper)
- CPU-bound goroutine without yields can starve others (preemption helps since 1.14)
- GOMAXPROCS defaults to NumCPU(), not 1 (changed in Go 1.5)

**Weak? Drill deeper** → [[prerequisites/P08 OS Threads vs Green Threads]]

---

### [[T13 Goroutine Internals]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T14 GMP Scheduler]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T15 Channel Internals]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T16 Buffered vs Unbuffered Channels]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T17 Select Statement Internals]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T18 Mutex & RWMutex Internals]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T19 Context Package Internals]]

> *Coming soon -- add block here after completing the topic.*

---

## Week 5-6: Patterns + GC

From knowing primitives to applying them, plus GC for the "production experience" signal.

---

### [[prerequisites/P09 GC Basics & Why It Matters]]

**Blurt check** (cover below, answer from memory):
1. What is garbage collection?
2. What are GC roots?
3. What is tri-color marking? Name the three colors.
4. What is a write barrier?
5. What is the #1 way to reduce GC pressure?
6. Are Go's GC pauses seconds-long like Java's? (rough numbers)

**5-second answer:**
> GC automatically finds and frees unreachable heap objects. Starts from roots (stack vars, globals), marks reachable objects (tri-color: white=unreachable, grey=examining, black=done), sweeps the rest. Go's GC runs mostly concurrently with short STW pauses (~100 us to ~1 ms). Write barriers track pointer updates during concurrent marking. #1 optimization: reduce allocations (stack > heap, reuse objects, sync.Pool).

> [!info]- Two-line answer (open if you forgot)
> GC finds and frees unreachable heap objects. It starts from roots (stack variables, globals, registers), walks all reachable objects using tri-color marking (white = unvisited/garbage, grey = found but children unscanned, black = fully scanned), and sweeps everything still white.
> Go's GC runs mostly concurrently with sub-millisecond STW pauses (~100 us to 1 ms). Write barriers track pointer updates during concurrent marking so the GC doesn't miss newly-created references. #1 optimization: reduce allocations (prefer stack, reuse objects with sync.Pool, pre-allocate slices) -- tuning GOGC is treating the symptom, not the cause.

**Key visual:**
```
Roots: [stack vars] [globals]
         │             │
         ▼             ▼
       [obj A]       [obj B] ──▶ [obj C]
                                     
       [obj D] ← unreachable → swept (freed)

Colors: White=unvisited  Grey=in-progress  Black=done+children-scanned
```

**Traps to remember:**
- `new()` does NOT always allocate on heap (escape analysis decides)
- GC pauses are sub-millisecond in Go, not seconds
- Reducing allocations > tuning GOGC (fix the source, not the symptom)

**Weak? Drill deeper** → [[prerequisites/P09 GC Basics & Why It Matters]]

---

### [[T20 Worker Pool Pattern]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T21 Fan-Out Fan-In Pattern]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T22 Graceful Shutdown]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T23 Goroutine Leak Prevention]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T24 Garbage Collector Deep Dive]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T25 GC Tuning (GOGC & GOMEMLIMIT)]]

> *Coming soon -- add block here after completing the topic.*

---

## Week 7: Production Go

Bridge Go knowledge into system design interviews.

---

### [[T26 net/http Internals]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T27 gRPC with Go]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T28 database/sql & Connection Pooling]]

> *Coming soon -- add block here after completing the topic.*

---

### [[T29 Observability (Logging, Metrics, Tracing)]]

> *Coming soon -- add block here after completing the topic.*

---

## Week 8: Full Revision

No new topics. Use the full daily revision pass, pick weak topics for drill-down, and do mock interviews. See [[Study Plan]] for the week 8 protocol.

---

> **Revision tips:**
> - **Focus topics** (weakest 5): full blurt check + open two-line answer if needed + drill deeper.
> - **Maintenance topics** (strong ones): read 5-second answer only, move on.
> - Rotate daily. Track which topics consistently need the drill-down.
> - If a topic feels solid for 3+ days straight, move it to maintenance.
