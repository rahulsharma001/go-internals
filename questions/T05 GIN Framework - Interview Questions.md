# T05 GIN Framework -- Interview Questions

> Comprehensive interview Q&A bank for [[frameworks/T05 GIN Framework]].
> Sorted by frequency at top tech companies. Tags: [COMMON] [ADVANCED] [TRICKY]

---

## Q1: How does Gin's routing differ from Go's default HTTP mux? [COMMON]

**Answer:**

**In one line:** Go's `DefaultServeMux` is map plus longest-prefix style matching with O(n) worst case and no native path parameters, while Gin's httprouter radix tree gives O(log n) lookups with method-specific trees, `:param` and `*wildcard` support, and strong middleware fit; Go 1.22 improved `ServeMux` but Gin still wins for large route sets and ecosystem depth.

**Visualize it:**

```
DefaultServeMux (simplified)          Gin / httprouter (per method)
---------------------------          ------------------------------
  [exact map]  --> key match           GET  tree:   /a --> /b --> :id
  [prefix]     --> walk / scan           POST tree:  /a --> *catchall
  O(n) paths in worst case             O(log n) radix / compressed trie
  no :id in stdlib (pre-1.22)          :param, *wildcard native
        |                                      |
   single mux                           GET /  POST /  PUT /  (separate trees)
```

**Key facts:**
- `DefaultServeMux` uses a map for exact matches and longest-prefix matching; worst case is O(n) and there were no native path parameters in older Go (Go 1.22 added pattern matching to `ServeMux`).
- Gin uses httprouter's radix tree (compressed trie): O(log n) route resolution with zero allocations during matching for typical paths.
- Gin supports `:param` path parameters and `*wildcard` segments natively; routes are split per HTTP method (separate trees for GET, POST, etc.).
- Since Go 1.22, `ServeMux` gained useful pattern matching, but Gin's radix tree remains faster for very large route sets and pairs with a richer middleware ecosystem.

**Interview tip:** Show awareness of Go 1.22 changes, then explain why Gin is still relevant for complex APIs and heavy middleware or validation.

> [!example]- Full Story: Mux map vs Gin's radix per method
>
> **The problem:** A growing REST surface needs fast lookups, named segments, and predictable behavior when two paths overlap; a flat map and prefix walk do not scale or express `:id` the same way a trie does.
>
> **How it works:** `DefaultServeMux` resolves registered patterns with exact and prefix rules; with many entries, you pay linear-style costs in the worst case. Gin builds compressed radix tries per HTTP verb so a single descent resolves the best match. Parameters become nodes or suffix captures; wildcards take remainder segments. That layout also keeps read-only data after `Run`, which pairs well with hot-path concurrency (see Q9).
>
> **What to watch out for:** Benchmarks and route counts matter: small services may not see the win. After Go 1.22, compare `ServeMux` patterns to Gin when deciding; still justify Gin for middleware, validation, and very large or dynamic route tables.

---

## Q2: Explain Gin's middleware execution model. [COMMON]

**Answer:**

**In one line:** Middleware in Gin is an ordered `[]HandlerFunc` chain where each step can run code before and after the rest of the stack via `c.Next()`, and `c.Abort()` short-circuits all downstream handlers, producing a Russian-doll wrap like Recovery around Logger around Auth around your route.

**Visualize it:**

```
Request -->
   [Global MW 1]  -- before --> c.Next() -- after -->
        [Group MW]   -- before --> c.Next() -- after -->
             [Route handler]
                   ^
   c.Abort() sets index: no more "inner" handlers run

"Russian doll":  Recovery( Logger( Auth( YOUR_HANDLER ) ) )
```

