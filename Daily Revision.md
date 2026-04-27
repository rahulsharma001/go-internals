# Daily Revision

> Your 8-week master guide: [[Study Plan]]. Check it first to know what to study today.

> **How to use this file:**
> 1. Open every morning. One scroll, top to bottom.
> 2. Read each question. Try to answer from memory first.
> 3. Tap the question to reveal the 1-2 line answer. Check yourself.
> 4. Still weak after reading the answer? Click "Drill deeper" at the bottom.
> ~2 min per topic. For "maintenance" topics (strong ones), just skim the questions without opening.

---

## Already Completed (Pre-Plan)

These 6 topics were done before the study plan started. Revise daily.

---

### [[T01 Go Type System & Value Semantics]]

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is structural typing? How does Go decide if a type satisfies an interface?
> A type satisfies an interface if it has all the required methods -- no `implements` keyword needed. This is called structural (implicit) typing: the compiler checks the method set, not explicit declarations.

> [!info]- 2. What are the three questions to ask about any Go type?
> (1) What is its underlying type? (2) What is its zero value? (3) What is its method set? These three determine assignability, initialization behavior, and interface satisfaction.

> [!info]- 3. Why can't a value type T satisfy an interface with pointer receiver methods?
> T's method set only has value-receiver methods. *T's method set has both value and pointer receiver methods. Since the interface requires a pointer-receiver method, only *T satisfies it -- a value T is missing that method from its set.

> [!info]- 4. What is the nil interface trap? What are the two fields?
> An interface is a two-field struct: {type, data}. It's nil only when BOTH fields are nil. `var err *MyError = nil; return err` sets the type field to `*MyError`, making the interface non-nil even though the data is nil.

> [!info]- 5. How does embedding differ from inheritance?
> Embedding promotes the inner type's fields and methods to the outer type (delegation). But the method receiver stays the inner type -- it's NOT inheritance. The outer type doesn't "become" the inner type.

> [!info]- 6. What's the difference between `type X int` and `type X = int`?
> `type X int` creates a new defined type -- X has its own identity, can have methods, and requires explicit conversion to/from int. `type X = int` is an alias -- X IS int, no conversion needed, can't add methods.

> [!info]- 7. What is the zero value of a struct, slice, map, interface?
> Struct: all fields at their zero values. Slice: nil (ptr=nil, len=0, cap=0). Map: nil (can read, panic on write). Interface: nil (both type and data fields nil). Pointer: nil.

> [!info]- 8. How does Go achieve polymorphism without classes?
> Through interfaces (behavioral contracts) and embedding (composition/delegation). A function accepting an interface can work with any concrete type that has the right methods. No class hierarchy needed.

> [!info]- 9. What does "accept interfaces, return structs" mean?
> Function parameters should be narrow interfaces (callers can pass any implementation). Return concrete structs (callers get full functionality). This maximizes flexibility for callers while keeping your API concrete.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What are the 4 triggers that cause escape to heap?
> (1) Returning a pointer to a local variable. (2) Sending to a goroutine or channel. (3) Storing in a global/package-level variable. (4) Unknown size at compile time (e.g., `make([]int, n)` where n is runtime).

> [!info]- 2. Stack alloc cost vs heap alloc cost? (rough numbers)
> Stack: ~1-2 ns, auto-freed when function returns (just move the stack pointer). Heap: ~25-50 ns + future GC work to scan and free. Heap is ~25-50x more expensive.

> [!info]- 3. Is Go pass-by-value or pass-by-reference? What about slices and maps?
> Go is strictly pass-by-value. Always. Slices pass a 24-byte header (ptr, len, cap) by value -- the backing array is shared via the pointer. Maps pass an 8-byte pointer to the underlying hmap by value. Both LOOK like pass-by-reference but aren't.

> [!info]- 4. What is mark assist and why is it the real GC bottleneck?
> When a goroutine allocates during a GC cycle, the runtime forces it to help with marking before the allocation proceeds. This adds unpredictable latency to hot paths -- worse than the brief STW pauses because it affects individual request latency.

