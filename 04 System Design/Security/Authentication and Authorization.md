---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: Security Protocols Deep Dive (2026-06-26, 6a3e58e8-4470-83e8-aadc-8775e79a5656)"
---

# Authentication and Authorization

## Problem it solves

Authentication establishes the identity/session behind a request; authorization decides whether that principal may perform this action on this resource under current policy.

## Mental model

AuthN answers “who/what are you?” AuthZ answers “may this principal do this here and now?” Every hop still validates the authority it relies on.

## How it works

An identity provider verifies credentials/MFA and issues a bounded session/token. Gateway/service validates issuer, audience, signature/session, expiry, and revocation policy. The resource service enforces RBAC/ABAC/relationship/ownership rules using authoritative resource context. Default deny and least privilege apply to users, services, and operators.

## Concrete example and detailed dry run

User `c-7` requests `GET /orders/o-42`. Gateway validates the access token and passes trusted identity context. Order service loads `owner_id` and checks `subject == owner` or a narrowly scoped support role. A valid token belonging to another customer receives 403; authentication alone never grants the read.

## Success scenario

Identity is verified with correct token/session context and the resource-level policy permits only the requested action; decision and sensitive access are audited.

## Failure scenario

The gateway checks the token but an internal service trusts a caller-supplied `user_id`. An attacker changes the ID and reads another object. Correct design derives subject from verified context and enforces object authorization at the owning service.

## Scaling considerations

Cache public signing keys and coarse policy carefully; avoid a synchronous central authorization call for every low-risk read unless required; propagate policy/version; invalidate/revoke high-risk sessions; batch relationship lookups while respecting freshness.

## Production technology choices

OIDC identity provider, short-lived access tokens or server-side sessions, OAuth scopes for delegated API access, OPA/Cedar/relationship-based engines where policy complexity justifies them, mTLS/workload identity for services.

## Trade-offs

Self-contained tokens reduce lookup latency but make immediate revocation and claim freshness harder. Central policy gives consistency/auditability but adds latency/availability dependency. Fine-grained rules improve control but increase evaluation and administration complexity.

## When not to use it

Do not encode rapidly changing resource authorization solely in long-lived token claims. Do not use client secrets or user passwords as service identity.

## Common interview mistakes

Treating JWT as authorization; checking only at gateway; no object-level rule; confusing 401/403; logging tokens; overbroad admin/service roles.

## Interview questions and follow-ups

Where is ownership enforced? How are roles revoked? What identity does a background worker use? How do services authenticate each other?

## Five-minute recall

Verify identity/session; validate token context; enforce action + resource policy at owner; default deny; least privilege; short lifetime/revocation; audit sensitive decisions.

## Related notes

[[OAuth JWT OIDC and mTLS]] · [[API Security]] · [[Order Processing System]]

## Source metadata

Primary extracted source: *Security Protocols Deep Dive*, 2026-06-26, conversation ID above. Protocol/version details require current specification verification.

