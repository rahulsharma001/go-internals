# Strings, Runes & UTF-8 Internals — Interview Questions

> Comprehensive interview Q&A bank for [[Strings, Runes & UTF-8 Internals]].
> Sorted by frequency at top tech companies. Tags: [COMMON] [ADVANCED] [TRICKY]

---

## Q1: What is the internal representation of a Go string? [COMMON]

**Answer:**

**In one line:** A Go `string` is a two-field header (pointer and length) pointing at a read-only or heap-backed UTF-8 byte sequence, and passing or assigning a `string` copies only that header, not the bytes.

**Visualize it:**

```
64-bit StringHeader (16 bytes total)
┌──────────────────┬────────────┐
│  Data *byte      │  Len int   │
└──────┬───────────┴────────────┘
       │
       ▼
   [byte, byte, byte, ...]   immutable UTF-8 sequence
   .rodata (literal)  OR  heap (Sprintf, string([]byte{...}), etc.)

fn(s string)  ──▶  copies 16 bytes on stack  ──▶  same Data pointer, shared backing
```

**Key facts:**
- The runtime layout is a two-field struct (`StringHeader` / `stringHeader`): a pointer to the byte sequence and a length; on 64-bit that header is 8 + 8 bytes.
- Pass-by-value only copies the header; the backing bytes are not copied, so argument passing is as cheap as passing two words.
- String literals are stored in the binary’s read-only data (`.rodata`); dynamically created strings (e.g. from `string([]byte{...})`, `fmt.Sprintf`, and similar) typically allocate the backing array on the heap.

**Interview tip:** The interviewer is testing whether you understand that strings are value types (the header is copied) but share their backing data, which sets up substrings, immutability, and GC.

> [!example]- Full Story: Header, pointer, and shared bytes
>
> **The problem:** If every string copy duplicated all bytes, passing strings through APIs and concatenation would be far too slow and memory-heavy.
>
> **How it works:** The compiler and runtime represent a value of type `string` as a pointer-length pair so each copy is O(1) in header size; all holders read the same byte slice, while the type system still presents `string` as an immutable value: shared backing under the hood with read-only safety at the type level, literals placed in read-only image memory, and no implicit duplication on assignment.
>
> **What to watch out for:** Shared backing means a small substring does not free the “rest” of the data (Q6), and you must not mutate those bytes through normal `string` APIs; breaking the immutability contract with `unsafe` (Q13) corrupts the model and can fault on read-only data.

---

## Q2: What does `len()` return for a string, and how do you get the character count? [COMMON]

**Answer:**

**In one line:** `len(s)` is the number of bytes stored in the string header, so it is O(1), while a true “character” count requires a scan, grapheme handling, or external Unicode segmentation, not a single built-in.

**Visualize it:**

```
StringHeader: Len = 5
              ↓
    "c a f é"  (in memory: c, a, f, 0xC3, 0xA9)  = 5 bytes, 4 runes
              └── len(s)=5  ──▶  utf8.RuneCountInString → must decode O(n)
                                            └── still ≠ user “glyph” if combining sequences

bytes vs runes vs grapheme:
  bytes:   [ .. .. .. | ..]
  runes:   O(n) scan    utf8....
  visual:  may need   normalization / segmentation   (not in stdlib alone)
```

**Key facts:**
- `len(s)` is the number of bytes in the UTF-8 data, not runes, because the length is part of the header; reading it is O(1).
- `utf8.RuneCountInString(s)` counts Unicode code points and is O(n) over the string because every byte of valid UTF-8 may need to be part of a decode.
- `len("café")` is 5 because “é” is two UTF-8 bytes; rune count is 4.
- One user-visible “character” (grapheme) can be multiple runes, e.g. base letter plus combining mark, so rune count can still under/over-represent what people mean by “character”.

**Interview tip:** The interviewer wants to see that you distinguish bytes, runes, and grapheme clusters, and that you can explain why Go keeps O(1) `len()` as byte length instead of scanning for “characters” on every use.

> [!example]- Full Story: Byte length in the header vs human “length”
>
> **The problem:** If the standard library had to return “number of display characters” for every `len` call, it would need a full scan or a cached, expensive structure on every use.
>
> **How it works:** The `Len` field in the string header is exactly the size of the UTF-8 byte sequence: cheap to read, aligned with I/O, protocols, and raw indexing; when you need rune count you pay explicitly with `utf8.RuneCountInString` or iteration, and when you need “real” user-perceived characters you may need grapheme or normalization work outside the core idiom, so you only pay for the abstraction you need.
>
> **What to watch out for:** Do not assume one glyph per rune; for UI, cursor movement, and collation, `utf8.RuneCountInString` alone is often insufficient.

