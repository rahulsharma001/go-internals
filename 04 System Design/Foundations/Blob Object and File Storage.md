---
type: canonical
domain: system-design
topic: blob-object-and-file-storage
status: active
last_verified: 2026-07-17
---
# Blob Object and File Storage

## 1. Problem it solves

Large byte sequences have different lifecycle, transfer, durability, and access needs from metadata rows. Storing media/files as ordinary database values increases cost and pressure.

## 2. Simple mental model

Object storage holds immutable/versioned bytes by key; a metadata store owns names, users, versions, ACLs, and workflow. File systems add hierarchical/path and random-write semantics; blob/object stores usually do not.

## 3. How it works

Create an upload session, issue short-lived signed part URLs, upload parts directly with checksums, complete/verify, atomically publish metadata/version, then serve through signed URLs/CDN. Lifecycle policies tier/delete unreferenced versions.

## 4. Concrete example

A 2 GB video uploads in 16 MB parts. Failed parts retry independently; completion verifies checksums. Transcoding jobs carry object keys, not bytes. A manifest pointer switches only after renditions verify.

## 5. Detailed success flow

Authorized client uploads parts to object storage; service records part manifest/version; checksum validates; metadata commit makes version visible; CDN serves immutable object; lifecycle retains according to policy.

## 6. Detailed failure flow

Client uploads bytes but metadata commit fails. Object remains unreferenced; reconciliation/expiry deletes it. If completion response is lost, stable upload ID returns existing completion. Corrupt checksum rejects publish.

## 7. Scaling behaviour

Direct upload avoids API bandwidth. Multipart parallelism improves throughput but needs bounded concurrency. Prefix/request limits, small-object overhead, egress, CDN hit rate, and lifecycle dominate cost.

## 8. Data consistency implications

Object-key updates may be atomic per provider, but application metadata/object publication is cross-system. Use immutable keys plus pointer/version transaction. Define replication lag and delete propagation.

## 9. Real implementation choices

S3/GCS/Azure Blob; multipart/resumable upload; checksums; versioning; lifecycle/archive tiers; signed URLs; CDN; relational/KV metadata.

## 10. Trade-offs

Immutable versions simplify caching/recovery but consume storage. Larger parts reduce requests but worsen retry granularity. Cross-region replication improves recovery/read locality but costs egress and may lag.

## 11. When not to use it

Do not use object storage for low-latency row mutation, relational query, or filesystem locking. Small frequently updated values fit a database.

## 12. Common interview mistakes

Bytes through API servers; queue carries bytes; no checksum/resume; metadata and object dual-write ignored; public bucket; signed URL too long; no orphan cleanup; CDN considered authorization.

## 13. How it appears inside larger systems

Video, file sync, logs/metrics blocks, backups, crawler content, exports, and large notification attachments.

## 14. Likely interviewer follow-ups

Multipart completion? Integrity? Orphans? overwrite/version conflict? revoke cached private object? regional replication? small objects? lifecycle and deletion?

## 15. Five-minute revision

Bytes in object store, metadata/ACL/version elsewhere. Direct multipart signed upload, checksum, immutable key, atomic pointer publish, CDN, orphan reconciliation, lifecycle.

## 16. Related notes

[[Caching and CDN Fundamentals]] · [[File Storage and Synchronization System]] · [[YouTube System Design]] · [[Multi-Region Design]]

## 17. Verified further reading

- [Amazon S3 multipart upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html) — official resumable multipart mechanics.\n- [Amazon S3 object integrity](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity-upload.html) — official checksum behavior.

