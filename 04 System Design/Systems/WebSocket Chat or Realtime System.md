---
status: learning
type: system-design
area: system-design
sources:
  - "ChatGPT: AWS WebSocket Architecture Overview (2025-06-09, 6846e928-6bfc-8013-8fb6-6961d4da1540)"
---

# WebSocket Chat or Realtime System

## 1. Problem statement

Design a one-to-one/group chat or realtime update system with long-lived connections, durable messages, per-conversation ordering, offline catch-up, presence, and reconnect recovery.

## 2. Functional requirements

Connect/authenticate; send messages with client IDs; deliver to online members; store history; acknowledge delivery/read state; reconnect from a cursor; expose best-effort presence. Media upload and end-to-end encryption internals are out of scope unless requested.

## 3. Non-functional requirements

Low online-delivery latency, durable accepted messages, per-conversation—not global—ordering, horizontal connection scale, backpressure for slow clients, and graceful reconnect.

## 4. Scale assumptions

Ask for concurrent connections, messages/second, group size distribution, message bytes, heartbeat interval, retention, and regions. Separate connection capacity from message throughput; real targets are `status: needs-verification`.

## 5. Core entities

`User`, `Conversation`, `Membership`, `Connection`, `Message`, `ConversationSequence`, `DeliveryCursor`, and `PresenceLease`.

## 6. API design

```text
GET /realtime  Upgrade: websocket; Authorization: Bearer ...
client → {type:"send", conversationId, clientMessageId, body}
server → {type:"accepted", messageId, sequence}
server → {type:"message", conversationId, sequence, ...}
client → {type:"ack", conversationId, sequence}
GET /v1/conversations/{id}/messages?afterSequence=...
```

## 7. Data model

Messages are unique by `(sender_id, client_message_id)` and ordered by `(conversation_id, sequence)`. Membership is authoritative. Connection routing and presence leases are ephemeral with TTL. Delivery cursor stores the highest contiguous acknowledged sequence per user/conversation or device policy.

## 8. High-level architecture

```text
Clients → L4/L7 load balancer → WebSocket gateways
                                      │ connection registry/presence
                                      ▼
                              Chat command service → message DB/outbox
                                                       ↓
                                                   message stream
                                                       ↓
                                               fan-out workers → gateways
Offline client → history API/message store
```

## 9. Component responsibilities

Gateway manages sockets, auth refresh, heartbeats, bounded buffers, and routing. Chat service validates membership and commits messages. Sequencer assigns conversation order. Stream distributes committed messages. Fan-out locates active connections. History API provides authoritative catch-up.

## 10. Complete request or event flow

Connect and register route → client sends stable ID → validate membership → atomically persist message/sequence/outbox → acknowledge sender → stream committed message → fan-out to online member gateways → recipients ack/update cursor → offline/reconnected members fetch after cursor.

## 11. Detailed success path

Sender retries `clientMessageId=m-9` after losing an acknowledgement. The uniqueness constraint returns the existing server message and sequence. A recipient gateway delivers it, the client advances its contiguous cursor, and reconnect requests only later sequences.

## 12. At least one detailed failure path

A gateway dies with many sockets. Its presence leases expire; clients reconnect with jitter to other gateways and provide last acknowledged cursor. They fetch a snapshot/history gap, then subscribe to live traffic. A slow client exceeds its bounded send buffer: optional presence/typing events are dropped first; if durable messages still cannot drain, close the socket and rely on catch-up rather than exhaust gateway memory.

## 13. Bottlenecks

Connection memory/file descriptors, reconnect storms, celebrity groups, hot conversation partitions, presence write amplification, fan-out duplication, and slow consumers.

## 14. Scaling strategy

Use many stateless gateways with external routing/leases; partition messages by conversation for order; shard very large fan-out separately; batch presence updates; use [[Backpressure Pattern]]; store durable history independent of socket lifetime.

## 15. Reliability and disaster recovery

Replicate message storage and stream; treat presence as reconstructible soft state; preserve a home region/epoch for conversation ordering or define conflict semantics; test gateway loss and regional reconnect capacity; use durable cursors and replay.

## 16. Observability

Track active connections, connect/auth failures, reconnect rate, heartbeat timeout, gateway buffer depth, send-to-accept and accept-to-deliver latency, duplicate sends, sequence gaps, fan-out errors, slow-client disconnects, and catch-up duration.

## 17. Security

Authorize every conversation action, rotate/refresh tokens, rate-limit sends/connects, cap frame size, validate content, encrypt transport, restrict connection-registry access, protect history, and avoid logging message bodies/tokens.

## 18. Concrete technology choices

Go/Java/Netty-style gateways; Redis/etcd-like ephemeral registry; Kafka/Pulsar for ordered partitions; PostgreSQL/Cassandra/DynamoDB-like message storage based on query and region needs; object storage for media.

## 19. Trade-offs

WebSockets give bidirectional low latency but require stateful connection operations. Fan-out-on-write speeds reads but amplifies huge groups; fan-out-on-read delays delivery. Strict global ordering is costly and unnecessary; per-conversation sequence is usually enough.

## 20. Interview follow-up questions

How are duplicate sends handled? What happens during reconnect? How do giant groups change fan-out? How is cross-region ordering defined? Which events may be dropped under pressure?

## 21. Five-minute revision

Socket gateway is not the source of truth. Persist and sequence first, then fan out. Deduplicate client IDs. Track cursors for reconnect. Presence is TTL soft state. Bound buffers and shed ephemeral events. Partition by conversation.

## Related notes

[[Load Balancing]] · [[Stateless and Stateful Services]] · [[Queues and Pub Sub]] · [[Idempotency Pattern]] · [[Graceful Degradation]]

## Source metadata

Based on the extracted *AWS WebSocket Architecture Overview* conversation (date/ID above) and curated foundations. Cloud-provider details require current official verification.
