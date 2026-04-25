# T04 Arrays & Slice Internals — Simplified

> This is the plain-English companion to [[T04 Arrays & Slice Internals]].
> Read this when the main note feels overwhelming.

---

## 1. What is this, in plain English?

Imagine you need a place to line up many values of the same type. Go gives you two different tools, and the names sound similar, but they are not the same thing.

**Why it matters at all?** If you do not know how a fixed list differs from a window into memory, you will get surprise sharing, surprise growth, and surprise holding on to memory you thought you had dropped.

An **array** in Go is a value whose size is part of the type. Think of a row of hotel rooms that was built with an exact number of rooms. The building permit says how many keys exist. You cannot add another room without changing the whole building. That fixed shape is the array.

A **slice** is different. It is not a second building. It is a small card you carry that describes a *view* into a row of storage somewhere else. The card says which room to start in, how many rooms count as “in use” for you, and how many room slots the hotel actually reserved behind that same stretch of hallway. The slice is the card. The long row of real rooms is the **backing array** in technical language — here, think of it as the real hotel block that holds the guests.

**Takeaway in one breath:** the array is the fixed row of cells. The slice is a tiny description that points at part of a row. Most everyday Go code that looks like a list is a slice, not an array.

---

## 2. The one thing to remember

**A slice is a small bundle of information that points at shared storage. Copying the slice copies the bundle, not the whole hotel.**

If two people have **photocopies of the same window card**, they are still looking at the **same** rooms. Change what is in a room, and the other person sees the change. That is the main mental model you need for interviews and for debugging.

---

## 3. How to picture it in your head

### The hotel and the building permit

Imagine a new hotel. The sign out front is frozen as soon as the building exists: “Exactly ten rooms, no more, no less.” You cannot go back and bolt on room eleven without building a new hotel. That is an array type in Go. The number of rooms is known when the type is written down.

A slice is not that sign. A slice is the **view card** the front desk gives a tour group. The card might say: start at room three, the tour covers four rooms, and the hotel’s floor actually has ten rooms along that same corridor. The card is cheap to print. The **hotel block** (backing array) is the expensive part. Many cards can point into the same block.

### Photocopying the window card

When you pass a slice to a function, you are not moving every guest. You are **photocopying the window card**: start index, how many you count, how many slots the hotel reserved. Both the caller and the function hold cards that can describe the same rooms. If one side writes into a room, the other side’s view of that same room changes.

### Adding a guest inside the space you can already use

**Append** is the usual way to add another item at the end. Think: “put one more person in a room the window can already see, and the hotel has an empty key for.” If the hotel has spare rooms **inside the capacity the slice already allows**, nobody moves the building. The desk updates the “how many rooms you count as in use” number. That is “append” staying inside the existing reservation.

### When the hotel is full

If you need a new room but every reserved slot along the corridor is taken, the hotel does not squeeze harder. The system books a **bigger** hotel, moves everyone, and gives you a **new** window card that points at the new block. The old view cards that still pointed at the old address now describe stale, abandoned rooms. If you did not get the return value from the append operation, you might still look at the old small hotel and think the new guest is there, when the real party is in the new building. That is the classic “append surprise.”

### A smaller view on the same block

A **sub-slice** is a second window card that looks at a middle stretch of the same row. The view might start at room two and end before room six. The **backing block** is still the same big hotel. Only the numbers on the card changed. That is why cutting a big slice into a small one can still keep the **whole** big block alive in memory, even if the small view only “needs” a few rooms — the hotel still counts the full reservation for garbage collection, unless you copy into a new, tight building.

### The three-index form

Sometimes you want a view card that says not only “where we start” and “where we end today,” but also “you may not grow past this line.” Think of a window with a **hard border** you cannot open past, even if the floor beyond exists. The three-index slice expression is that: a window with an explicit end to how far the slice is allowed to grow on that backing row. It is a safety rail on the card.

---

## 4. How it works under the hood (simple version)

**Under the hood** means: what does the program actually pass around, in memory, when you juggle these ideas? Imagine you could open the front desk drawer and read the numbers written on each slice’s small card. That is what this section names in slow motion.

