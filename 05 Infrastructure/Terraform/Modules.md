---
type: canonical
domain: infrastructure
topic: terraform-modules
status: learning
---

# Modules

## Problem and mental model

Encapsulates a reviewed infrastructure contract for reuse without copying resource blocks.

## End-to-end flow and internals

Root module selects provider/backend/environment and calls child module with typed inputs; module creates resources and exposes minimal outputs. Module version change produces a plan that must be reviewed like code.

## Failure modes and troubleshooting

Over-general modules become boolean matrices; hidden provider config/implicit dependencies surprise callers. Use `terraform providers`, graph/address and plan; migrate addresses with `moved` blocks where supported.

## Production security, scaling and trade-offs

Small cohesive modules, documented invariants, validation, examples/tests, semantic versioning and upgrade notes. Do not put secrets or environment-specific policy inside a generic module.

## Interview questions and five-minute revision

What belongs in a module, and when is duplication cheaper than abstraction? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[Providers Resources and Data Sources]] · [[Terraform Production Practices]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
