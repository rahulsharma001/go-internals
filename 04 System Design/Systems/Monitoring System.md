---
status: learning
type: system-design
area: system-design
sources:
  - "ChatGPT: Logging Monitoring Alerting BFF (2025-01-24, 6793a2b8-aacc-8013-a770-860633f9d45e)"
  - "Google SRE Workbook: Monitoring"
  - "OpenTelemetry documentation"
---

# Monitoring System

## 1. Problem statement

Design a multi-tenant monitoring platform that ingests metrics, evaluates recording/alert rules, serves time-series queries and dashboards, and notifies responders without letting monitoring failure overload production.

## 2. Functional requirements

Ingest timestamped samples; discover/scrape or accept push; store/query recent and retained data; evaluate rules; group, route, silence, and deduplicate alerts; support dashboards and audit configuration changes. Full log search and trace storage are out of scope unless requested.

## 3. Non-functional requirements

High ingest availability, bounded query/rule latency, tenant isolation, controlled cardinality, durable enough alert state, predictable retention/cost, and independent monitoring of the monitoring system.

## 4. Scale assumptions

Ask for samples/second, active series, labels/series, bytes/sample, retention tiers, query concurrency, rule count, and tenant skew. Active-series cardinality and query fan-out are primary capacity drivers; values need verification.

## 5. Core entities

`Tenant`, `Metric`, `LabelSet`, `Sample`, `Series`, `Chunk`, `RuleGroup`, `AlertInstance`, `Silence`, and `NotificationRoute`.

## 6. API design

```text
POST /v1/metrics/write  {timeseries:[{labels,samples}]}
GET /v1/query_range?query=...&start=...&end=...&step=...
PUT /v1/rule-groups/{id}
POST /v1/silences
GET /v1/alerts
```

## 7. Data model

A normalized label set maps to a series ID. Recent sorted samples form compressed blocks/chunks; an inverted index maps label matchers to series IDs; object storage holds immutable long-term blocks; metadata records block time ranges/checksums. Alert state records pending/firing/resolved and last notification.

## 8. High-level architecture

```text
Agents/scrapers → regional ingest → validation/rate limit → WAL → distributor
                                                          ↓
                                                  time-series ingesters
                                                    ↓           ↓
                                            recent store    object blocks/index
Dashboard/API → query frontend → query workers ────────────────┘
Rules → query path → alert state → dedupe/group/router → notification providers
```

## 9. Component responsibilities

Collectors capture/export; distributors authenticate and shard; ingesters buffer and compact; store gateway/index locates blocks; query frontend caches/splits/fair-schedules; ruler evaluates; alert manager groups, deduplicates, inhibits, silences, and routes.

## 10. Complete request or event flow

Collector batches samples → ingest validates timestamps/labels/cardinality → WAL acknowledges → series owner appends → compact immutable block → upload/index → query frontend parses/splits → workers fetch recent + long-term blocks → merge/deduplicate → dashboard. Separately, rules query; sustained violation changes alert pending→firing; alert router groups and sends.

## 11. Detailed success path

A service latency histogram is accepted after tenant limits, replicated/recorded durably, and queryable from recent storage. A burn-rate rule remains above threshold for its evaluation window, creates one firing instance, groups it by service/region, and routes a deduplicated page with dashboard/runbook links.

## 12. At least one detailed failure path

A deployment emits unbounded `user_id` labels. Tenant active-series and ingest limits reject/quarantine the excess before exhausting shared memory; the platform reports dropped samples and alerts on the tenant symptom. Existing tenants continue through fair queues. If object storage is slow, recent queries continue, long-range queries degrade with explicit partial/error semantics, and alerts relying on missing data avoid silently reporting healthy.

## 13. Bottlenecks

Label cardinality, hot series, index expansion, long unbounded queries, compaction, object-store requests, ruler query bursts, notification storms, and multi-tenant noisy neighbours.

## 14. Scaling strategy

Shard series by tenant+label hash with replication; separate ingest and query planes; cache query results and metadata; split long time ranges; downsample/record common queries; tier retention; cap concurrency/cardinality; fair-schedule tenants; batch alerts.

## 15. Reliability and disaster recovery

Replicate/WAL recent samples, keep immutable object blocks with lifecycle policy, back up configuration/alert routing, run rule evaluators redundantly with deduplication, and maintain an external dead-man signal. Define whether short metric loss or duplicate samples are acceptable.

## 16. Observability

Monitor accepted/rejected samples, active series, distributor/ingester errors, WAL/compaction/object lag, query latency/failures/scanned bytes, cache hit rate, rule evaluation duration/misses, alert delivery failures, and control-plane changes. Use logs/traces for the platform itself.

## 17. Security

Authenticate collectors/users; authorize tenant queries/config; encrypt links; isolate tenant labels/storage; limit query/ingest cost; audit rules/silences; prevent secret labels; sanitize notification templates and outbound webhooks.

## 18. Concrete technology choices

Prometheus/OpenTelemetry collectors; Mimir/Thanos/Cortex-like distributed TSDB; object storage for blocks; Grafana-like dashboards; Alertmanager/PagerDuty-like routing. Specific compatibility and durability are `status: needs-verification`.

## 19. Trade-offs

Pull simplifies target health but cannot reach every environment; push fits short-lived jobs but risks spoofed liveness. Longer retention and raw resolution improve analysis but cost more. Aggressive aggregation controls cost but loses debugging dimensions. Alert redundancy may duplicate notifications without shared state/deduplication.

## 20. Interview follow-up questions

How is cardinality controlled? How are late/out-of-order samples handled? What happens if the monitoring region fails? How are alerts deduplicated? How are long queries isolated from rules?

## 21. Five-minute revision

Cardinality drives cost. Validate/rate-limit → WAL/replicated ingest → compressed recent chunks → immutable object blocks + index. Split/cache/fair-schedule queries. Rules produce stateful alerts; group/dedupe/route. Monitor the monitor with an external signal.

## Related notes

[[Logs Metrics and Traces]] · [[SLI SLO and Error Budgets]] · [[Alerting Strategy]] · [[Backpressure Pattern]] · [[Data Storage Selection]]

## Source metadata

Curated from the extracted logging/monitoring conversation, Google SRE monitoring guidance, and OpenTelemetry concepts. This is a generic interview architecture, not a production-ownership claim.