---

## Q3: What's the difference between a `byte` and a `rune` in Go? [COMMON]

**Answer:**

**In one line:** `byte` is a raw 8-bit unit (`uint8`) that is what a `string` stores in memory, while `rune` is a Unicode code point (`int32` up to U+10FFFF) that UTF-8 encodes as one to four `byte` values per code point.

**Visualize it:**

```
byte  = uint8     [0 .. 255]     one octet
                        │
         string:  [B][B][B]...[B]   (UTF-8 stream)

rune  = int32     code point U+0000 .. U+10FFFF
         '世'  ──▶  U+4E16  ──▶  3 bytes in UTF-8: E4 B8 96

'Z'  single-quoted  ── rune literal   (value 0x5A = one byte in UTF-8)
"Z"  double-quoted  ── string
```

**Key facts:**
- `byte` is an alias for `uint8`; it is the element type of a string’s backing array in memory.
- `rune` is an alias for `int32` and holds a single Unicode code point; UTF-8 maps each code point to 1–4 `byte` values in the string.
- ASCII characters align one `byte` and one `rune`; many scripts need multiple bytes for one `rune` (e.g. three bytes for 世 in UTF-8).
- Single-quoted literals are runes; double-quoted literals are strings, and `int32` is conventional for a character type even though the code point space fits in 21 bits.

**Interview tip:** This tests mapping types to the encoding model: connect `byte` to I/O and wire format and `rune` to logical scalar values and iteration semantics.

> [!example]- Full Story: Octets, code points, and UTF-8 as the bridge
>
> **The problem:** You sometimes need to move raw octets on the wire (`byte`, `[]byte`) and sometimes reason about logical Unicode scalars as `rune` or via `for range` on `string`, without the type system conflating the two.
>
> **How it works:** The aliases make intent clear: `byte` carries no text semantics beyond octets, while `rune` is a decoded scalar from Unicode; a `string` is UTF-8 at rest, so storage stays compact for ASCII and Latin-1 while still representing the full space when you decode, and the dual literal syntax (`'x'` vs `"x"`) encodes that distinction at the source level.
>
> **What to watch out for:** A `rune` is a code point, not necessarily a user-perceived character: combining marks, flag sequences, ZWJ, and similar need higher-level treatment.

---

## Q4: How does `for range` over a string differ from an index-based loop? [COMMON]

**Answer:**

**In one line:** An index loop walks byte positions and `s[i]` is a `byte`, while `for i, r := range s` decodes UTF-8 rune by rune and the first value is a byte offset into the string, not a 0,1,2 “rune index” unless every code unit is one byte.

**Visualize it:**

```
Index loop:  i=0,1,2,3...   s[i] is byte
       "G" "o" 是多 ...
        0   1  2 3 4 (bytes)

Range:  (i, r) = (0,'G') (1,'o') (2,'是') (5,'多') (8,...)
         └── i jumps by UTF-8 width of each rune

Invalid UTF-8:  for each bad byte, emit U+FFFD, width 1
                (compiled via runtime path such as decoderune)
```

**Key facts:**
- `for i := 0; i < len(s); i++` visits each index as a byte position; `s[i]` has type `byte`.
- `for i, r := range s` decodes the next rune on each step; `i` is the starting byte index of that rune in the original string, not 0,1,2 for “2nd, 3rd rune” except when every rune is 1 byte.
- In `"Go是好的"`, byte indices jump (e.g. 0,1,2 then 5,8 for the two CJK runes) because each of those need three UTF-8 bytes.
- If the data is not valid UTF-8, the range loop yields the replacement character U+FFFD per bad byte, advancing by one byte; the implementation uses the runtime’s decode path.

**Interview tip:** The interviewer checks whether you know the first value in `range` is a byte offset—many candidates assume a simple 0,1,2,3 sequence and get confused by gaps.

