# Daily Revision

> Your 8-week master guide: [[Study Plan]]. Check it first to know what to study today.

> Open this every morning. One scroll, top to bottom.
> ~2 min per topic. Cover the "Blurt check" prompts BEFORE reading answers.
> Weak on something? Click the drill-down link at the bottom of each block.

---

### [[T01 Go Type System & Value Semantics]]

**Blurt check** (cover below, answer from memory):
1. What is structural typing and how does Go use it?
2. What are the three questions to ask about any Go type?
3. Why can't a value type satisfy an interface with pointer receiver methods?
4. What is the nil interface trap? Draw the two-field layout.
5. How does embedding differ from inheritance?

**5-second answer:**
> Go is statically typed with structural (implicit) interface satisfaction. Every type has an underlying type, zero value, and method set. Value T only has value-receiver methods; *T has both. Interfaces are two-field structs {type, data} -- a typed nil pointer makes a non-nil interface. Embedding is delegation, not inheritance.

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
2. Stack alloc cost vs heap alloc cost?
3. Is Go pass-by-value or pass-by-reference? What about slices?
4. What is mark assist and why is it worse than STW pauses?
5. How do you reduce GC pressure? (systematic approach)

**5-second answer:**
> Go is strictly pass-by-value. The compiler uses escape analysis to decide stack (~1-2ns, auto-freed) vs heap (~25-50ns, GC-managed). Escape triggers: returned pointer, goroutine/channel, global, unknown size. Mark assist is the real GC bottleneck. Reduce pressure: profile first, sync.Pool, value semantics, pre-allocate, GOMEMLIMIT.

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
1. What are the two fields in StringHeader? Total size?
2. What does `len("cafe")` return and why?
3. Why is `+=` in a loop O(n^2)? What replaces it?
4. How does `strings.Builder.String()` avoid allocation?
5. What happens if you copy a Builder value?

**5-second answer:**
> A string is an immutable 16-byte header (ptr + len) over a UTF-8 byte array. `len()` counts bytes, not characters. `for range` decodes runes. Builder wraps `[]byte` with zero-copy String() via unsafe.String. Substring slicing shares the backing array -- can leak memory.

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

### [[frameworks/T05 GIN Framework]]

**Blurt check** (cover below, answer from memory):
1. How does Gin's radix tree routing differ from DefaultServeMux?
2. How does c.Next() create the before/after middleware lifecycle?
3. Why is gin.Context not goroutine-safe? What's the fix?
4. Bind vs ShouldBind -- which to use and why?
5. Why should you NOT use r.Run() in production?

**5-second answer:**
> Gin uses httprouter's radix tree for O(log n) routing with path params. Middleware chains execute via c.Next() (before/after pattern). gin.Context is recycled from sync.Pool -- not goroutine-safe, use c.Copy(). In production: ShouldBind for error control, explicit http.Server for timeouts and graceful shutdown.

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

**5-second answer:**
> Schema design is driven by query patterns. Embed for 1:few always-read-together; reference for 1:many independent data. Compound indexes follow leftmost prefix (ESR: Equality, Sort, Range). 16MB limit → bucketing or referencing. Transactions have overhead -- prefer schema design. Use w:majority for durability.

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

### [[T04 Arrays & Slice Internals]]

**Blurt check** (cover below, answer from memory):
1. What are the 3 fields in a slice header? Total size?
2. Array vs slice: what's copied on assignment/pass?
3. What happens when append exceeds capacity?
4. Why doesn't the caller see appended elements? (the append trap)
5. What is the three-index slice expression `a[l:h:m]` for?

**5-second answer:**
> A slice is a 24-byte header (ptr + len + cap) describing a window into a backing array. Passing copies the header, sharing the array. Append within capacity writes to the shared array; beyond capacity allocates a new array. Growth doubles below 256, smoothly transitions to ~1.25x for large slices. The caller's header is stale after append -- always return and reassign.

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

### [[prerequisites/P01 Structs & Struct Memory Layout]]

**Blurt check** (cover below, answer from memory):
1. What is a struct? How does it differ from a class?
2. What is the zero value of a struct?
3. What happens when you assign one struct to another?
4. Why does field ordering affect struct size?
5. Can you compare two structs with `==`?

