---
type: quick-revision
domain: system-design
review_time: 5-minutes
---
# Database Selection Guide

| Need | Strong default candidate | Watch for |
| --- | --- | --- |
| multi-row invariant, constraints, flexible query | PostgreSQL/MySQL | write hotspots, partition operations, cross-region write latency |
| key-value at very high scale | DynamoDB/Cassandra | access-pattern rigidity, hot keys, secondary-index limits |
| sub-millisecond derived state | Redis/Memcached | memory cost, eviction, failover staleness; not automatically truth |
| immutable large bytes | S3/GCS | metadata/object atomicity, signed access, orphan cleanup |
| full-text/prefix/filter search | OpenSearch/Lucene | index freshness, rebuild, shard skew, expensive queries |
| time-series ranges and aggregates | Prometheus-compatible TSDB/ClickHouse | cardinality, retention, compaction |
| durable ordered event replay | Kafka/Kinesis/PubSub | partitions, lag, duplicate processing, retention |

## Selection sentence

“The owner needs **access pattern**, **invariant/consistency**, **scale**, and **retention**. I select **X** because ___. **Y** is viable but costs ___. I would reverse the choice when ___.”

Technology is an example, not the design. See [[Database and Storage Selection]] and [[Choosing Databases and Storage]].
