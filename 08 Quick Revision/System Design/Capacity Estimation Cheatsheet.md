---
type: quick-revision
domain: system-design
review_time: 5-minutes
---
# Capacity Estimation Cheatsheet

## Anchors

- 1 day = 86,400 seconds ≈ 100,000 for interview arithmetic.
- 1M/day ≈ 12/s; 100M/day ≈ 1,160/s; 1B/day ≈ 11,600/s.
- Peak QPS = average QPS × stated peak multiplier.
- Concurrent work ≈ arrival rate × average time in system.
- Bandwidth = events/s × bytes/event.
- Storage = events/day × bytes/event × retention × replicas/index factor.
- Cache memory = active keys × bytes/key ÷ target load factor × replica factor.
- Partitions = max(throughput-bound, capacity-bound, hotspot-bound) × headroom.

## What to calculate

Calculate only values that change the architecture:

- queue/event rate for async systems
- concurrent sockets for realtime systems
- object ingress/egress for media/files
- fan-out writes for feeds/notifications
- rows/series/index bytes for storage/search
- residual source load after cache hit rate

State assumptions and units. Sanity-check orders of magnitude. Finish every estimate with: “Therefore this forces/does not yet force ___.” See [[Back-of-the-Envelope Estimation]].
