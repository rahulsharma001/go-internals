---
type: canonical
domain: infrastructure
topic: terraform-state-backends
status: learning
---

# State and Remote Backends

## Problem and mental model

Stores the binding between resource addresses and real remote objects and enables safe team collaboration.

## End-to-end flow and internals

Plan refreshes remote APIs into working state → apply changes objects → backend stores a new serial/lineage snapshot. Remote backend can provide encryption/access/audit/locking; state may contain sensitive values even when outputs are marked sensitive.

## Failure modes and troubleshooting

Backend unavailable/failed write requires stop and preserve local recovery state. `terraform state pull` exposes sensitive data; manual push is dangerous. Check lineage/serial and backend audit before recovery.

## Production security, scaling and trade-offs

Use separate state per environment/blast radius, encryption, versioning, backups, least access and supported locking. Do not commit state. Prefer explicit outputs or a service registry over broad remote-state sharing.

## Interview questions and five-minute revision

Why is `sensitive=true` not removal from state? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[State Locking]] · [[Terraform Production Practices]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
