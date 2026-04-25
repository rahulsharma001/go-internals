# Daily Revision

> Open this every morning. One scroll, top to bottom.
> ~2 min per topic. Cover the "Blurt check" prompts BEFORE reading answers.
> Weak on something? Click the drill-down link at the bottom of each block.

---

### [[Go Type System & Value Semantics]]

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

**Weak? Drill deeper** → [[revision/Go Type System & Value Semantics - Revision]]

---

### [[Go Memory Allocation & Value Semantics]]

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

**Weak? Drill deeper** → [[revision/Go Memory Allocation & Value Semantics - Revision]]

---

### [[Strings, Runes & UTF-8 Internals]]

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

**Weak? Drill deeper** → [[revision/Strings, Runes & UTF-8 Internals - Revision]]

---

### [[frameworks/GIN Framework]]

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

**Weak? Drill deeper** → [[revision/GIN Framework - Revision]]

---

### [[databases/MongoDB]]

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

**Weak? Drill deeper** → [[revision/MongoDB - Revision]]

---

> **Revision tips:**
> - When you have 15+ topics, split into "focus" (weakest 5) and "maintenance" (strong ones)
> - Focus topics: full blurt check + read answers. Maintenance: 5-second answer only.
> - Rotate daily. Track which topics consistently need the drill-down.
