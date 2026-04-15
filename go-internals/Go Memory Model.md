
## 1. Concept

Go Memory Model defines how data is stored, passed, and shared across functions and goroutines.

---

## 2. Core Insight (TL;DR)

Go is **strictly pass-by-value**, and the **compiler (via escape analysis)** decides whether data lives on the **stack (fast)** or **heap (GC-managed)**.

---

## 3. Mental Model (Lock this in)

### Stack → “Your Desk”

- Private, fast, auto-cleaned
    
- Lives within function scope
    

---

### Heap → “Shared Storage”

- Used when data outlives function
    
- Managed by GC
    
- Slower due to allocation + scanning
    

---

### Pass-by-value → “Everything is copied”

- Even pointers are copied
    
- Sharing happens only via internal pointers
    

---

## 4. Stack vs Heap (Real Rule)

> **Stack vs Heap decision is made entirely by escape analysis at compile time**

---

## 5. Escape Analysis (Decision Engine)

### Mental Decision Tree

1. Returned from function? → **Heap**
    
2. Shared outside (goroutine, channel, global)? → **Heap**
    
3. Too large (> ~64KB)? → **Heap**
    
4. Size unknown at compile time? → **Heap**
    
5. Stored in interface? → **Often Heap**
    

---

### Example

```go
func foo() *int {
    x := 10
    return &x
}
```

→ escapes → heap

---

### Verify (non-negotiable skill)

```bash
go build -gcflags="-m"
```

---

## 6. Stack Internals (Critical Detail)

- Starts small (~2KB per goroutine)
    
- **Grows dynamically**
    
- Growth = allocate new stack + **copy old data**
    

### Senior Insight:

> Go pointers are **movable**

When stack grows:

- Memory shifts
    
- All pointers are **adjusted**
    

This is why:

> Go disallows pointer arithmetic (unlike C)

---

## 7. Heap + GC Reality

- Managed by **concurrent GC**
    
- Still has **Stop-The-World (STW)** phases
    

### Key cost:

> More heap → more GC scan → more latency

### Critical rule:

> **More pointers = more GC work**

---

## 8. Pass-by-Value (Strict, No Exceptions)

---

### Primitive

```go
func update(x int) {
    x = 20
}
```

---

### Pointer

```go
func update(x *int) {
    *x = 20
}
```

> Pointer is copied, underlying data is shared

---

## 9. Reference-like Types (Actual Truth)

---

### Slice (Most Important)

```go
type slice struct {
    ptr *T
    len int
    cap int
}
```

### Visual Mental Model:

**Slice = Window**

- `ptr` → start of window
    
- `len` → visible area
    
- `cap` → max expansion
    

> Passing slice = copying the **window**, not the data

---

### Behavior

```go
func modify(s []int) {
    s[0] = 100
}
```

→ visible outside

```go
func modify(s []int) {
    s = append(s, 4)
}
```

→ new array possible → NOT visible outside

---

### Map

- Internally pointer to runtime (`hmap`)
    
- Always behaves like shared structure
    

---

### Interface (Senior-Level Detail)

```go
type iface struct {
    tab  *itab
    data unsafe.Pointer
}
```

- Copying interface = copying this struct
    
- Dynamic type may trigger heap allocation
    

### Important nuance:

> Not all interface usage causes escape—but many do

---

## 10. Why This Design Exists

- Stack → fast, cache-friendly
    
- Heap → flexible but GC-heavy
    
- Compiler handles allocation → simpler than C++
    

Goal:

> Performance + simplicity balance

---

## 11. Tradeoffs (What matters in real systems)

### Value types

- ✅ Better cache locality
    
- ✅ Less GC pressure
    
- ❌ Expensive for large structs
    

---

### Pointer types

- ✅ Avoid copying
    
- ❌ Increase GC scanning
    
- ❌ Hurt locality
    
- ❌ Can trigger escapes
    

---

## 12. GC Tax (Non-Negotiable Insight)

> Heap allocations are not free—they create **future GC work**

- GC must **traverse pointers**
    
- More objects → longer mark phase
    
- Leads to latency spikes
    

---

## 13. Critical Edge Cases

---

### Slice append trap

```go
func modify(s []int) {
    s = append(s, 4)
}
```

---

### Loop variable trap (UPDATED)

```go
for _, v := range arr {
    go func() {
        fmt.Println(v)
    }()
}
```

### Pre-Go 1.22:

- Same variable reused → bug
    

### Go 1.22+:

> Loop variable is **per-iteration**

Fix is no longer needed:

```go
v := v // NOT required anymore
```

### Interview line:

> “This was fixed in Go 1.22 at the compiler level.”

---

## 14. Common Misconceptions

- ❌ Go is pass-by-reference → WRONG
    
- ❌ Pointer = always faster → WRONG
    
- ❌ Slice is reference → HALF TRUE
    

Correct:

> Everything is pass-by-value, some values contain pointers

---

## 15. Real-world Impact

- Heap-heavy systems → GC latency spikes
    
- Pointer-heavy design → slower under load
    
- Value semantics → better performance at scale
    

---

## 16. Interview Gold Question

### Q:

`map[string]User` vs `map[string]*User` for 10M users?

### A:

> Use `map[string]User` because storing values reduces pointer count, which reduces GC scan work and improves latency.

---

## 17. Final Verbal Answer

> “Go is strictly pass-by-value. The compiler uses escape analysis to decide whether variables are allocated on the stack or heap. Stack allocation is fast and automatically managed, while heap allocation introduces garbage collection overhead. Types like slices, maps, and interfaces appear reference-like because they contain internal pointers, but they are still passed by value. In high-performance systems, minimizing heap allocations and pointer usage is critical to reducing GC pressure and improving latency.”

---