> [!example]- Full Story: Byte walk vs decode walk on the same UTF-8
>
> **The problem:** You must know whether you are iterating the wire format (bytes) or logical code points (runes), and you must not confuse “string index” with “nth rune” when characters span multiple bytes.
>
> **How it works:** `for range` walks the string as UTF-8, yielding a valid `rune` (or U+FFFD) and the exact byte index for slicing the original `string` or re-scanning; that index is a byte position on purpose because it is O(1) to produce, stable, and lines up with how the UTF-8 is laid out in memory, while a manual `i++` over multi-byte runes can land in the middle of a sequence and produce corrupt interpretations unless you use `utf8` helpers or `for range` for decode-aware steps.
>
> **What to watch out for:** Do not advance by `i++` through multi-byte characters without understanding UTF-8 boundaries; use `utf8` package operations or `for range` when movement must be rune-correct (Q12 ties into replacement behavior for bad bytes).

---

## Q5: Why are Go strings immutable, and what are the implications? [COMMON]

**Answer:**

**In one line:** Immutability lets the implementation share one read-only byte sequence across many string values, literals, and concurrent readers without data races, at the cost of only producing new strings or using mutable buffers (for example `[]byte` or `strings.Builder`) when you “change” text.

**Visualize it:**

```
Why:
  many readers, one backing  ──▶  no data races on content
  substring shares bytes     ──▶  must not let anyone mutate
  literals in .rodata        ──▶  segfault if you could write

Implications:
  s[i] = x   // illegal
  s += t     in loop: repeated alloc + copy  ──  O(n²) for naive +=
  strings.Builder:  mutable []byte  ──▶  String() can transfer to string
```

**Key facts:**
- Immutability supports concurrent use without locks for read-only string data and prevents one holder from mutating bytes another holder still observes.
- The compiler and runtime may coalesce, intern, and place literals in read-only memory because user code cannot change bytes through the `string` type.
- You cannot subscript-assign into a `string`; apparent edits allocate new backing storage (a new `string`) unless you use a `[]byte` or a builder.
- `s += t` in a loop repeatedly allocates and copies in full; building with `+=` is quadratic in total length for typical patterns.
- `strings.Builder` holds a `[]byte` you append to; `String()` can transfer that buffer to an immutable `string` without a copy of the content (see Q9).

**Interview tip:** This often leads to `strings.Builder` vs `bytes.Buffer` and to unsafe “mutation” of string memory; be ready to connect immutability to performance and to why `Builder` exists.

> [!example]- Full Story: Share everywhere, write nowhere
>
> **The problem:** If `string` were mutable, substrings, map keys, and concurrent readers would need extra copies or locking to keep aliasing and races predictable, and the compiler could not treat literals and shared substrings as safely read-only.
>
> **How it works:** A `string` value names a fixed byte sequence: mutating that sequence is not a valid language operation, so the runtime can keep one physical copy for many uses; `strings.Builder` and `[]byte` are where growth and mutation live, and the transition to a final `string` is a controlled, documented step so you get amortized appends in the builder and an immutable value at the end (Q9).
>
> **What to watch out for:** `unsafe` or reflection that writes string-backed memory breaks the model and can fault on read-only data; naive `+=` in hot loops is a classic performance trap.

---

## Q6: How does substring slicing work, and what's the memory leak risk? [ADVANCED]

**Answer:**

**In one line:** Slicing `s[i:j]` creates a new pointer-and-length header over the same backing array as the original string, so a tiny substring can keep a huge underlying allocation alive until you `strings.Clone` or copy through `[]byte` if you need an independent, small lifetime.

**Visualize it:**

```
Huge string (10MB log line)        Small substring: s[1e6:1e6+5]
[................................................]
  ^-- Data points here              New header:  Data' = oldData + 1e6, Len' = 5
       └── GC still sees 10MB alive because the substring is interior pointer into same block

Fix: strings.Clone(s[i:j])  or  string([]byte(s[i:j]))
  ──▶  new small allocation, old huge block can be collected (if unreferenced)
```

**Key facts:**
- `s[i:j]` is O(1): a new 16-byte header, `Data` adjusted to `i` bytes in, `Len` = `j-i`, with no copy of the bytes in the operation itself.
- The substring is a view into the original allocation, so the full backing array remains reachable and is not collected while the substring is reachable.
- A short extract from a very large string (for example a log line) can pin the large allocation for the life of the small substring.
- `strings.Clone` (Go 1.20+) or `string([]byte(s[i:j]))` forces a copy to a new backing store so the large string can be freed if nothing else references it.

**Interview tip:** This tests the memory model: interviewers may ask how you would see this in production (for example `pprof` heap profiles showing large `inuse` blocks tied to small strings).

