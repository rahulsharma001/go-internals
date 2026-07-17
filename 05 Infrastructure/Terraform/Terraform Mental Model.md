---
type: canonical
domain: infrastructure
topic: terraform-mental-model
status: learning
---

# Terraform Mental Model

## Problem and mental model

Terraform is a declarative reconciliation tool: configuration plus state and provider reads produce a dependency graph and proposed operations; apply asks remote APIs to change reality.

## End-to-end flow and internals

`init` installs providers/backend → `plan` refreshes/reads and evaluates graph → saved reviewed plan → `apply` executes dependencies/concurrency → provider reads final state → backend stores snapshot. It is not a general configuration-management runtime.

## Failure modes and troubleshooting

Unexpected destroy/replace requires stop and inspect address, lifecycle, provider diff and state binding. Never edit/push state casually. `terraform validate`; `fmt -check`; `plan -out`; `show`; `state list/show`.

## Production security, scaling and trade-offs

Use version constraints/lock file, remote encrypted access-controlled state, CI plan/apply separation, least-privilege role and reviewed modules. Declarative automation improves repeatability but amplifies wrong plans.

## Interview questions and five-minute revision

Why does Terraform need state if cloud APIs can be read? Recall owner, data path, failure evidence, mitigation and trade-off.

## Related notes

[[State and Remote Backends]] · [[Plan Apply and Drift]]

## Source metadata

Curated from *AWS Terraform Overview* (2025-06-09, `684734b5-7220-8013-a3a3-90bcad6c1448`) and HashiCorp official state/backend documentation. Backend/provider/version behavior is `needs-verification`.
