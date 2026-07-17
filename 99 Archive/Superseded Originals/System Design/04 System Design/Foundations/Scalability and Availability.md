> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Scalability Availability and Reliability]].

---
type: canonical
domain: system-design
topic: scalability-availability
status: learning
source_conversations:
  - "System Design Prep Hub | 2026-05-30 | 6a1ae0f4-402c-8324-b49e-754f47133b80"
---
# Scalability and Availability

## Problem it solves

Scalability keeps acceptable service as load/data grows; availability keeps the user-facing operation working despite faults.

## Mental model and how it works

Scale the constrained resource, not the diagram. Vertical scaling adds capacity to one node; horizontal scaling adds nodes and requires partitioning, load distribution, statelessness or state coordination. Availability removes single failure points through redundancy, health detection, failover, and degraded modes. Redundancy without independent failure domains is false safety.

## Concrete example and dry run

A read-heavy URL service begins with two stateless API instances behind a load balancer and a primary database. Reads rise: add cache and read replicas. Writes rise: optimize/index, then partition by short-code hash if one primary is actually exhausted. During one API failure, health checks stop routing to it; during cache failure, requests fall back to the DB with admission control to prevent a stampede.

## Success and failure scenarios

Success: load spreads and user-visible SLO remains healthy. Failure: autoscaling APIs opens too many DB connections, replicas lag, or a shared region/network fails all “redundant” nodes. Cap concurrency, pool connections, isolate zones, and test failover.

## Scaling and production choices

Use load balancers, horizontal autoscaling, caches, queues, partitioned stores, replicas, CDNs, and bulkheads only for measured limits. Track traffic, latency, errors, saturation, queue age, DB connections, cache hit rate, and skew.

## Trade-offs and when not to use

Redundancy costs money and operational complexity; async scaling adds eventual consistency; partitioning complicates transactions. A simple single-region service is correct when requirements do not justify multi-region or sharding.

## Interview mistakes and follow-ups

Equating scalability with availability; “add servers” while DB remains bottleneck; no peak/hot-key analysis; active-active without conflict rules. Follow-ups: first bottleneck? one-zone loss? cache loss? 10× writes? graceful degradation?

## Five-minute recall

Load dimension → bottleneck → scale unit → distribute → isolate failure → degrade → observe → test.

Related: [[Load Balancing]], [[Partitioning and Sharding]], [[Replication]], [[Graceful Degradation]].

## Source metadata

Existing framework and sanitized preparation source; examples are generic assumptions.