> [!example]- Full Story: Interior pointers and the “leak that is not a leak”
>
> **The problem:** You may believe you “threw away” a large string when you only keep a small token from a long line, but the runtime still treats the full backing object as live because the substring holds an interior pointer into it.
>
> **How it works:** Slices and string headers that share an array are cheap exactly because one allocation holds all bytes; the garbage collector follows the object, not a logical sub-range of it, and `s[i:j]` only adjusts the header to point at a sub-slice of those bytes, so retention is by design, not a GC bug, and when you need a small value with an independent lifetime you pay an explicit `memcpy` via clone or `[]byte` conversion.
>
> **What to watch out for:** `inuse_space` in `pprof` can show large string-related blocks; the fix is the clone pattern when you must shrink retention, not assuming the runtime will split physical storage.

---

## Q7: Explain the UTF-8 encoding scheme and why Go chose it. [ADVANCED]

**Answer:**

**In one line:** UTF-8 encodes each code point in one to four bytes using a prefix and continuation pattern that makes the stream self-synchronizing, and Go adopted it for ASCII alignment, no BOM, wire efficiency, and because its designers were central to defining the encoding.

**Visualize it:**

```
Code points  U+00 .. U+7F  ── 1 byte: 0xxxxxxx
             U+80 .. U+7FF  ── 2 bytes: 110xxxxx 10xxxxxx
            U+800 .. U+FFFF  ── 3 bytes: 1110xxxx 10xxxxxx 10xxxxxx
          U+10000+        ── 4 bytes: 11110xxx 10... (total 4)

Continuation bytes always 10xxxxxx  ──  scan to non-10 byte to resync
ASCII text (0-127)  identical in UTF-8  ──  backward compatible
```

**Key facts:**
- Each Unicode scalar value uses one to four bytes; the pattern of leading `0`, `110`, `1110`, `11110` and `10` continuation bytes makes misaligned reads recoverable to the next character boundary.
- Go adopted UTF-8 because the language designers (including Rob Pike and Ken Thompson) were involved in its design, it is wire-format friendly, and it matches the web’s de facto text encoding.
- Any ASCII bytestring is valid UTF-8 for the same text; you do not need a byte order mark in normal use.
- Go source is UTF-8, and the `string` plus `for range` path natively decodes this encoding; ordered comparisons on raw bytes align with code point order for well-formed UTF-8 (Q14).

**Interview tip:** Mentioning that Go’s designers helped invent UTF-8 signals depth; be ready for follow-up on why UTF-8 beats UTF-16 for NUL-terminated C interop and for avoiding surrogate pairs in the language model.

> [!example]- Full Story: Bit patterns, compatibility, and Go’s single on-wire form
>
> **The problem:** The industry needed one encoding for legacy ASCII and for the full Unicode repertoire without invalidating byte-oriented C tools, pipes, and protocols.
>
> **How it works:** UTF-8’s prefixes and continuation bytes give compact storage for common ASCII, unambiguous resynchronization after damage or a mid-stream join, and a single encoding of each scalar; for Go, a `string` is that byte sequence: no separate wide-character representation in the language—decode to runes when you need them, keep bytes when you do not, and `len` counts bytes while `for range` walks runes (Q2, Q4, Q12).
>
> **What to watch out for:** Byte length is not rune length; invalid input is still storable, and validation is explicit when you need invariants (Q12).

---

## Q8: What happens when you convert between `string`, `[]byte`, and `[]rune`? [COMMON]

**Answer:**

**In one line:** `string` and `[]byte` convert with a full copy each way to keep immutability separate from a mutable slice, while `[]rune` decodes or re-encodes UTF-8 with `int32` per code point, and `map` indexing has a special case for `[]byte` string keys to avoid some allocations.

**Visualize it:**

```
string  ──[]byte(s)──▶  new []byte, memcpy O(n)   (mutability / copy)
[]byte  ──string(b)──▶  new string, memcpy O(n)

string  ──[]rune(s)──▶  decode UTF-8, 4·n bytes for n runes (often ≫ UTF-8 size)
[]rune  ──string(r)──▶  encode to UTF-8, new string

m[string(key)]  where key is []byte  ──▶  no heap string: compiler uses tmpstring / map key pattern (special case, direct in map index expression)
```

**Key facts:**
- `[]byte(s)` allocates and copies all bytes: O(n) time and space, because a slice is mutable and must not alias mutable memory with an immutable `string` view.
- `string(b)` copies from a slice to a new immutable backing array; again O(n) unless you deliberately use `unsafe` (Q13).
- `[]rune(s)` decodes the entire string and uses four bytes per rune; memory can be up to about four times the rune count, independent of the UTF-8 byte length of each rune.
- `string(runes)` re-encodes the rune slice to UTF-8 in a new `string`.
- A narrow compiler optimization: in `m[string(byteSlice)]`, the `[]byte` is not always converted to a separately allocated `string` for the key in the way naive code would; it must appear as the direct map access form for that path.

