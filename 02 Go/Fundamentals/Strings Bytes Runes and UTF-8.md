---
type: canonical
domain: go
topic: strings-runes-utf8
status: implementation-needed
aliases:
  - T03 Strings, Runes & UTF-8 Internals
source_notes:
  - "[[99 Archive/Superseded Originals/root/T03 Strings, Runes & UTF-8 Internals]]"
---

# Strings, Bytes, Runes and UTF-8

## Why this matters

Backend services validate, truncate, search, log, and serialize text. Bugs appear when code treats byte offsets as character positions. Go strings are immutable byte sequences; UTF-8 is a common encoding, not a promise that every string is valid UTF-8.

## Explain like I am 12

A string is a sealed row of bytes. ASCII characters use one box; many other characters use several boxes. A rune is the number identifying one Unicode code point. A visible symbol can still contain more than one code point.

## Mental model and core concepts

- `len(s)` counts bytes.
- `s[i]` returns one byte.
- `for i, r := range s` decodes runes and reports each rune's starting byte index.
- `[]byte` is appropriate for raw or byte-oriented mutation; `[]rune` enables code-point indexing at an allocation cost.
- `utf8.ValidString`, `utf8.RuneCountInString`, and `strings` helpers make intent explicit.
- Grapheme clusters such as combined emoji are a layer above runes; user-visible truncation may need a Unicode segmentation library.

## Minimum executable example and complete main usage

```go
package main

import (
	"fmt"
	"unicode/utf8"
)

func runeSummary(s string) (bytes, runes int) {
	return len(s), utf8.RuneCountInString(s)
}

func main() {
	s := "Go界"
	bytes, runes := runeSummary(s)
	fmt.Println(bytes, runes) // 5 3
	for index, r := range s {
		fmt.Printf("byte=%d rune=%c\n", index, r)
	}
}
```

## Detailed dry run

`G` and `o` occupy one byte each. `界` occupies three UTF-8 bytes, so the byte length is five while the rune count is three. Range starts decoding at byte offsets 0, 1, and 2. Converting to `[]rune` would materialize three code points and allow rune indexing.

## Under the hood

A string value describes immutable bytes. Slicing a string uses byte indexes and can split an encoded rune. Substrings can share underlying storage, so copy a small substring when it must outlive a very large source and retention matters. Avoid depending on runtime layout details; measure allocation behavior for the actual Go version.

## Production usage, success, and failure

Success: validate external text at the boundary, document byte-versus-code-point limits, and truncate using the unit the product contract specifies. Failure: `s[:10]` is called “ten characters,” splits UTF-8, or a database byte limit is confused with a UI character limit.

Use `strings.Builder` for incremental string construction when the result is a string. Use `bytes.Buffer` when the surrounding API is byte-oriented. Convert only when the operation requires it.

## Common mistakes and trade-offs

- Assuming valid UTF-8 because the type is `string`.
- Using `len` as a character count.
- Reversing bytes rather than runes.
- Treating runes as user-perceived characters.
- Repeated `string`/`[]byte`/`[]rune` conversion in a hot loop.

Byte operations are fast and exact for protocols; rune operations preserve code points but decode and may allocate; grapheme-aware operations match users but need more machinery.

## Google / Senior Interview Lens

Start with “string is bytes; rune is a Unicode code point; UTF-8 is variable-width.” Then show byte indexes from `range`, invalid-input behavior, and the distinction between runes and graphemes. For an implementation, state the unit required by the contract and include empty, invalid, and multi-byte cases. Complexity is normally O(bytes) for decoding.

## Active recall and blank-editor challenge

Write `reverseRunes(string) string`, test ASCII, `Go界`, empty input, and invalid UTF-8, then explain whether preserving code points is enough for emoji clusters.

## Related notes

- [[Go Learning Path]]
- [[Strings Bytes Runes and UTF-8 - Quick Revision]]
- [[Collection Transformations in Go]]

Parent MOC: [[Go Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
