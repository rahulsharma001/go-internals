---
type: canonical
domain: system-design
topic: search-and-geospatial-indexes
status: active
last_verified: 2026-07-17
---
# Search and Geospatial Indexes

## 1. Problem it solves

Transactional stores are poor at relevance-ranked text, prefix completion, facets, or nearby/radius queries. Specialized derived indexes map terms or spatial cells to candidates.

## 2. Simple mental model

An inverted index maps term→documents; autocomplete maps prefix→ranked suggestions; a spatial index maps coordinates→cells/trees. The index finds candidates; authoritative state revalidates correctness.

## 3. How it works

Normalize/tokenize and build postings with scores/filters. For geo, encode points into hierarchical cells/geohash/S2/H3 or tree indexes, query target and neighbouring cells, then exact-distance/ETA rank. Update asynchronously with versions.

## 4. Concrete example

Ride matching maps pickup to an H3/S2/geohash-like cell, expands neighbouring rings, filters stale/busy drivers, and ranks by ETA. Final driver claim occurs in authoritative trip state.

## 5. Detailed success flow

Source commits item/version, change pipeline updates index, query returns candidates, service filters authorization/current state, ranks, paginates, and reports index freshness.

## 6. Detailed failure flow

Index lags deletion or availability. Sensitive reads recheck truth; stale hit is suppressed. Rebuild from snapshot+change log; query can degrade to limited exact lookup rather than let index become truth.

## 7. Scaling behaviour

Partition by term/document/geo region; hot prefixes/cells need caching, sub-shards, and caps. Query fan-out and merge drive tail. Control index refresh, segment merge, cardinality, and rebuild time.

## 8. Data consistency implications

Search is usually eventual. Include document version/tombstone; define read-your-writes if needed. Final inventory/driver/ACL decisions must revalidate authority.

## 9. Real implementation choices

OpenSearch/Elasticsearch/Lucene; PostgreSQL full-text/GiST for smaller scope; Redis GEO; H3/S2/geohash cells; trie/FST for autocomplete.

## 10. Trade-offs

Freshness versus indexing throughput; fine geo cells versus boundary expansion/churn; precomputed suggestions versus update lag; search flexibility versus operational complexity.

## 11. When not to use it

Do not add a search cluster for exact primary-key lookup or small SQL text search. Do not rely on geo candidates for final assignment correctness.

## 12. Common interview mistakes

Index as truth; unexplained geohash; no boundary/neighbour search; no version/delete; global query fan-out; ranking without candidate generation; location retention/privacy ignored.

## 13. How it appears inside larger systems

Autocomplete, web crawler, feed search, nearby drivers, event discovery, logs, and metadata search.

## 14. Likely interviewer follow-ups

How index updates? freshness? deletion? hot prefix/cell? typo tolerance? ranking? geo boundary? exact distance? rebuild without downtime?

## 15. Five-minute revision

Derived index maps query→candidates; source remains truth. Version/tombstone, partition/merge, hot query control, revalidate invariant/ACL, rebuild from snapshot+log.

## 16. Related notes

[[Search Autocomplete System]] · [[Uber System Design]] · [[Web Crawler System]] · [[Change Data Capture]]

## 17. Verified further reading

- [OpenSearch documentation](https://docs.opensearch.org/latest/) — official indexing/search concepts.\n- [PostgreSQL text search](https://www.postgresql.org/docs/current/textsearch.html) — official smaller-scale full-text alternative.

