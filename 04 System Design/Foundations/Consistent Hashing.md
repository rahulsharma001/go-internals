---
type: canonical
domain: system-design
topic: consistent-hashing
status: learning
---
# Consistent Hashing

## Problem it solves

It maps keys to changing nodes while moving fewer keys than `hash(key) mod N` when membership changes.

## Mental model and how it works

Place node tokens and key hashes on a ring; a key belongs to the next token clockwise. Adding/removing a token affects only a neighboring range. Virtual nodes give each physical node many tokens, improving balance and allowing capacity weighting. Replicas can be assigned to later distinct nodes.

## Concrete example and dry run

Tokens: A=10, B=40, C=80 on a 0–99 ring. Keys 12 and 35 map to B; 50 maps to C; 90 wraps to A. Add D at 30: only keys in `(10,30]` move from B to D. With modulo hashing, many keys would remap because `N` changed.

## Success and failure scenarios

Success: cache/shard membership changes cause bounded movement. Failure: one token owns a huge or hot range; a node disappears and all its keys stampede one successor. Use virtual nodes, replicas, bounded rebalancing, admission control, and hotspot detection.

## Scaling and production choices

Used in distributed caches/storage and client-side sharding; rendezvous hashing is a simpler alternative that ranks nodes per key. Membership needs a reliable control plane, not each client inventing a different ring.

## Trade-offs and when not to use

It balances key ranges, not request cost; range queries are awkward; rebalancing still consumes bandwidth. Do not use when a database already owns partition routing or when a few static shards can use explicit ranges.

## Interview mistakes and follow-ups

No virtual nodes, confusing replication with partitioning, claiming zero movement, ignoring hot keys. Follow-ups: heterogeneous capacity? node loss? replication placement? ring version skew? hotspot?

## Five-minute recall

Hash ring → successor token → virtual nodes → minimal movement → replicas → membership/version → hotspot caveat.

Related: [[Partitioning and Sharding]], [[Caching Pattern]], [[Replication]].

## Source metadata

Curated stable foundation; no personal scale claims.
