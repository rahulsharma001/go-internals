---
type: canonical
domain: system-design
topic: scalability-availability-and-reliability
status: active
last_verified: 2026-07-17
---
# Scalability Availability and Reliability

## 1. Problem it solves

A system can handle today’s load yet fail under growth or faults. This note separates scalability (more useful work under more demand), availability (successful service when requested), and reliability (correct service over time).

## 2. Simple mental model

Think of capacity, continuity, and correctness as three different budgets. Scaling adds or uses capacity; availability keeps an operation reachable; reliability keeps its promised outcome correct. A replicated wrong answer can be highly available and unreliable.

## 3. How it works

Measure a workload unit, find the limiting resource, then scale vertically, horizontally, or by partitioning. Remove single failure domains with redundant instances and state replication. Define user-centred SLIs and an SLO; design retries, degradation, backup, and recovery around the promised operation.

## 4. Concrete example

For checkout, stateless API instances scale behind a load balancer, but order acceptance is available only if the authoritative order transaction can commit. Email may degrade without making checkout unavailable. An SLO such as successful durable order acceptance is more useful than host uptime.

## 5. Detailed success flow

01. A request reaches a healthy API instance, passes admission control, commits to replicated order storage, and returns an order ID.
11. Optional events are buffered.
21. Autoscaling responds before saturation and the SLO counts the durable result.

## 6. Detailed failure flow

01. During database loss of quorum, the API must not acknowledge an order it cannot durably commit.
11. It fails or returns unavailable, while read-only status may use a safe replica.
21. Recovery restores quorum, reconciles uncertain requests by idempotency key, and measures error-budget burn.

## 7. Scaling behaviour

Scale the first saturated resource, not every tier. Stateless compute scales by replicas; stateful write paths scale with partitioning, batching, or contention reduction. Plan for peak and skew, dependency quotas, deploy headroom, and queue drain time.

## 8. Data consistency implications

Higher availability during a network partition may require serving stale data or accepting conflicting writes. Apply strong consistency only to invariants; allow bounded/eventual consistency for derived views.

## 9. Real implementation choices

Kubernetes or an autoscaling group can manage stateless replicas; PostgreSQL/RDS or a distributed database owns durable state; a regional load balancer routes requests; multi-zone replicas reduce host/AZ faults. Products do not replace SLO, quorum, or failover semantics.

## 10. Trade-offs

More redundancy costs money and can increase coordination latency. Horizontal scale adds partition/routing complexity. Overprovisioning absorbs bursts but wastes capacity; aggressive autoscaling reacts late to sudden load. High availability can conflict with strict consistency.

## 11. When not to use it

Do not shard or deploy multi-region because the words sound senior. A single well-backed-up database and two application instances may satisfy a small workload.

## 12. Common interview mistakes

Equating uptime with correctness; saying “scale horizontally” without a unit; averages without peaks; replicas without failover/lag; every feature given the same availability; no load shedding; no restore test.

## 13. How it appears inside larger systems

Every system note uses this foundation when it identifies the first bottleneck, failure domain, graceful degradation, and SLO.

## 14. Likely interviewer follow-ups

Which operation’s availability? What fails first at 10×? How much headroom? What happens during deploy or AZ loss? Which work is shed? What is RPO/RTO?

## 15. Five-minute revision

Capacity ≠ availability ≠ reliability. Name workload and SLI, find first limit, add targeted capacity/redundancy, protect invariants, shed optional work, test restore/failover.

## 16. Related notes

[[Latency Throughput and Capacity]] · [[Replication]] · [[Partitioning and Sharding]] · [[Observability and SLOs]] · [[Multi-Region Design]]

## 17. Verified further reading

- [Google Cloud: detect failures with observability](https://cloud.google.com/architecture/framework/reliability/slo-and-alerts) — connects reliability to metrics, logs, traces, and actionable alerts.
- [Google SRE Book](https://sre.google/sre-book/table-of-contents/) — primary public material on SLOs, overload, and reliable operations.

