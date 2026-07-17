---
type: quick-revision
domain: infrastructure
status: active
---

# Networking Interview Revision

## TCP/TLS/HTTP connection

SYN → SYN-ACK → ACK; sequence/ACK/window/retransmission move ordered bytes; FIN/ACK closes each direction, RST aborts, TIME_WAIT protects old segments. TLS ClientHello/SNI/ALPN → certificate validation/key exchange → encrypted HTTP. Pool reuse amortizes handshakes.

## DNS and HTTP

Stub → recursive cache → authoritative lookup → TTL answer. HTTP/1.1 reuses connections, HTTP/2 multiplexes streams over TCP, HTTP/3 uses QUIC/UDP. DNS change does not close pooled connections.

## Kubernetes packet

CoreDNS → Service ClusterIP → ready EndpointSlice → kube-proxy/eBPF → CNI → Pod IP. Direct Pod works but Service fails: inspect endpoint/rules. Name fails but IP works: inspect DNS.

## Realtime/NAT/LB

WebSocket upgrades to bidirectional frames; SSE is one-way stream; webhook is signed retrying server callback; polling is simplest. NAT rewrites statefully. ALB is L7; NLB L4. Long-lived connections balance at connect.

## Networking-role fundamentals

IPsec/IKE negotiates SAs; ESP protects packets; VTI/XFRM makes a routable tunnel; OSPF neighbor/LSDB/SPF installs dynamic routes; SNMP trap is fast but lossy, so reconcile by poll/heartbeat.

## Troubleshooting

Source/destination/time → DNS → `ip route get` → `ss` listener → firewall/SG/policy → SYN → TLS → LB target → HTTP → return. Small works/large fails: MTU/MSS.

## Related

[[Network Troubleshooting]]

Return: [[Infrastructure Dashboard]]
