---
type: quick-revision
domain: infrastructure
status: active
---

# Terraform Interview Revision

## Model and lifecycle

Configuration + state + provider reads → dependency graph/plan → reviewed apply → new state. `init` installs backend/providers; plan refreshes; apply changes APIs. State maps addresses to real objects and can contain secrets.

## Core objects

Resource owns lifecycle; data source reads; provider maps API. Modules are cohesive versioned contracts. Prefer stable `for_each` keys and explicit outputs.

## Safety

Remote encrypted access-controlled state, supported locking, CI serialization by state, plan/apply separation, saved plan, least-privilege federated role, lock file/version constraints. Never commit/edit state or force-unlock without proving no live writer.

## Drift and change review

Scheduled plan detects drift. Investigate destroy/replace, IAM/network widening, database retention and provider/default changes. Emergency console fix is recorded, then imported/encoded/reconciled.

## AWS/EKS layering

Foundation VPC/IAM state → EKS cluster/node/add-on state → controller/bootstrap layer → GitOps/app rollout. Smaller states reduce blast radius but add interfaces/order.

## Commands

`fmt -check`; `validate`; `plan -out`; `show`; `state list/show`; `providers`. `-target` and manual state surgery are exceptional recovery tools.

## Related

[[Terraform Mental Model]] · [[Terraform Production Practices]]

Return: [[Infrastructure Dashboard]]