**Interview tip:** The natural follow-up is zero-copy `unsafe` conversions (Q13): know Go 1.20’s `unsafe.String` / `unsafe.StringData` and the rule that a `[]byte` view of `string` data must not be written.

> [!example]- Full Story: Three representations, two ownership contracts
>
> **The problem:** The same logical text can exist as raw bytes, UTF-8 `string`, or a `[]rune` table, but mutability, aliasing, and map-key behavior differ, so the language cannot in general share storage between `string` and `[]byte` without a copy.
>
> **How it works:** Each `string`↔`[]byte` conversion creates a new owner: copy once, then treat the destination as read-only `string` or mutable `[]byte`; `[]rune` is a different projection (random access by code-point index, higher memory) with decode cost to build from `string` and encode cost back; the `map` plus `m[string(b)]` pattern can avoid a heap-allocated `string` key when written in the recognized form, which matters on hot paths.
>
> **What to watch out for:** Full copies dominate in performance-sensitive code, which is where vetted `unsafe` use appears, always with the immutability rule from Q13.

---

## Q9: How does `strings.Builder` work internally? [ADVANCED]

**Answer:**

**In one line:** `strings.Builder` is a growable `[]byte` that uses append-style growth and then `String()` can materialize a `string` with `unsafe.String` from that buffer without a final copy of the content, and copying a `Builder` by value and writing panics to prevent aliased mutation.

**Visualize it:**

```
strings.Builder
   buf []byte
   Write*  ──▶  append, double-ish growth
   String()  ──▶  unsafe.String(ptr, len)  zero-copy from buf to string, buffer “handed over”
   (later writes reset / new buffer semantics per implementation)

Copy Builder by value
   b2 := b1
   b2.Write...  ──▶  panic: copy check detaches, prevents two builders aliasing one buf
```

**Key facts:**
- The implementation is essentially a resizable `[]byte`; `WriteString`, `WriteByte`, and `WriteRune` append and grow the slice with the usual capacity-doubling strategy.
- `String()` is the headline optimization: the final `string` can share the address of the builder’s buffer via `unsafe.String`, avoiding a final `memcpy` of the content (allocation cost shows up in earlier appends, not the final `string` conversion).
- After `String()`, the contract treats ownership of the buffer as transferred; further use of the `Builder` follows the documented reset and reuse story.
- Copying a `Builder` by value and writing through the copy is detected and panics, blocking two `Builder` values from mutating the same backing slice.
- `Grow` reserves capacity in advance, which is important when the approximate output size is known to avoid many reallocations.

**Interview tip:** Interviewers look for append amortization vs repeated `+` on `string`, and for understanding `String()` and the copy-on-write-safety of `Builder`’s no-alias rule.

> [!example]- Full Story: Append like a slice, finish like a string
>
> **The problem:** Repeated `+` on `string` builds a new string every time and copies the entire prefix over and over, which is O(n^2) aggregate work for simple concatenation loops.
>
> **How it works:** `Builder` reuses a single growing `[]byte` with the same capacity-doubling story as `append`, so work is amortized linear in output size, then `String()` can attach a `string` header to the final buffer in O(1) without copying the bytes again; the copy check on a duplicated `Builder` value prevents two structs from silently sharing one internal buffer and corrupting it.
>
> **What to watch out for:** `bytes.Buffer` is heavier in API and fields; use `Builder` for UTF-8 text building, re-read the docs for post-`String()` reuse, and profile when uncertain.

---

## Q10: How would you reverse a Unicode string in Go? [TRICKY]

**Answer:**

**In one line:** Reverse at the rune level with `[]rune(s)`, a two-index swap, and `string(runes)`—never reverse raw UTF-8 bytes—and remember that combining characters and some emoji still make “reversed for display” wrong without grapheme handling.

**Visualize it:**

```
Wrong (bytes):  [E4 B8] [96]  swapped  →  invalid UTF-8, garbage
Right (runes):  [U+4E16] [U+2F]  swap  →  re-encode to UTF-8 string

rune reverse:
  runes := []rune(s)
  for i,j := 0, len(runes)-1; i < j; i,j = i+1, j-1 { runes[i], runes[j] = runes[j], runes[i] }
  return string(runes)

Cost:  allocate []rune + allocate new string.  ASCII-only:  byte reverse OK and cheaper.

Grapheme edge:  e + combining acute  ──  two runes, reversal moves accent to wrong base without cluster logic (x/text, norm, segmentation).
```

