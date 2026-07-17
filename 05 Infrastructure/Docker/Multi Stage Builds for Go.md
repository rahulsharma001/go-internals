---
type: canonical
domain: infrastructure
topic: docker-multistage-go
status: learning
---

# Multi Stage Builds for Go

## Problem and mental model

Builds a Go binary with toolchain/tests while shipping only required runtime artifacts.

## Internal/end-to-end flow

Builder stage copies module files, downloads, copies source and builds with explicit target/CGO policy; runtime stage copies binary and CA/time-zone data only when needed. Run as non-root and set ENTRYPOINT.

## Failure modes and troubleshooting

`docker build --target build`; run unit tests in builder; inspect `file`/runtime error. `exec format error` means architecture mismatch; missing CA causes TLS failures; CGO binary may need libc.

## Production security, scaling and trade-offs

Distroless/scratch minimizes attack surface but reduces shell debugging. Use ephemeral debug containers rather than adding tools permanently. Produce SBOM/signature in CI.

## Interview questions and five-minute revision

Static versus CGO trade-offs? What runtime files does HTTPS need? Recall the layer, evidence, mitigation and permanent fix.

## Related notes

[[Containers and Images]] · [[Docker Layers and Build Cache]] · [[Minikube Practical Labs]]

## Source metadata

Curated from *Docker VPN Subnet Conflict* (2025-01-27, `6797b48a-68b4-8013-a35d-bcc3ed7e533c`) plus Docker official documentation. Runtime/version behavior is `needs-verification`.
