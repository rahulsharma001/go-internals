---
type: canonical
domain: infrastructure
topic: terraform-state-locking
status: learning
---

# State Locking

## Problem and mental model

Prevents concurrent writers from calculating/applying against the same state snapshot.

## End-to-end flow and internals

A locking-capable backend acquires lock before state mutation → operation refreshes/plans/applies → state persists → lock releases. Not every backend supports locking; confirm backend documentation.

## Failure modes and troubleshooting

A lock may be active or stale. Identify holder/run and backend health before force-unlock; never force while another apply may run. CI concurrency should serialize by state key.

## Production security, scaling and trade-offs

Locking prevents concurrent writers, not wrong configuration, out-of-band drift or two states owning one object. Central run queue/approval adds stronger coordination.

## Interview questions and five-minute revision

When is force-unlock safe? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[State and Remote Backends]] · [[Plan Apply and Drift]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
