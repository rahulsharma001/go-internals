---
type: quick-revision
domain: go
topic: strings-runes-utf8
canonical: "[[Strings Bytes Runes and UTF-8]]"
---

# Strings, Bytes, Runes and UTF-8 - Quick Revision

## 30-second definition and mental model

A Go string is immutable bytes. UTF-8 encodes a Unicode code point in one or more bytes. A rune is a code point, not necessarily one user-visible character.

## Essential syntax

```go
len(s)                         // bytes
utf8.RuneCountInString(s)      // decoded runes
for byteIndex, r := range s {} // rune + starting byte index
valid := utf8.ValidString(s)
```

## Five facts

1. `s[i]` is a byte.
2. String slicing uses byte indexes.
3. Range replaces invalid encodings with `utf8.RuneError` while advancing.
4. `[]rune(s)` supports code-point indexing but allocates.
5. Grapheme clusters can contain multiple runes.

Common trap: calling `s[:n]` “the first n characters.”

Production example: validate external text and define whether a limit is in bytes, code points, or displayed characters.

Interview answer: “I choose the text unit from the contract; strings are bytes, range decodes UTF-8, and grapheme-aware behavior needs a higher-level segmenter.”

Active recall: reverse `Go界` by runes and explain the behavior for invalid UTF-8.

Canonical: [[Strings Bytes Runes and UTF-8]]

Index: [[Quick Revision Index]]
