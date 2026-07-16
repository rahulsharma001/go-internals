---
type: canonical
domain: databases
topic: mongodb-with-go
status: learning
aliases:
  - T06 MongoDB
  - T06 MongoDB with Go
verification_needed: driver and database version details
source_notes:
  - "[[99 Archive/Superseded Originals/databases/T06 MongoDB]]"
---

# MongoDB with Go

## Problem and mental model

MongoDB stores BSON documents and favors modeling around aggregate access patterns. In Go, a long-lived client manages connections; repository methods pass context, encode filters/updates, decode results, and translate driver errors at a boundary.

Think of a document as an aggregate that can often be read or updated together. Embedding keeps related data local but duplicates it and can grow documents. Referencing separates lifecycles and reduces duplication but requires additional queries or application joins.

## When to use and when not to use

Use MongoDB when document-shaped aggregates, evolving optional fields, and its query/operational model fit the workload. Do not choose it merely to avoid schema design. Strong cross-aggregate relational constraints, join-heavy analytics, or existing relational expertise may favor a relational database.

## Core concepts and minimum program shape

```go
package main

import (
	"context"
	"fmt"
	"time"

	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

type User struct {
	ID   bson.ObjectID `bson:"_id,omitempty"`
	Name string        `bson:"name"`
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	client, err := mongo.Connect(options.Client().ApplyURI("mongodb://localhost:27017"))
	if err != nil { panic(err) }
	defer func() { _ = client.Disconnect(context.Background()) }()

	var user User
	err = client.Database("app").Collection("users").
		FindOne(ctx, bson.D{{Key: "name", Value: "Rahul"}}).Decode(&user)
	fmt.Println(user.Name, err)
}
```

The current official v2 driver documentation confirms these import paths and the `mongo.Connect(options.Client().ApplyURI(uri))` shape. A production application normally creates the client during startup, checks connectivity according to its readiness policy, injects a repository, and shuts down with a bounded context.

## Data model, success flow, and failure flow

Design from reads, writes, atomicity, cardinality, growth, and retention. Use ordered BSON structures where order is semantically relevant. Create indexes for actual filter/sort shapes; compound index order matters. Confirm with query plans and workload measurements rather than accumulating indexes.

Success: request context reaches the repository, the query uses an appropriate index/projection, one document decodes into an explicit type, and latency/result metrics are recorded.

Failure: deadline/cancellation stops waiting; not-found becomes a stable domain error; duplicate-key and transient infrastructure failures are classified without leaking driver types upward; cursor operations check iteration and close errors. Timeout ambiguity requires idempotent or reconcilable write design.

## Production usage and observability

Reuse the client and its pool. Bound request time, result size, document growth, and queueing. Observe operation latency/error rate, pool wait/usage, slow queries, examined-versus-returned documents, index size/use, replication lag, storage growth, and application correctness. Backups and restore tests matter more than merely enabling replication.

## Trade-offs and common mistakes

- Creating a client per request.
- Using unordered documents where pipeline/sort order matters.
- Omitting projections and returning unbounded arrays/documents.
- Forgetting cursor closure or iteration errors.
- Treating flexible schema as schema-free data.
- Adding indexes without measuring write/storage cost.
- Embedding unbounded child collections.
- Assuming a timeout proves a write did not happen.

## Google / Senior Interview Lens

Start with access patterns, aggregate boundary, indexes, consistency, and failure behavior—not product branding. Compare embedding/reference and MongoDB/relational choices. For system design, cover partitioning, replication/failover, hot keys, migrations, observability, and recovery. Google does not require MongoDB or Go.

## Active recall and design challenge

Model orders with items and customer references for two query patterns. Propose compound indexes, trace one timeout/duplicate write failure, and explain when the design should move to a relational model.

## Related notes

- [[System Design Interview Framework]]
- [[Context Cancellation]]
- [[Go Error Handling]]
- [[MongoDB with Go - Quick Revision]]

Official verification: [Go driver connection targets](https://www.mongodb.com/docs/drivers/go/current/connect/connection-targets/) · [connection pools](https://www.mongodb.com/docs/drivers/go/current/connect/connection-options/connection-pools/) · [indexes](https://www.mongodb.com/docs/drivers/go/current/indexes/)

Parent MOC: [[System Design Map of Content]]

Mistakes and re-tests: [[Mistake Index]]
