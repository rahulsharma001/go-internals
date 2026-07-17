---
type: canonical
domain: infrastructure
topic: linux-networking-tools
status: learning
---

# Linux Networking Tools

## Problem and mental model

Selects the least invasive tool for each packet-path question.

## Internal/end-to-end flow

Name → `dig/getent`; local listener → `ss`; route → `ip route get`; neighbor/interface → `ip`; HTTP/TLS → `curl -v`/`openssl s_client`; path → `tracepath`; packets → `tcpdump`; firewall → approved nftables tooling.

## Failure modes and troubleshooting

Run from the affected namespace/Pod. Compare DNS, connect, TLS and HTTP separately. `ping` success neither proves TCP port nor application health; traceroute may be filtered.

## Production security, scaling and trade-offs

Start read-only and low-volume; packet captures can contain sensitive payloads. Capture metadata/filter narrowly, follow access and retention controls.

## Interview questions and five-minute revision

Given timeout, which three commands distinguish DNS, route and listener? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Network Troubleshooting]] · [[Client to Pod Request Flow]]

## Source metadata

Curated from the networking-focused Go interview extracts and established Linux/Go operational mechanics. Kernel, cgroup and distribution-specific behavior is `needs-verification`.
