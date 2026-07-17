---
type: canonical
domain: system-design
topic: load-balancing
status: active
last_verified: 2026-07-17
---
# Load Balancing

## 1. Problem it solves

Clients need a stable entry point that distributes work across changing backends without sending traffic to unhealthy or overloaded instances.

## 2. Simple mental model

A load balancer chooses an eligible backend under a policy. It cannot create capacity or fix a saturated shared database; it only routes and may terminate protocols.

## 3. How it works

L4 balances connections; L7 understands HTTP routes/headers and may authenticate, rate limit, or retry cautiously. Algorithms include round robin, least outstanding, weighted, and hashing for affinity. Health, readiness, draining, outlier detection, and slow start keep routing safe.

## 4. Concrete example

An API gateway sends `/payments` to payment instances using least outstanding. Readiness removes a warming pod; connection draining lets in-flight calls finish. Retries are disabled for unsafe mutations unless idempotency is known.

## 5. Detailed success flow

DNS/anycast reaches a regional load balancer; TLS terminates; request is routed to a ready backend; deadlines and trace context pass end to end; response returns without hidden retry amplification.

## 6. Detailed failure flow

A backend is alive but slow. Passive outlier detection and latency/concurrency limits eject it; active checks verify recovery. If all backends saturate, admission control rejects instead of queueing indefinitely.

## 7. Scaling behaviour

The balancer needs connection, packet, and TLS capacity; distribute across zones/regions. Long-lived sockets balance by connections, not request QPS, and can skew after scaling. Affinity keys can create hotspots.

## 8. Data consistency implications

Routing to replicas affects read freshness. Sticky routing may provide session read-your-writes but is not a durability strategy. Writes should reach the correct authoritative partition/leader.

## 9. Real implementation choices

Cloud L4/L7 load balancers, Envoy/NGINX/HAProxy, Kubernetes Service/Gateway API, DNS/anycast for global routing. Choose from protocol and control needs.

## 10. Trade-offs

L7 adds features and CPU/latency; L4 is simpler/faster. Least-outstanding adapts to work but needs good signals. Hash affinity improves locality but hurts balance and failover.

## 11. When not to use it

Do not add multiple balancing layers without clear responsibilities. Direct service discovery may suit trusted internal clients with client-side balancing.

## 12. Common interview mistakes

Health check equals capacity; retry at load balancer plus client; no draining; round robin for highly variable work; sticky sessions to preserve durable state; global DNS called instant failover.

## 13. How it appears inside larger systems

Every client-facing system, service-to-service calls, WebSocket gateways, sharded caches, and multi-region ingress.

## 14. Likely interviewer follow-ups

L4 or L7? What health proves readiness? How drain deploys? How balance sockets? Where retry occurs? How route to shard/leader or nearest healthy region?

## 15. Five-minute revision

Stable endpoint → eligible set → policy → readiness/outlier/drain → overload behavior. Balancing routes capacity; it does not create it.

## 16. Related notes

[[Stateless and Stateful Services]] · [[Consistent Hashing]] · [[Bulkhead Pattern]] · [[Multi-Region Design]]

## 17. Verified further reading

- [Kubernetes Services, Load Balancing, and Networking](https://kubernetes.io/docs/concepts/services-networking/) — official routing abstractions.\n- [Kubernetes Service](https://kubernetes.io/docs/concepts/services-networking/service/) — stable endpoints and service types.

