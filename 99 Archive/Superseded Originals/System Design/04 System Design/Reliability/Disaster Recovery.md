> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Multi-Region Design]].

---
status: learning
type: canonical
area: system-design
sources:
  - "Curated system-design synthesis"
---

# Disaster Recovery

## Problem it solves

A zone, region, datastore, operator action, or corruption event can exceed ordinary high-availability mechanisms. Recovery must restore usable service and trustworthy data.

## Mental model

Backups are inventory; recovery is the rehearsed journey from failure declaration to validated service. RPO defines tolerable data loss; RTO defines tolerable recovery time.

## How it works

Classify failure domains; set RPO/RTO per business capability; choose backups, replication, point-in-time recovery, immutable copies, warm/cold capacity, failover authority, data reconciliation, and return-to-primary plan. Document and exercise runbooks.

## Concrete example and detailed dry run

An operator corrupts order rows at time `t`. Replication has copied the corruption, so automatic replica failover is insufficient. Freeze writes, identify last good recovery point, restore into an isolated environment, replay validated events after that point, reconcile payments/inventory, test invariants, redirect traffic, then monitor and record exceptions.

## Success scenario

The declared recovery meets agreed objectives, restores dependency order, validates data and security controls, and produces an auditable list of lost/repaired operations.

## Failure scenario

Backups exist but restore credentials, schema migrations, encryption keys, or dependency order were never tested. Recovery exceeds RTO. Correct preparation includes isolated restore drills and measured time for each step.

## Scaling considerations

Backup throughput, change-log retention, restore bandwidth, dataset size, DNS/cache propagation, warm capacity, and downstream replay rate all grow. Throttle replay so recovery does not cause a second outage.

## Production technology choices

Database PITR/WAL archives, immutable/versioned object storage, infrastructure as code, replicated container/artifact registries, secret/key recovery process, DNS/traffic management, and reconciliation tooling.

## Trade-offs

Lower RPO/RTO costs more and increases operational complexity. Synchronous replication reduces data loss but adds latency/coupling; active-active improves availability but complicates conflict and recovery.

## When not to use it

Do not use DR as a substitute for normal HA, safe migrations, access controls, or tested application-level repair.

## Common interview mistakes

Equating replicas with backups; naming RPO/RTO without business input; no corruption scenario; no restore verification; no failback or reconciliation.

## Interview questions and follow-ups

What failures does replication not solve? How are backups validated? Who declares failover? How is data divergence repaired?

## Five-minute recall

Failure domain → capability RPO/RTO → protected artifacts → runbook/authority → isolated restore → replay/reconcile → validate → failover → failback drill.

## Related notes

[[Multi Region Architecture]] · [[Replication]] · [[Failure Handling Strategy]] · [[Consistency Models]]

## Source metadata

Curated synthesis. Recovery objectives and provider guarantees require explicit verification.

