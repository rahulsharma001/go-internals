---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: Security Protocols Deep Dive (2026-06-26, 6a3e58e8-4470-83e8-aadc-8775e79a5656)"
  - "OWASP API Security Top 10"
---

# API Security

## Problem it solves

Public and internal APIs expose identities, objects, workflows, and expensive operations to untrusted or compromised callers. Security must preserve confidentiality, integrity, availability, and auditability.

## Mental model

For every endpoint ask: who calls, which object/action, which input/output, what resource cost, what downstream trust, and what evidence remains.

## How it works

Maintain API inventory and schemas. Authenticate, then enforce object/function/property authorization. Validate types, sizes, ranges, content types, URLs, and state transitions; parameterize data access; limit request body, concurrency, and rate; protect outbound fetches from SSRF; minimize responses; encrypt; manage secrets outside code/payloads; audit privileged and sensitive actions.

## Concrete example and detailed dry run

`POST /orders/o-42/cancel` validates token context, loads order ownership, checks the transition is cancellable, requires a stable idempotency key, constrains payload, applies per-user and system rate/concurrency limits, records actor/reason/result, and emits a safe event without token/PII. A second request returns the stored outcome.

## Success scenario

Authorized input triggers one valid state transition; sensitive fields remain minimized; quotas protect capacity; audit data supports investigation without containing secrets.

## Failure scenario

An image-import endpoint fetches a caller URL and can reach cloud metadata/private services. Correct design denies private/link-local ranges after DNS resolution, restricts schemes/ports/redirects, uses an egress proxy and isolated credentials, caps response size/time, and revalidates redirects to resist DNS rebinding.

## Scaling considerations

Enforce cheap limits early at edge/gateway and invariant/object authorization in the owner service. Use layered per-IP/user/tenant/resource budgets, distributed rate limiting with clear failure policy, schema validation, and asynchronous security scanning for expensive content.

## Production technology choices

API gateway/WAF for TLS, coarse authentication, size/rate controls; service authorization libraries/policy engine; secret manager/KMS; mTLS/workload identity; SAST/DAST/dependency scanning; centralized tamper-resistant audit pipeline.

## Trade-offs

Strict validation and quotas reduce abuse but can reject legitimate extremes; gateway policy centralizes control but lacks resource context; detailed audit improves forensics but increases privacy/storage obligations.

## When not to use it

Do not rely only on a WAF/gateway, hide authorization in UI, accept arbitrary outbound URLs, expose internal fields by default, or log credentials/tokens/request bodies indiscriminately.

## Common interview mistakes

Only “HTTPS + JWT”; no object-level authorization; no abuse/cost controls; missing SSRF and webhook validation; secrets in logs; no key/certificate rotation; security bolted on at the end.

## Interview questions and follow-ups

How is BOLA prevented? Where are limits enforced? How are webhooks verified/replay-protected? How is SSRF contained? What is audited/redacted?

## Five-minute recall

Inventory/schema; AuthN; object/function AuthZ; validate/limit; safe state/idempotency; SSRF/egress controls; encrypt/minimize; secret management; audit/monitor; least privilege.

## Related notes

[[Authentication and Authorization]] · [[OAuth JWT OIDC and mTLS]] · [[Rate Limiting Pattern]] · [[Idempotency Pattern]]

## Source metadata

Based on the extracted security conversation and OWASP API Security project. Current threat guidance and gateway/provider behavior should be verified.
