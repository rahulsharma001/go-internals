# T03 Strings, Runes & UTF-8 Internals — Visual Map

> Visual-only reference for [[T03 Strings, Runes & UTF-8 Internals]].
> No prose — just diagrams, layouts, and cheat tables.

---

## Concept Map

```mermaid
graph TD
    s[string]
    h[StringHeader]
    b[backing read-only []byte]
    r[rune int32]
    fr[for range decodes UTF-8]
    bl[strings Builder]
    cp[byte string copies]
    sh[substring shares backing]
    s --> h
    h --> b
    b --> r
    fr --> r
    bl --> s
    b <--> cp
    s --> sh
    sh --> b
```

---

## Data Structure Layouts

```
StringHeader (unsafe; conceptual)     total 16 bytes (amd64)
+------------------+------------------+
| Data  uintptr    | Len   int        |
+------------------+------------------+
| points to        | byte length      |
| read-only byte   | (not rune count) |
+------------------+------------------+

UTF-8: "café"  (4 runes, 5 bytes)
Index: 0    1    2    3    4
Bytes: 63  61  66  c3  a9
       c   a   f   +--- é (U+00E9) = 2 bytes
Rune#  [0][1][2]        [3]

strings.Builder (simplified)
+------------------+
| buf []byte       |  -> grows with append-like logic
| dst  *strings... |  String() may zero-copy to string
+------------------+
```

---

## Decision Table

| Need to... | Use | Why |
|---|---|---|
| Store or pass read-only text | `string` | Idiomatic, immutable, cheap copy (header) |
| Mutate byte content in place | `[]byte` | Mutable; `string` cannot be changed |
| Index by rune or random "character" | `[]rune` | O(1) rune access; `string` index is byte offset |
| Build text in a tight loop | `strings.Builder` | O(n) amortized; avoids O(n^2) `+=` |
| I/O, byte streaming, Fprintf | `bytes.Buffer` | R/W buffer; different API than Builder |

---

## Before/After Comparisons

```
Naive += in loop                 strings.Builder
----------------                ----------------
s := ""                          var b strings.Builder
for _, x := range xs {          for _, x := range xs {
  s += x      // O(n^2)            b.WriteString(x)  // O(n) amort
}                                }
                                 s := b.String()

s[i:j] substring (same backing)   strings.Clone(s[i:j])
----------------                  ----------------------
Cheap share; if parent freed      Independent copy; safe if parent
GC keeps large backing            must not pin large buffer
```

---

## Cheat Sheet

1. A `string` is an immutable length-prefixed view over bytes, not a `[]rune` by default.
2. `StringHeader` is `Data` (pointer) + `Len` (bytes); 16 bytes on 64-bit.
3. `rune` is an alias for `int32` (Unicode code point), not a UTF-8 byte count.
4. `len(s)` is bytes; `utf8.RuneCountInString(s)` counts runes.
5. `for i, r := range s` decodes UTF-8; `i` advances by byte index.
6. `string(b)` and `[]byte(s)` allocate and copy (unless compile proves otherwise for some edge cases).
7. Substring `s[i:j]` shares the same backing array as `s` (slices a byte view).
8. Naive `s += t` in a loop resizes and copies repeatedly — quadratic time.
9. `strings.Builder` holds `[]byte` internally; `String()` is efficient after build.
10. `bytes.Buffer` is for I/O-style read/write, not the same as `Builder`.
11. Invalid UTF-8 in a `string` is allowed; `range` uses replacement char rules.
12. `[]rune(s)` decodes the whole string — allocates a new rune slice.
13. `utf8.RuneError` (U+FFFD) appears when decoding broken sequences (per iterator rules).
14. `strings.Clone` was added to get an independent string copy of a slice of bytes-as-string.
15. `unsafe` conversion between `*StringHeader` and `string` is possible but avoid unless required.

---
