> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Stateless and Stateful Services]].

---
type: canonical
domain: system-design
topic: stateless-stateful-services
status: learning
---
# Stateless and Stateful Services

## Problem it solves

It clarifies where durable/session/connection state lives and therefore how instances scale, fail, and deploy.

## Mental model and how it works

A stateless request handler can serve any request using external durable/shared state. A stateful component owns data or a long-lived session/connection that cannot freely move. Stateless does not mean “no cache” and stateful does not mean “bad”; make ownership, recovery, and routing explicit.

## Concrete example and dry run

Chat HTTP APIs are stateless: authenticate token, read/write message store, return. WebSocket gateways are connection-stateful: connection `c7` lives on pod P2, while a shared connection directory maps user to gateway. A message for that user routes to P2. If P2 dies, the client reconnects, refreshes mapping, and fetches missed messages from durable storage.

## Success and failure scenarios

Success: stateless APIs autoscale and connection state has a documented reconnect/recovery path. Failure: in-memory sessions disappear, sticky routing hides a single point, or two gateways believe they own one connection. Use leases/TTL, heartbeat, fencing/version, durable offsets, and client retry.

## Scaling and production choices

Examples: stateless containers behind a load balancer; Redis/database for shared session metadata; partitioned brokers/databases as intentionally stateful components. Observe active sessions, reconnect rate, mapping staleness, state transfer, and drain duration.

## Trade-offs and when not to use

Externalizing all state adds network latency and dependency load. Affinity can be sensible for sockets or caches if loss is tolerated. Do not force statelessness onto storage/broker ownership.

## Interview mistakes and follow-ups

Calling JWT-based services stateless while storing local workflows; no deploy drain; sticky sessions as recovery. Follow-ups: pod crash? rolling deploy? reconnect storm? session revocation? ownership transfer?

## Five-minute recall

Name state → owner → durability → routing → failure/recovery → scale unit → drain/transfer metrics.

Related: [[Load Balancing]], [[WebSocket Chat or Realtime System]], [[Leader Election]].

## Source metadata

Curated foundation using generic WebSocket material (`AWS WebSocket Architecture Overview`, `6846e928…`); AWS-specific claims excluded.
