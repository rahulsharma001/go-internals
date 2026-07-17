---
type: canonical
domain: infrastructure
topic: incident-investigation
status: learning
---

# Incident Investigation

## Problem and mental model

Turns an alert into stabilization, evidence-based diagnosis, recovery verification and prevention.

## End-to-end flow and internals

Acknowledge/assign lead → state user impact/blast radius/timeline → mitigate reversible risk → preserve evidence → follow request/event path and compare dimensions → test one hypothesis/change → verify SLI recovery → communicate → post-incident actions.

## Failure modes and troubleshooting

Avoid simultaneous unrecorded changes and confirmation bias. Use deploy annotations, traces, logs, events, profiles and cloud audit. Record exact UTC/local timestamps and decisions; never include secrets/customer payloads.

## Production security, scaling and trade-offs

Incident command roles scale coordination; rollback/load shedding/failover have correctness costs. Permanent actions should improve detection, containment, recovery or cause—not blame.

## Interview questions and five-minute revision

How do you distinguish mitigation from root-cause fix? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[Kubernetes Production Failures]] · [[Linux Production Debugging]] · [[Network Troubleshooting]]

## Source metadata

Curated from *Logging Monitoring Alerting BFF* (2025-01-24, `6793a2b8-aacc-8013-a770-860633f9d45e`), *Kibana Structured Logging* (2025-02-25, `67bd8e4b-4c10-8013-a4fb-761c32d6ce15`), existing system-design canonicals, and OpenTelemetry official concepts. Vendor/version behavior is `needs-verification`.