**Key facts:**
- Gin stores middleware as `[]HandlerFunc`. For a matched route the chain is: global middleware, then group middleware, then the route handler.
- An internal index drives sequential execution. `c.Next()` calls the next handler; code before `c.Next()` is the request phase, code after is the response phase (after inner handlers return).
- `c.Abort()` sets the index to a sentinel so subsequent handlers never run—use when auth fails or a response is already written.
- The pattern matches Express or Django style middleware: outer wrappers see the full round trip for inner work.

**Interview tip:** Draw the nesting on a whiteboard. Mention that this is the same pattern as Express.js middleware or Django middleware.

> [!example]- Full Story: Building and traversing the handler chain
>
> **The problem:** You need cross-cutting behavior (log, auth, recovery) without duplicating it in every handler, and you need a clear order when a request must be rejected early.
>
> **How it works:** Gin appends `HandlerFunc` values. When a request hits, the engine runs the first function. If it calls `c.Next()`, control descends; when the deepest handler returns, control unwinds so "after" code in outer middleware runs. `c.Abort()` prevents any deeper handler from running, which is how you short-circuit after sending 401.
>
> **What to watch out for:** Forgetting that `c.Next()` is what creates before/after; writing response twice; assuming order does not matter—register recovery outermost, auth before business logic, and do not call `c.Next()` after you have already written the final body unless you know the chain is designed for it.

---

## Q3: What is gin.Context and why is it not goroutine-safe? [COMMON]

**Answer:**

**In one line:** `gin.Context` is the per-request basket for `Request`, `ResponseWriter`, path params, `Keys`, errors, and chain state, recycled through `sync.Pool` for performance, but it is unsafe across goroutines because its map and writer are not synchronized and the struct is reused after the handler returns.

**Visualize it:**

```
Request goroutine                Another goroutine (BAD)
        |                                 |
  gin.Context                          reads c.Keys
  ├─ Request                           or writes body
  ├─ Writer  <--- not concurrent         while handler
  ├─ Keys map     <--- no mutex          still running? DATA RACE
  └─ pool: Put(c)  ---- after return ---- stale/wrong c reused

Safe pattern:  go func() { c2 := c.Copy(); ... use c2 ... }()
```

**Key facts:**
- `gin.Context` wraps `http.Request`, `http.ResponseWriter`, path params, a string-keyed store (`Keys`), collected errors, and internal chain index state.
- Contexts are obtained from a `sync.Pool` and returned to the pool after the request completes, cutting allocations and GC under load.
- It is not goroutine-safe: the `Keys` map has no mutex; the `ResponseWriter` cannot tolerate concurrent writes; after the handler returns the context can be reset and given to another request.
- For background work, call `c.Copy()` to get a snapshot safe to use in another goroutine (still respect response semantics—do not write to the original writer from multiple goroutines without design).

**Interview tip:** Connecting to `sync.Pool` shows you understand the performance optimization behind Gin's design.

> [!example]- Full Story: Lifecycle and the pool
>
> **The problem:** Per-request state must be cheap to allocate at high RPS, but sharing that state with async work breaks isolation and data races.
>
> **How it works:** The engine gets a `Context` from the pool, fills it for the current request, runs the chain, then resets and `Put`s it back. That implies any reference you leak past the request must not assume the `Context` remains valid. `c.Copy()` duplicates what is needed for async logging or slow IO without holding the pooled struct's mutable fields incorrectly.
>
> **What to watch out for:** Launching `go` with the bare `c`; double responses; reading `c.Keys` in a deferred goroutine after the client disconnected—use `Copy()` and document writer rules for your app.

---

## Q4: What's the difference between c.Bind, c.ShouldBind, and c.MustBind? [COMMON]

**Answer:**

**In one line:** `Bind`/`BindJSON` auto-reply 400 and plain text on failure; `ShouldBind` returns the `error` so you own status and JSON shape; `MustBindWith` panics and is a footgun—prefer `ShouldBind` for consistent API error bodies.

**Visualize it:**

```
BindJSON failure          ShouldBindJSON failure           Must*
      |                            |                        |
  HTTP 400                    return err              panic
  text/plain                  you write JSON            (avoid)
  lose format control         consistent errors
```

