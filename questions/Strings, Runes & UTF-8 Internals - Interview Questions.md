# Strings, Runes & UTF-8 Internals — Interview Questions

> Comprehensive interview Q&A bank for [[Strings, Runes & UTF-8 Internals]].
> Sorted by frequency at top tech companies. Tags: [COMMON] [ADVANCED] [TRICKY]

---

## Q1: What is the internal representation of a Go string? [COMMON]

**Answer:**
A Go string is a two-field struct called StringHeader containing a pointer to an immutable byte array and an integer length. On 64-bit systems this is always 16 bytes: 8 bytes for the pointer and 8 bytes for the length. When you pass a string to a function, Go copies this 16-byte header, never the underlying byte data. This makes string passing extremely cheap — essentially the same cost as passing two integers. String literals have their byte data stored in the binary's read-only data section (`.rodata`), while dynamically created strings (from `string([]byte{...})`, `fmt.Sprintf`, etc.) allocate on the heap.

**Interview tip:** The interviewer is testing whether you understand that strings are value types (the header is copied) but share their backing data. This leads naturally to questions about substring memory leaks and immutability.

---

## Q2: What does `len()` return for a string, and how do you get the character count? [COMMON]

**Answer:**
`len(s)` returns the number of bytes in the string, not the number of characters or runes. This is because the length is stored directly in the StringHeader, making `len()` an O(1) operation. To get the rune (Unicode code point) count, use `utf8.RuneCountInString(s)` which is O(n) because it must scan and decode the entire UTF-8 sequence. For example, `len("café")` returns 5 (not 4) because the accented "é" takes 2 bytes in UTF-8. Even `utf8.RuneCountInString` doesn't give you the visual character count in all cases — combining characters (like separate base character + accent mark) mean one visual glyph can be multiple runes.

**Interview tip:** The interviewer wants to see that you understand the distinction between bytes, runes, and grapheme clusters, and why Go chose O(1) `len()` over an O(n) character count.

---

## Q3: What's the difference between a byte and a rune in Go? [COMMON]

**Answer:**
`byte` is an alias for `uint8` — it represents a single byte value (0-255) and is the fundamental unit of a Go string. `rune` is an alias for `int32` — it represents a Unicode code point (0 to 0x10FFFF). The distinction matters because UTF-8 is a variable-width encoding: a single rune may require 1 to 4 bytes. ASCII characters (like 'A') are both a single byte and a single rune. But characters like '世' are one rune encoded as 3 bytes. Single quotes in Go create rune literals (`'A'` is `rune(65)`), while double quotes create strings. `rune` uses `int32` (signed) rather than `uint32` because Unicode only uses code points up to 0x10FFFF, and the signed type is conventional for character types.

**Interview tip:** This tests your understanding of Go's type system and encoding. A strong answer connects the types to their practical use: bytes for I/O and protocols, runes for text processing.

---

## Q4: How does `for range` over a string differ from an index-based loop? [COMMON]

**Answer:**
An index-based loop (`for i := 0; i < len(s); i++`) iterates byte-by-byte, with `s[i]` returning a `byte`. A `for range` loop (`for i, r := range s`) iterates rune-by-rune, decoding UTF-8 at each step. The index `i` in the range loop is the byte offset of the rune start, not a sequential rune index — so for `"Go是好的"`, the indices would be 0, 1, 2, 5, 8 (jumping by 3 for each CJK character). If the string contains invalid UTF-8, the range loop produces `U+FFFD` (replacement character) for each invalid byte and advances by 1 byte. The range loop compiles down to calls to `runtime.decoderune()`.

**Interview tip:** The interviewer is checking whether you know the byte-offset behavior of the range index. Many candidates assume the index is sequential (0, 1, 2, 3...) and get confused by the jumps.

---

## Q5: Why are Go strings immutable, and what are the implications? [COMMON]

