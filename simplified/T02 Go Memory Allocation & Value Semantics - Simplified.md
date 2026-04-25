# T02 Go Memory Allocation & Value Semantics — Simplified

> This is the plain-English companion to [[T02 Go Memory Allocation & Value Semantics]].
> Read this when the main note feels overwhelming. Every concept is explained with real-world analogies.

---

## 1. What is this, in plain English?

When your Go program creates a variable (a number, a string, a struct), that data has to live somewhere in your computer's memory. Go has two places it can put things: the **stack** and the **heap**. This topic is about how Go decides where to put things, and what happens when you pass data between functions.

---

## 2. The one thing to remember

**Go always makes a photocopy of your data when passing it to a function — it never hands over the original.**

---

## 3. How to picture it in your head

### The Stack — Your Personal Notepad

Imagine you're at your desk. You have a small notepad where you jot down quick notes while working on a task. When you finish the task, you rip off the page and throw it away. That's the stack.

- It's fast — scribbling on a notepad is instant
- It's private — only you can see your notepad
- It auto-cleans — when the task is done, the page is gone
- It's small — your notepad only has so many pages

In Go, every function call is like a "task." When the function starts, it gets a fresh page on the notepad. When the function returns, that page is thrown away.

### The Heap — The Office Whiteboard

Now imagine there's a big whiteboard in the shared office area. Anyone in the office can walk up and read it. Things written on the whiteboard stay there until a cleaning crew (the **Garbage Collector**) comes around and erases the stuff nobody is looking at anymore.

- It's slower — you have to walk to the whiteboard instead of just looking at your desk
- It's shared — any goroutine (think: any coworker) can see it
- Someone has to clean it — the Garbage Collector periodically checks what's still needed
- Every item on the whiteboard creates cleanup work for the Garbage Collector

### When does Go use the whiteboard instead of your notepad?

Go's compiler (the program that turns your code into an executable) looks at your code **before it runs** and asks:

> "When this function ends and the notepad page is thrown away, will anyone else still need this data?"

If yes → put it on the whiteboard (heap).
If no → keep it on the notepad (stack).

This decision process is called **escape analysis**. The compiler checks if the variable "escapes" beyond the function's lifetime.

**Four situations where data escapes to the heap:**
1. You return a pointer to a local variable — the function is about to end, but someone outside still needs the data
2. You send data to another goroutine or a channel — another "coworker" needs to see it
3. The size isn't known until the program runs — the compiler can't plan the notepad space
4. You put a value into an interface — the value gets "boxed" into a standard-sized container on the heap

If none of these apply → data stays on the stack (notepad). Fast and free.

### Pass-by-value — The Photocopy Machine

Every time you pass data to a function in Go, imagine you're running it through a photocopy machine. The function gets a copy, not the original.

**Even pointers are copied.** But here's the trick: if you photocopy a piece of paper that says "look in locker #42," both the original and the copy point to the same locker. So while the pointer itself is copied, the thing it points to is shared.

---

## 4. How it works under the hood (simple version)

### Why does Go have two memory locations?

Think of it this way:
- The **stack** is like a pile of papers on your desk. Adding a paper (pushing) and removing the top paper (popping) is nearly instant. But the pile only works if you always remove the most recent paper first.
- The **heap** is like a big filing cabinet. You can put files in any drawer and retrieve any file at any time. But organizing the filing cabinet and cleaning out old files takes effort.

Functions in Go follow a strict order — A calls B, B calls C, C returns, then B returns, then A returns. This "last in, first out" pattern is perfect for a stack. But if C creates data that A needs after B and C are done, that data can't stay on C's stack page — it has to go in the filing cabinet (heap).

### Escape Analysis — How the Compiler Decides

The compiler reads your code and follows a simple checklist:

1. **Does the data leave the function?** (returned as a pointer) → Heap
2. **Does the data go to another goroutine?** (sent through a channel or used in a `go` statement) → Heap
3. **Is the size unknown until runtime?** (like `make([]byte, userInput)`) → Heap
4. **None of the above?** → Stack

You can ask the compiler to show you its decisions:
```bash
go build -gcflags="-m" your_file.go
```
It will print lines like `x escapes to heap` or `x does not escape`.

### The Garbage Collector — The Cleaning Crew

Since heap data doesn't get automatically cleaned up like stack data, Go has a background cleaning crew called the Garbage Collector. It works like this:

1. It looks at all the data your program is currently using (starting from global variables and function stacks)
2. It follows every pointer to see what's still reachable
3. Anything that's NOT reachable from any active part of the program = garbage
4. Garbage gets freed, making room for new data

The Garbage Collector runs **while your program is running** (concurrently). It only pauses everything for a tiny moment (less than a millisecond) to do some bookkeeping.

**Why this matters for performance:** Every piece of data on the heap is something the Garbage Collector has to check. More heap data = more work for the cleaning crew = occasional slowdowns. This is why Go developers care about reducing heap allocations.

