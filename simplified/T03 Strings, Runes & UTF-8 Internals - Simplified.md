# T03 Strings, Runes & UTF-8 Internals — Simplified

> This is the plain-English companion to [[T03 Strings, Runes & UTF-8 Internals]].
> Read this when the main note feels overwhelming. Every concept is explained with real-world analogies.

---

## 1. What is this, in plain English?

A Go string is like a sealed envelope with a letter inside. The envelope has a label that says how many ink marks (bytes) are on the letter. You can look at the letter, you can photocopy parts of it, but you can never erase or change the ink on the original letter.

The twist: some characters take up more ink marks than others. The letter "A" takes one ink mark. The Chinese character "世" takes three ink marks. An emoji like "😀" takes four ink marks. When Go tells you "this letter has 13 ink marks," it's telling you about ink marks, not about how many characters you'd count if you read it.

---

## 2. The one thing to remember

**A Go string measures its length in bytes (ink marks), not in characters (letters you can read).**

---

## 3. How to picture it in your head

### The Address Card Analogy

Imagine you have a library card. The card has two things on it:
1. **A shelf address** — which shelf in the library holds your book
2. **A page count** — how many pages the book has

That's exactly what a Go string is. It's a tiny card (16 bytes) with:
1. A pointer — the memory address of where the text lives
2. A length — how many bytes the text takes up

When you hand someone your string, you're not giving them the whole book. You're giving them a **photocopy of your library card**. They can go look at the same book, but they can't write in it.

### The Morse Code Analogy

Think of how Morse code works. The letter "E" is just one dot. The letter "Q" is dash-dash-dot-dash — four symbols. If someone sends you a Morse message that's 20 symbols long, you can't just divide by one to know how many letters there are. You have to decode it.

That's exactly how Go strings work with a system called "UTF-8":
- Simple English letters = short codes (1 byte each, like "E" in Morse)
- Accented letters like "é" = medium codes (2 bytes)
- Chinese/Japanese characters = longer codes (3 bytes)
- Emojis = the longest codes (4 bytes)

When Go says `len(s) = 13`, it's counting Morse symbols. When you want to know actual letters, you need to decode.

### Bytes vs Runes — The Gift Box Analogy

Think of it like wrapping gifts:
- A **byte** is one piece of wrapping paper. Small gifts need one piece. Big gifts need more.
- A **rune** is the actual gift inside the wrapping. It's what you care about — the character.
- A **string** is a sealed box containing many wrapped gifts in a row.

When you ask "how big is the box?" (`len()`), you get the total wrapping paper count. When you ask "how many gifts are inside?" (`RuneCountInString()`), you get the number of actual characters.

---

## 4. How it works under the hood (simple version)

### The String Card

Every string in Go is really just a tiny card with two numbers:

```
┌───────────────────────────┐
│ Where the text is: 0x1234 │  (an address in memory)
│ How many bytes:    5      │  (NOT how many characters)
└───────────────────────────┘
```

This card is always exactly 16 bytes, no matter if the string is "hi" or the entire works of Shakespeare. The text itself is stored somewhere else in memory, and the card just points to it.

### Why strings can't be changed

Imagine the book in the library is printed, bound, and shelved. You can't erase a word from a printed book. If you want a different version, you need to print a new book.

Same with Go strings. The bytes are "printed" and sealed. To change a string, Go creates a brand new set of bytes, copies what it needs (with your changes), and gives you a new card pointing to the new text.

### How the variable-width encoding works

Imagine a parking lot where compact cars get 1 space and trucks get 2-4 spaces:

```
Parking lot for "café":
  Space 0: [c]       — compact car (1 space)
  Space 1: [a]       — compact car (1 space)
  Space 2: [f]       — compact car (1 space)
  Space 3: [é part1] — truck (takes 2 spaces)
  Space 4: [é part2]

Total spaces used: 5
Total vehicles: 4
```

When Go tells you there are 5 spaces, it's counting parking spots (bytes). The actual vehicle count (characters) is 4.

### How "for range" reads characters correctly

When you write `for i, r := range s`, Go walks through the parking lot intelligently:

1. Look at space 0 → compact car? Take 1 space. Character: 'c'
2. Look at space 1 → compact car? Take 1 space. Character: 'a'
3. Look at space 2 → compact car? Take 1 space. Character: 'f'
4. Look at space 3 → truck front bumper? Take 2 spaces. Character: 'é'
5. Space 5 → past the end, stop.

It knows how many spaces each vehicle takes by looking at the first byte (the front bumper). That byte has a pattern that says "I'm a 1-space vehicle" or "I'm a 2-space vehicle" and so on.

---

## 6. The code, explained line by line

### The length trap

```go
s := "café"
fmt.Println(len(s))  // Prints 5, not 4!
```

Why 5? Because "c", "a", and "f" each take 1 byte, but "é" takes 2 bytes. Total: 1+1+1+2 = 5 bytes. The `len()` function counts bytes, not letters.

To count actual letters:

```go
fmt.Println(utf8.RuneCountInString(s))  // Prints 4 — the letter count
```

### The two ways to loop

**Way 1 — byte by byte** (usually wrong for text):

```go
for i := 0; i < len(s); i++ {
    fmt.Printf("%x ", s[i])  // prints each raw byte
}
// For "café": 63 61 66 c3 a9
// That's 5 values — the 'é' got split into two bytes (c3 and a9)
```

**Way 2 — character by character** (usually what you want):

```go
for i, ch := range s {
    fmt.Printf("%c ", ch)  // prints each actual character
}
// For "café": c a f é
// That's 4 values — 'é' is handled as one character
```

### The integer-to-string surprise

```go
fmt.Println(string(65))   // Prints "A", NOT "65"!
```

Why? `string(65)` treats 65 as a character code (Unicode code point). Code point 65 is the letter "A". If you want the text "65", use `strconv.Itoa(65)`.

---

## 7. The traps, explained simply

### Trap 1: Keeping a huge string alive by accident

Imagine you have a 1000-page book and you photocopy page 1. Your photocopy is just a card that says "go to shelf X, start at page 1, read 1 page." The library can't throw away the 1000-page book because your card still points to it.

Same with Go strings. If you do `small := huge[:5]`, that tiny string still holds a reference to the entire original. The garbage collector can't free the big one.

**Fix:** Make an actual copy: `small := strings.Clone(huge[:5])`

### Trap 2: Reversing a string by reversing bytes

If you reverse the bytes of "café", you get garbage. The two bytes of "é" (which are like two halves of a puzzle piece) get separated and reversed, so they no longer make sense together.

**Fix:** Convert to a character list first, reverse that, then convert back. In Go: convert to `[]rune`, reverse, convert to `string`.

### Trap 3: Thinking all characters are the same size

People often write code assuming every character is exactly one byte. This works perfectly for English — every ASCII letter is one byte. But the moment you have accented letters, Chinese characters, or emojis, the assumption breaks and your code either crashes or produces wrong results.

**Fix:** Use `for range` instead of `for i := 0; i < len(s); i++` when processing text.

---

> Ready for the full technical version? → [[T03 Strings, Runes & UTF-8 Internals]]
