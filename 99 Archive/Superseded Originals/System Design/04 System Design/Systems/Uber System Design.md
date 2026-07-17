> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Uber System Design]].

---
status: learning
type: system-design
area: system-design
sources:
  - "ChatGPT: Uber System Design Breakdown (2026-07-12, 6a530517-5914-83ee-bb99-41c31e2067da)"
---

# Uber System Design

## 1. Problem statement

Design a ride-hailing system that continuously ingests driver locations, finds nearby eligible drivers, matches one driver to one rider, maintains a real-time trip lifecycle, and completes pricing and payment despite mobile and regional failures.

## 2. Functional requirements

- Drivers publish availability and location.
- Riders request an origin/destination and receive an estimate.
- System finds candidates, sends offers, and commits one acceptance.
- Both parties receive live trip state/location.
- Trip completes with final price and payment.
- Cancellation and timeout paths are explicit.

Out of scope unless requested: pooled rides, scheduled trips, fraud modelling, navigation algorithm internals, and driver incentives.

## 3. Non-functional requirements

Low-latency nearby search and offer delivery; one committed driver per trip; high location-ingestion availability; durable trip/payment state; bounded stale-location risk; regional fault isolation; privacy controls.

## 4. Scale assumptions

Ask for active drivers, location update interval, request rate by city, acceptable match latency, and retention. Express ingest as `active drivers ÷ update interval`; do not assert unsourced real-world numbers. Hot-region skew matters more than an average.

## 5. Core entities

`Rider`, `Driver`, `DriverAvailability`, `LocationUpdate`, `RideRequest`, `MatchAttempt`, `Offer`, `Trip`, `Fare`, and `Payment`.

Important invariants: one active trip per driver, at most one accepted driver per request, valid trip-state transitions, and monotonic location sequence per device session.

## 6. API design

```text
POST /v1/ride-requests {pickup, destination, product}
Idempotency-Key: rider-session-request
→ 202 {requestId, state:"SEARCHING", estimate}

PUT /v1/drivers/me/location {lat, lon, accuracy, recordedAt, sequence}
POST /v1/offers/{offerId}/accept {driverSessionId}
GET /v1/trips/{tripId}
WebSocket: trip.{tripId} state/location events
```

## 7. Data model

Durable relational state stores ride requests, match attempts, offers, trip transitions, fare, and payment references. A geo-index stores current driver position with timestamp, sequence, availability, vehicle type, and cell. An append stream retains location/events according to policy. The current-location view is disposable; the trip ledger is not.

## 8. High-level architecture

```text
Driver app → Location Gateway → stream → geo-index/current-location store
                                          │
Rider app → API Gateway → Ride Service → Matching Service → Offer Service
                                               │                │
                                               └──── candidates └→ push/WebSocket → drivers
Accepted offer → Trip Service → realtime gateway → rider + driver
Trip completed → Pricing → Payment → receipt/notification
```

## 9. Component responsibilities

- Location gateway authenticates sessions, rejects invalid/out-of-order samples, and publishes updates.
- Geo index supports cell/radius lookup and TTL-based freshness.
- Matching ranks eligible candidates and manages attempts.
- Offer service delivers time-bounded offers.
- Trip service owns the authoritative state machine.
- Realtime gateways fan out ephemeral updates; payment records durable side effects.

## 10. Complete request or event flow

`Rider request → location ingestion → nearby-driver lookup → matching → offer dispatch → driver acceptance → trip lifecycle → pricing and payment`.

1. Drivers send sequenced updates; ingestion writes a partitioned stream and refreshes the latest geo entry.
2. Ride service validates the request and creates `SEARCHING`.
3. Matching maps pickup to an H3/S2/geohash cell, queries the cell and neighbouring rings, filters stale/busy/incompatible drivers, then ranks by ETA and policy.
4. Offer service sends a small batch or staged offers over WebSocket/push with deadlines.
5. Acceptance executes a conditional transaction: claim driver if available and request if still searching; the winner creates the trip.
6. Trip transitions `DRIVER_ASSIGNED → ARRIVING → IN_PROGRESS → COMPLETED` and streams updates.
7. Pricing computes the final fare from the agreed policy and trip facts; payment uses an idempotency key; receipt notification is asynchronous.

