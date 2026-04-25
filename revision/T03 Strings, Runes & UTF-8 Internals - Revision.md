# Strings, Runes & UTF-8 Internals — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[Strings, Runes & UTF-8 Internals]]
> Q&A bank → [[questions/Strings, Runes & UTF-8 Internals - Interview Questions]]

---

## Recall Grid (answer each, then check)

| # | Prompt | Check |
|---|--------|-------|
| 1 | `StringHeader` layout (2 fields, size) | `ptr` + `len` (16 bytes on 64-bit) |
| 2 | What does `len(s)` count? | Byte length, not character count |
| 3 | `byte` vs `rune` | `uint8` vs `int32` (Unicode code point) |
| 4 | `for range` on a string | Decodes UTF-8 runes; loop index is byte offset, not rune index |
| 5 | String mutability | Immutable; reassigning `s` replaces the header, not in-place |
| 6 | Substring with slicing (`s[i:j]`) and memory | Same backing array; long-lived sub-slice of huge string can leak |
| 7 | `string(65)` | Converts integer to UTF-8: `"A"` (one byte) |
| 8 | UTF-8 code unit width | 1–4 bytes per rune; variable width |
| 9 | `[]byte` / `string` / `[]rune` conversions | Each conversion may allocate/copy; avoid in hot loops |

---

## Core Visual

```
StringHeader
  data *byte ──────►  [ 63  61  66  C3  A9 ]   "café"  (5 bytes, 4 runes: c a f é)
  len  = 5
          ^ byte index s[3] is 0xC3 (not full 'é')
```

---

## Top Interview Questions (quick-fire)

**Q: What is a Go string internally?**
A `StringHeader` is a two-word struct: pointer to read-only byte data plus length. The compiler/runtime treat the backing bytes as immutable.

**Q: Why is `len("café")` 5, not 4?**
`len` counts bytes. The é in UTF-8 is two bytes (`C3 A9`), so 4 letters but 5 bytes.

**Q: How does `strings.Builder` help and how does it produce the final `string`?**
Builder keeps a growable `[]byte` and appends in place. `String()` returns a string that shares the buffer when safe (no extra copy in the common case), avoiding repeated `+=` which is O(n²).

---

## Verbal Answer (say this out loud)

> "A string is an immutable two-word header (ptr + len) backed by a read-only byte array. len() returns bytes, s[i] returns a byte, for range decodes runes. Common traps: len counts bytes not chars, += in loops is O(n^2) (use Builder), substring slicing can leak memory."

---