**Answer:**
Go strings are immutable for three reasons: safety (concurrent reads without locks), simplicity (no aliasing bugs — you can't modify a string someone else holds), and optimization (the compiler can share backing arrays, store literals in read-only memory, and skip defensive copies). The implications are: you cannot assign to `s[i]`, any "modification" creates a new string with a new backing array, and string concatenation with `+=` in a loop is O(n^2) because each iteration allocates a new string. The solution for building strings is `strings.Builder`, which maintains a mutable internal `[]byte` buffer and provides a zero-copy `String()` method that transfers ownership of the buffer.

**Interview tip:** This often leads to follow-up questions about `strings.Builder` vs `bytes.Buffer` performance, or about unsafe tricks to mutate strings.

---

## Q6: How does substring slicing work, and what's the memory leak risk? [ADVANCED]

**Answer:**
Substring slicing `s[i:j]` creates a new 16-byte StringHeader with the data pointer offset by `i` bytes and length set to `j-i`. No bytes are copied — it's O(1). The risk is that the small substring keeps the entire original string's backing array alive in memory. If you extract a 5-byte word from a 10MB log line, the garbage collector cannot free the 10MB because the substring's pointer references into it. The fix is to explicitly copy: `strings.Clone(s[i:j])` (Go 1.20+) or `string([]byte(s[i:j]))` which forces a byte copy and creates an independent backing array.

**Interview tip:** This tests your understanding of Go's memory model and GC. The interviewer often follows up asking how you'd detect this leak (heap profiles with pprof).

---

## Q7: Explain the UTF-8 encoding scheme and why Go chose it. [ADVANCED]

**Answer:**
UTF-8 is a variable-width encoding where each Unicode code point uses 1 to 4 bytes. The encoding is self-synchronizing: single-byte characters start with `0`, multi-byte sequences start with `110`, `1110`, or `11110`, and continuation bytes start with `10`. This means you can jump into the middle of a string and find the next rune boundary by scanning forward for a non-continuation byte. Go chose UTF-8 because it was co-designed by Rob Pike and Ken Thompson (both Go creators), it's backward-compatible with ASCII (every ASCII string is valid UTF-8), it requires no byte-order marks, and it's the dominant encoding on the web. Go source files must be UTF-8, and the `range` loop natively decodes it.

**Interview tip:** Mentioning that Go's creators literally invented UTF-8 shows deep knowledge. The interviewer may follow up asking about NUL-safety (UTF-8 only has 0x00 for NUL, unlike UTF-16/UTF-32).

---

## Q8: What happens when you convert between `string`, `[]byte`, and `[]rune`? [COMMON]

**Answer:**
`[]byte(s)` allocates a new byte slice and copies all bytes from the string — O(n) time and memory. This is required because `[]byte` is mutable but strings are immutable. `string(b)` does the reverse copy. `[]rune(s)` decodes every UTF-8 rune and stores each as an `int32` in a new slice — this uses 4 bytes per rune regardless of the original UTF-8 size, so it can use up to 4x the memory. `string(runes)` re-encodes back to UTF-8. The compiler has one important optimization: `m[string(key)]` where `key` is `[]byte` does NOT allocate a string — it uses a temporary string for the map lookup. This optimization only works when the string is used directly in the map access expression.

**Interview tip:** The follow-up is usually about zero-copy conversions using unsafe. Know that Go 1.20 introduced `unsafe.StringData` and `unsafe.String` for this, with the critical caveat that the resulting `[]byte` must never be modified.

---

## Q9: How does `strings.Builder` work internally? [ADVANCED]

**Answer:**
`strings.Builder` wraps a `[]byte` slice internally. `WriteString`, `WriteByte`, and `WriteRune` all append to this slice using standard slice growth (doubling capacity). The key optimization is `String()`: instead of copying the bytes into a new string, it uses `unsafe.String` to create a string header pointing directly at the builder's byte slice — zero allocation for the final string. After calling `String()`, the builder effectively transfers ownership of the buffer. `strings.Builder` also has a copy-detection mechanism: if you copy a Builder value, the copy will panic on write, preventing two Builders from sharing the same buffer. `Grow(n)` pre-allocates capacity, which is critical for performance when you know the approximate final size.

**Interview tip:** The interviewer tests whether you understand why Builder is faster than concatenation (amortized O(1) appends vs O(n) per concatenation) and the zero-copy String() optimization.

---

## Q10: How would you reverse a Unicode string in Go? [TRICKY]

**Answer:**
Convert to `[]rune`, reverse the slice, convert back to string: `runes := []rune(s); for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 { runes[i], runes[j] = runes[j], runes[i] }; return string(runes)`. You cannot reverse `[]byte` because multi-byte UTF-8 sequences would get their bytes scrambled, producing invalid UTF-8. The cost is two allocations: one for `[]rune` and one for the result `string`. For ASCII-only strings, byte reversal is safe and more efficient. Even the rune approach has a subtle bug with combining characters (e.g., "e" + combining accent) — the accent would end up on the wrong base character. For fully correct Unicode reversal, you'd need to handle grapheme clusters using `golang.org/x/text/unicode/norm`.

**Interview tip:** The interviewer starts with the basic solution but may push you on grapheme clusters. Acknowledging the combining character limitation shows senior-level awareness.

---

## Q11: What is `string(65)` and why is it a common source of bugs? [TRICKY]

**Answer:**
`string(65)` produces `"A"`, not `"65"`. When you pass an integer to `string()`, Go treats it as a Unicode code point and creates a one-rune string. Code point 65 is 'A' (U+0041). This catches people coming from languages where `String(int)` gives the decimal representation. For the decimal string `"65"`, use `strconv.Itoa(65)` or `fmt.Sprintf("%d", 65)`. Starting with Go 1.15, `go vet` warns about `string(int)` conversions that might be unintentional.

**Interview tip:** This is a quick gotcha question. The interviewer is testing your awareness of Go's type conversion semantics and the distinction between rune-to-string vs integer-to-string.

---

## Q12: How does Go handle invalid UTF-8 in strings? [ADVANCED]

**Answer:**
Go strings can hold arbitrary bytes, including invalid UTF-8. The type system does not enforce valid UTF-8 at the storage level. Invalid UTF-8 only matters when you interpret the string. `for range` produces `U+FFFD` (Unicode Replacement Character) for each invalid byte, advancing by 1 byte. `utf8.ValidString(s)` checks whether a string contains only valid UTF-8. `utf8.DecodeRuneInString` returns `(RuneError, 1)` for invalid bytes, which is the signal to detect corruption. Functions in the `strings` package generally treat strings as opaque bytes and don't validate UTF-8. The practical implication: data from network I/O, file reads, or external APIs might contain invalid UTF-8, and you should validate with `utf8.ValidString` before assuming rune-level operations will behave correctly.

**Interview tip:** This tests your understanding of Go's practical approach to string safety — it's permissive at storage time but graceful at interpretation time.

---

## Q13: What are the zero-copy string conversion techniques in Go? [ADVANCED]

**Answer:**
Go 1.20 introduced `unsafe.StringData(s)` which returns a pointer to the string's bytes, and `unsafe.String(ptr, len)` which creates a string from a byte pointer without copying. For `[]byte` to `string`: `unsafe.String(unsafe.SliceData(b), len(b))`. For `string` to `[]byte`: `unsafe.Slice(unsafe.StringData(s), len(s))`. Before Go 1.20, the technique used `reflect.StringHeader` and `reflect.SliceHeader` with `unsafe.Pointer` casts. The critical rule: after zero-copy conversion from string to `[]byte`, you must never modify the byte slice — doing so breaks string immutability, and if the string data is in `.rodata`, writing to it may cause a segfault. These techniques are only appropriate in performance-critical code where profiling proves the allocation is a bottleneck.

**Interview tip:** The interviewer is testing your knowledge of unsafe and your judgment about when to use it. Always mention the immutability constraint and the "profile before optimizing" principle.

---

## Q14: How does Go compare strings internally? [TRICKY]

**Answer:**
String comparison follows an optimized path. First, if the lengths differ, the strings are not equal — this is O(1) and catches most mismatches. Second, if both strings have the same Data pointer (they share the same backing array and same starting point), they're equal — also O(1). Third, for same-length strings with different pointers, Go performs `memcmp` on the byte arrays, which is O(n) but often SIMD-accelerated by the runtime. For ordered comparisons (`<`, `>`), Go does lexicographic byte comparison, which happens to match Unicode ordering for valid UTF-8 strings because UTF-8 was designed to preserve code-point ordering in byte representation.

**Interview tip:** The pointer-equality shortcut and the UTF-8 lexicographic ordering property are the advanced details that distinguish a senior answer.

---

## Q15: When should you use `[]byte` vs `string` vs `[]rune`? [COMMON]

**Answer:**
Use `string` for storing and passing around text — it's immutable (safe for concurrent reads), cheap to pass (16-byte header copy), and the standard type for text APIs. Use `[]byte` when you need to modify text in place, work with I/O operations (`io.Reader`/`io.Writer`), or process binary/protocol data where characters aren't the relevant unit. Use `[]rune` when you need random access to Unicode characters by index (e.g., reversing a string, accessing the nth character) — but be aware it uses 4 bytes per character regardless of the original UTF-8 size. In practice, most code should default to `string` and use `for range` for iteration. Convert to `[]byte` or `[]rune` only at the boundaries where mutation or random character access is needed.

**Interview tip:** The interviewer wants practical judgment. A strong answer explains the tradeoffs (memory cost of `[]rune`, I/O compatibility of `[]byte`, safety of `string`) and gives concrete use cases for each.

---
