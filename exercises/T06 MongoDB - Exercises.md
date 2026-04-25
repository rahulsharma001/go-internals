# MongoDB -- Exercise Solutions

> Complete solutions for Practice Checkpoint exercises from [[databases/MongoDB]].

---

## Tier 1: Predict the Output -- Answer

```go
filter := bson.M{"name": "Rahul", "age": bson.M{"$gt": 25}}
```

This produces: `{name: "Rahul", age: {$gt: 25}}` -- finds documents where name equals "Rahul" AND age is greater than 25.

If `name` field doesn't exist in some documents, those documents simply don't match and are excluded. MongoDB doesn't error on missing fields -- it treats them as "not matching."

---

## Tier 2: Fix the Bug -- Answer

Three critical bugs:

1. **Creating a new `mongo.Client` per request** -- each call opens a new connection pool. Under load, this exhausts connections and crashes the database.
2. **Ignoring errors** -- `mongo.Connect` and `cursor.All` errors are silently dropped.
3. **Not disconnecting/closing** -- the client and cursor are never cleaned up, leaking connections.

**Fixed version:**

```go
// Global client, initialized once at startup
var mongoClient *mongo.Client

func initMongo() error {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    var err error
    mongoClient, err = mongo.Connect(ctx, options.Client().ApplyURI("mongodb://localhost:27017"))
    if err != nil {
        return err
    }
    return mongoClient.Ping(ctx, nil)
}

func getUsers(ctx context.Context) ([]User, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    collection := mongoClient.Database("app").Collection("users")
    cursor, err := collection.Find(ctx, bson.D{})
    if err != nil {
        return nil, fmt.Errorf("find users: %w", err)
    }
    defer cursor.Close(ctx)

    var users []User
    if err := cursor.All(ctx, &users); err != nil {
        return nil, fmt.Errorf("decode users: %w", err)
    }
    return users, nil
}
```

### What to observe
The pattern is identical to `sql.DB` in Go: one global client, context with timeout on every operation, proper error handling, and cursor cleanup.

---

## Tier 3: Build It -- Solution

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "go.mongodb.org/mongo/v2"
    "go.mongodb.org/mongo/v2/options"
    "go.mongodb.org/mongo/v2/bson"
)

type Product struct {
    Name     string  `bson:"name"`
    Price    float64 `bson:"price"`
    Category string  `bson:"category"`
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    client, err := mongo.Connect(ctx, options.Client().ApplyURI("mongodb://localhost:27017"))
    if err != nil {
        log.Fatal(err)
    }
    defer client.Disconnect(ctx)

    if err := client.Ping(ctx, nil); err != nil {
        log.Fatal("Cannot connect:", err)
    }

    coll := client.Database("shop").Collection("products")

    // Create index on category
    indexModel := mongo.IndexModel{
        Keys: bson.D{{"category", 1}},
    }
    _, err = coll.Indexes().CreateOne(ctx, indexModel)
    if err != nil {
        log.Fatal("Index creation failed:", err)
    }
    fmt.Println("Index created on 'category'")

    // Insert 5 products
    products := []interface{}{
        Product{"Laptop", 999.99, "electronics"},
        Product{"Phone", 699.99, "electronics"},
        Product{"Desk", 249.99, "furniture"},
        Product{"Chair", 199.99, "furniture"},
        Product{"Headphones", 149.99, "electronics"},
    }
    result, err := coll.InsertMany(ctx, products)
    if err != nil {
        log.Fatal("Insert failed:", err)
    }
    fmt.Printf("Inserted %d products\n", len(result.InsertedIDs))

    // Aggregation: average price per category
    pipeline := mongo.Pipeline{
        {{"$group", bson.D{
            {"_id", "$category"},
            {"avgPrice", bson.D{{"$avg", "$price"}}},
            {"count", bson.D{{"$sum", 1}}},
        }}},
        {{"$sort", bson.D{{"avgPrice", -1}}}},
    }

    cursor, err := coll.Aggregate(ctx, pipeline)
    if err != nil {
        log.Fatal("Aggregation failed:", err)
    }
    defer cursor.Close(ctx)

    var results []bson.M
    if err := cursor.All(ctx, &results); err != nil {
        log.Fatal("Decode failed:", err)
    }

    fmt.Println("\nAverage price per category:")
    for _, r := range results {
        fmt.Printf("  %s: $%.2f (%v products)\n", r["_id"], r["avgPrice"], r["count"])
    }

    // Cleanup
    coll.Drop(ctx)
}
```

### Output
```
Index created on 'category'
Inserted 5 products

Average price per category:
  electronics: $616.66 (3 products)
  furniture: $224.99 (2 products)
```

### What to observe
- Single client, context timeout on every operation
- `bson.D` used for pipeline stages (order matters in `$group` and `$sort`)
- Cursor properly closed with defer
- Aggregation pipeline stages: `$group` (like SQL GROUP BY) then `$sort`
- `InsertMany` takes `[]interface{}` not `[]Product` (driver requirement)

---

> Exercise from [[databases/MongoDB]] -- Section 6.5
