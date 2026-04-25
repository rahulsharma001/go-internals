# T03 Strings, Runes & UTF-8 Internals

> **Reading Guide**: Sections 1-3 and 6 are essential first read (20 min).
> Sections 4-5 deepen understanding (15 min).
> Sections 7-12 are interview-specific — read closer to interview day.
> Section 13 is your comprehensive interview Q&A bank → [[questions/T03 Strings, Runes & UTF-8 Internals - Interview Questions]]
> Something not clicking? → [[simplified/T03 Strings, Runes & UTF-8 Internals - Simplified]]

---

## 1. Concept

A Go **string** is an immutable, read-only sequence of bytes — not characters, not runes, not Unicode code points — just raw bytes. The runtime represents it as a two-word **StringHeader** (pointer to byte data + length). Runes (`int32`) decode those bytes into Unicode code points. **UTF-8** is the variable-width encoding that bridges the two: it tells you how many bytes each rune consumes (1-4).

---

## 2. Core Insight (TL;DR)

**Go strings are byte arrays with a UTF-8 interpretation, not character arrays.** `len(s)` returns bytes, `s[i]` returns a byte, and only `for range` over a string decodes runes. Every "string is characters" assumption from other languages will bite you. The StringHeader is just **16 bytes** (pointer + length) on 64-bit systems, making string passing essentially free — you're always copying the header, never the data.

---

## 3. Mental Model (Lock this in)