1. An **array value** is a solid block. If you have ten integers in the type, the value *is* those ten cells lined up, right there. Copying the array **copies every room’s contents** into a new building of the same size. The two rows are independent. Change one, the other is untouched.

2. A **slice value** is a small struct-like bundle: where the first visible room is in the backing block, how many elements count for this slice, and what total span of the backing block this slice is allowed to use before a move must happen. The words programmers use in the main note for those three are **pointer**, **length**, and **capacity** — in this companion, read them as **address of first used room**, **count of in-use elements**, and **count of room slots you could fill before the runtime must get a new block**. No abbreviations in your head: three separate numbers, each doing a job.

3. **Passing a slice to a function** copies that small bundle. The copy still points to the same backing block. So element writes show up everywhere. Appending, though, can replace the **pointer** in the result bundle if the block was full, while an older bundle in the caller still points at the old place. That is why you assign the return value of the append from the same package’s variables.

4. **Copy** in the standard library means: walk two windows, move elements from the source view into the destination view, up to the smaller of the two lengths. The buildings involved may be the same or different, but the **element values** are what get copied, not the window card structure.

5. The **empty slice** is often a card that says: start nowhere useful, count zero, capacity zero. Sometimes it is a card with capacity but length zero, meaning “a reserved stretch is paid for, but no guest has checked in yet” — a common pattern for performance if you know many guests are coming.

---

## 6. The code, explained line by line

**Example: a fixed array type**

```go
var rooms [3]int
rooms[0] = 10
```

You have exactly three `int` cells, names `rooms[0]`, `rooms[1]`, `rooms[2]`. The size `3` is not a runtime option; it is baked into the type. This is the small hotel with three built-in keys and no wiggle room.

**Example: make a slice, append, and share**

```go
a := make([]int, 0, 4)
a = append(a, 1)
b := a
b[0] = 99
// a[0] is now 99 as well, because a and b share the first backing view
```

`make` with three arguments builds an empty “used length” with room to grow. The first number is **length** (how many you count in use, here zero). The second number to `make` is **capacity** (how many slots exist in the block before a move). The next line appends a single `1` into the first slot, growing the used count. Then `b := a` copies the slice **header**, not a deep list. Both names look at the same block, so writing through `b` changes what you see through `a`.

**Example: sub-slice and shared backing**

```go
all := []int{0, 1, 2, 3, 4, 5, 6}
part := all[1:3]
// part is length 2, but still backed by the same array as all
```

The window opens at index one, runs for two values. The big and small views are different cards, but the same underlying row of `int` values.

**Example: three index slice, limiting growth on the same block**

```go
s := all[1:3:3] // from index 1, length 2, capacity 2
```

The third number caps how far the slice can extend without a new block. The main note will spell out the exact rules; here, the picture is: your window is **nailed** on the right side, so the slice cannot be extended in place to eat room three from the same backing row.

Read the main note for the full rules about when **append** copies to a new block, and for how the compiler and the garbage collector see slice headers.

---

## 7. The traps, explained simply

**You forgot that append can move everyone.** You append, ignore the return value, and the old slice still points at a small, abandoned block. The fix: always write `s = append(s, x)` for the name that should track the new view.

**You thought sub-slicing shrank the hotel.** Slicing only changes the window card. The big block behind the full original slice can stay alive, which keeps a lot of data around if a tiny sub-view is all you still need in a long-running program. The fix: copy into a new slice of exactly the right length if you need a tight, independent value.

**You copied slices into a new struct and expected independence.** A struct copy is shallow: each slice field’s header is copied, but the backing block is the same. Two structs can still trample the same memory.

**You mixed up length and capacity.** **Length** is what you treat as the real count for loops and for “is this empty.” **Capacity** is how many slots exist before a move. They only match when the slice is full. Think of a party in four reserved rooms: length is how many people are inside; capacity is how many key slots the hotel tied to the same string of doors.

**You read “pass by value” and thought a slice is safe to pass without side effects on storage.** The value passed is small, but the **storage** is shared. Pass by value does not clone the hotel, only the window card.

---

> Ready for the full technical version? → [[T04 Arrays & Slice Internals]]
