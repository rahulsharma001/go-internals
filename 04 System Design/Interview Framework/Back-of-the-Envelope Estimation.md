---
type: canonical
domain: system-design
topic: estimation
status: active
---
# Back-of-the-Envelope Estimation

## Purpose and mental model

Estimation finds the first architectural constraint. Use round, labelled interview assumptions and show units. Precision is less valuable than translating a result into a design decision.

## Core formulas

- average rate = operations per day ÷ 86,400;
- peak rate = average × explicit peak factor;
- storage = records × bytes × retention × replication/index overhead;
- bandwidth = requests/s × bytes/request;
- concurrent work ≈ arrival rate × average service time (Little’s Law intuition);
- fan-out rate = source events × recipients/channels;
- partition count ≥ peak work ÷ safe capacity per partition, then add headroom and skew allowance;
- cache memory = hot keys × key/value bytes × metadata/replica overhead.

Always ask whether averages hide celebrity, tenant, city, or release-event skew.

## A seven-step worksheet

1. Write the main read, write, event, or connection unit.
2. Assume daily/active volume and convert to average per second.
3. Apply peak and skew separately.
4. Estimate payload and retention only for authoritative or expensive data.
5. Include fan-out, replicas, indexes, or multiple renditions when relevant.
6. Identify the first limit: CPU, database write/lock, network, queue, connection, or hot key.
7. State the consequence: “Therefore I partition by conversation and need about N partitions with headroom.”

## Worked example: notification intake

Interview assumptions: 100 million requests/day, 1 KB request record, 5× peak, average 1.5 selected channels, 30-day hot retention.

- average intake ≈ `100,000,000 / 86,400 ≈ 1,200/s`;
- peak intake ≈ `6,000/s`;
- peak channel jobs ≈ `9,000/s` before retries;
- raw request storage ≈ `100 GB/day`, or `3 TB/30 days`, before replicas and indexes.

Consequences: durable async buffering, separate channel/priority consumers, provider quota isolation, hot storage plus archival, and alerts on oldest queued item. The numbers are assumptions, not facts about a company.

## Worked example: chat connections

Assume 20 million concurrent sockets and a gateway safely handles 50,000 after measured memory/file-descriptor headroom. Baseline is 400 gateways; add capacity for rolling deploys and reconnect bursts. Message QPS is a different dimension: idle sockets consume connection resources without sending messages.

## Common mistakes

- active users treated as QPS;
- no units or peak factor;
- ignoring fan-out and amplification;
- using total storage to choose a partition key;
- dividing evenly while ignoring hot keys;
- calculating ten values and changing no decision;
- presenting assumptions as private product facts.

## Interview follow-ups

- What if one tenant is 20% of traffic?
- How much queue accumulates in a one-hour outage?
- How many connections reconnect in 30 seconds?
- What is storage after replication, indexes, and multiple media renditions?
- Does egress or compute dominate cost?

## Five-minute revision

Unit → average → peak → skew → payload → retention/amplification → concurrency/fan-out → first limit → design consequence.

Related: [[Latency Throughput and Capacity]] · [[Finding Bottlenecks]] · [[Partitioning and Sharding]] · [[Capacity Estimation Cheatsheet]].