Think of a Go string as a **read-only window into a byte array**. The window (StringHeader) is tiny — just a pointer and a size. The actual bytes sit somewhere in memory (often in the binary's `.rodata` section for string literals).

```
StringHeader (16 bytes on amd64)
┌─────────────────────────────────┐
│  Data  *byte  │   Len  int     │
│  0xc000010020 │      5         │
└───────┬───────┴────────────────┘
        │
        ▼
  Backing byte array (immutable)
  ┌─────┬─────┬─────┬─────┬─────┐
  │ 'h' │ 'e' │ 'l' │ 'l' │ 'o' │
  │ 0x68│ 0x65│ 0x6c│ 0x6c│ 0x6f│
  └─────┴─────┴─────┴─────┴─────┘
```

Now consider a multi-byte string like `"café"`:

```
  Backing byte array (5 bytes, NOT 4)
  ┌─────┬─────┬─────┬─────┬─────┐
  │ 'c' │ 'a' │ 'f' │ 0xC3│ 0xA9│
  │  1B │  1B │  1B │  2B for 'é' │
  └─────┴─────┴─────┴───────────┘
  len("café") = 5    (bytes)
  RuneCount  = 4     (characters)
```

**UTF-8 is a variable-width encoding.** Each rune takes 1-4 bytes:

| Byte Count | Range | Examples |
|---|---|---|
| 1 byte | U+0000 – U+007F | ASCII: `a`, `Z`, `7`, `!` |
| 2 bytes | U+0080 – U+07FF | `é`, `ñ`, `ü`, `ä` |
| 3 bytes | U+0800 – U+FFFF | `中`, `日`, `한`, `₹` |
| 4 bytes | U+10000 – U+10FFFF | `😀`, `🎉`, `𝕳` |

> **Coming from PHP:** PHP strings are also byte sequences, and `strlen()` returns bytes just like Go's `len()`. But PHP has `mb_strlen()` as a separate function. In Go, the equivalent is `utf8.RuneCountInString()`. The key difference: PHP's string functions default to single-byte (Latin-1), and you need `mb_*` functions for multi-byte. Go's `for range` natively handles UTF-8 — there's no separate "multibyte" mode. Also, PHP strings are mutable (`$s[0] = 'H'` works); Go strings are **immutable** — you must convert to `[]byte` or `[]rune` first.

---

## 4. How It Actually Works (Internals) [INTERMEDIATE → ADVANCED]

### 4.1 The StringHeader Runtime Struct

Every Go string is represented at runtime by `reflect.StringHeader` (deprecated in favor of `unsafe.StringData` in Go 1.20+):

```go
// reflect package (pre-1.20 view)
type StringHeader struct {
    Data uintptr  // pointer to UTF-8 byte data
    Len  int      // byte length (NOT rune count)
}
```

On 64-bit systems: `sizeof(StringHeader) = 16 bytes` always.

When you pass a string to a function, Go copies this 16-byte header — never the underlying bytes. This is why string passing is cheap and why there's no need for `*string` parameters.

### 4.2 Where String Data Lives

| String Source | Memory Location | GC Managed? |
|---|---|---|
| String literals (`"hello"`) | `.rodata` section of binary | No — lives forever |
| `string(byteSlice)` | Heap allocation | Yes |
| Substring `s[i:j]` | Same backing array as `s` | Shares reference |
| `strings.Builder.String()` | Takes ownership of builder's buffer | Yes |
| `fmt.Sprintf(...)` | Heap allocation | Yes |

### 4.3 Immutability Enforcement

Go enforces string immutability at the compiler level. There is no runtime check — the compiler simply refuses to generate code that writes to a string's backing array. The only way around this is `unsafe.Pointer`, which breaks the immutability contract.

```go
s := "hello"
s[0] = 'H' // COMPILE ERROR: cannot assign to s[0] (strings are immutable)
```

### 4.4 UTF-8 Encoding Internals

UTF-8 uses a prefix-code scheme that's self-synchronizing:

```
1-byte:  0xxxxxxx                            (ASCII, 0x00-0x7F)
2-byte:  110xxxxx 10xxxxxx                    (0x80-0x7FF)
3-byte:  1110xxxx 10xxxxxx 10xxxxxx           (0x800-0xFFFF)
4-byte:  11110xxx 10xxxxxx 10xxxxxx 10xxxxxx  (0x10000-0x10FFFF)
```

The leading bits tell the decoder how many bytes to consume:
1. Starts with `0`? → 1-byte rune (ASCII)
2. Starts with `110`? → 2-byte rune, read 1 continuation byte
3. Starts with `1110`? → 3-byte rune, read 2 continuation bytes
4. Starts with `11110`? → 4-byte rune, read 3 continuation bytes
5. Starts with `10`? → This is a continuation byte, not a rune start

This prefix scheme means you can jump into the middle of a UTF-8 string and re-synchronize — you'll never mistake a continuation byte (`10xxxxxx`) for a rune start.

### 4.5 How `for range` Decodes Runes

When you write `for i, r := range s`, the compiler generates a call to `runtime.decoderune()` at each iteration:

```
Decoding "café" (bytes: 63 61 66 C3 A9)

Iteration 1: i=0, look at byte 0x63
  Leading bits: 0... → 1-byte rune
  r = 'c' (U+0063), advance 1 byte

Iteration 2: i=1, look at byte 0x61
  Leading bits: 0... → 1-byte rune
  r = 'a' (U+0061), advance 1 byte

Iteration 3: i=2, look at byte 0x66
  Leading bits: 0... → 1-byte rune
  r = 'f' (U+0066), advance 1 byte

Iteration 4: i=3, look at byte 0xC3
  Leading bits: 110... → 2-byte rune
  Read continuation byte 0xA9 (10 101001)
  Combine: 00011 101001 = U+00E9
  r = 'é' (U+00E9), advance 2 bytes

Done: i would be 5, which equals len(s)
```

Key observation: **the index `i` in `for range` is the byte offset, not the rune index.** This catches people who expect sequential 0, 1, 2, 3 indices.

### 4.6 Zero-Copy Substring Slicing

`s[i:j]` creates a new StringHeader pointing into the same backing array:

```
s := "Hello, World!"

sub := s[7:12]   // "World"

s header:     { Data: 0x1000, Len: 13 }
sub header:   { Data: 0x1007, Len: 5  }
                       ▲
                       └── 0x1000 + 7 = 0x1007

Both point to the SAME bytes in memory. No copy.
```

This is O(1) time and O(1) memory. But beware: `sub` keeps the entire original string alive in memory (the GC won't free the 13 bytes even though you only need 5).

### 4.7 String Comparison

The runtime compares strings with an optimized path:

```
Are string lengths equal?
1. Different lengths? → Not equal (O(1) short-circuit)
2. Same Data pointer? → Equal (O(1) — same string)
3. Same length, different pointer? → memcmp byte-by-byte (O(n), often SIMD-accelerated)
```

> **Coming from PHP:** PHP's `===` strict comparison for strings also compares byte-by-byte, but PHP strings carry no length field — they use NUL-termination internally (with a separate length for binary safety). Go's length-first comparison is faster for the mismatch case.

---

## 5. Key Rules & Behaviors

1. **`len(s)` returns byte count, not rune count.** Always. No exceptions. Use `utf8.RuneCountInString(s)` for character count.

2. **`s[i]` returns a `byte`, not a `rune`.** For multi-byte characters, you get one piece of the encoding, not the character.

3. **`for range s` iterates runes**, automatically decoding UTF-8. The index variable is the byte offset, not the rune index.

4. **`for i := 0; i < len(s); i++` iterates bytes.** This is almost never what you want for text processing.

5. **Strings are immutable.** Assignment to `s[i]` is a compile error. Convert to `[]byte` or `[]rune` to modify, then convert back.

6. **`string(n)` where `n` is an integer creates a one-rune string**, not the numeric representation. `string(65)` is `"A"`, not `"65"`. Use `strconv.Itoa(65)` for `"65"`.

7. **String concatenation with `+` is O(n)** — it allocates a new string every time. In a loop, this becomes O(n^2). Use `strings.Builder` instead.

8. **Substring slicing `s[i:j]` is zero-copy** — it shares the backing array. The original string is kept alive by the GC even if you only hold the substring.

9. **`[]byte(s)` and `string(b)` each allocate and copy.** The only safe zero-copy path uses `unsafe` (Go 1.20+: `unsafe.StringData`, `unsafe.String`).

10. **Invalid UTF-8 in range loop produces `U+FFFD`** (Unicode Replacement Character, `\uFFFD`) for each bad byte.

11. **`rune` is `int32`, `byte` is `uint8`.** Single quotes create rune literals: `'a'` is `rune(97)`. Double quotes create strings: `"a"` is `string`.

---

## 6. Code Examples (Show, Don't Tell)

### Example 1: `len()` trap — bytes vs runes

```go
package main

import (
    "fmt"
    "unicode/utf8"
)

func main() {
    s := "Hello, 世界!"  // mixed ASCII + CJK + ASCII
    fmt.Println(len(s))                    // 13
    fmt.Println(utf8.RuneCountInString(s)) // 9
}
```

```
Step 1: s = "Hello, 世界!"
  Bytes: H  e  l  l  o  ,     世(3B)  界(3B) !
         48 65 6C 6C 6F 2C 20 E4B896  E7958C 21
         1  2  3  4  5  6  7  8 9 10  11 12  13

Step 2: len(s) = 13 bytes

Step 3: RuneCountInString(s) = 9 runes
  Runes: H  e  l  l  o  ,     世  界  !
         1  1  1  1  1  1  1   3  3  1  = 13 bytes total
```

### Example 2: Byte indexing vs rune indexing

```go
package main

import "fmt"

func main() {
    s := "café"
    fmt.Printf("byte s[3] = %c (%x)\n", s[3], s[3])   // not 'é'
    fmt.Printf("rune []rune(s)[3] = %c\n", []rune(s)[3]) // 'é'
}
```

```
Step 1: s = "café"
  Bytes:  c    a    f    0xC3  0xA9
  Index:  [0]  [1]  [2]  [3]   [4]

Step 2: s[3] = 0xC3 = 195 = 'Ã'  <-- THIS is the trap!
  We got the FIRST byte of the 2-byte UTF-8 encoding of 'é'
  Not the character 'é' itself

Step 3: []rune(s) = ['c', 'a', 'f', 'é']
  Index:             [0]  [1]  [2]  [3]
  []rune(s)[3] = 'é' (U+00E9)  <-- correct
```

### Example 3: `for range` vs index-based loop

```go
package main

import "fmt"

func main() {
    s := "Go是好的"

    fmt.Println("--- byte loop ---")
    for i := 0; i < len(s); i++ {
        fmt.Printf("  i=%d byte=%x\n", i, s[i])
    }

    fmt.Println("--- range loop ---")
    for i, r := range s {
        fmt.Printf("  i=%d rune=%c (U+%04X)\n", i, r, r)
    }
}
```

```
--- byte loop --- (11 iterations)
  i=0 byte=47   (G)
  i=1 byte=6f   (o)
  i=2 byte=e6   (first byte of 是)
  i=3 byte=98   (second byte of 是)
  i=4 byte=af   (third byte of 是)
  i=5 byte=e5   (first byte of 好)
  i=6 byte=a5   (second byte of 好)
  i=7 byte=bd   (third byte of 好)
  i=8 byte=e7   (first byte of 的)
  i=9 byte=9a   (second byte of 的)
  i=10 byte=84  (third byte of 的)

--- range loop --- (5 iterations)
  i=0 rune=G (U+0047)      <-- byte offset 0
  i=1 rune=o (U+006F)      <-- byte offset 1
  i=2 rune=是 (U+662F)     <-- byte offset 2, next will skip to 5
  i=5 rune=好 (U+597D)     <-- byte offset 5, skipped 3,4
  i=8 rune=的 (U+7684)     <-- byte offset 8, skipped 6,7

Key: i jumps from 2 → 5 → 8 because CJK runes are 3 bytes each
```

### Example 4: `string(int)` surprise

```go
package main

import (
    "fmt"
    "strconv"
)

func main() {
    n := 65
    fmt.Println(string(n))       // "A" — treats 65 as rune U+0041
    fmt.Println(strconv.Itoa(n)) // "65" — numeric string
    fmt.Println(string(rune(0x1F600))) // "😀" — emoji U+1F600
}
```

```
Step 1: string(65)
  65 = U+0041 = 'A'
  Result: "A"  <-- NOT "65"!

Step 2: strconv.Itoa(65)
  Converts integer to decimal string representation
  Result: "65"

Step 3: string(rune(0x1F600))
  0x1F600 = U+1F600 = '😀'
  UTF-8 encoding: F0 9F 98 80 (4 bytes)
  Result: "😀"
```

### Example 5: strings.Builder vs concatenation

```go
package main

import (
    "fmt"
    "strings"
)

func concatSlow(words []string) string {
    result := ""
    for _, w := range words {
        result += w + " "  // O(n) each time → O(n^2) total
    }
    return result
}

func concatFast(words []string) string {
    var b strings.Builder
    for _, w := range words {
        b.WriteString(w)
        b.WriteByte(' ')
    }
    return b.String()  // zero-copy return of internal buffer
}

func main() {
    words := []string{"hello", "world", "from", "Go"}
    fmt.Println(concatSlow(words))
    fmt.Println(concatFast(words))
}
```

```
concatSlow with 4 words:
  Step 1: "" + "hello " → alloc "hello " (6 bytes)
  Step 2: "hello " + "world " → alloc "hello world " (12 bytes)
  Step 3: "hello world " + "from " → alloc "hello world from " (17 bytes)
  Step 4: "hello world from " + "Go " → alloc "hello world from Go " (20 bytes)
  Total allocations: 4, total bytes copied: 6+12+17+20 = 55

concatFast with 4 words:
  Internal buffer grows once (or with Grow() — zero reallocs)
  String() returns buffer directly — no final copy
  Total allocations: 1-2, total bytes: ~20
```

---

## 6.5. Practice Checkpoint

### Tier 1: Predict the Output (2 min)

What does this print?

```go
s := "日本語"
fmt.Println(len(s))
for i, r := range s {
    fmt.Printf("%d:%c ", i, r)
}
```

<details>
<summary>Answer</summary>

```
9
0:日 3:本 6:語
```

Each CJK character is 3 bytes in UTF-8. `len(s)` = 9 bytes. The range indices are byte offsets: 0, 3, 6.

</details>

### Tier 2: Fix the Bug (5 min)

This function should reverse a Unicode string, but it corrupts multi-byte characters:

```go
func reverseString(s string) string {
    b := []byte(s)
    for i, j := 0, len(b)-1; i < j; i, j = i+1, j-1 {
        b[i], b[j] = b[j], b[i]
    }
    return string(b)
}
```

What's wrong and how do you fix it?

<details>
<summary>Hint</summary>

It reverses bytes, not runes. A 3-byte CJK character gets its bytes scrambled.

</details>

### Tier 3: Build It (15 min)

Build a function `RuneStats(s string)` that returns a struct with:
- `ByteLen`: total byte length
- `RuneCount`: number of runes
- `ASCIICount`: number of ASCII characters (1-byte runes)
- `MultiByteCount`: number of multi-byte runes
- `MaxRuneBytes`: size of the widest rune in bytes
- `HasInvalidUTF8`: whether the string contains any invalid UTF-8

Test with: `"Hello, 世界! 🎉"` and `string([]byte{0xff, 0xfe, 0x41})`

> Full solutions with explanations → [[exercises/T03 Strings, Runes & UTF-8 Internals - Exercises]]

---

## 7. Edge Cases & Gotchas

### Gotcha 1: Substring keeps entire original string alive

```go
func getFirstWord(huge string) string {
    i := strings.Index(huge, " ")
    if i < 0 {
        return huge
    }
    return huge[:i]  // shares backing array with 'huge'!
}
```

```
huge = "hello ......(10MB of data)......"
  header: { Data: 0x1000, Len: 10000006 }

result = huge[:5]
  header: { Data: 0x1000, Len: 5 }
                  ▲
                  └── SAME pointer! GC cannot free the 10MB

Fix: return string([]byte(huge[:i]))   <-- forces a copy, releases huge
  Or: return strings.Clone(huge[:i])   <-- Go 1.20+ idiomatic
```

> **Coming from PHP:** PHP strings use copy-on-write refcounting. `substr($huge, 0, 5)` creates an independent copy in PHP. In Go, substring slicing is zero-copy, which is fast but can leak memory.

### Gotcha 2: `string(intValue)` creates a character, not digit string

```go
fmt.Println(string(48))   // "0" (rune U+0030)
fmt.Println(string(9731)) // "☃" (snowman!)
```

Fix: Use `strconv.Itoa()` or `fmt.Sprintf("%d", n)`.

### Gotcha 3: Modifying `[]byte` from unsafe string conversion

```go
s := "hello"
b := unsafe.Slice(unsafe.StringData(s), len(s))
b[0] = 'H'  // UNDEFINED BEHAVIOR — may crash, corrupt, or silently break
```

String literals live in `.rodata` (read-only memory). Writing to them may cause a segfault or silently corrupt data depending on the platform.

### Gotcha 4: Invalid UTF-8 in range loop

```go
s := string([]byte{0xff, 0xfe, 'A', 0x80})
for i, r := range s {
    fmt.Printf("i=%d r=%U\n", i, r)
}
```

```
i=0 r=U+FFFD   (0xFF is invalid UTF-8 start → replacement char)
i=1 r=U+FFFD   (0xFE is invalid UTF-8 start → replacement char)
i=2 r=U+0041   ('A' — valid ASCII)
i=3 r=U+FFFD   (0x80 is a lone continuation byte → replacement char)

Each bad byte produces exactly one U+FFFD and advances by 1 byte.
```

> **Coming from PHP:** PHP doesn't validate UTF-8 by default — `for` loops just process raw bytes. Go's range loop actively detects and replaces invalid sequences. This is safer but can be surprising if you expect raw byte pass-through.

### Gotcha 5: Rune count != visual character count (grapheme clusters)

```go
s := "é"  // This might be 1 rune (U+00E9) or 2 runes (U+0065 + U+0301)
fmt.Println(utf8.RuneCountInString(s))  // could be 1 or 2!
```

Unicode allows combining characters. The visual character "é" can be:
- Precomposed: U+00E9 (1 rune, 2 bytes)
- Decomposed: U+0065 + U+0301 (2 runes, 3 bytes)

For true visual character count, you need `golang.org/x/text/unicode/norm` for normalization or a grapheme cluster library.

### Gotcha 6: `[]byte` to `string` conversion in map lookups allocates

```go
key := []byte("hello")
m := map[string]int{"hello": 1}
_ = m[string(key)]  // compiler optimizes: NO allocation (temporary string)
s := string(key)    // this DOES allocate
_ = m[s]            // and this uses the allocated string
```

The compiler has a special optimization: `m[string(b)]` does not allocate if the result is used directly in a map lookup. But assigning to a variable first defeats this optimization.

---

## 8. Performance & Tradeoffs

### String Building Approaches

| Approach | Time (10K items) | Allocs | Use When |
|---|---|---|---|
| `+=` concatenation | ~750 ns/op | O(n) | Never in loops |
| `fmt.Sprintf` | ~106 ns/op | 2 | Complex formatting |
| `bytes.Buffer` | ~65 ns/op | 1-2 | Need `io.Reader`/`io.Writer` |
| `strings.Builder` | ~37 ns/op | 1 | Default choice for building strings |
| `strings.Builder` + `Grow()` | ~30 ns/op | 1 | Know approximate final size |

### Conversion Costs

| Operation | Cost | Allocates? |
|---|---|---|
| `string([]byte{...})` | O(n) copy | Yes |
| `[]byte(string)` | O(n) copy | Yes |
| `[]rune(string)` | O(n) decode + alloc | Yes (4x byte size) |
| `string([]rune{...})` | O(n) encode + alloc | Yes |
| `s[i:j]` substring | O(1) | No (shares backing) |
| `strings.Clone(s)` | O(n) copy | Yes (releases backing) |
| `unsafe.String(ptr, len)` | O(1) | No (zero-copy, dangerous) |

### When to Use Which Type

| Need | Use | Why |
|---|---|---|
| Store text, pass around | `string` | Immutable, safe, cheap to copy (16B header) |
| Modify text in place | `[]byte` | Mutable, avoids repeated alloc |
| Process Unicode characters | `[]rune` | Random access to code points |
| Build strings in a loop | `strings.Builder` | Amortized O(1) appends |
| Read/write I/O | `[]byte` + `bytes.Buffer` | `io.Reader`/`io.Writer` compatible |
| Parse known ASCII protocol | `[]byte` | Avoid rune overhead |

---

## 9. Common Misconceptions

| Misconception | Reality |
|---|---|
| `len(s)` returns character count | `len(s)` returns **byte** count. Use `utf8.RuneCountInString(s)` for rune count |
| `s[i]` gives the i-th character | `s[i]` gives the i-th **byte** (`uint8`). Use `[]rune(s)[i]` for i-th rune |
| Strings are arrays of characters | Strings are immutable **byte** slices with a UTF-8 interpretation |
| `string(65)` returns `"65"` | `string(65)` returns `"A"` (treats int as rune code point) |
| `for range` index is sequential (0,1,2...) | Index is **byte offset**, may jump: 0, 1, 2, 5, 8 for multi-byte runes |
| Rune count = visual character count | Combining characters mean one visual glyph can be multiple runes |
| String comparison is O(1) | Length comparison is O(1), but same-length strings need O(n) `memcmp` |
| Substring slicing copies data | `s[i:j]` is **zero-copy** — shares the backing array |
| `[]byte(s)` is free | It **copies** all bytes. Only `unsafe` conversion is zero-copy |
| `string` can only hold valid UTF-8 | A `string` can hold **any** bytes, including invalid UTF-8 |

---

## 10. Related Tooling & Debugging

### Inspect string internals

```bash
# See escape analysis for string operations
go build -gcflags="-m" ./...

# Look for "moved to heap" on string conversions
go build -gcflags="-m -m" ./... 2>&1 | grep string
```

### Benchmark string operations

```go
func BenchmarkConcat(b *testing.B) {
    for i := 0; i < b.N; i++ {
        s := ""
        for j := 0; j < 100; j++ {
            s += "x"  // measure O(n^2) cost
        }
    }
}

func BenchmarkBuilder(b *testing.B) {
    for i := 0; i < b.N; i++ {
        var sb strings.Builder
        for j := 0; j < 100; j++ {
            sb.WriteString("x")
        }
        _ = sb.String()
    }
}
```

### Useful packages

| Package | Purpose |
|---|---|
| `unicode/utf8` | `ValidString`, `DecodeRuneInString`, `RuneCountInString` |
| `strings` | `Builder`, `Contains`, `Split`, `Join`, `TrimSpace`, `Map` |
| `strconv` | `Itoa`, `Atoi`, `FormatInt`, `ParseFloat` — numeric ↔ string |
| `bytes` | `Buffer` — mutable byte buffer with `io.Reader`/`io.Writer` |
| `unicode` | `IsLetter`, `IsDigit`, `IsSpace`, `ToUpper`, `ToLower` — rune classification |
| `golang.org/x/text/unicode/norm` | NFC (Normalization Form Canonical Composition) / NFD (Normalization Form Canonical Decomposition) normalization |

---

## 11. Interview Gold Questions

### Q1: "Why does Go use `len()` for bytes instead of rune count?"

**Answer:** Because O(1) vs O(n). If `len()` returned rune count, it would need to scan the entire string to count variable-width UTF-8 runes — making `len()` O(n) instead of O(1). This would break every bounds check, allocation calculation, and performance assumption in the language. Bytes are the fundamental unit, and length is stored directly in the StringHeader. Rune count is a derived property that requires scanning.

**Verbal summary:** "len returns bytes because that's what's stored in the string header — it's O(1). Rune counting requires scanning the UTF-8 encoding and is necessarily O(n). Go made the pragmatic choice to keep len constant-time and provide utf8.RuneCountInString for when you actually need rune count."

### Q2: "What happens when you do `for range` over a string with invalid UTF-8?"

**Answer:** Each invalid byte produces `U+FFFD` (Unicode Replacement Character) and advances exactly one byte. This is defined behavior, not a panic. For example, `string([]byte{0xff, 0x41})` iterated with range yields: index 0 = U+FFFD, index 1 = 'A'. This matters because Go strings can hold arbitrary bytes — they don't enforce valid UTF-8. The `range` loop is the point where UTF-8 interpretation happens, and it handles invalid sequences gracefully.

**Verbal summary:** "Range over invalid UTF-8 produces U+FFFD replacement characters, one per bad byte. Go strings can hold arbitrary bytes — they don't enforce valid UTF-8 at storage time. The range loop does graceful decoding, never panics on bad data."

### Q3: "How would you efficiently reverse a Unicode string in Go?"

**Answer:** Convert to `[]rune`, reverse the rune slice, convert back: `r := []rune(s); for i, j := 0, len(r)-1; i < j; i, j = i+1, j-1 { r[i], r[j] = r[j], r[i] }; return string(r)`. You cannot reverse `[]byte` because multi-byte UTF-8 characters would get their bytes scrambled. The tradeoff: `[]rune(s)` allocates (4 bytes per rune regardless of UTF-8 size), and `string(r)` allocates again. For ASCII-only strings, byte reversal is safe and avoids the rune allocation.

**Verbal summary:** "Convert to a rune slice so each character is a single element, reverse the slice, convert back. Byte-level reversal corrupts multi-byte characters. The cost is two allocations — one for []rune and one for the result string."

---

## 12. Final Verbal Answer

> "In Go, a string is an immutable two-word header — just a pointer and a byte length — backed by a read-only byte array. The bytes are conventionally UTF-8 encoded, but a string can hold arbitrary bytes. This means `len()` returns bytes, not characters, and indexing with `s[i]` gives you a byte. To work with Unicode characters, you use runes — which are int32 aliases for Unicode code points. The `for range` loop over a string automatically decodes UTF-8 into runes, with the loop index being the byte offset. Common traps include thinking `len()` counts characters, byte-indexing multi-byte characters, and O(n^2) string concatenation in loops — which is why `strings.Builder` exists. The zero-copy nature of substring slicing is powerful but can cause memory leaks if a small slice keeps a huge backing string alive."

---

## 13. Comprehensive Interview Questions

> Full interview question bank (15 questions) → [[questions/T03 Strings, Runes & UTF-8 Internals - Interview Questions]]

Preview:
- What is the internal representation of a Go string, and what does passing a string to a function actually copy?
- Explain the difference between `len()`, `utf8.RuneCountInString()`, and the number of grapheme clusters in a string.
- How does `strings.Builder` work internally, and why is it faster than `+=` concatenation?

---

> See [[Glossary]] for term definitions.
