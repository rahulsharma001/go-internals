---
type: canonical
domain: infrastructure
topic: terraform-providers-resources-data
status: learning
---

# Providers Resources and Data Sources

## Problem and mental model

Maps HCL declarations to provider API schemas and existing read-only information.

## End-to-end flow and internals

Provider config authenticates/targets API; resource owns lifecycle binding; data source reads an external object; expressions create graph edges. `for_each` with stable keys preserves identity better than index-based count for changing sets.

## Failure modes and troubleshooting

Unknown values appear at plan; provider defaults/normalization can create perpetual diff. Diagnose schema/version, alias/provider inheritance, address changes and API permissions.

## Production security, scaling and trade-offs

Do not put credentials in HCL; use workload/federated identity. Pin provider constraints and commit dependency lock. Data sources create runtime coupling to external naming/availability.

## Interview questions and five-minute revision

Resource versus data source; why stable `for_each` keys? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[Terraform Mental Model]] · [[Modules]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