**Key facts:**
- Reversing `[]byte` in place shuffles continuation bytes and breaks well-formed UTF-8 for non-ASCII text.
- The usual correct library answer is `[]rune` reverse then `string`, costing at least the rune buffer and the new UTF-8 `string`.
- For known ASCII, reversing bytes is valid and more efficient in both allocation and work.
- Combining sequences, emoji with joiners, flags, and similar cases need grapheme or normalization-aware processing (for example `golang.org/x/text/unicode/norm` and UAX-based segmentation) for a fully correct “display reverse.”

**Interview tip:** A solid answer gives rune-level reversal first; senior signal is acknowledging grapheme limits without claiming `[]rune` is always end-user-correct.

> [!example]- Full Story: Bytes corrupt, runes help, clusters finish the job
>
> **The problem:** Naive “reverse the array” in interviews usually ignores encoding; byte reversal corrupts any multi-byte character and yields invalid UTF-8 or mojibake.
>
> **How it works:** `[]rune` reversal operates on Unicode code points, which matches many string algorithms that define “character” as a code point, at the cost of O(n) decode to `[]rune`, O(n) in-place rune reversal, and O(n) encode back to `string`, while ASCII-only text can be byte-reversed safely and more cheaply when you can prove the invariant.
>
> **What to watch out for:** Rune-level reversal can still reorder combining marks and bases incorrectly; for “what a person sees in an editor” you need UAX grapheme cluster boundaries, not just `[]rune`.

---

## Q11: What is `string(65)` and why is it a common source of bugs? [TRICKY]

**Answer:**

**In one line:** `string(65)` yields the one-code-point `string` `"A"` (U+0041), not the decimal text `"65"`, so you need `strconv` or `fmt` for decimal formatting, and `go vet` can flag suspicious int-to-`string` conversions.

**Visualize it:**

```
string(65)   ──▶  Unicode  U+0041  ──▶  "A"

string(65)  ≠  decimal "65"  ──▶  strconv.Itoa(65)  or  fmt.Sprintf("%d", 65)

go vet (1.15+):  flags suspicious int──▶string (often mistaken intent)
```

**Key facts:**
- The conversion from a non-negative integer in range to `string` is defined as a `string` containing a single `rune` with that value as its code point; 65 is Latin capital A.
- It does not produce decimal digits; that is a different operation (`strconv` family, `fmt` verbs, or manual formatting).
- Developers from languages where a string constructor “stringifies” the numeral are caught by this rule regularly.
- Since Go 1.15, `go vet` warns on `string(x)` of integer `x` when it is likely a mistaken conversion, not a deliberate code point cast.

**Interview tip:** This tests the distinction between rune-to-string conversion and decimal formatting, not general “integer to text.”

> [!example]- Full Story: Character cast, not `FormatInt`
>
> **The problem:** You may log a port, ID, or error code and see a single odd character or rune instead of digit text because the conversion you used was a code-point cast, not base-10 rendering.
>
> **How it works:** The language spec ties integer-to-`string` in this form to a single-Unicode-scalar `string` for that integer value, so `string(65)` is `"A"`, and producing `"65"` requires an explicit decimal or formatting API; `vet` exists partly to catch the common mistaken pattern in review and CI.
>
> **What to watch out for:** Run `vet` in CI, and in review question any `string(1234)` that was meant to be human-readable numerals.

---

## Q12: How does Go handle invalid UTF-8 in strings? [ADVANCED]

**Answer:**

**In one line:** A `string` may hold arbitrary bytes, invalid UTF-8 is not rejected at the type, and interpretation varies by API: `for range` substitutes U+FFFD per bad byte, while `utf8.ValidString` and `utf8.DecodeRuneInString` let you test or handle errors explicitly.

**Visualize it:**

```
Storage:  arbitrary []byte  ─▶  string  (no validation in type)

Interpret:
  for range  ─▶  bad byte  ─▶  U+FFFD, advance 1
  utf8.ValidString  ─▶  false if any bad sequence
  utf8.DecodeRuneInString  ─▶  (RuneError, 1) on invalid lead/continuation
  many strings/ functions  ─▶  treat as byte blobs, not validated text
```