**Key facts:**
- `c.Bind` / `c.BindJSON`: on bind or validation failure, Gin automatically responds with 400 and `Content-Type: text/plain`—you lose a unified JSON error envelope.
- `c.ShouldBind` / `c.ShouldBindJSON`: return the error; you map it to your standard problem JSON and status in one place.
- `c.MustBindWith()`: like `Bind` but panics on error—not recommended in production.
- All bind methods ultimately lean on `go-playground/validator/v10` for struct tags, so custom validators and messages can be added consistently when you use `ShouldBind` and central handling.

**Interview tip:** Mention that all bind methods use `go-playground/validator/v10` under the hood, and you can add custom validators.

> [!example]- Full Story: Control vs convenience
>
> **The problem:** Inconsistent 400 bodies across handlers frustrate clients and break monitoring; auto-responses from `Bind` split your error model in two places.
>
> **How it works:** `Bind` is optimized for quick demos: fail fast to the client. `ShouldBind` returns `error` to your code path where middleware or helpers translate validation into `{ "error": { "code", "message", "details" } }`. `MustBind` is only appropriate when failure must never happen, which is almost never in HTTP handlers.
>
> **What to watch out for:** Mixing `Bind` and `ShouldBind` in one codebase; swallowing `validator` error types without unwrapping for field-level messages; not binding `form` vs `json` as intended for the content type.

---

## Q5: How would you structure a production Gin API? [COMMON]

**Answer:**

**In one line:** Layer `handlers` on `services` on `models`, inject dependencies via interfaces, group routes and middleware for versions, set `gin.ReleaseMode`, give `http.Server` real timeouts, use structured logging instead of the default dev logger, and add graceful shutdown plus health and readiness for orchestration.

**Visualize it:**

```
cmd/api/main.go
    -> routes.Register(v1)   // groups: /api/v1
    -> gin.New() + middleware chain (log, auth, errors)
    -> http.Server{ Handler: r, ReadHeaderTimeout, ... }

packages/
  handlers/  -> call services, bind ShouldBind, c.Error
  services/  -> business rules, DB
  models/    -> DTOs, domain types
  middleware/
  routes/    -> groups, versions
```

**Key facts:**
- Package by concern: `handlers/`, `services/`, `models/`, `middleware/`, `routes/` keeps HTTP wiring separate from business rules.
- Handlers depend on service interfaces; wire concrete implementations in `main` or a small `wire`/constructor layer for testability.
- Use route groups for `/api/v1` and to scope middleware. Set `gin.ReleaseMode` in production.
- Avoid bare `r.Run()`: it hides missing server-side timeouts. Prefer explicit `http.Server` with `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`, `IdleTimeout`.
- Add structured logging middleware, `pprof` where appropriate, health and readiness routes for Kubernetes, and graceful `Shutdown` (see Q11).

**Interview tip:** Show that you think beyond "it works" to "it's production-ready." Mention health check endpoints, readiness probes for K8s, and pprof integration.

> [!example]- Full Story: From demo router to operable service
>
> **The problem:** A single `main.go` with global state becomes untestable and hard to change; without timeouts and health signals, the service is fragile in real clusters.
>
> **How it works:** Handlers stay thin: bind, call service, hand off errors. Services hold transactions, caching, and domain validation. `routes` builds versioned groups so v2 can differ without forking the binary. `ReleaseMode` disables debug output and stack traces in responses. The server is constructed explicitly so you can pass it to `Shutdown` and tune for your LB and client behavior.
>
> **What to watch out for:** Circular imports between `handlers` and `services`—define interfaces in the consumer package or a small `ports` package; do not use Gin's default logger in prod; do not block readiness on deep dependencies you do not need for the kubelet check.

---

## Q6: How do you handle errors consistently across a Gin API? [COMMON]

