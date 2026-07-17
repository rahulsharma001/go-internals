---
type: canonical
domain: infrastructure
topic: terraform-production-practices
status: learning
---

# Terraform Production Practices

## Problem and mental model

Makes infrastructure change reviewable, recoverable and bounded.

## End-to-end flow and internals

PR → format/validate/lint/security policy → speculative plan → human/risk review → approved saved plan → serialized apply → post-apply checks → drift detection. Separate credentials and state by environment.

## Failure modes and troubleshooting

Never approve unreadable giant plans. Flag destroy/replace, public access, IAM wildcard, SG widening, database retention and state move. Back up state before exceptional state surgery; rehearse imports/moves.

## Production security, scaling and trade-offs

No secrets in repo/vars output; use CI federation, least-privilege apply role, module provenance, version locks and audit. Small states reduce blast radius but add interfaces and ordering.

## Interview questions and five-minute revision

Describe a safe emergency console change and reconciliation flow. Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[State Locking]] · [[Plan Apply and Drift]] · [[AWS Reliability and Multi AZ]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
