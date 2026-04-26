# Go Terms Glossary

> Quick reference for abbreviations, runtime struct names, and technical terms used across the notes.
> Every term is expanded with its full form and a one-line plain-English meaning.

---

## Runtime & Compiler Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| GC | Garbage Collector | Background system that automatically frees memory you're no longer using |
| STW | Stop-The-World | A brief pause where ALL goroutines are frozen so the GC can do bookkeeping (sub-millisecond in Go) |
| GMP | Goroutine-Machine-Processor | Go's scheduler model: G = goroutine, M = OS thread, P = logical processor with a run queue |
| AST | Abstract Syntax Tree | Tree-shaped representation of your source code that the compiler analyzes |
| SSA | Static Single Assignment | Compiler intermediate form where each variable is assigned exactly once — enables optimizations |
| GOGC | Go Garbage Collection ratio | Environment variable controlling how aggressively GC runs (default 100 = trigger when heap doubles) |
| GOMEMLIMIT | Go Memory Limit | Soft memory cap (Go 1.19+) — runtime adjusts GC pacing to stay under this budget |

## Runtime Struct Names

| Term | What It Is | Plain-English Meaning |
|------|------------|------------------------|
| iface | Interface with methods (runtime struct) | Two-field struct: {pointer to method table, pointer to actual data} — how Go stores typed interfaces |
| eface | Empty interface (runtime struct) | Two-field struct: {pointer to type info, pointer to data} — how Go stores `any` / `interface{}` |
| itab | Interface Table | Cached lookup table mapping a concrete type to an interface's method addresses — avoids repeated lookups |
| hmap | Hash Map | The runtime struct backing every `map[K]V` — contains buckets, hash seed, count, and overflow pointers |
| bmap | Bucket Map | Individual bucket in a map — holds up to 8 key-value pairs plus tophash bytes for fast probing |
| sudog | Pseudo-G (waiting goroutine) | A goroutine that's parked waiting on a channel send or receive operation |
| g | Goroutine struct | Runtime representation of a goroutine — contains stack info, status, scheduling state |
| m | Machine struct | Runtime representation of an OS thread |
| p | Processor struct | Logical processor with its own run queue of goroutines — GOMAXPROCS controls how many exist |
| mcache | M-Cache | Per-P cache of small memory spans — avoids locking the central allocator for small allocations |
| mcentral | M-Central | Central free list for a specific size class — shared across all P's, requires locking |
| mheap | M-Heap | The global heap manager — allocates large spans and manages page-level memory |
| mspan | M-Span | A contiguous run of memory pages managed by the heap — the basic unit of Go's memory allocator |
| hchan | Hash Channel | The runtime struct backing every channel — contains a circular buffer, send/recv queues, mutex |

## Performance & Measurement Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| p50 | 50th Percentile (median) | Half of all requests are faster than this value |
| p99 | 99th Percentile | 99% of requests are faster than this value — measures worst-case typical experience |
| p999 | 99.9th Percentile | Only 1 in 1000 requests is slower than this — measures tail latency |
| allocs/op | Allocations per operation | How many heap allocations a single operation triggers — fewer = less GC pressure |
| ns/op | Nanoseconds per operation | How long a single operation takes in benchmark — lower is faster |

## Memory & Allocation Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| Escape analysis | — | Compiler's decision process for whether a variable lives on the stack (fast, auto-freed) or heap (slower, GC-managed) |
| Stack | — | Per-goroutine private memory, auto-cleaned on function return (~1-2ns allocation) |
| Heap | — | Shared memory managed by the garbage collector (~25-50ns allocation + future GC work) |
| Write barrier | — | Hidden runtime check on pointer writes during GC — preserves the tri-color marking invariant |
| Mark assist | — | When a goroutine allocating during GC is forced to help with marking before its allocation proceeds — the real cause of tail latency |
| Tri-color marking | — | GC algorithm: objects are White (unvisited), Grey (visited but children unscanned), Black (fully scanned). Remaining White = garbage. |
| Size class | — | Predefined memory sizes (8B, 16B, 32B, ..., 32KB) the allocator uses — avoids fragmentation |
| Tiny allocator | — | Special fast path for allocations ≤ 16 bytes with no pointers — packs multiple tiny objects into one 16-byte block |

