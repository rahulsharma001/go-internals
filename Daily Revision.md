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

> **Revision tips:**
> - When you have 15+ topics, split into "focus" (weakest 5) and "maintenance" (strong ones)
> - Focus topics: full blurt check + read answers. Maintenance: 5-second answer only.
> - Rotate daily. Track which topics consistently need the drill-down.