**Answer:**

**In one line:** Centralize mapping from domain errors to HTTP: handlers attach with `c.Error(err)`, a terminal middleware reads `c.Errors` and writes one JSON problem shape, and `CustomRecovery` turns panics into the same style instead of raw stack traces in production.

**Visualize it:**

```
handler:  c.Error(validationErr)  -->  c.Errors grew
         (chain continues)
...
error_middleware (last or near last):
  for _, e := range c.Errors { map to code + status }
  c.JSON(4xx/5xx, { "error": { "code", "message", "details" } })

Panic path:  CustomRecovery  -->  same JSON / log, not plaintext 500
```

**Key facts:**
- Define app error types with stable codes and optional HTTP status; handlers never write random JSON bodies for the same class of failure.
- Use `c.Error(err)` to collect errors; a dedicated middleware at the end of the chain iterates `c.Errors` and serializes a single consistent payload such as `{"error":{"code":"VALIDATION_FAILED","message":"...","details":[...]}}`.
- That keeps responses uniform for clients, metrics, and support; logging can happen once in the same middleware.
- `gin.Recovery()` stops crashes from killing the process; `gin.CustomRecovery()` lets you log with structure and return JSON that matches your API for panics.

**Interview tip:** This demonstrates production API design thinking. Mention that consistent errors help frontend teams and improve debugging.

> [!example]- Full Story: One pipeline for every failure mode
>
> **The problem:** Each handler returning a different `gin.H` for errors makes clients and SLOs impossible to standardize; you need one contract for 400, 404, 409, and 500.
>
> **How it works:** Application code wraps failures in types the middleware understands (or use sentinel errors and `errors.As`). The middleware serializes, logs with trace IDs, and never leaks internal messages you do not want public. `c.Errors` can hold multiple; usually you only emit the first client-facing and log the rest.
>
> **What to watch out for:** Double-writing: handler already wrote body then `c.Error` still runs—set flags or `c.IsAborted()` patterns; logging sensitive validation details in production; forgetting to test the panic path in CI.

---

## Q7: How do you test Gin handlers? [COMMON]

**Answer:**

**In one line:** Use `httptest.NewRecorder` with `gin.CreateTestContext` to call the handler directly with a synthetic `Request` and asserted `Params`, or mount the real router on `httptest.NewServer` for integration tests, with dependencies mocked behind interfaces and cases driven by table-driven tests.

**Visualize it:**

```
Unit:                          Integration:
  httptest.NewRecorder()          full gin.Engine
  + CreateTestContext(w)        + httptest.NewServer(router)
  + NewRequest/Params             real HTTP client
  -> handler(c)                 -> end-to-end status/body
  -> assert w.Code, body
```

**Key facts:**
- For unit tests: `w := httptest.NewRecorder()`, `c, _ := gin.CreateTestContext(w)`, set `c.Request` and `c.Params` to mimic routing, call `handler(c)`, assert `w.Code`, body, and headers.
- Mock services via small interfaces; inject fakes in tests. Table-driven subtests keep cases for 200, 400, 404, 500 in one function.
- For integration tests, build the same router you use in production and hit it with `httptest.NewServer` or a real local port, asserting external behavior and middleware ordering.

```go
w := httptest.NewRecorder()
c, _ := gin.CreateTestContext(w)
c.Request = httptest.NewRequest("GET", "/users/1", nil)
c.Params = gin.Params{{Key: "id", Value: "1"}}
handler(c)
assert.Equal(t, 200, w.Code)
```

**Interview tip:** Show that you test handlers in isolation (unit) and together (integration). Mention table-driven tests for multiple scenarios.