### Stack Growth — The Expanding Notepad

Each goroutine starts with a small stack (about 2-8 kilobytes). If a function needs more space than is available, Go allocates a bigger stack, copies everything over, and fixes all the pointers that pointed to the old location.

Think of it like: your notepad is full, so you get a bigger notepad, carefully copy all your notes to the new one, and update any "see page X" references to point to the right pages in the new notepad.

This is also why Go doesn't allow pointer arithmetic (doing math on memory addresses directly) — if the stack moves, those calculated addresses would become wrong.

---

## 6. The code, explained line by line

### Example 1: Why returning a pointer causes heap allocation

```go
func foo() *int {
    x := 10      // x is created on foo's stack page
    return &x    // we return the ADDRESS of x
}                // foo's stack page is about to be destroyed!
```

The problem: `foo` is returning a pointer to `x`, but `x` lives on `foo`'s notepad page. When `foo` returns, that page gets thrown away. So Go moves `x` to the whiteboard (heap) where it'll survive.

If we DON'T return a pointer:

```go
func bar() int {
    x := 10      // x is created on bar's stack page
    p := &x      // p points to x (both on the same notepad page)
    return *p    // we return the VALUE (10), not the address
}                // nothing needs to survive — stack is fine
```

Here, nothing escapes. We return the number 10, not a pointer. When `bar` returns, `x` and `p` are thrown away — and that's fine because nobody outside needs them.

### Example 2: The slice append trap

A slice in Go is like a window into an array. The slice itself is a small sticky note with three pieces of info:

```
Slice sticky note:
  1. Where does the array start? (a pointer)
  2. How many items am I showing? (length)
  3. How many items COULD I show? (capacity)
```

When you pass a slice to a function, Go photocopies this sticky note. Both the original and the copy look at the same array.

```go
data := []int{10, 20, 30}   // sticky note pointing to [10, 20, 30]
modify(data)                  // photocopy the sticky note
```

Inside `modify`, if you change `s[0] = 100`, it changes the actual array — both sticky notes still point to the same array. The change is visible.

But if you `append` and the array is full:

```go
func grow(s []int) {
    s = append(s, 4)   // array is full! Go creates a NEW bigger array
}                       // s (the photocopy) now points to the new array
                        // but the caller's sticky note still points to the OLD array!
```

The caller never sees the new element because their sticky note wasn't updated. The fix: return the new sticky note.

```go
func grow(s []int) []int {
    return append(s, 4)    // return the updated sticky note
}
data = grow(data)           // caller updates their sticky note
```

### Example 3: The interface nil trap

Think of a Go interface as a gift box with two parts:
1. **A label** on the outside saying what's inside (the type)
2. **The actual thing** inside (the value)

The box is truly empty (nil) only when there's **no label AND nothing inside**.

```go
var p *MyStruct = nil       // a nil pointer — like an empty toy car box
var i interface{} = p       // put it in a gift box
```

Now the gift box has:
- Label: "contains a *MyStruct"
- Contents: nil (nothing)

Is the gift box empty? **No!** It has a label. Go sees the label and says "this box has something going on."

```go
fmt.Println(i == nil)   // false! — the box has a label
```

To make a truly nil interface (empty box with no label):

```go
var i interface{} = nil   // no label, no contents → truly nil
fmt.Println(i == nil)     // true
```

**The practical trap:** If a function returns an error interface, NEVER do this:

```go
// BAD
func getUser() error {
    var err *MyError = nil
    return err          // returns a "box with label but no contents" — NOT nil!
}

// GOOD
func getUser() error {
    return nil          // returns a truly empty box — IS nil
}
```

---

## 7. The traps, explained simply

### Trap 1: Append doesn't update the caller

Think of it like giving someone a photocopy of a map showing where your house is. If you move to a new house (append causes a new array), the person with the photocopy still has the old address. You need to give them a new map (return the new slice).

### Trap 2: Sub-slice memory leak

If you have a 1000-page book and you tear out pages 1-3, you still have a reference to the binding that holds all 1000 pages. The book can't be recycled. Instead, photocopy pages 1-3 onto fresh paper (use `copy`), and the 1000-page book can be recycled.

### Trap 3: Copying a mutex

A mutex is like a bathroom key at a coffee shop — there's only one, and whoever has it gets to use the bathroom. If you photocopy the key (value receiver copies the struct), now there are TWO keys — two people can be in the "bathroom" at the same time. That defeats the purpose. Always use a pointer receiver with mutexes so everyone uses the same key.

### Trap 4: Loop variable capture (pre-Go 1.22)

Imagine a tour guide saying "look at what I'm pointing at" to three different groups, but by the time each group looks, the guide is pointing at the last stop. All three groups see the same thing. The fix (before Go 1.22): take a photo of what the guide is pointing at right now (copy the variable). Go 1.22 fixed this automatically.

---

> Ready for the full technical version? → [[T02 Go Memory Allocation & Value Semantics]]
