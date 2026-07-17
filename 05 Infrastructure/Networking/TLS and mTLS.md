---
type: canonical
domain: infrastructure
topic: tls-mtls
status: learning
---

# TLS and mTLS

## Problem and mental model

Authenticates endpoints and encrypts/integrity-protects transport; mTLS authenticates both peers.

## Packet or connection flow

TCP/QUIC reachability → ClientHello (versions, ciphers, SNI, ALPN) → server certificate/chain and key exchange → client validates name/trust/time → optional client certificate validation → traffic keys → HTTP. Session resumption reduces repeat work.

## Failure modes and senior diagnosis

`openssl s_client -connect host:443 -servername host`; `curl -v`; inspect chain, SAN, expiry, clock, SNI/ALPN and trust store. Handshake timeout differs from TCP connect. mTLS failures can occur on either trust/identity side.

## Production security, scaling and trade-offs

Automate issuance/rotation, short-lived workload identity where feasible, minimum versions/ciphers per policy, protect private keys and never log tokens/certs. Termination point defines plaintext boundary.

## Interview questions and five-minute revision

Server TLS versus mTLS; what does encryption not authorize? Recall the exact packet/connection sequence and the first diagnostic evidence at each boundary.

## Related notes

[[IAM Roles and Policies]] · [[Network Policies]] · [[HTTP 1 2 and 3]]

## Source metadata

Curated from *Golang Interview Prep Guide* (2026-06-29, `6a420622-0d40-83ee-8a64-955c416c4a67`) for the networking-focused role, plus relevant Kubernetes/AWS extracts. Protocol and implementation details are `needs-verification` against RFC/vendor/kernel documentation.
