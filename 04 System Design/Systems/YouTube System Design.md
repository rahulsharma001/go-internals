---
status: learning
type: system-design
area: system-design
sources:
  - "Curated interview design using existing system-design foundations"
---

# YouTube System Design

## 1. Problem statement

Design a video platform that accepts resumable uploads, asynchronously produces multiple playable renditions, distributes content globally through a CDN, serves metadata and playback, and records analytics without blocking viewing.

## 2. Functional requirements

- Initiate, upload, resume, and finalize a video.
- Store metadata, ownership, visibility, and processing state.
- Transcode into multiple resolutions/codecs and package manifests/segments.
- Play through a CDN with adaptive bitrate.
- Search/list metadata and collect view/quality analytics.
- Retry failed processing and allow creator status inspection.

Out of scope unless requested: recommendations, comments, live streaming, copyright matching, and ad auctions.

## 3. Non-functional requirements

Durable uploads; high playback availability; low startup latency; global delivery; eventual metadata/search/analytics consistency; isolation of untrusted media processing; cost-aware storage and bandwidth.

## 4. Scale assumptions

Ask for upload bytes/time, videos/day, rendition count, playback concurrency, geographic distribution, retention, and target startup time. Derive storage from `source bytes + encoded renditions + replication`, and egress mainly from playback. All numeric targets are `status: needs-verification` until supplied.

## 5. Core entities

`Video`, `UploadSession`, `UploadPart`, `SourceObject`, `TranscodeJob`, `Rendition`, `Manifest`, `PlaybackSession`, and `AnalyticsEvent`.

## 6. API design

```text
POST /v1/videos/uploads {title, visibility, contentType, size}
→ {videoId, uploadId, signedPartURLs}

PUT signed-object-URL  (chunk bytes; checksum)
POST /v1/videos/{videoId}/uploads/{uploadId}:complete {parts}
GET /v1/videos/{videoId} → {metadata, processingState}
GET /v1/videos/{videoId}/playback → {manifestURL, playbackToken}
POST /v1/analytics/events {sessionId, sequence, events}
```

## 7. Data model

Relational/strong metadata stores ownership, visibility, source key, processing state, and version. Object storage holds immutable source, renditions, thumbnails, manifests, and segments. The queue carries IDs and object references—not video bytes. Search and analytics are derived, rebuildable stores.

Example state machine: `UPLOADING → UPLOADED → PROCESSING → READY`, with `PROCESSING_FAILED` retaining retry/debug information. A new encode generation writes new object keys before atomically switching the active manifest pointer.

## 8. High-level architecture

```text
Creator → Upload API ──signed URLs──→ Object Storage (source)
              │ complete                    │ event
              ▼                             ▼
         Metadata DB ← Processing Coordinator → Durable Queue
                                                   │
                                      Transcode workers (sandboxed)
                                                   │
                        Object Storage (renditions/manifests/thumbnails)
                                                   │
Viewer → Playback API → signed manifest → CDN → origin/object storage
  └──────────────── quality/view events → event stream → analytics stores
```

## 9. Component responsibilities

- Upload API authenticates creator, validates metadata, and manages resumable sessions.
- Object storage durably receives chunks and verifies checksums.
- Coordinator creates idempotent jobs and owns processing generation/state.
- Workers probe, transcode, package, and produce thumbnails in isolation.
- Playback API authorizes visibility and issues short-lived access.
- CDN caches immutable segments close to viewers.
- Analytics pipeline accepts batched, duplicate-tolerant events.

## 10. Complete request or event flow

`Upload → object storage → metadata creation → asynchronous transcoding → multiple renditions → CDN distribution → playback → analytics`.

1. Creator creates metadata and upload session, then sends numbered chunks directly to object storage with per-part checksums.
2. Completion validates the part manifest/object and atomically marks the source `UPLOADED` plus writes a processing event.
3. Queue consumers create idempotent jobs for codec/resolution outputs.
4. Workers read the source, emit temporary output, verify it, then publish immutable rendition segments and manifest.
5. Coordinator marks the generation `READY`; search indexing catches up asynchronously.
6. Playback API checks authorization and returns a signed HLS/DASH manifest URL.
7. Player fetches manifest/segments through CDN and adapts bitrate from observed network/buffer.
8. Client batches sequenced analytics; stream processors aggregate views and quality signals asynchronously.