> [!example]- Full Story: Isolation and realism
>
> **The problem:** Testing only the full server is slow; testing only internal functions misses binding, params, and middleware.
>
> **How it works:** `CreateTestContext` gives a real `Context` with a `ResponseRecorder` in memory, so the handler's writes are inspectable. Set `c.Request` with the method, path, and body; set `c.Params` for `:id` matches. For DB-heavy handlers, the service is mocked: you verify HTTP mapping and error paths without PostgreSQL. Integration tests can seed data or use testcontainers for confidence before release.
>
> **What to watch out for:** Forgetting to set `Params` when the handler reads `c.Param` without going through the router; mode (`gin.SetMode(gin.TestMode)`) to silence logs; not resetting global state if any exists between subtests.

---

## Q8: When would you NOT use Gin? [TRICKY]

**Answer:**

**In one line:** Skip Gin when a few stdlib routes suffice, when the main surface is gRPC, when you are building WebSocket-first servers, in tight serverless cold paths, or when you need features Gin does not expose (like HTTP/2 server push) because extra routing and abstractions are pure overhead.

**Visualize it:**

```
Use stdlib / minimal          Use Gin
--------------------          -------
 2-3 endpoints                 many routes
 zero deps                    middleware, validation, groups
gRPC (grpc-go)                 HTTP router N/A
WebSocket (gorilla/nhooyr)     Gin not the core value
AWS Lambda micro-handler       small binary / cold start
HTTP/2 push                    not Gin's focus
```

**Key facts:**
- Simple internal services with 2-3 endpoints: `net/http` is enough; zero framework dependency and tiny binaries.
- gRPC: use `google.golang.org/grpc`—Gin is HTTP-only for RPC-style APIs on that stack.
- WebSocket-heavy apps: `gorilla/websocket` or `nhooyr.io/websocket` on `net/http`; Gin does not provide the connection upgrade story as the main value.
- Serverless (Lambda, Cloud Run with tiny functions): a full router is often unnecessary; map event to a single handler.
- HTTP/2 server push is not a first-class story in typical Gin use—go lower level if you must. Gin's value is many routes, middleware, and request validation in one place.

**Interview tip:** This shows you choose tools pragmatically, not because of hype. It demonstrates senior engineering judgment.

> [!example]- Full Story: Right-sized HTTP stacks
>
> **The problem:** Every service does not need the same cost model; importing Gin for a health check and one POST adds dependency churn and build time for no gain.
>
> **How it works:** Evaluate traffic shape: if REST surface grows, middlewares multiply, and validation rules explode, Gin pays back. If your team standardizes on gRPC for service-to-service, the HTTP part might be a tiny admin API—stdlib or chi-like minimalism can win. WebSockets are long-lived; you spend time in the conn handler, not the router. Serverless might prefer single-purpose handlers mapped 1:1 in the provider.
>
> **What to watch out for:** Rejecting Gin because of microbenchmarks when your real cost is dev velocity; conversely, dragging Gin into a repo that is 99% gRPC and one JSON ping—be honest about ownership boundaries.

---

## Q9: How does Gin handle concurrent requests? [TRICKY]

**Answer:**

**In one line:** Like `net/http`, Gin runs each accepted connection in its own goroutine, resolves routes on a read-only radix tree, allocates `Context` from `sync.Pool` per request, and only your shared mutable app state needs explicit synchronization.

**Visualize it:**

```
net/http Server
  Accept
    +--> goroutine 1  --> Engine.ServeHTTP  --> match route (read-only tree)
    +--> goroutine 2  -->  same, no lock on tree
    +--> goroutine N  -->  Context from sync.Pool (per request)

   Shared maps / caches in YOUR code  -->  sync.Mutex, channels, or sharding
```

**Key facts:**
- Concurrency is goroutine-per-request, identical in spirit to `http.Server` dispatch.
- `Engine.ServeHTTP` runs in the connection goroutine, resolves the route, runs the chain. The radix tree is read-only after configuration, so lookups do not need locks.
- `gin.Context` is pooled to reduce allocation rate; that is a runtime optimization, not a concurrency model by itself.
- If you add global maps, in-memory rate limiters, or counters, you must protect them—Gin does not do that for you.

