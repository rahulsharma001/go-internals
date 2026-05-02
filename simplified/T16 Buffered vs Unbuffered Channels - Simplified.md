# T16 Buffered vs Unbuffered Channels — Simplified

> Layman companion to [[T16 Buffered vs Unbuffered Channels]]. Read the main note for traces and interview drills.

---

## One sentence

**Unbuffered** = no storage; sender and receiver must meet at the same time. **Buffered** = a fixed shelf of `k` items; sender waits only when the shelf is packed full.

---

## Memory picture

| | Unbuffered | Buffered |
|--|------------|----------|
| `make` | `make(chan Order)` → capacity **0** | `make(chan Order, k)` → **k slots** |
| Send blocks when... | Nobody is receiving **right now** | **k** items already waiting and nobody took any |
| Receive blocks when... | Nobody is sending **right now** | Shelf is empty |
| Typical use | "Tell me you're done," strict order | Worker queue, burst absorption, concurrency cap |

---

## Rules you say out loud

1. **Default capacity is zero** — `make(chan T)` is unbuffered, not buffered.
2. **Buffer helps bursts, not miracles** — if consumers are always slower, the shelf fills and senders still block.
3. **Big buffer = big memory + hidden lag** — you only postponed the pain.
4. **`<-struct{}` / `struct{}{}` channel** with fixed size is a common **"only N at a time"** pattern — easy to leak a token if you forget `defer` release.
5. **Closing** works the same — buffered may still have items to drain first.

---

## When interviewers smile

- You name **blocking conditions** (`qcount == dataqsiz`, empty buffer, closed).
- You pick unbuffered for **handshake** and buffered for **bounded queue / semaphore** with a **numeric reason** for `k`.
- You admit **channel has a lock inside** — mutex still wins for tiny shared counters sometimes.

---

> Deep runtime walkthrough: [[T15 Channel Internals]]