## 11. Detailed success path

A fresh location places driver `d-7` in the pickup cell. Matching expands one ring, ranks candidates, and creates expiring offers. `d-7` accepts; a compare-and-set/transaction changes both driver availability and ride request, rejecting later acceptances. Both clients subscribe to the trip channel. On completion, a durable trip event triggers final fare and one payment; the trip closes only according to the defined payment policy.

## 12. At least one detailed failure path

**Driver accepts while the network response is lost:** the app retries with the same offer/command ID. The offer service returns the stored acceptance; it does not create another trip. If a second driver accepts, the conditional claim loses and receives `OFFER_EXPIRED`.

**Location/realtime degradation:** stale entries expire and are excluded; matching expands the search or reports no cars instead of using unsafe positions. WebSocket reconnect uses last seen event/version to obtain a snapshot plus newer events. Payment-provider timeout is handled by [[Idempotency Pattern]] and [[Retry Pattern]]; unknown outcome is reconciled before another charge.

## 13. Bottlenecks

Dense airport/stadium cells, synchronized location updates, expensive neighbour expansion, offer fan-out, one city/partition hot spot, WebSocket connection concentration, and third-party maps/payment latency.

## 14. Scaling strategy

Partition location streams and match workers by region/cell, add random sub-shards for very hot cells, batch/coalesce redundant updates, keep geo indexes regional, cap candidate fan-out, and move drivers between cells atomically enough for a freshness-tolerant lookup. Matching consistency must be strong only at the final claim, not for the entire candidate search.

## 15. Reliability and disaster recovery

Persist trip-state transitions and payment references across availability zones. Treat location as soft state rebuilt from new updates. Isolate cities/regions, maintain a tested regional failover policy, and avoid cross-region double matching with a single home region/epoch for each active trip. Recovery objectives are `status: needs-verification`.

## 16. Observability

Measure location ingest lag/drop rate, stale-driver ratio, geo-query latency, rings expanded, candidate count, offer delivery/acceptance latency, match success and timeout rates, trip transition failures, WebSocket reconnects, and payment unknown outcomes. Trace by `request_id`, `match_attempt_id`, `offer_id`, and `trip_id`.

## 17. Security

Authenticate devices and rotate sessions; authorize rider/driver access to a trip; encrypt location; minimize retention/precision; prevent location scraping with rate limits; validate samples; protect payment tokens; audit support access; avoid exposing exact driver coordinates before appropriate assignment.

## 18. Concrete technology choices

Kafka/Pulsar for partitioned location and lifecycle streams; H3/S2 or geohash for geo bucketing; Redis/Aerospike/custom in-memory shards for current locations; PostgreSQL/CockroachDB-like relational storage for trip invariants; WebSocket gateways for active trip streaming. Exact choices require latency, regional, and operational constraints.

## 19. Trade-offs

Finer geo cells reduce candidates but increase cell-boundary/partition churn. Sequential offers improve driver efficiency but increase rider latency; small parallel batches reduce latency but cause more losing offers. Eventual location consistency is acceptable; final assignment needs atomic conditional ownership. Multi-region availability raises split-brain complexity.

## 20. Interview follow-up questions

- How is ETA ranking different from geometric distance?
- How do you handle a stadium hot spot?
- How do you prevent double acceptance?
- What is authoritative after a reconnect?
- How do surge pricing and privacy constraints change the design?

## 21. Five-minute revision

Ingest sequenced driver locations into regional geo cells; expire stale entries. Query nearby rings and rank by ETA. Send bounded offers. Atomically claim request + driver on acceptance. Persist trip state; stream live updates with reconnect snapshots. Make payment idempotent. Shard hot regions and fence cross-region ownership.

## Related notes

[[Consistent Hashing]] · [[Partitioning and Sharding]] · [[WebSocket Chat or Realtime System]] · [[Rate Limiting Pattern]] · [[Multi Region Architecture]]

## Source metadata

Primary source: extracted *Uber System Design Breakdown*, 2026-07-12, conversation ID above. Architecture is an interview design, not a claim about Uber's current private implementation. Product-specific details remain `status: needs-verification`.