## String & Encoding Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| StringHeader | reflect.StringHeader | Two-field struct (Data pointer + Len int) backing every Go string — always 16 bytes on 64-bit |
| UTF-8 | Unicode Transformation Format — 8-bit | Variable-width encoding where each Unicode character uses 1-4 bytes. Co-designed by Rob Pike and Ken Thompson (Go's creators) |
| Rune | — | Alias for `int32` representing a single Unicode code point (U+0000 to U+10FFFF) |
| Code point | — | A unique number assigned to each character in Unicode (e.g., U+0041 = 'A', U+1F600 = '😀') |
| Grapheme cluster | — | One visual character as perceived by a human — may be composed of multiple runes (e.g., base char + combining accent) |
| U+FFFD | Unicode Replacement Character | The character Go produces when decoding invalid UTF-8 bytes in a range loop |
| NFC | Normalization Form Canonical Composition | Unicode normalization that composes characters into precomposed forms (é as one code point) |
| NFD | Normalization Form Canonical Decomposition | Unicode normalization that decomposes characters (é as e + combining accent) |
| .rodata | Read-Only Data section | Section of the compiled binary where string literals are stored — immutable at runtime |
| strings.Builder | — | Mutable byte buffer optimized for string construction — uses zero-copy String() method |

## Array & Slice Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| SliceHeader | reflect.SliceHeader | Three-field struct (Data pointer + Len int + Cap int) backing every Go slice — always 24 bytes on 64-bit |
| Backing array | — | The actual contiguous memory block that a slice's pointer field references — shared between sub-slices |
| growslice | runtime.growslice | Runtime function called when append needs a larger backing array — allocates, copies, returns new slice |
| nextslicecap | runtime.nextslicecap | Runtime function that calculates the new capacity during slice growth — uses threshold of 256 |
| Size class | — | Predefined memory sizes the allocator uses — growslice rounds up to the nearest one, so actual cap may exceed calculated value |
| Three-index slice | `a[low:high:max]` | Full slice expression that limits capacity to `max-low` — prevents append from overwriting shared backing data |
| nil slice | `var s []int` | Slice with nil pointer, len=0, cap=0 — valid for append/len/cap but marshals to JSON `null` |
| Empty slice | `s := []int{}` | Slice with non-nil pointer, len=0, cap=0 — marshals to JSON `[]` |
| slices.Clone | slices.Clone (Go 1.21+) | Creates an independent copy of a slice — equivalent to make+copy but cleaner |
| copy() | — | Built-in that copies elements between slices — returns number of elements copied (min of src/dst length) |

## Go Language Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| Defined type | `type X int` | Creates a brand-new type with its own identity and method set — `X` and `int` are distinct |
| Type alias | `type X = int` | Just another name for the same type — `X` IS `int`, no conversion needed |
| Underlying type | — | The base type in a type definition — `type Celsius float64` has underlying type `float64` |
| Zero value | — | The default value Go assigns to every variable — `0` for numbers, `""` for strings, `nil` for pointers/slices/maps |
| Method set | — | The set of methods available on a type — determines which interfaces it satisfies |
| Value receiver | `func (t T) Method()` | Method gets a COPY of the value — can't modify the original |
| Pointer receiver | `func (t *T) Method()` | Method gets the memory address — CAN modify the original |
| Embedding | `type Outer struct { Inner }` | Composition: Inner's fields and methods are promoted to Outer — NOT inheritance |
| Interface satisfaction | — | A type satisfies an interface if it has all the required methods — implicit, no `implements` keyword |

## Pointer Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| &x | Address-of operator | Returns the memory address of variable x — gives you a pointer to x |
| *p | Dereference operator | Follows the pointer p to read or write the value it points to |
| *T | Pointer to T | A variable that holds the memory address of a value of type T — always 8 bytes on 64-bit |
| nil pointer | — | A pointer that holds address 0x0 — dereferencing it causes a runtime panic |
| Addressable | — | A value whose memory address can be taken with &. Map values and bare return values are NOT addressable |
| weak.Pointer[T] | Weak pointer (Go 1.24+) | A pointer that doesn't prevent garbage collection — returns nil if the target is collected |

## Struct & Method Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| Struct | — | A named bundle of typed fields -- Go's replacement for classes. Value type: assignment copies all fields |
| Padding | Memory alignment padding | Invisible spacer bytes the compiler inserts between struct fields so each field sits on a CPU-friendly boundary |
| Alignment | — | The memory address rule: a field of size N must start at an address divisible by N (e.g., int64 at 8-byte boundary) |
| Anonymous struct | — | A struct type defined inline without a name -- useful for one-off JSON unmarshaling or test tables |
| Struct tag | — | Metadata string after a field type (e.g., `` `json:"name"` ``) -- read by packages like encoding/json via reflection |
| Struct embedding | `type Outer struct { Inner }` | Including one struct type inside another without a field name -- promotes Inner's fields and methods to Outer |
| Promoted field | — | A field from an embedded struct that can be accessed directly on the outer struct without naming the embedded type |
| Receiver | — | The value or pointer a method is attached to -- appears before the method name: `func (r Receiver) Method()` |
| Method expression | `T.Method` | A function value that takes the receiver as its first argument -- `T.Method` becomes `func(T)` |
| Method value | `instance.Method` | A function value bound to a specific receiver instance -- `x.Method` becomes `func()` with x captured |

## Hash & Map Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| Hash function | — | A deterministic function that maps any key to a fixed-size number -- same key always gives same number |
| Collision | Hash collision | When two different keys map to the same hash value -- normal, not a bug, handled by chaining or probing |
| Chaining | Separate chaining | Collision resolution: each bucket is a linked list of entries that hashed to the same index |
| Open addressing | — | Collision resolution: on collision, probe the next bucket slot (linear probing, quadratic, etc.) |
| Load factor | — | Ratio of entries to buckets -- Go maps grow when average entries per bucket exceeds ~6.5 |
| Hash seed | — | Random value mixed into hash computation -- different per map instance, prevents hash-flooding attacks |
| aeshash | AES hardware-accelerated hash | Go's hash function for strings on CPUs with AES instructions -- fast and well-distributed |

## Function & Closure Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| First-class function | — | Functions are values: you can assign them to variables, pass as arguments, and return from other functions |
| Anonymous function | Function literal | A function defined without a name, inline: `func() { ... }` |
| Closure | — | A function that captures variables from its enclosing scope -- holds references (pointers) to those variables |
| Capture by reference | — | How Go closures work: the closure gets a pointer to the outer variable, not a copy of its value |
| Loop variable trap | — | Classic bug: goroutines in a loop all share one loop variable and see its final value, not the value at creation |
| loopvar | Go 1.22 loop variable fix | Starting Go 1.22, each loop iteration gets its own copy of the variable, eliminating the trap by default |

## OS & Threading Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| OS thread | Kernel thread | Thread managed by the operating system -- has its own stack (~1-8 MB), expensive to create and switch |
| Context switch | — | Saving one thread's state and loading another's -- costs ~1-10 microseconds for OS threads |
| Green thread | User-space thread | Thread managed by the language runtime, not the kernel -- cheaper to create and switch than OS threads |
| M:N model | M-to-N threading | Multiplexing M user-space threads onto N OS threads -- Go's approach with goroutines |
| TLB | Translation Lookaside Buffer | CPU cache for virtual-to-physical address mappings -- flushed on context switch, making switches expensive |

## Call Stack Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| Call stack | — | LIFO structure of stack frames, one per active function call -- grows on call, shrinks on return |
| Stack frame | — | Block of memory holding a function's local variables, parameters, and return address |
| Stack overflow | — | Error when the call stack exceeds its limit -- usually caused by infinite recursion |
| Contiguous stack | — | Go's stack model: when a goroutine's stack needs to grow, it's copied to a larger allocation (not segmented) |
| Named return value | — | Return variable declared in the function signature -- lives in the caller's frame, modifiable by defer |

## Concurrency Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| Goroutine | — | Lightweight thread managed by Go's runtime — costs ~2-8 KB stack, can run millions |
| Channel | — | Typed pipe for goroutines to communicate — can be buffered (queue) or unbuffered (handshake) |
| Mutex | Mutual Exclusion lock | Only one goroutine can hold it at a time — protects shared data from concurrent access |
| RWMutex | Read-Write Mutex | Multiple readers OR one writer — optimizes for read-heavy workloads |
| Data race | — | Two goroutines access the same memory concurrently, at least one writing, with no synchronization |
| Happens-before | — | The formal ordering guarantee: if A happens-before B, then B sees A's memory writes |
| GOMAXPROCS | Go Max Processors | How many OS threads can execute goroutines simultaneously — defaults to number of CPU cores |

## Database Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| BSON | Binary JSON | MongoDB's binary-encoded JSON format — more efficient than text JSON, supports typed fields |
| ObjectId | — | 12-byte unique identifier in MongoDB — contains timestamp + random + counter, generated client-side |
| WiredTiger | — | MongoDB's default storage engine since v3.2 — handles B-tree indexes, document-level locking, compression |
| Aggregation Pipeline | — | MongoDB's data processing framework — documents flow through stages ($match, $group, $sort) like Unix pipes |
| Replica Set | — | Group of MongoDB servers maintaining the same data — one primary (writes), multiple secondaries (reads/failover) |
| Shard Key | — | Field used to distribute data across shards — bad choice = hotspots, can't change easily |
| Write Concern | — | Durability guarantee level — `w:1` (primary ack), `w:majority` (most nodes ack), `w:0` (no ack) |
| COLLSCAN | Collection Scan | MongoDB scanning every document — equivalent of SQL full table scan, means missing index |
| IXSCAN | Index Scan | MongoDB using an index to find documents — what you want to see in explain() output |

## Framework Terms

| Term | Full Form | Plain-English Meaning |
|------|-----------|------------------------|
| Radix Tree | Compressed Trie | Data structure Gin uses for O(log n) route matching — pre-compiled at startup, zero allocation |
| gin.Context | — | Per-request object wrapping request, response, params, key-value store — NOT goroutine-safe |
| Handler Chain | — | Ordered slice of middleware + handler functions — executed sequentially with c.Next() for nesting |
| c.Next() | — | Yields to next handler in chain — code after c.Next() runs in response phase (reverse order) |
| c.Abort() | — | Stops remaining handlers from executing — sets chain index to sentinel, but current function continues |
| ShouldBindJSON | — | Deserialize + validate JSON body to struct — returns error (unlike BindJSON which auto-responds 400) |
| gin.H | — | Shortcut for `map[string]any` — convenience type for JSON responses |

---

> This glossary is updated as new notes are added. If you encounter a term not listed here, check the specific topic's note or the [[Roadmap]].