**5-second answer:**
> A struct is a named bundle of typed fields -- Go's replacement for classes. Structs are value types: assignment copies all fields. The compiler inserts padding for alignment, so field order matters for memory size. Two structs are comparable with `==` only if all fields are comparable. Embedding promotes fields and methods but is NOT inheritance.

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
1. What is a method in Go?
2. Value receiver vs pointer receiver -- what's the key difference?
3. What is T's method set vs *T's method set?
4. When should you use a pointer receiver?
5. What happens when you call a method on a nil pointer?

**5-second answer:**
> A method is a function with a receiver parameter. Value receivers get a copy (can't mutate original), pointer receivers get the address (can mutate). T's method set has value-receiver methods only; *T has both. Use pointer receiver when: need mutation, struct is large, consistency with other methods, contains sync.Mutex. Nil pointer receiver won't panic unless you access a field.

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

**5-second answer:**
> A mutex provides mutual exclusion -- only one goroutine enters the critical section at a time. Always pair Lock() with defer Unlock() to avoid forgetting unlock on error paths. NEVER copy a mutex (pass by pointer or embed). RWMutex allows multiple concurrent readers OR one exclusive writer. Locking twice without unlock = deadlock.

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
4. What is load factor?
5. Why can't slices be map keys?

**5-second answer:**
> A hash function maps a key to a fixed-size number deterministically. Collisions (two keys, same hash) are normal, not bugs -- Go handles them with chaining (overflow buckets). Load factor is entries/buckets; Go grows at ~6.5 avg per bucket. Only comparable types can be map keys (no slices, maps, or functions). Each map gets a random hash seed to prevent hash-flooding attacks.

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
2. How does a type satisfy an interface?
3. What is the error interface?
4. When is an interface value nil?
5. What is a type assertion?

**5-second answer:**
> An interface is a contract -- a set of method signatures. Types satisfy interfaces implicitly (no `implements` keyword). The `error` interface has one method: `Error() string`. An interface is nil only when BOTH its type and value fields are nil. A nil pointer inside a non-nil interface is NOT nil. Type assertions extract the concrete type: `v, ok := i.(ConcreteType)`.

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
5. What's special about goroutine stacks in Go?

**5-second answer:**
> The call stack is a LIFO structure of frames, one per active function call. Each frame holds local variables, parameters, and return address. Call pushes a frame, return pops it. Defer runs in reverse (LIFO) because deferred functions sit on a stack within the frame. Named return values live in the caller's frame, so defer can modify them. Go goroutine stacks start small (~2-8 KB) and grow automatically by copying to a larger allocation.

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
2. Pointer receiver vs value receiver — what's the difference in mutation?
3. What's the method set of T vs *T? Why does it matter for interfaces?
4. When does a pointer cause heap allocation? How to check?
5. What is the typed nil interface trap?

**5-second answer:**
> A pointer holds a memory address (8 bytes). Go is always pass-by-value — passing a pointer copies the address. Pointer receivers can modify the struct; value receivers get a copy. T's method set has only value-receiver methods; *T has both — this determines interface satisfaction. Returning a pointer escapes data to the heap. Key traps: nil dereference panics, typed-nil interface, never copy mutex.

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

**5-second answer:**
> A Go map is a hash table backed by hmap. 2^B buckets, each holding 8 KV pairs with tophash filters for fast matching. Low hash bits select bucket, top 8 bits filter within it. Growth at load factor 6.5, incremental evacuation. NOT concurrent-safe — Go panics on detected races. Map values aren't addressable because growth moves entries. Iteration order deliberately randomized.

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

**5-second answer:**
> Go's error is just an interface with `Error() string`. Three patterns: sentinel errors (predefined values, checked with `errors.Is`), custom error types (struct with extra fields, extracted with `errors.As`), and error wrapping (`fmt.Errorf %w` preserves the chain). `errors.Is` walks the unwrap chain comparing values. `errors.As` walks it looking for a matching type. Never use `==` on wrapped errors. Never return a typed nil pointer through an error interface.

**Key visual:**
```
fmt.Errorf("save: %w", fmt.Errorf("validate: %w", ErrRequired))

Unwrap chain: "save: validate: required" → "validate: required" → ErrRequired
errors.Is(err, ErrRequired) → walks chain → true at depth 2
```

**Traps to remember:**
- `==` breaks after wrapping (use `errors.Is` always)
- `%v` formats but doesn't wrap — `errors.Is` won't find the original
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

**5-second answer:**
> `defer` schedules cleanup to run when the function returns. Three rules: args evaluated at defer time, LIFO execution, can modify named return values. `panic` unwinds the stack, running defers. `recover` only works inside a directly deferred function in the same goroutine. Panics are goroutine-isolated — unrecovered panic in any goroutine crashes the whole program. Never defer in loops — accumulates until function returns.

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
- os.Exit() bypasses ALL defers — use return + defer for cleanup

**Weak? Drill deeper** → [[revision/T10 Defer, Panic & Recover Internals - Revision]]

---

### [[T11 Interface Internals (iface & eface)]]

**Blurt check** (cover below, answer from memory):
1. What are the two internal representations of interfaces?
2. What fields does iface have vs eface?
3. What is the itab and what does it cache?
4. When is an interface nil? Why does the typed nil trap exist?
5. What's the method set of T vs *T for interface satisfaction?

**5-second answer:**
> Go interfaces are two-word structs. Empty interfaces (any) use eface: {_type, data}. Non-empty interfaces use iface: {tab, data} where tab points to an itab containing method pointers. itabs are cached globally — computed once per type-interface pair. An interface is nil only when BOTH words are nil. Assigning a typed nil pointer sets the type word, making the interface non-nil. T's method set has value receivers; *T has both.

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
3. Where should interfaces be defined — at the producer or consumer?
4. What is interface pollution? Give an example.
5. When should you NOT create an interface?

**5-second answer:**
> Go interface design follows three rules: keep interfaces small (1-2 methods like io.Reader), define them at the consumer (not the producer), and never create them "just in case." Return concrete structs from constructors — let callers define their own narrow interfaces. Interface composition (io.ReadWriter = Reader + Writer) beats fat interfaces. Interface pollution — creating interfaces for every type — is the #1 design mistake from Java/C# backgrounds.

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

### [[prerequisites/P07 Functions, Closures & Variable Capture]]

**Blurt check** (cover below, answer from memory):
1. Can you assign a function to a variable in Go?
2. What is a closure?
3. Does a closure capture by value or by reference?
4. What is the loop variable trap with goroutines?
5. How do you fix the loop variable trap?

**5-second answer:**
> Functions are first-class values in Go -- assign, pass, return them. A closure is a function that captures variables from its enclosing scope by REFERENCE (pointer to the variable). The loop variable trap: goroutines in a loop all share one loop variable, so they all see the final value. Fix: pass as argument (copy), shadow locally, or use Go 1.22+ loopvar. Captured variables escape to heap.

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
3. What is a green thread?
4. What is the M:N threading model?
5. What does GOMAXPROCS control?

**5-second answer:**
> OS threads are kernel-managed, ~1-8 MB stack, ~1-10 us context switch. Green threads (goroutines) are runtime-managed, ~2-8 KB stack, ~200 ns switch. Go uses M:N model: M goroutines multiplexed onto N OS threads. GOMAXPROCS controls N (defaults to CPU cores). This lets you spawn millions of goroutines cheaply. Goroutine blocking doesn't block the OS thread -- runtime handles it.

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

### [[prerequisites/P09 GC Basics & Why It Matters]]

**Blurt check** (cover below, answer from memory):
1. What is garbage collection?
2. What are GC roots?
3. What is tri-color marking? Name the three colors.
4. What is a write barrier?
5. What is the #1 way to reduce GC pressure?

**5-second answer:**
> GC automatically finds and frees unreachable heap objects. Starts from roots (stack vars, globals), marks reachable objects (tri-color: white=unreachable, grey=examining, black=done), sweeps the rest. Go's GC runs mostly concurrently with short STW pauses (~100 us to ~1 ms). Write barriers track pointer updates during concurrent marking. #1 optimization: reduce allocations (stack > heap, reuse objects, sync.Pool).

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

> **Revision tips:**
> - When you have 15+ topics, split into "focus" (weakest 5) and "maintenance" (strong ones)
> - Focus topics: full blurt check + read answers. Maintenance: 5-second answer only.
> - Rotate daily. Track which topics consistently need the drill-down.
