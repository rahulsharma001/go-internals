# T05 GIN Framework -- Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[frameworks/T05 GIN Framework]].

---

## Tier 1: Predict the Output -- Answer

```
A-before
Handler
A-after
```

With `c.Next()`: Middleware runs "A-before", then yields to handler which prints "Handler", then middleware resumes and prints "A-after".

With `c.Abort()` instead: Only "A-before" prints. The handler is skipped because `Abort()` prevents the chain from continuing. "A-after" still prints because it's in the same function body after the `Abort()` call -- `Abort()` doesn't return from the current function.

---

## Tier 2: Fix the Bug -- Answer

The bug: missing `c.Abort()` and `return` after the unauthorized response.

```go
func authMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "no token"})
            // BUG: Without Abort + return, c.Next() below still executes!
            // The handler runs with no authenticated user
        }
        c.Next()
    }
}
```

**Fixed:**

```go
func authMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "no token"})
            return
        }
        c.Next()
    }
}
```

### What to observe
Two things were missing: `c.Abort()` (or `c.AbortWithStatusJSON` which combines both) to stop the chain, and `return` to stop the current function. Without `return`, the code falls through to `c.Next()` and the handler executes despite the 401 response already being written.

---

## Tier 3: Build It -- Solution

```go
package main

import (
    "fmt"
    "net/http"
    "strconv"
    "time"

    "github.com/gin-gonic/gin"
)

type User struct {
    ID    int    `json:"id"`
    Name  string `json:"name"  binding:"required,min=2"`
    Email string `json:"email" binding:"required,email"`
}

// Mock data
var users = map[int]User{
    1: {ID: 1, Name: "Rahul", Email: "rahul@example.com"},
    2: {ID: 2, Name: "Alice", Email: "alice@example.com"},
}

func timingMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        c.Next()
        duration := time.Since(start)
        fmt.Printf("[TIMING] %s %s - %v\n", c.Request.Method, c.Request.URL.Path, duration)
    }
}

func tokenAuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("X-API-Key")
        if token != "secret-token-123" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "error": "invalid or missing API key",
            })
            return
        }
        c.Next()
    }
}

func main() {
    gin.SetMode(gin.ReleaseMode)
    r := gin.New()
    r.Use(gin.Recovery(), timingMiddleware())

    // Public endpoints
    r.GET("/health", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{"status": "ok"})
    })

    // Protected endpoints
    api := r.Group("/api")
    api.Use(tokenAuthMiddleware())
    {
        api.GET("/users/:id", func(c *gin.Context) {
            idStr := c.Param("id")
            id, err := strconv.Atoi(idStr)
            if err != nil {
                c.JSON(http.StatusBadRequest, gin.H{"error": "invalid user ID"})
                return
            }

            user, exists := users[id]
            if !exists {
                c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
                return
            }
            c.JSON(http.StatusOK, gin.H{"user": user})
        })

        api.POST("/users", func(c *gin.Context) {
            var req User
            if err := c.ShouldBindJSON(&req); err != nil {
                c.JSON(http.StatusBadRequest, gin.H{
                    "error":   "validation failed",
                    "details": err.Error(),
                })
                return
            }

            req.ID = len(users) + 1
            users[req.ID] = req
            c.JSON(http.StatusCreated, gin.H{"user": req})
        })
    }

    r.Run(":8080")
}
```

### Test with curl
```bash
# Health check (public)
curl localhost:8080/health

# Get user (needs auth)
curl -H "X-API-Key: secret-token-123" localhost:8080/api/users/1

# Create user (needs auth + valid body)
curl -X POST -H "X-API-Key: secret-token-123" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bob","email":"bob@test.com"}' \
  localhost:8080/api/users

# Missing auth (returns 401)
curl localhost:8080/api/users/1

# Invalid ID (returns 400)
curl -H "X-API-Key: secret-token-123" localhost:8080/api/users/abc
```

### What to observe
- `gin.New()` (bare) + explicit `Recovery()` and custom timing middleware
- Route groups with `api.Use()` for scoped middleware
- `ShouldBindJSON` for validation (not `BindJSON`)
- Proper `return` after every error response
- `c.Param("id")` for path params, manual int conversion with error handling

---

> Exercise from [[frameworks/T05 GIN Framework]] -- Section 6.5