> [!info]- 5. How do you reduce GC pressure? (systematic approach)
> Profile first with pprof (don't guess). Then: use sync.Pool for reusable objects, prefer value semantics over pointers, pre-allocate slices/maps with known capacity, avoid interface boxing in hot paths, tune GOMEMLIMIT as a last resort.

> [!info]- 6. What is the difference between `new()` and `make()`?
> `new(T)` allocates zeroed memory for type T and returns a `*T`. `make()` only works for slices, maps, and channels -- it initializes the internal data structure (len/cap for slices, hash table for maps, buffer for channels). `new()` may stack-allocate if it doesn't escape.

> [!info]- 7. What does `go build -gcflags="-m"` show you?
> Escape analysis decisions. The compiler tells you which variables escape to heap and why (e.g., "moved to heap: x" or "leaking param: p"). Use `-m -m` for more detail.

> [!info]- 8. What is GOGC and what is GOMEMLIMIT?
> GOGC (default 100) controls how much the heap can grow before the next GC cycle -- 100 means trigger when heap doubles. GOMEMLIMIT (Go 1.19+) is a soft memory cap -- runtime adjusts GC pacing to stay under this budget. Use GOMEMLIMIT for container environments.

> [!info]- 9. What is sync.Pool and when should you use it?
> A per-P pool of reusable objects that reduces heap allocations. Objects may be evicted on GC. Use for short-lived, frequently-allocated objects (buffers, structs) in hot paths. Don't use for objects that need long lifetimes or precise cleanup.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What are the two fields in StringHeader? Total size on 64-bit?
> Pointer to byte array + length (int). Total: 16 bytes on 64-bit. No capacity field (strings are immutable, can't grow).

> [!info]- 2. What does `len("cafe")` return and why?
> Returns 5, not 4. `len()` counts bytes. The accented "e" (U+00E9) is 2 bytes in UTF-8 (0xC3, 0xA9). To count characters: `utf8.RuneCountInString("cafe")` returns 4.

> [!info]- 3. What's the difference between `byte` and `rune`?
> `byte` = alias for `uint8` (one byte, 0-255). `rune` = alias for `int32` (one Unicode code point, can represent any character including multi-byte ones). A single rune may occupy 1-4 bytes in UTF-8.

> [!info]- 4. How does `for range` over a string differ from index-based loop?
> `for range` decodes UTF-8 and yields (byte_index, rune) pairs -- correctly handling multi-byte characters. Index loop `for i := 0; i < len(s); i++` yields raw bytes -- multi-byte chars get split into individual bytes.

> [!info]- 5. Why is `+=` in a loop O(n^2)? What replaces it?
> Each `+=` creates a new string, copying all previous bytes. 100 appends of 10 bytes = ~50KB of wasted copies. Use `strings.Builder` -- it wraps a `[]byte` with amortized O(1) appends.

> [!info]- 6. How does `strings.Builder.String()` avoid allocation?
> It uses `unsafe.String` to create a string header pointing directly at the builder's internal `[]byte` -- zero copy, zero allocation. The builder effectively transfers ownership of the buffer.

> [!info]- 7. What happens if you copy a Builder value?
> The copy panics on write. Builder has a copy-detection mechanism (stores a pointer to itself). After copy, the pointer still points to the original, detecting the mismatch. This prevents two builders from corrupting shared memory.

> [!info]- 8. What is `string(65)` and why is it a trap?
> `string(65)` = "A" (the Unicode character at code point 65), NOT the string "65". To convert the number 65 to "65", use `strconv.Itoa(65)` or `fmt.Sprintf("%d", 65)`.

> [!info]- 9. How does substring slicing cause memory leaks?
> `small := huge[:5]` creates a string header pointing into the same backing array as `huge`. The entire backing array stays alive for GC. Fix: `small := strings.Clone(huge[:5])` to copy into a new, independent allocation.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What are the 3 fields in a slice header? Total size on 64-bit?
> ptr (unsafe.Pointer to backing array) + len (int) + cap (int) = 24 bytes on 64-bit. The header IS the slice value.

> [!info]- 2. Array vs slice: what's copied on assignment/pass?
> Array: the ENTIRE array is copied (value type). `[1000]int` copies 8000 bytes. Slice: only the 24-byte header is copied. Both copies share the same backing array via the pointer.

> [!info]- 3. What happens when append exceeds capacity?
> Runtime allocates a new, larger backing array, copies all existing elements, appends the new elements, and returns a new slice header pointing at the new array. The old array becomes eligible for GC.

> [!info]- 4. Why doesn't the caller see appended elements? (the append trap)
> Slice header is passed by value (24 bytes copied). Append inside a function updates the local copy's len and possibly ptr (if reallocated). The caller's copy still has the old len/ptr. Fix: always return and reassign `s = append(s, x)`.

> [!info]- 5. What is the three-index slice expression `a[l:h:m]` for?
> It limits capacity to `m-l`. Without it, `a[l:h]` has capacity extending to the end of the backing array. With `a[l:h:h]`, capacity = 0 spare slots, so any append forces a new allocation -- preventing overwrite of shared backing data.

> [!info]- 6. nil slice vs empty slice: how do they differ?
> `var s []int` = nil (ptr=nil, len=0, cap=0). `s := []int{}` = non-nil (ptr=valid, len=0, cap=0). Both work with len, cap, append. But: JSON marshals nil as `null`, empty as `[]`. `s == nil` is true only for nil slice.

> [!info]- 7. `make([]T, 5)` vs `make([]T, 0, 5)` -- what's the difference?
> `make([]T, 5)` = 5 zero-valued elements, len=5, cap=5 (ready to index). `make([]T, 0, 5)` = empty, len=0, cap=5 (ready for append without reallocation). Use the first when you know the exact count; second when building up via append.

> [!info]- 8. How does sub-slicing cause memory leaks?
> `s2 := s1[2:5]` creates a header pointing into the same backing array. Even if s1 goes out of scope, the entire backing array stays alive because s2's pointer references it. Fix: `copy()` into a new slice or use `slices.Clone()`.

> [!info]- 9. What's the growth formula for slices in Go 1.18+?
> Below 256 elements: double (2x). At/above 256: `newcap += (newcap + 3*256) / 4` -- smooth transition from 2x down to ~1.25x for large slices. Final capacity rounded up to nearest memory size class.

> [!info]- 10. `[]Struct` vs `[]*Struct` -- which is more cache-friendly and why?
> `[]Struct` stores structs contiguously in memory -- iterating walks sequential addresses (cache-line friendly). `[]*Struct` stores pointers, each dereference is a potential cache miss to a random heap location. Prefer `[]Struct` for iteration-heavy workloads.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. How does Gin's radix tree routing differ from DefaultServeMux?
> DefaultServeMux uses a flat map (O(n) worst case, no path params). Gin uses httprouter's radix tree (compressed trie) compiled at startup -- O(log n) matching with zero allocation, supports path params (`:id`) and wildcards (`*path`).

> [!info]- 2. How does c.Next() create the before/after middleware lifecycle?
> Middleware chain: `[Recovery → Logger → Auth → Handler]`. Each calls `c.Next()` to proceed to the next handler. Code before c.Next() runs on the request path (left to right). Code after c.Next() runs on the response path (right to left, reverse order).

> [!info]- 3. Why is gin.Context not goroutine-safe? What's the fix?
> gin.Context is recycled from sync.Pool after each request completes. If a goroutine holds a reference to `c`, it reads stale/recycled data belonging to a different request. Fix: `cCopy := c.Copy()` creates an independent copy safe for goroutines.

> [!info]- 4. Bind vs ShouldBind vs MustBind -- which to use and why?
> `c.Bind()` / `c.MustBind()` auto-respond with 400 on error (no control). `c.ShouldBind()` returns the error to you -- you decide how to respond. Always use `ShouldBind` in production for proper error handling and consistent API responses.

> [!info]- 5. Why should you NOT use r.Run() in production?
> `r.Run()` wraps `http.ListenAndServe` with no read/write timeouts and no graceful shutdown. Use an explicit `http.Server{Addr, Handler: r, ReadTimeout, WriteTimeout}` with signal-based graceful shutdown.

> [!info]- 6. How does Gin handle concurrent requests?
> Gin runs on top of Go's net/http server, which spawns one goroutine per request. Gin's router and middleware chain execute within that goroutine. The radix tree is read-only after startup, so it's safe for concurrent access.

> [!info]- 7. How would you structure a production Gin API? (layers)
> Router (routes + middleware groups) → Handler (parse request, call service, write response) → Service (business logic) → Repository (database access). Each layer has its own interface for testability. Keep handlers thin.

> [!info]- 8. How do you implement graceful shutdown with Gin?
> Create explicit `http.Server`. Listen for OS signals (SIGINT, SIGTERM) in a goroutine. On signal, call `srv.Shutdown(ctx)` with a timeout context -- this stops accepting new connections and waits for in-flight requests to finish.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. Embedding vs referencing -- when to use each?
> Embed for 1:few relationships that are always read together (atomic reads, single document). Reference for 1:many or many:many, independently accessed data, or documents that grow unboundedly. Schema design is driven by query patterns, not normalization.

> [!info]- 2. What is the compound index prefix rule? What's ESR?
> Compound index {a,b,c} supports queries on {a}, {a,b}, {a,b,c} but NOT {b} or {c} alone (leftmost prefix rule). ESR = Equality first, Sort next, Range last -- this ordering maximizes index efficiency.

> [!info]- 3. What is the 16MB document limit and how to handle it?
> Each BSON document is capped at 16MB. For unbounded arrays (e.g., chat messages), use the bucket pattern (fixed-size sub-documents) or reference pattern (separate collection with foreign key).

> [!info]- 4. bson.D vs bson.M -- when to use which?
> `bson.D` = ordered slice of key-value pairs (preserves field order). `bson.M` = unordered map (random field order). Use `bson.D` for pipelines, sorts, index definitions where order matters. `bson.M` for simple filters.

> [!info]- 5. Why should you avoid transactions when possible?
> MongoDB transactions add ~2x latency and hold locks across multiple operations. Prefer designing schemas so operations are single-document atomic writes. Transactions should be the fallback, not the default.

> [!info]- 6. What is write concern w:majority and when do you use it?
> `w:majority` means the write is acknowledged only after a majority of replica set members confirm it. Use for critical data (financial transactions, user records). It ensures writes survive primary failure but adds latency.

> [!info]- 7. Why should you NOT create a new mongo.Client per HTTP request?
> `mongo.Client` manages its own connection pool internally. Creating one per request = TCP handshake + auth + TLS per request. Use a single client at application startup, share it across handlers.

> [!info]- 8. How do you diagnose slow queries?
> Use `.Explain("executionStats")` to see query plan (IXSCAN = good, COLLSCAN = bad). Enable the database profiler (`db.setProfilingLevel(1, {slowms: 100})`). Check for missing indexes, large document scans, and unselective queries.

> [!info]- 9. What's the difference between replica set and sharding?
> Replica set = copies of the same data across multiple nodes (high availability, read scaling). Sharding = splitting data across multiple nodes by shard key (horizontal scaling for writes and storage). They're often used together.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is a struct? How does it differ from a class?
> A struct is a named bundle of typed fields -- Go's replacement for classes. No inheritance, no constructors, no access modifiers (just exported/unexported via capitalization). Behavior is added through methods with receivers.

> [!info]- 2. What is the zero value of a struct?
> Every field set to its own zero value: 0 for numbers, "" for strings, nil for pointers/slices/maps, false for bools. A zero-value struct is always valid -- Go designs APIs around this.

> [!info]- 3. What happens when you assign one struct to another?
> Full copy of every field (value semantics). `b := a` copies all fields. Modifying `b` does not affect `a`. This includes nested value-type fields, but pointer/slice/map fields still share their backing data.

> [!info]- 4. Why does field ordering affect struct size?
> The compiler inserts padding bytes for memory alignment (e.g., uint8 before int64 needs 7 padding bytes). Ordering fields from largest to smallest alignment minimizes wasted padding.

> [!info]- 5. Can you compare two structs with `==`?
> Only if ALL fields are comparable types. Slices, maps, and functions are not comparable -- a struct containing them causes a compile error with `==`. Use `reflect.DeepEqual` as a fallback.

> [!info]- 6. What types of fields make a struct non-comparable?
> Slices (`[]T`), maps (`map[K]V`), and functions (`func(...)`). If any field is one of these, the struct can't be used with `==`, as a map key, or in a `switch` case.

> [!info]- 7. How does embedding work? Is it inheritance?
> `type Outer struct { Inner }` promotes Inner's fields and methods to Outer. But it's delegation, NOT inheritance -- Inner's method receiver is still Inner, not Outer. Outer doesn't "become" Inner for type assertions.

**Key visual:**
```
type User struct { Age uint8; Score int64 }
Memory: [Age][pad 7 bytes][Score 8 bytes] = 16 bytes
Better: struct { Score int64; Age uint8 } = 16 bytes (same alignment, less waste)
```

**Traps to remember:**
- Struct with slice/map/func fields is NOT comparable (compile error with `==`)
- `bump(c Counter)` copies c -- the original is unchanged
- Embedding is delegation, not inheritance -- the embedded type's receiver is still the inner type

**Weak? Drill deeper** → [[prerequisites/P01 Structs & Struct Memory Layout]]

---

### [[prerequisites/P02 Methods & Receivers]]

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is a method in Go? How does it differ from a function?
> A method is a function with a receiver parameter bound to a type: `func (a Account) Deposit(n int)`. It's syntactic sugar -- the compiler transforms it into a function with the receiver as the first argument.

> [!info]- 2. Value receiver vs pointer receiver -- what's the key difference?
> Value receiver `func (a Account)` gets a COPY -- modifications are silently lost. Pointer receiver `func (a *Account)` gets the ADDRESS -- can mutate the original. This is the #1 Go gotcha for beginners.

> [!info]- 3. What is T's method set vs *T's method set?
> T (value type) method set = only value-receiver methods. *T (pointer type) method set = value + pointer receiver methods. This asymmetry determines which interfaces T vs *T can satisfy.

> [!info]- 4. When should you use a pointer receiver? (4 cases)
> (1) Need to mutate the receiver. (2) Struct is large (avoid copy overhead). (3) Consistency -- if one method needs pointer, use pointer for all. (4) Struct contains sync.Mutex or similar non-copyable fields.

> [!info]- 5. What happens when you call a method on a nil pointer?
> The method is called normally -- it doesn't panic until you try to access a field through the nil pointer. You can write nil-safe methods that check `if a == nil` first.

> [!info]- 6. What happens if you mix value and pointer receivers on the same type?
> It's inconsistent and confusing. A value T can only satisfy interfaces whose methods are all value-receiver. Mixing means some interfaces work with T, others only with *T. Convention: pick one and stick with it.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is a mutex? What problem does it solve?
> Mutual exclusion -- ensures only one goroutine accesses a critical section (shared resource) at a time. Without it, concurrent reads and writes cause data races with unpredictable results.

> [!info]- 2. What is a critical section?
> The code between Lock() and Unlock() that accesses shared state. Only one goroutine can be inside the critical section at a time. Keep it as small as possible to minimize contention.

> [!info]- 3. Why should you always use `defer mu.Unlock()`?
> If any code path between Lock() and Unlock() panics or returns early, the mutex stays locked forever -- deadlocking all other goroutines waiting for it. `defer` guarantees unlock happens regardless of how the function exits.

> [!info]- 4. What happens if you copy a mutex?
> The copy gets a snapshot of the lock state -- it might be held, unheld, or corrupted. Two goroutines now think they hold different locks but might not. Never copy a mutex -- pass by pointer or embed with pointer receiver methods.

> [!info]- 5. RWMutex: how many readers can hold the lock at once?
> Unlimited concurrent readers (RLock). But only ONE writer (Lock) at a time, and a writer blocks all readers. Use when reads far outnumber writes.

> [!info]- 6. Can you upgrade RLock to Lock without releasing first?
> No -- this deadlocks. The goroutine holds RLock and waits for Lock, but Lock waits for all RLocks to release. You must RUnlock() first, then Lock(). Between those calls, state may have changed.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What does a hash function do?
> Maps any input (key) to a fixed-size number deterministically. Same input always gives same output. Different inputs may give same output (collision). Used to compute bucket indices in hash tables.

> [!info]- 2. What is a collision and is it a bug?
> Two different keys hashing to the same value. Not a bug -- it's mathematically inevitable (pigeonhole principle: more possible keys than hash values). Hash tables must handle collisions gracefully.

> [!info]- 3. How does Go handle collisions in maps?
> Chaining with overflow buckets. Each bucket holds 8 KV pairs. When a bucket is full, an overflow bucket is allocated and linked. The tophash array (top 8 bits of hash) allows fast filtering before full key comparison.

> [!info]- 4. What is load factor? What's Go's threshold?
> Load factor = total entries / total buckets. Higher load = more collisions = slower lookups. Go triggers map growth when average load exceeds ~6.5 entries per bucket.

> [!info]- 5. Why can't slices be map keys?
> Slices are not comparable (can't use `==`). Go requires map keys to be comparable types. This excludes slices, maps, and functions. Arrays ARE comparable and CAN be map keys.

> [!info]- 6. Why does map iteration order change between runs?
> Each map gets a random hash seed at creation. Different seed = different bucket assignments = different iteration order. Go deliberately randomizes to prevent code from depending on a specific order.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is an interface in Go?
> A set of method signatures that defines a behavioral contract. Any type that has all the methods automatically satisfies the interface. Interfaces are the primary mechanism for abstraction and polymorphism in Go.

> [!info]- 2. How does a type satisfy an interface? Is there an `implements` keyword?
> No `implements` keyword. Satisfaction is implicit (structural typing). If a type has all the methods the interface requires, it satisfies it. The compiler checks at assignment/call time.

> [!info]- 3. What is the error interface? How many methods?
> `type error interface { Error() string }` -- exactly one method. Any type with an `Error() string` method is an error. This is Go's entire error handling foundation.

> [!info]- 4. When is an interface value nil?
> Only when BOTH its internal fields (type and data) are nil. If you assign a typed nil pointer to an interface, the type field is set -- the interface is NOT nil even though the data is nil.

> [!info]- 5. What is a type assertion? What happens without comma-ok?
> `v, ok := i.(ConcreteType)` extracts the concrete type from an interface. If the type doesn't match: with comma-ok, ok=false and v is zero value. Without comma-ok (`v := i.(T)`), it panics.

> [!info]- 6. What is the typed nil trap?
> `var p *MyError = nil; var err error = p` -- err is NOT nil because the type field is set to `*MyError`. Always return bare `nil` from error-returning functions, never a typed nil pointer.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is the call stack?
> Every function call gets its own workspace called a frame. The call stack is the pile of these frames. The frame on top is whoever's running right now. Think of cafeteria trays — you only touch the top one.

> [!info]- 2. What happens when you call a function? When it returns?
> Calling pushes a new frame on top (with arguments, local variables, and a "go back to" address). Returning pops that frame — its local variables are gone. The caller picks up where it left off.

> [!info]- 3. Why do defers run in reverse order?
> They stack up like plates. The last defer you registered is on top, so it runs first. This makes cleanup nest correctly: if you open a transaction then open a file, the file closes first, then the transaction rolls back.

> [!info]- 4. How can defer modify what the caller receives?
> Only with named return values. Named returns like `(err error)` are real variables in the function's frame. A defer can read and change them before the function truly exits — so the caller gets the modified value.

> [!info]- 5. What's different about goroutine stacks?
> Each goroutine has its own stack, starting small (~2-8 KB) and growing automatically. Two goroutines running the same function have completely separate stacks and separate local variables.

> [!info]- 6. When does defer capture argument values?
> At the `defer` line, NOT when the defer actually runs. `defer fmt.Println(x)` captures x's value right now. If x changes later, the deferred call still uses the old value. Use a closure to read the variable live.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is a pointer's size on 64-bit? What's its zero value?
> 8 bytes (holds a 64-bit memory address). Zero value = nil. Dereferencing a nil pointer panics at runtime.

> [!info]- 2. Is Go pass-by-value or pass-by-reference?
> Strictly pass-by-value. Always. Passing a pointer copies the address (8 bytes), not the data. The called function gets its own copy of the pointer, but both copies point to the same memory.

> [!info]- 3. Pointer receiver vs value receiver -- what's the difference in mutation?
> Pointer receiver `func (a *Account)` gets the address -- can mutate the original struct. Value receiver `func (a Account)` gets a full copy -- modifications are silently lost and don't affect the caller.

> [!info]- 4. What's the method set of T vs *T? Why does it matter for interfaces?
> T's method set: value-receiver methods only. *T's method set: value + pointer receiver methods. A value T can't satisfy an interface that requires a pointer-receiver method. This determines interface satisfaction.

> [!info]- 5. When does a pointer cause heap allocation? How to check?
> When the pointed-to data outlives the function (escape analysis decides). Common trigger: returning a pointer to a local variable. Check with `go build -gcflags="-m"` -- it prints escape decisions.

> [!info]- 6. What is the typed nil interface trap?
> `var p *MyError = nil; var err error = p` -- err is NOT nil. The interface's type field is set to `*MyError` even though the data is nil. Always return bare `nil`, not a typed nil pointer through an interface.

> [!info]- 7. What happens when you dereference a nil pointer?
> Runtime panic: "invalid memory address or nil pointer dereference." Always check `if p != nil` before dereferencing. This is a common crash cause in production Go code.

> [!info]- 8. Why should you never copy a struct containing sync.Mutex?
> Copying the struct copies the mutex's internal state. The copy might appear unlocked when the original is locked (or vice versa). This causes races. Always use pointer receivers on mutex-containing types.

> [!info]- 9. What's the difference between `*[]int` and `[]*int`?
> `*[]int` = pointer to a slice (rarely needed -- slices are already reference-like headers). `[]*int` = slice of pointers to ints (common for optional/nullable values or shared references).

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What struct backs every Go map? How many KV pairs per bucket?
> `hmap` struct (runtime/map.go). Contains count, B (log2 of bucket count), hash seed, and a pointer to 2^B buckets. Each bucket (`bmap`) holds exactly 8 key-value pairs plus an overflow pointer.

> [!info]- 2. What triggers map growth? Is it done all at once?
> Growth triggers when load factor exceeds ~6.5 (avg entries/bucket) or too many overflow buckets exist. Growth is incremental -- old buckets are evacuated gradually during subsequent inserts and deletes, not all at once.

> [!info]- 3. Why is map not safe for concurrent access? What happens?
> The runtime has a concurrent-access detector. If two goroutines access the same map without synchronization and at least one writes, the runtime panics with a fatal error (not recoverable with recover()). Use sync.RWMutex or sync.Map.

> [!info]- 4. Can you take the address of a map value? Why not?
> No. `&m["key"]` doesn't compile. Map values aren't addressable because the map may grow/reorganize at any time, moving entries to new memory. A stored pointer would become dangling.

> [!info]- 5. What's the tophash array for?
> An 8-byte array at the start of each bucket storing the top 8 bits of each key's hash. Allows fast filtering -- if tophash doesn't match, skip the expensive full key comparison. Most lookups in a bucket check only 1-2 tophash bytes.

> [!info]- 6. What happens when you write to a nil map?
> Panic: "assignment to entry in nil map." A nil map can be read from (returns zero value, ok=false) but not written to. Always initialize with `make(map[K]V)` or a literal before writing.

> [!info]- 7. What types can be map keys? What can't?
> Keys must be comparable (support `==`). Allowed: all basic types, arrays, structs (if all fields comparable), pointers, channels, interfaces. NOT allowed: slices, maps, functions.

> [!info]- 8. Does a map shrink after mass deletion?
> No. The bucket array never shrinks. After deleting millions of entries, the memory stays allocated. To reclaim it, create a new map and copy the remaining entries. This is a known Go limitation.

> [!info]- 9. How do low hash bits and high hash bits work together?
> Low hash bits select the bucket index (`hash & (2^B - 1)`). High 8 bits are stored as tophash inside the bucket for fast filtering. Together they provide O(1) average-case lookup: bucket selection + fast probe.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is the error interface? How many methods?
> `type error interface { Error() string }` -- exactly one method. Any type that implements `Error() string` is an error. Go's entire error system is built on this simple interface.

> [!info]- 2. What are the three error patterns?
> (1) Sentinel errors: predefined package-level variables like `io.EOF`, checked with `errors.Is`. (2) Custom error types: structs with extra context, extracted with `errors.As`. (3) Error wrapping: `fmt.Errorf("context: %w", err)` preserves the original for unwrapping.

> [!info]- 3. What's the difference between errors.Is and errors.As?
> `errors.Is(err, target)` walks the Unwrap() chain comparing values (for sentinels). `errors.As(err, &target)` walks the chain looking for a matching TYPE and populates the target (for custom error types with extra fields).

> [!info]- 4. What does %w do in fmt.Errorf that %v doesn't?
> `%w` wraps the error: the result has an Unwrap() method that returns the original. `errors.Is` and `errors.As` can find it in the chain. `%v` just formats as string -- the original error is lost, chain is broken.

> [!info]- 5. What is the typed nil error trap?
> `var e *MyError = nil; return e` returns a non-nil `error` interface because the type field is set to `*MyError`. Always return bare `nil` from error-returning functions, not a typed nil pointer.

> [!info]- 6. When should you NOT wrap an error?
> When wrapping would leak internal implementation details (e.g., database errors exposed to HTTP handlers). When the error is from an unstable/internal package -- wrapping couples your API to their error types. Return a new sentinel or custom error instead.

> [!info]- 7. How do you create a custom error type that works with errors.As?
> Define a struct implementing `Error() string`. Optionally implement `Unwrap() error` to chain a cause. Then `errors.As(err, &myErrVar)` will match and populate it when found in the chain.

> [!info]- 8. Why shouldn't you use panic for normal error handling?
> Panics unwind the stack and crash the goroutine (and the program if unrecovered). They're for unrecoverable programmer errors, not expected failures. Expected failures (file not found, invalid input) should return errors.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. When are deferred function arguments evaluated?
> At the defer statement, NOT when the deferred function executes. `defer fmt.Println(x)` captures x's current value immediately. Use a closure `defer func() { fmt.Println(x) }()` to capture the latest value.

> [!info]- 2. What order do deferred functions execute in?
> LIFO (last-in, first-out). Last deferred = first to run. `defer A(); defer B(); defer C()` → executes C, B, A. Like a stack of plates.

> [!info]- 3. Can deferred functions modify return values? How?
> Yes, but only named return values. Named returns live in the caller's frame, accessible to deferred functions before the frame is popped. Common pattern: `defer func() { err = wrap(err) }()`.

> [!info]- 4. Where must recover() be called to work?
> Directly inside a deferred function in the same goroutine. NOT in a non-deferred function, NOT in a nested call inside a defer, NOT in a different goroutine. `defer func() { r := recover() }()` is the pattern.

> [!info]- 5. Can a parent goroutine catch a child goroutine's panic?
> No. Panics are goroutine-isolated. An unrecovered panic in ANY goroutine crashes the entire program. The parent has no mechanism to catch it. Always add recover() inside goroutines that might panic.

> [!info]- 6. What happens to defers when os.Exit() is called?
> os.Exit() terminates the process immediately -- ALL defers are bypassed. No cleanup runs. If you need cleanup, use `return` from main() and put cleanup in deferred calls, or handle OS signals.

> [!info]- 7. Why should you never defer inside a loop?
> Defers don't run until the enclosing function returns. In a loop, they accumulate for every iteration -- file handles, DB connections, etc. stack up until the function returns. Wrap the loop body in a helper function so defers run per-iteration.

> [!info]- 8. When should you use panic vs returning an error?
> Return errors for expected failures (invalid input, file not found, network timeout). Panic only for truly unrecoverable programmer errors (index out of bounds, nil pointer in a "can't happen" path). Libraries should almost never panic.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What are the two internal representations of interfaces?
> eface (empty interface / `any`): for interfaces with zero methods. iface (non-empty interface): for interfaces with one or more methods. Both are two-word (16-byte) structs.

> [!info]- 2. What fields does iface have vs eface?
> eface = {_type, data}: type descriptor + pointer to data. iface = {tab, data}: itab pointer (contains method table + type info) + pointer to data. Both are 16 bytes on 64-bit.

> [!info]- 3. What is the itab and what does it cache?
> itab maps a (concrete type, interface) pair to a method table. Contains: the interface type descriptor, the concrete type descriptor, a hash for type switches, and an array of function pointers for the interface's methods. itabs are computed once and cached globally.

> [!info]- 4. When is an interface nil? Why does the typed nil trap exist?
> An interface is nil only when BOTH words (type and data) are nil. The trap: assigning a typed nil (`*MyError(nil)`) sets the type word, making the interface non-nil even though data is nil. The two-field structure makes this unavoidable.

> [!info]- 5. What's the method set of T vs *T for interface satisfaction?
> T: value-receiver methods only. *T: value + pointer receiver methods. This determines which interfaces a type satisfies. A value of T can't satisfy an interface requiring pointer-receiver methods.

> [!info]- 6. What happens when you compare two interfaces with uncomparable dynamic types?
> Runtime panic. If the dynamic types stored in the interfaces are not comparable (e.g., slices), `==` panics. The compiler can't catch this since the dynamic type is only known at runtime.

> [!info]- 7. Why is *io.Reader (pointer to interface) almost always wrong?
> `io.Reader` is already a two-word struct containing a pointer to the data. `*io.Reader` is a pointer to that struct -- an unnecessary extra indirection. Interfaces are designed to be passed by value.

> [!info]- 8. How big is an interface value in memory?
> 16 bytes on 64-bit (two 8-byte words). Both eface and iface. Regardless of how large the concrete type is -- the data word is a pointer to the actual value (which may be heap-allocated if it doesn't fit in a pointer).

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What does "accept interfaces, return structs" mean?
> Function parameters: narrow interfaces (callers can pass any implementation). Return types: concrete structs (callers get full functionality). This maximizes caller flexibility while keeping your API concrete and predictable.

> [!info]- 2. Why should interfaces be small (1-2 methods)?
> Smaller interfaces are easier to implement, easier to mock in tests, and more reusable. io.Reader (1 method) is implemented by files, network connections, buffers, etc. A 15-method interface forces every consumer to depend on everything.

> [!info]- 3. Where should interfaces be defined -- at the producer or consumer?
> At the consumer. The consumer knows what methods it needs. The producer returns a concrete struct. This prevents the producer from imposing a fat interface that most consumers don't need.

> [!info]- 4. What is interface pollution? Give an example.
> Creating interfaces for every type "just in case" -- especially one-to-one interface-to-struct mappings copied from Java/C#. Example: `type UserService interface` mirroring every method of `type userService struct`. Unnecessary indirection with zero benefit.

> [!info]- 5. When should you NOT create an interface?
> When there's only one implementation and no testing need. When the interface just mirrors a concrete type. When you're doing it "for future flexibility" without a current consumer. Wait until you have two implementations or a testing need.

> [!info]- 6. How does interface composition work?
> `type ReadWriter interface { Reader; Writer }` embeds two interfaces. A type satisfies ReadWriter if it has all methods from both Reader and Writer. This is Go's alternative to fat interfaces -- compose small ones.

> [!info]- 7. What's wrong with exporting interfaces prematurely?
> Exported interfaces are part of your public API contract -- once published, you can't add methods without breaking all implementations. Keep interfaces unexported until you're sure of the contract. Export concrete types freely.

> [!info]- 8. Why is using `any` everywhere an anti-pattern?
> `any` (empty interface) bypasses Go's type system -- you lose compile-time type checking and need runtime assertions everywhere. It makes code harder to read, maintain, and debug. Use specific interfaces or generics instead.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. Can you assign a function to a variable in Go?
> Yes. Functions are first-class values. `f := func(x int) int { return x*2 }` assigns an anonymous function. You can also assign named functions: `f := strings.ToUpper`. Pass them as arguments, return them from functions.

> [!info]- 2. What is a closure?
> A function literal that captures (closes over) variables from its enclosing scope. The closure holds a reference to the variable, not a copy of its value. It can read and modify the original variable.

> [!info]- 3. Does a closure capture by value or by reference?
> By reference (pointer to the variable). The closure sees the variable's current value at the time it executes, not at the time it was defined. This is why the loop variable trap exists.

> [!info]- 4. What is the loop variable trap with goroutines?
> `for i := 0; i < 3; i++ { go func() { fmt.Println(i) }() }` -- all goroutines print 3 (the final value of i). They all share a reference to the same `i` variable, and by the time they run, the loop has finished.

> [!info]- 5. How do you fix the loop variable trap? (3 ways)
> (1) Pass as argument: `go func(n int) { fmt.Println(n) }(i)` (copies current value). (2) Shadow locally: `i := i` inside the loop creates a new variable per iteration. (3) Go 1.22+ per-iteration loop variables (automatic fix).

> [!info]- 6. Do captured variables escape to heap?
> Yes. If a closure outlives the function that created the captured variable (e.g., returned or sent to a goroutine), the variable escapes to heap. This adds GC pressure.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is an OS thread? How big is its stack?
> A kernel-managed unit of execution with its own stack (~1-8 MB, fixed at creation). Creating/destroying threads is expensive (kernel calls). Limited to thousands per process.

> [!info]- 2. What is a context switch and why is it expensive?
> Saving one thread's CPU state (registers, program counter, stack pointer) and restoring another's. Expensive because it involves kernel mode transition, TLB flush, and cache pollution. ~1-10 microseconds for OS threads.

> [!info]- 3. What is a green thread / goroutine?
> A user-space thread managed by the Go runtime, not the kernel. ~2-8 KB initial stack (grows automatically). ~200 ns context switch (user-space only). Can create millions cheaply.

> [!info]- 4. What is the M:N threading model?
> M goroutines multiplexed onto N OS threads. Go's runtime scheduler maps many goroutines (M) to a smaller number of OS threads (N). This gives the concurrency of many goroutines with the parallelism of multiple CPU cores.

> [!info]- 5. What does GOMAXPROCS control?
> The number of OS threads (N) that can execute goroutines simultaneously. Defaults to the number of CPU cores. Setting it to 1 gives concurrency (interleaving) but not parallelism (simultaneous execution).

> [!info]- 6. How much cheaper is a goroutine than an OS thread?
> Stack: ~2-8 KB vs ~1-8 MB (1000x smaller). Switch: ~200 ns vs ~1-10 us (50x faster). Creation: ~300 ns vs ~10+ us. This allows millions of goroutines vs thousands of threads per process.

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

**Blurt check** (try from memory, tap to reveal):

> [!info]- 1. What is garbage collection?
> Automatic memory management. The runtime finds and frees heap objects that are no longer reachable from any live variable (stack, globals, registers). Eliminates manual free() and use-after-free bugs.

> [!info]- 2. What are GC roots?
> Starting points for reachability analysis: stack variables in all goroutines, global/package-level variables, and CPU registers. Every object reachable from a root (directly or through pointers) is alive; everything else is garbage.

> [!info]- 3. What is tri-color marking? Name the three colors.
> White = unvisited (assumed garbage). Grey = discovered but children not yet scanned. Black = fully scanned (alive, all children queued). After marking: everything still white is unreachable → swept (freed).

> [!info]- 4. What is a write barrier?
> A small piece of code injected by the compiler on every pointer write during a GC cycle. It notifies the GC when a pointer changes, preventing the GC from missing newly-created references during concurrent marking.

> [!info]- 5. What is the #1 way to reduce GC pressure?
> Reduce allocations. Prefer stack over heap (escape analysis), reuse objects with sync.Pool, pre-allocate slices/maps, use value semantics to avoid pointer boxing. Tuning GOGC/GOMEMLIMIT treats the symptom, not the cause.

> [!info]- 6. Are Go's GC pauses seconds-long like Java's?
> No. Go's STW pauses are sub-millisecond (~100 us to 1 ms). Most GC work happens concurrently with the application. The real latency issue is mark assist (goroutines forced to help GC during allocation), not STW pauses.

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
> - **Focus topics** (weakest 5): go through all questions, open answers you miss, then drill deeper.
> - **Maintenance topics** (strong ones): skim questions without opening -- if you can answer all mentally, move on.
> - Rotate daily. Track which topics consistently need the drill-down.
> - If a topic feels solid for 3+ days straight, move it to maintenance.