**Key facts:**
- The `string` type does not guarantee valid UTF-8; the underlying bytes are unconstrained.
- `for range` on a `string` replaces each invalid byte with the Unicode replacement character U+FFFD and advances by one byte for that case.
- `utf8.ValidString` reports whether the entire value is well-formed UTF-8.
- `utf8.DecodeRuneInString` returns `RuneError` with width 1 for bad bytes for explicit error handling or scanning.
- Many `strings` package routines operate on bytes without first validating, which is both fast and a footgun if the input is untrusted and you assume “text” invariants; for network, files, and external APIs, validate or defensively program when you need rune-level guarantees.

**Interview tip:** The interviewer wants the pragmatic model: permissive storage, well-defined behavior at decode time, not a separate “valid string” type in the language.

> [!example]- Full Story: Arbitrary bytes at rest, rules when you read
>
> **The problem:** Real I/O is not always well-formed UTF-8, but programs still need to read it as `string` or `[]byte` without crashing on every odd byte, while strict text pipelines need a way to detect or scrub bad data.
>
> **How it works:** The type stays simple: any byte sequence can be named as `string`; `for range` and `utf8` give replacement or detectable `RuneError` instead of panics, so you can build tolerant UIs or fail closed when you call `ValidString` early; `strings` helpers often work at byte level for speed, pushing validation to the caller when semantics require it.
>
> **What to watch out for:** Comparing, hashing, or normalizing unvalidated data can have subtle results; for strict contracts, run `ValidString` or a scrub pass at the trust boundary (Q4, Q8).

---

## Q13: What are the zero-copy string conversion techniques in Go? [ADVANCED]

**Answer:**

**In one line:** Go 1.20+ offers `unsafe.String`, `unsafe.StringData`, and `unsafe.Slice` / `unsafe.SliceData` to reinterpret `string` and `[]byte` without copying, only when you will never violate `string` immutability and you accept that writing through a `[]byte` view of read-only `string` data can fault.

**Visualize it:**

```
string s  ──▶  []byte:  unsafe.Slice(unsafe.StringData(s), len(s))   (no copy)
[]byte b  ──▶  string: unsafe.String(unsafe.SliceData(b), len(b))   (no copy)

Pre-1.20:  reflect StringHeader / SliceHeader + unsafe (obsolete pattern)

After string──▶[]byte view:  never write  │  .rodata can SIGSEGV on write
Profile first  ──  only in hot paths after proof of allocation cost
```

**Key facts:**
- `unsafe.StringData(s)` returns `*byte` to the first byte of the `string`’s data; `unsafe.String(p, n)` makes a `string` header from a `*byte` and length with no copy.
- Converting `[]byte` to `string` with `unsafe.String(unsafe.SliceData(b), len(b))` and the reverse with `unsafe.Slice` avoid allocation when used correctly.
- Reflect-based `StringHeader`/`SliceHeader` tricks predated 1.20 and are legacy patterns; new code should use the `unsafe` helpers.
- If you form a `[]byte` from a `string` with this route, you must not mutate the elements: doing so breaks the immutability contract, and if the `string` points at read-only image memory, writes can crash.
- These tools belong behind profiling evidence and a clear comment; misuse is a security and stability bug.

**Interview tip:** Interviewers test both API knowledge and judgment: always pair zero-copy with the immutability rule and with “profile first.”

> [!example]- Full Story: Same bits, two names, unbroken rules
>
> **The problem:** Hot code that bounces between `string` and `[]byte` pays O(n) copies on every conversion; in rare cases you can prove read-only or controlled lifetimes and want to re-view the same memory.
>
> **How it works:** Go 1.20 standardized `unsafe.String` and `unsafe.StringData` (and the slice data helpers) so you can build well-defined headers from pointers, replacing brittle `reflect` `StringHeader` hacks; the runtime still enforces that a `string` is immutable logical text—`unsafe` only reinterprets bytes, it does not grant permission to write into `.rodata` or to break invariants on shared `string` data.
>
> **What to watch out for:** A mutable `[]byte` that aliases read-only or shared `string` storage is undefined behavior at the process level; default to normal conversions unless profiling proves allocation is the bottleneck and the lifetime story is clear (Q5, Q8, Q9).

---

## Q14: How does Go compare strings internally? [TRICKY]

**Answer:**

**In one line:** Equality first compares lengths, then can short-circuit when the same memory range is in play, and otherwise uses a byte `memcmp` on the contents, and ordering is lexicographic on UTF-8 bytes, which for valid UTF-8 matches Unicode scalar order by design of UTF-8.

