# T16 Buffered vs Unbuffered Channels — Exercises

> Solutions for Tier 3 live in this file. Tiers 1–2 are warm-ups inside [[T16 Buffered vs Unbuffered Channels]] Section 6.

---

## Tier 1 — Warm-up (do in main note)

Predict-the-output problems 1–3 — answers collapsed in Section 6.2.

---

## Tier 2 — Short design answers (5 min each)

1. You have **one writer** and **one reader** for a shutdown flag. Argue for **unbuffered** vs **buffer size 1**.
2. Your API ingests **10×** traffic for **30s** daily; sink is **3×** steady. What role does a buffer play? What fails if buffer is too small? Too large?

---

## Tier 3 — Code (15–25 min)

### Exercise 3.1 — Bounded parallel image fetches

Write `FetchAll(ctx, urls []string, limit int) ([]byte, error)` that fetches with **at most `limit` concurrent HTTP requests**, using **only** a `chan struct{}` semaphore and `errgroup` or manual `WaitGroup`. Handle **context cancel**: waiting acquires must give up.

> [!success]- Solution sketch
> ```go
> package main
>
> import (
> 	"context"
> 	"io"
> 	"net/http"
> 	"sync"
> )
>
> func FetchAll(ctx context.Context, urls []string, limit int) ([][]byte, error) {
> 	if limit < 1 {
> 		limit = 1
> 	}
> 	sem := make(chan struct{}, limit)
> 	var wg sync.WaitGroup
> 	out := make([][]byte, len(urls))
> 	var errOnce sync.Once
> 	var firstErr error
> 	for i, u := range urls {
> 		i, u := i, u
> 		wg.Add(1)
> 		go func() {
> 			defer wg.Done()
> 			select {
> 			case <-ctx.Done():
> 				return
> 			case sem <- struct{}{}:
> 			}
> 			defer func() { <-sem }()
> 			req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
> 			if err != nil {
> 				errOnce.Do(func() { firstErr = err })
> 				return
> 			}
> 			resp, err := http.DefaultClient.Do(req)
> 			if err != nil {
> 				errOnce.Do(func() { firstErr = err })
> 				return
> 			}
> 			defer resp.Body.Close()
> 			b, err := io.ReadAll(resp.Body)
> 			if err != nil {
> 				errOnce.Do(func() { firstErr = err })
> 				return
> 			}
> 			out[i] = b
> 		}()
> 	}
> 	wg.Wait()
> 	return out, firstErr
> }
> ```
> **Note:** Prefer `errgroup.Group` when you want the first error to cancel peers; semaphore pattern stays the lesson.

### Exercise 3.2 — Explain buffer size for worker pool

Given `workers = 8` and **variable-length** `[]Order`, why might you set `jobs := make(chan Order, workers*4)` instead of `workers`? When is `workers*4` **worse** than `workers`?

> [!success]- Model answer
> **Skew:** some jobs fast, some slow — extra depth lets producers stay ahead while stragglers finish.** **Worse:** if each `Order` is huge in memory, `*4` holds more live objects and raises RSS; if consumers die, you hide failure longer.

---

## Self-check

- [ ] I can state **four** send-blocking reasons from memory.
- [ ] I can implement **semaphore** without looking.
- [ ] I can explain why **unbuffered** `done` is often cleaner than `done` with buffer 1 for simple shutdown.
