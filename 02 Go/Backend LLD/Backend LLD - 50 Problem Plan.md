---
type: curriculum-plan
domain: backend-lld
language: go
company_focus: [apple, uber]
problem_count: 50
status: active
---

# Backend LLD - 50 Problem Plan

The target is clean running code under a 60–90 minute interview constraint. First lock requirements and ownership; then implement the smallest invariant, tests, cancellation/shutdown, and a spoken trade-off review. P0 precedes P1 and P2.

| # | Problem | Category | Priority | Concepts | Note |
| ---: | --- | --- | :---: | --- | --- |
| 1 | Generic Stack | foundation | P1 | generics, slices, zero values | [[02 Go/Backend LLD/01 Foundations/01 Generic Stack/Generic Stack|open]] |
| 2 | Generic Queue | foundation | P1 | generics, queue indexing, memory retention | [[02 Go/Backend LLD/01 Foundations/02 Generic Queue/Generic Queue|open]] |
| 3 | Circular Deque | foundation | P1 | ring buffers, index arithmetic, capacity | [[02 Go/Backend LLD/01 Foundations/03 Circular Deque/Circular Deque|open]] |
| 4 | Thread-Safe Set | foundation | P1 | maps, mutexes, snapshot semantics | [[02 Go/Backend LLD/01 Foundations/04 Thread-Safe Set/Thread-Safe Set|open]] |
| 5 | Thread-Safe Bounded Queue | foundation | P0 | mutexes, condition signaling, context cancellation, close semantics | [[02 Go/Backend LLD/01 Foundations/05 Thread-Safe Bounded Queue/Thread-Safe Bounded Queue|open]] |
| 6 | Worker Pool | foundation | P0 | goroutines, channels, backpressure, cancellation, shutdown | [[02 Go/Backend LLD/01 Foundations/06 Worker Pool/Worker Pool|open]] |
| 7 | Priority Worker Pool | foundation | P0 | heap, goroutines, scheduling, shutdown | [[02 Go/Backend LLD/01 Foundations/07 Priority Worker Pool/Priority Worker Pool|open]] |
| 8 | Fan-Out Fan-In Processing Pipeline | foundation | P1 | channels, ownership, cancellation, error propagation | [[02 Go/Backend LLD/01 Foundations/08 Fan-Out Fan-In Processing Pipeline/Fan-Out Fan-In Processing Pipeline|open]] |
| 9 | Concurrent Batch Processor | foundation | P1 | batching, timers, goroutines, backpressure | [[02 Go/Backend LLD/01 Foundations/09 Concurrent Batch Processor/Concurrent Batch Processor|open]] |
| 10 | Semaphore With Context Cancellation | foundation | P1 | channels, context, admission control | [[02 Go/Backend LLD/01 Foundations/10 Semaphore With Context Cancellation/Semaphore With Context Cancellation|open]] |
| 11 | In-Memory Key-Value Store | foundation | P1 | maps, interfaces, synchronization | [[02 Go/Backend LLD/01 Foundations/11 In-Memory Key-Value Store/In-Memory Key-Value Store|open]] |
| 12 | TTL Cache | foundation | P0 | maps, mutexes, clock injection, expiration | [[02 Go/Backend LLD/01 Foundations/12 TTL Cache/TTL Cache|open]] |
| 13 | LRU Cache | foundation | P0 | maps, doubly linked lists, mutexes, invariants | [[02 Go/Backend LLD/01 Foundations/13 LRU Cache/LRU Cache|open]] |
| 14 | LFU Cache | foundation | P1 | frequency buckets, linked lists, eviction | [[02 Go/Backend LLD/01 Foundations/14 LFU Cache/LFU Cache|open]] |
| 15 | Expiring Priority Queue | foundation | P1 | heap, timers, expiration, synchronization | [[02 Go/Backend LLD/01 Foundations/15 Expiring Priority Queue/Expiring Priority Queue|open]] |
| 16 | In-Process Pub Sub Broker | foundation | P0 | channels, subscriber ownership, backpressure, shutdown | [[02 Go/Backend LLD/01 Foundations/16 In-Process Pub Sub Broker/In-Process Pub Sub Broker|open]] |
| 17 | Typed Event Bus | foundation | P1 | generics, handlers, synchronization, dispatch | [[02 Go/Backend LLD/01 Foundations/17 Typed Event Bus/Typed Event Bus|open]] |
| 18 | Middleware Chain | foundation | P0 | interfaces, functions, composition, ordering | [[02 Go/Backend LLD/01 Foundations/18 Middleware Chain/Middleware Chain|open]] |
| 19 | Router With Path Parameters | foundation | P0 | tries, parsing, precedence, interfaces | [[02 Go/Backend LLD/01 Foundations/19 Router With Path Parameters/Router With Path Parameters|open]] |
| 20 | In-Memory File System | foundation | P0 | trees, path normalization, locking, interfaces | [[02 Go/Backend LLD/01 Foundations/20 In-Memory File System/In-Memory File System|open]] |
| 21 | Token-Bucket Rate Limiter | infrastructure | P0 | mutexes, clocks, refill math, context | [[02 Go/Backend LLD/02 Infrastructure Components/21 Token-Bucket Rate Limiter/Token-Bucket Rate Limiter|open]] |
| 22 | Sliding-Window Rate Limiter | infrastructure | P1 | time windows, queues, locking, bounded state | [[02 Go/Backend LLD/02 Infrastructure Components/22 Sliding-Window Rate Limiter/Sliding-Window Rate Limiter|open]] |
| 23 | Retry Executor | infrastructure | P0 | context, errors, backoff, jitter, idempotency | [[02 Go/Backend LLD/02 Infrastructure Components/23 Retry Executor/Retry Executor|open]] |
| 24 | Circuit Breaker | infrastructure | P0 | state machines, atomics or mutexes, clocks | [[02 Go/Backend LLD/02 Infrastructure Components/24 Circuit Breaker/Circuit Breaker|open]] |
| 25 | Bulkhead Executor | infrastructure | P1 | semaphores, queues, rejection, context | [[02 Go/Backend LLD/02 Infrastructure Components/25 Bulkhead Executor/Bulkhead Executor|open]] |
| 26 | Timeout and Deadline Budget | infrastructure | P1 | context, deadlines, budget propagation | [[02 Go/Backend LLD/02 Infrastructure Components/26 Timeout and Deadline Budget/Timeout and Deadline Budget|open]] |
| 27 | Idempotency-Key Store | infrastructure | P0 | state transitions, locking, TTL, result replay | [[02 Go/Backend LLD/02 Infrastructure Components/27 Idempotency-Key Store/Idempotency-Key Store|open]] |
| 28 | Singleflight Request Coalescer | infrastructure | P0 | maps, waiters, panic safety, context | [[02 Go/Backend LLD/02 Infrastructure Components/28 Singleflight Request Coalescer/Singleflight Request Coalescer|open]] |
| 29 | Connection Pool | infrastructure | P0 | resource lifecycle, channels, health, shutdown | [[02 Go/Backend LLD/02 Infrastructure Components/29 Connection Pool/Connection Pool|open]] |
| 30 | Resilient API Client | infrastructure | P1 | HTTP, context, retries, breakers, observability | [[02 Go/Backend LLD/02 Infrastructure Components/30 Resilient API Client/Resilient API Client|open]] |
| 31 | Delayed Job Queue | infrastructure | P0 | heap, timers, wakeups, shutdown | [[02 Go/Backend LLD/02 Infrastructure Components/31 Delayed Job Queue/Delayed Job Queue|open]] |
| 32 | Cron-Like Scheduler | infrastructure | P0 | scheduling, clocks, goroutines, cancellation | [[02 Go/Backend LLD/02 Infrastructure Components/32 Cron-Like Scheduler/Cron-Like Scheduler|open]] |
| 33 | Durable Job Scheduler Simulation | infrastructure | P1 | state persistence simulation, recovery, leases | [[02 Go/Backend LLD/02 Infrastructure Components/33 Durable Job Scheduler Simulation/Durable Job Scheduler Simulation|open]] |
| 34 | Message Queue With Acknowledgements | infrastructure | P0 | delivery state, ack deadlines, redelivery, shutdown | [[02 Go/Backend LLD/02 Infrastructure Components/34 Message Queue With Acknowledgements/Message Queue With Acknowledgements|open]] |
| 35 | Partitioned Message Broker | infrastructure | P2 | partitioning, ordering, offsets, concurrency | [[02 Go/Backend LLD/02 Infrastructure Components/35 Partitioned Message Broker/Partitioned Message Broker|open]] |
| 36 | Write-Ahead Log | infrastructure | P2 | encoding, checksums, fsync trade-offs, recovery | [[02 Go/Backend LLD/02 Infrastructure Components/36 Write-Ahead Log/Write-Ahead Log|open]] |
| 37 | Transactional In-Memory Database | infrastructure | P2 | transactions, isolation, locking, rollback | [[02 Go/Backend LLD/02 Infrastructure Components/37 Transactional In-Memory Database/Transactional In-Memory Database|open]] |
| 38 | Metrics Aggregator | infrastructure | P1 | concurrent counters, snapshots, bounded cardinality | [[02 Go/Backend LLD/02 Infrastructure Components/38 Metrics Aggregator/Metrics Aggregator|open]] |
| 39 | Splitwise Expense Manager | machine-coding | P0 | domain modeling, money, validation, strategy interfaces | [[02 Go/Backend LLD/03 Machine Coding/39 Splitwise Expense Manager/Splitwise Expense Manager|open]] |
| 40 | Parking Lot | machine-coding | P2 | domain modeling, allocation, concurrency, state transitions | [[02 Go/Backend LLD/03 Machine Coding/40 Parking Lot/Parking Lot|open]] |
| 41 | Train-Platform Management System | machine-coding | P1 | intervals, scheduling, conflict detection | [[02 Go/Backend LLD/03 Machine Coding/41 Train-Platform Management System/Train-Platform Management System|open]] |
| 42 | Elevator Controller | machine-coding | P2 | state machines, scheduling, concurrency | [[02 Go/Backend LLD/03 Machine Coding/42 Elevator Controller/Elevator Controller|open]] |
| 43 | Notification Service | machine-coding | P1 | interfaces, fan-out, retries, idempotency | [[02 Go/Backend LLD/03 Machine Coding/43 Notification Service/Notification Service|open]] |
| 44 | Logger Library | machine-coding | P2 | interfaces, levels, outputs, concurrency | [[02 Go/Backend LLD/03 Machine Coding/44 Logger Library/Logger Library|open]] |
| 45 | Food-Delivery Order State Machine | machine-coding | P2 | state machines, validation, events | [[02 Go/Backend LLD/03 Machine Coding/45 Food-Delivery Order State Machine/Food-Delivery Order State Machine|open]] |
| 46 | Cab-Booking Core | machine-coding | P2 | domain modeling, matching, concurrency, location abstraction | [[02 Go/Backend LLD/03 Machine Coding/46 Cab-Booking Core/Cab-Booking Core|open]] |
| 47 | Inventory Reservation System | machine-coding | P0 | atomic state transitions, idempotency, expiry, concurrency | [[02 Go/Backend LLD/03 Machine Coding/47 Inventory Reservation System/Inventory Reservation System|open]] |
| 48 | Library Management System | machine-coding | P2 | domain modeling, repositories, borrowing rules | [[02 Go/Backend LLD/03 Machine Coding/48 Library Management System/Library Management System|open]] |
| 49 | Feature-Flag Service | machine-coding | P1 | evaluation rules, caching, snapshots, concurrency | [[02 Go/Backend LLD/03 Machine Coding/49 Feature-Flag Service/Feature-Flag Service|open]] |
| 50 | API Gateway Request Pipeline | machine-coding | P2 | middleware, authentication, limits, routing, observability | [[02 Go/Backend LLD/03 Machine Coding/50 API Gateway Request Pipeline/API Gateway Request Pipeline|open]] |

## Completion Gate

requirements-understood → design-ready → running-code → unit tests → race test where relevant → graceful shutdown verified → explain aloud → cold reconstruction → mock-needed → interview-ready.

Scaffold compilation never advances the tracker. Use [[Backend LLD Practice Tracker]] and [[LLD Machine Coding Mock Template]].