**Visualize it:**

```
s == t:
  len(s) != len(t)  ──▶  false  O(1)
  data(s) == data(t)  && same start (shared backing, same view)  ──▶  can short-circuit true  O(1) when applicable
  else  memcmp(bytes, n)  O(n), often SIMD-optimized

s < t:  lexicographic byte order
  for valid UTF-8, byte order  mirrors  code point order  (property of encoding)
```

**Key facts:**
- Mismatched lengths return inequality without touching payload bytes.
- If both `Data` and length describe the same range (including shared substrings of the same view), the runtime can return equality without a full `memcmp` in the general pattern you describe.
- When lengths match but pointers or offsets differ, the bytes are compared with `memcmp`-style work, O(n) in the common case, with hardware help on many platforms.
- For `<`/`>`/`Compare`, the comparison is unsigned byte order on the UTF-8 byte sequence, which for valid well-formed data is the same order you would get comparing Unicode code points, because of how UTF-8 maps scalars to bytes.
- The UTF-8 ordering property is the bridge between “byte sort” and “Unicode code point order” in practice for well-formed data.

**Interview tip:** Strong answers name the length and pointer short paths and the UTF-8 lexicographic property for ordering.

> [!example]- Full Story: Cheap rejects, then memory, and UTF-8’s sort gift
>
> **The problem:** `string` comparison sits on every map lookup, cache key, and hot branch, so the implementation needs cheap failures and fast equality on the common case of identical or shared data.
>
> **How it works:** Compare lengths first, then in cases where the headers describe the same already-equal span of memory the implementation can return true without scanning all bytes, and only then fall back to a block `memcmp` when needed; for ordering, a plain byte-wise comparison is O(n) and matches scalar Unicode order for valid UTF-8 because the encoding is monotone in code point (Q7).
>
> **What to watch out for:** Locale-sensitive collation, normalization, and “human” sort order are not what raw byte `Compare` does; use `golang.org/x/text/collate` and related packages when the product requires linguistic sorting.

---

## Q15: When should you use `[]byte` vs `string` vs `[]rune`? [COMMON]

**Answer:**

**In one line:** Use `string` as the default for text you store and pass, `[]byte` for mutation, streaming I/O, and binary or non-text buffers, and `[]rune` when you need random access by code-point index or rune-slice algorithms, accepting the memory cost of up to four bytes per `rune`.

**Visualize it:**

```
string:     default API, immutable, cheap copy(16B),  for range = runes
[]byte:     io.Read/Write, in-place edit, wire/binary — may not be "text" at all
[]rune:     random access to code point k,  4*len  memory,  decode cost to build

Most code:  string + for range,  convert at boundaries
```

**Key facts:**
- `string` is the idiomatic type for text in function signatures, struct fields, and maps; it is read-only, safe to read concurrently, and only the header is copied on assignment.
- `[]byte` fits streaming I/O, scanners, and buffers where you append, mutate, or treat data as not necessarily UTF-8 text.
- `[]rune` is appropriate when you need subscripting by the nth code point or algorithms (like rune-level reverse) that are awkward on UTF-8 bytes, at the cost of up to 4 bytes per rune in the slice and O(n) to build from a `string`.
- The usual pattern is to keep `string` in the program, use `for range` to walk runes, and convert to `[]byte` or `[]rune` only at narrow boundaries for mutation, protocol handling, or random rune access.
- The tradeoff is memory and CPU of `[]rune` vs simplicity of `string` and raw bytes on the wire.

**Interview tip:** A strong answer names concrete use cases and tradeoffs (memory of `[]rune`, I/O of `[]byte`, immutability and sharing of `string`) rather than only naming types.

> [!example]- Full Story: Match the type to the operation
>
> **The problem:** Using the wrong representation wastes memory if you `[]rune` everything, or corrupts data if you byte-hack valid UTF-8, or multiplies copies if you convert unnecessarily at every layer.
>
> **How it works:** Pass and store as `string` for stable, shared, read-only text; mutate, stream, and speak protocols with `[]byte`, which may or may not be UTF-8; materialize `[]rune` when the algorithm’s complexity demands O(1) rune subscripting or a rune buffer, and use `for range` on `string` when a linear rune pass suffices without allocating a full rune slice.
>
> **What to watch out for:** Product language “character” is often a grapheme; none of `string`, `[]byte`, and `[]rune` is a full substitute for UAX cluster segmentation when that is the requirement (Q2, Q10).

---
