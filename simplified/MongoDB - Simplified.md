# MongoDB -- Simplified

> This is the plain-English companion to [[databases/MongoDB]].
> Read this when the main note feels overwhelming. Every concept is explained with real-world analogies.

---

## 1. What is this, in plain English?

MongoDB is a database where instead of storing data in rows and columns (like a spreadsheet), you store data as "documents" -- think of each document as a JSON file. Each document can have different fields, like how different people's business cards might have different information on them.

## 2. The one thing to remember

**Design your documents around how you'll search for them, not how the data relates to each other.**

## 3. How to picture it in your head

Imagine a **filing cabinet**:
- The cabinet itself is a **database**
- Each drawer is a **collection** (like "users", "orders")
- Each folder in a drawer is a **document**
- Unlike a spreadsheet where every row looks the same, each folder can contain different papers

The big question is always: **do I put related papers in the SAME folder (embedding) or in SEPARATE folders with a sticky note pointing between them (referencing)?**

Put papers together if you always need them at the same time. Keep them separate if one folder would get too thick.

## 4. How it works under the hood (simple version)

When you save a document, MongoDB converts your JSON into a compact binary format called BSON (Binary JSON). It stores this on disk with a special engine called WiredTiger that handles the actual file management.

The most important piece: **indexes**. Think of an index like the index at the back of a textbook. Without it, MongoDB has to flip through every single page (document) to find what you want. With an index, it jumps directly to the right page.

In Go, you talk to MongoDB through a "client" -- think of it as a phone line to the database. You open ONE phone line when your app starts, and all your goroutines share that line. Don't open a new phone line for every request -- that's like calling the same person 100 times simultaneously.

## 6. The code, explained line by line

The most important pattern -- connecting once and reusing:

```go
// Create ONE client at startup (like opening a phone line)
client, err := mongo.Connect(ctx, options.Client().ApplyURI("mongodb://localhost:27017"))

// Get a reference to your collection (like a drawer in the filing cabinet)
collection := client.Database("myapp").Collection("users")

// Insert a document (like putting a folder in the drawer)
collection.InsertOne(ctx, bson.D{{"name", "Rahul"}, {"age", 30}})

// Find documents (like searching the drawer)
cursor, _ := collection.Find(ctx, bson.D{{"age", bson.D{{"$gte", 25}}}})
```

## 7. The traps, explained simply

1. **Don't create a new client per request** -- it's like hanging up and redialing the phone every time you want to ask a question. One client, shared by everyone.

2. **Always set timeouts** -- if MongoDB is down and you don't set a timeout, your app waits forever. Always use `context.WithTimeout`.

3. **`bson.D` vs `bson.M`** -- `bson.D` keeps your fields in order (like a numbered list). `bson.M` shuffles them randomly (like a bag of items). Use `bson.D` when order matters (sorting, commands).

4. **Close your cursors** -- when you search for documents, MongoDB keeps a bookmark open. If you don't close it (`defer cursor.Close(ctx)`), you waste server resources.

---

> Ready for the full technical version? --> [[databases/MongoDB]]