**Interview tip:** Connect this to Go's GMP scheduler. Show that Gin doesn't add concurrency magic -- it relies on Go's runtime.

> [!example]- Full Story: What is actually shared
>
> **The problem:** Interviewers probe whether the router is a lock-covered bottleneck. It is not, but your application might be if you use globals unsafely.
>
> **How it works:** After routes are registered, the trie is not mutated, so many goroutines can traverse it. Each request gets a distinct `Context` from the pool (sequentially, per goroutine) for its lifetime. The heavy lifting is in your service layer, DB pool, and cache clients—those are where you coordinate.
>
> **What to watch out for:** Relying on `c.Keys` from multiple goroutines; `sync.Pool` giving you "sometimes shared" feel—still one writer per request unless you `Copy` and follow rules in Q3.

---

## Q10: How do you implement rate limiting in a Gin API? [ADVANCED]

**Answer:**

**In one line:** Add middleware on top of a per-key limiter: process-local token bucket with `golang.org/x/time/rate` and a sharded or mutex map, or Redis for distributed token/sliding windows across replicas, and return `429` with `c.AbortWithStatusJSON` when the limiter says no; leaky-bucket is an alternative on channels when single-process semantics are enough.

**Visualize it:**

```
Request
  -> extract key (IP, API key, sub claim)
  -> Limiter.Tokens / Redis INCR + TTL
        |
        v allowed?  -- no --> 429 + Abort
                    -- yes -> Next()

Single instance:  x/time/rate + map[string]*Limiter
Multi instance:  Redis (sliding window or token)
```

**Key facts:**
- In-process: token bucket via `golang.org/x/time/rate`, one limiter (or a struct holding one) per client identity in a `sync.Map` or striped map; middleware calls `Allow()` and aborts on false.
- Distributed: use Redis with atomic increments, expiry, or scripts for sliding window fairness—required when multiple pods sit behind a load balancer.
- Leaky-bucket: model with a buffered channel if you need smooth output shaping in one process. Less common in HTTP than token bucket in Go.
- On exceed: `c.AbortWithStatusJSON(http.StatusTooManyRequests, body)` to stop the chain and return a clear retry policy if you use one.

**Interview tip:** Mention that in a Kubernetes deployment, in-memory rate limiting doesn't work because requests are load-balanced across pods. You need distributed state (Redis).

> [!example]- Full Story: From laptop to cluster
>
> **The problem:** A per-process map of IP to limiter is correct until you scale horizontally; then each pod has its own counts and attackers multiply their quota by `replicas`.
>
> **How it works:** Single-node prototypes use `rate.Limiter` keyed by `X-Forwarded-For` or authenticated subject ID. For production clusters, a Redis key per window—e.g. `INCR` with `EXPIRE` for fixed window, or `ZSET` sliding window in Lua—for atomicity. The Gin middleware is thin: parse identity, run limit check, set standard headers `X-RateLimit-Remaining` if you publish them.
>
> **What to watch out for:** Trusting `X-Forwarded-For` without validation behind your proxy; hot keys in Redis; thundering herd when everyone retries at once—add jitter or `Retry-After`.

---

## Q11: How do you implement graceful shutdown with Gin? [ADVANCED]

**Answer:**

**In one line:** Do not use `r.Run()`; construct `http.Server` with the Gin engine, run `ListenAndServe` in a goroutine, block on `SIGINT`/`SIGTERM`, then `Shutdown` with a bounded context so in-flight work drains, and in Kubernetes add readiness and optional preStop sleep for LB drain.

**Visualize it:**

```
main goroutine:                    serve goroutine:
  srv := &http.Server{...}         ListenAndServe (blocks)
  go srv.ListenAndServe()               |
  <- signal                         clients finish
  Shutdown(ctx) w/ 5s timeout  -->  closes listeners, waits handlers
  exit 0
```

