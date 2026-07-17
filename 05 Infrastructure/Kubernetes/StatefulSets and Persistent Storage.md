---
type: canonical
domain: infrastructure
topic: statefulsets-storage
status: learning
---

# StatefulSets and Persistent Storage

## Problem and mental model

Runs workloads needing stable identity, ordered lifecycle and per-replica persistent volumes.

## Internal and end-to-end flow

StatefulSet Pod ordinal/DNS identity persists across replacement; volumeClaimTemplates create stable claims; CSI provisions/attaches storage. A PVC is not a backup, multi-AZ database, or replication strategy.

## Failure modes and troubleshooting

Pending/ContainerCreating often means topology, attach limit, access mode, CSI or zone mismatch. Check Pod/PVC/PV/StorageClass events, volume attachment, node zone and application recovery logs.

## Production choices, security and trade-offs

Prefer managed RDS/MSK/ElastiCache for state when their service model fits. In-cluster state requires backup/restore drills, anti-affinity, quorum and upgrade expertise. StatefulSet preserves identity, not data correctness.

## Interview lens and five-minute revision

When is StatefulSet insufficient for a database? Recall: Runs workloads needing stable identity, ordered lifecycle and per-replica persistent volumes.

## Related notes

[[RDS Aurora and DynamoDB]] · [[MSK and Kafka on AWS]] · [[Volumes and Persistence]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and *AWS EKS App Deployment* (2026-06-25, `6a3ce123-1794-83e8-83ea-0c20e4b4424c`). Version/controller/CNI-specific behavior is `needs-verification`; Kubernetes and AWS official documentation are authoritative.

