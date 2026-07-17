---
type: canonical
domain: system-design
topic: data-storage-selection
status: learning
source_conversations:
  - "PostgreSQL for Production Systems | 2026-06-28 | 6a41070b-052c-83ee-bf6b-ceb1d4910e0e"
---
# Data Storage Selection

## Problem it solves

It maps invariants and access patterns to the smallest storage portfolio that meets them.

## Mental model and how it works

Start with source-of-truth operations: key lookup, range/time query, relational join, transaction, text search, graph traversal, blob delivery, or analytics scan. Add consistency, write/read ratio, retention, size, locality, and operating skill. One system often uses an authoritative store plus derived cache/search/warehouse—not multiple competing sources of truth.

## Concrete example and dry run

YouTube-like design: relational or scalable metadata store owns video state/ACL; object storage owns uploaded and transcoded blobs; CDN serves immutable renditions; search index is a rebuildable view; analytics events enter a stream/warehouse. Upload completion changes metadata only after a durable object manifest exists. Search lag is acceptable; ACL enforcement on playback is not.

## Success and failure scenarios

Success: each store has one role and repair path. Failure: cache/search becomes authoritative, dual writes diverge, or a flexible document model accumulates unbounded arrays. Use outbox/CDC, versioned events, reconciliation, retention, and query-plan/index review.

## Scaling and production choices

Relational: constraints, joins, transactions. Key-value/wide-column: predictable key/range access and partition scale. Document: aggregate-shaped evolving records. Search: text/facets. Object: large immutable blobs. Time-series/columnar: metrics/analytics. Validate product/version behavior before implementation.

## Trade-offs and when not to use

Polyglot storage improves fit but multiplies operations, security, backups, and skill needs. Prefer one relational store initially when it meets requirements; do not choose NoSQL only because the prompt says scale.

## Interview mistakes and follow-ups

Technology-first choice; no index/access pattern; ignoring deletion/backup; treating replicas as write scale. Follow-ups: transaction boundary? largest query? schema evolution? hot key? restore? derived-view lag?

## Five-minute recall

Invariant/source of truth → access patterns → consistency/transactions → scale/retention → store → index/partition → derived views → backup/repair.

Related: [[Database Selection Guide]], [[Core Entities APIs and Data Model]], [[Replication]], [[Partitioning and Sharding]], [[Caching Pattern]].

## Source metadata

Curated technical source above plus existing [[MongoDB with Go]]; no personal use claim.