## 11. Detailed success path

An interrupted upload resumes only missing chunks. Finalization verifies checksums and emits one logical processing request. Workers can retry by `(video_id, generation, rendition)` without overwriting active content. After every required rendition is verified, the metadata pointer changes to the ready manifest. First playback may miss CDN and fetch origin; later viewers hit cached immutable segments. Analytics loss does not interrupt playback.

## 12. At least one detailed failure path

**Failed transcode:** a corrupt source or worker crash fails one rendition. Transient infrastructure failures retry with backoff and a cap; deterministic media errors move the job to quarantine with reason and creator-visible `PROCESSING_FAILED`/partial policy. Temporary objects expire. Completion is not published until required outputs verify; retry uses the same generation ID.

**Popular-video hot spot:** request collapsing, origin shielding, tiered CDN caches, and immutable cache keys prevent a miss wave from overwhelming object storage. If one CDN/region fails, DNS/traffic policy can use another path, accepting higher startup latency.

## 13. Bottlenecks

Upload egress into one region, CPU/GPU transcode capacity, queue skew from long videos, object-store request rate, origin traffic on cache misses, metadata hot keys for viral videos, cache invalidation after visibility changes, and analytics cardinality.

## 14. Scaling strategy

Upload directly to regional object endpoints; partition jobs by video but schedule by estimated cost; maintain separate queues/pools for priority or codec; use autoscaling with queue age and capacity limits; keep segments immutable; use CDN origin shielding; cache hot metadata; shard analytics streams independently from playback.

## 15. Reliability and disaster recovery

Object versioning/replication policy and metadata backups must meet agreed RPO/RTO. Jobs are replayable from source objects; queue messages are at-least-once and workers idempotent. Store generation state durably. Cross-region playback can use replicated renditions while new uploads temporarily remain homed to one region.

## 16. Observability

Track upload completion/error/resume rates, checksum failures, queue age by job class, transcode duration/failure/retry, time-to-ready, rendition completeness, CDN hit ratio, origin egress, playback startup time, rebuffer ratio, playback errors, and analytics ingest lag. Correlate `video_id`, `upload_id`, `job_id`, generation, and playback session.

## 17. Security

Use short-lived signed upload/playback URLs, ownership and visibility checks, malware/media validation, sandboxed least-privilege workers, encryption, rate/size limits, private origin access, secrets outside payloads, PII-minimized analytics, and auditable moderation/admin access.

## 18. Concrete technology choices

S3/GCS-like object storage; multipart/resumable upload; Kafka/Pub/Sub/SQS-like durable queue; FFmpeg-based isolated workers; PostgreSQL/Spanner-like metadata store based on scale/region needs; HLS/DASH; multi-CDN where justified; ClickHouse/BigQuery-like analytics. These are candidate choices, not claims about YouTube internals.

## 19. Trade-offs

More renditions improve playback but increase compute/storage and time-to-ready. Immediate metadata availability improves UX while search and playback remain eventual. Immutable content simplifies caching; visibility revocation then needs short token TTL and purge controls. Multi-CDN improves resilience but adds routing and contract complexity.

## 20. Interview follow-up questions

- How do resumable chunk checksums and finalization work?
- How do you schedule a two-hour video versus a short clip?
- What becomes ready if one optional rendition fails?
- How do you revoke private content already cached?
- How would live streaming alter the pipeline?

## 21. Five-minute revision

Direct chunked upload to object storage; durable metadata + processing event; queue IDs, not bytes; idempotent sandboxed transcoders create immutable renditions; atomically publish manifest generation; CDN + origin shield serves playback; analytics is asynchronous and non-blocking. Watch time-to-ready and rebuffering.

## Related notes

[[Queues and Pub Sub]] · [[Backpressure Pattern]] · [[Caching Pattern]] · [[Data Storage Selection]] · [[Graceful Degradation]] · [[Multi Region Architecture]]

## Source metadata

Curated interview synthesis from existing system-design material. It contains no claim about YouTube's private current architecture or personal production experience; technology/version details require verification.