**Key facts:**
- `r.Run()` is a convenience that does not call `http.Server.Shutdown` or tie into signals—you cannot drain gracefully with it alone.
- Build `srv := &http.Server{Addr, Handler: router, ReadHeaderTimeout, ...}`; `go srv.ListenAndServe()`.
- `signal.Notify` on `SIGINT` and `SIGTERM` (K8s uses SIGTERM to pods). On signal, `context.WithTimeout` and `srv.Shutdown(ctx)`.
- In Kubernetes, expose `/ready` that fails during shutdown, and optionally `preStop` + sleep to let the service mesh or cloud LB stop sending traffic before the process exits.

```go
srv := &http.Server{Addr: ":8080", Handler: router}
go srv.ListenAndServe()
quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()
srv.Shutdown(ctx)
```

**Interview tip:** This is a production-readiness question. Connect it to your K8s experience at Netcore Cloud.

> [!example]- Full Story: Draining the right things
>
> **The problem:** Killing the process on signal drops active uploads and in-flight DB transactions, causing 502s and confused clients. You need a controlled quiesce.
>
> **How it works:** `Shutdown` stops accepting, waits for running handlers (up to the context), then returns. You reject new work via readiness, finish old work, and close dependencies in `defer` order after `Shutdown` succeeds. The Gin `Engine` is just the `Handler`; the lifecycle is 100% `http.Server` semantics.
>
> **What to watch out for:** Forgetting `ReadHeaderTimeout` and hanging goroutines; setting shutdown timeout shorter than your longest request; not wiring `pprof` or metrics closure if your process is slow to exit.

---

## Q12: How does Gin's validator work, and can you extend it? [ADVANCED]

**Answer:**

**In one line:** Gin integrates `go-playground/validator/v10` for struct tags, lets you `RegisterValidation` and struct-level/cross-field checks on the shared `validate.Validate` engine, and you should still put deep business invariants in the service layer while relying on the library's cached reflection for fast repeat validation.

**Visualize it:**

```
Struct tags on DTO:   `json:"email" binding:"required,email"`
         |
v10 Validate.Struct(dto)
  ├-- built-in: required, min, gte, oneof, ...
  ├-- RegisterValidation("slug", fn)
  └-- RegisterStructValidation(crossField, T{})

Gin ShouldBind* -->  uses binding.Validator
Complex rules  -->  service / DB constraints
```

**Key facts:**
- `binding.Validator` wraps `*validator.Validate` from v10. Tags like `required`, `email`, `min`, `max`, `gte`, `lte`, `oneof` are built in.
- Custom field validators: get the engine, `RegisterValidation("custom", yourFunc)`.
- Cross-field: `eqfield`, `gtfield`, or `RegisterStructValidation` for multi-field business checks at bind time.
- For heavy domain rules, validate in the service after basic shape checks; DB constraints are the last line of defense.
- v10 caches struct metadata after the first `Struct` call, so repeat validation avoids full reflection work.

**Interview tip:** Show that validation has layers: struct tags for format, service layer for business rules, database constraints for integrity.

> [!example]- Full Story: Composing v10 with your domain
>
> **The problem:** Tags are great for shape and simple rules but become unreadable if you encode every product rule in `binding` tags. You need a clear boundary between "HTTP DTO is well-formed" and "order is allowed to ship."
>
> **How it works:** DTOs carry `json` and `binding` tags; Gin's binding decodes and runs `validate`. For cross-field, use struct-level validators or `eqfield`/`gtfield` when appropriate. When a rule needs DB, call the service after bind passes. The validator engine is global—register custom validators at startup once.
>
> **What to watch out for:** Registering the same name twice; confusing `dive` and slice validation; error messages that leak internals—use `RegisterTranslation` and uniform JSON from Q6; relying only on tags for financial constraints—use DB and service checks too.

---