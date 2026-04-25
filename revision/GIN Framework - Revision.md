# GIN Framework — Revision Card

> Drill-down from [[Daily Revision]] | Full notes → [[frameworks/GIN Framework]]
> Q&A bank → [[questions/GIN Framework - Interview Questions]]

---

## Recall Grid (answer each, then check)

| # | Prompt | Check |
|---|--------|-------|
| 1 | Route lookup complexity | Radix tree (httprouter): about O(path length) / O(log n) vs flat map in spirit |
| 2 | Middleware chain and `c.Next()` | Handlers wrap; code before/after `c.Next()` is before/after child handler |
| 3 | `gin.Context` lifetime | Pooled via `sync.Pool`; not safe to use after request returns; not goroutine-safe by default |
| 4 | Async work in handlers | Use `c.Copy()` if passing context to another goroutine |
| 5 | `Bind` vs `ShouldBind` | `ShouldBind` does not `Abort()`/write 400; prefer for explicit error handling in prod |
| 6 | `r.Run()` in production | Hides `http.Server`; need graceful shutdown, so build server explicitly |
| 7 | Hardening HTTP server | Set `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`, `IdleTimeout` on `http.Server` |
| 8 | Concurrency model | One goroutine per request (from net/http); handlers should not block the pool unbounded |

---

## Core Visual

```
  Request
     │
     ▼
  Recovery            Logger            Auth            Handler
  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
  │ (before)   │   │ (before)   │   │ (before)   │   │  handle()  │
  │  c.Next()  │—►│  c.Next()  │—►│  c.Next()  │—►│  (200/JSON) │
  │ (after)    │◄─│ (after)    │◄─│ (after)    │   └────────────┘
  └────────────┘   └────────────┘   └────────────┘
        inward: Recovery then Logger then Auth then Handler; outward retrace for "after" code
```

---

## Top Interview Questions (quick-fire)

**Q: How does Gin routing differ from `http.DefaultServeMux`?**
Gin (via httprouter) uses a radix tree for parameterized routes and efficient matching. `DefaultServeMux` is a simpler pattern/suffix matcher and is not a drop-in for high-throughput path-param APIs.

**Q: Why is `gin.Context` not goroutine-safe?**
Contexts are reset and returned to `sync.Pool` after the request; another request may get the same struct. You must not share one context across concurrent work without `c.Copy()`.

**Q: How do you shut down Gin gracefully?**
Run `http.Server` yourself with `ListenAndServe` in a goroutine, trap `SIGINT`/`SIGTERM`, call `Shutdown` with a timeout context, then exit. Avoid only calling `r.Run()` with no signal handling.

---

## Verbal Answer (say this out loud)

> "Gin uses httprouter's radix tree for O(log n) routing. Middleware forms a handler chain executed via c.Next() creating before/after phases. gin.Context is recycled from sync.Pool and is NOT goroutine-safe. In production: use ShouldBind, explicit http.Server with timeouts, graceful shutdown via signal handling."

---
