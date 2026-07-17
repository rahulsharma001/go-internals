---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: Security Protocols Deep Dive (2026-06-26, 6a3e58e8-4470-83e8-aadc-8775e79a5656)"
  - "OpenID Connect Core 1.0"
  - "RFC 9700 OAuth 2.0 Security Best Current Practice"
---

# OAuth JWT OIDC and mTLS

## Problem it solves

Modern systems need safe delegated API access, federated user login, portable token formats, and authenticated service-to-service transport. These technologies solve different layers.

## Mental model

- **OAuth:** authorization delegation framework.
- **OIDC:** identity layer on OAuth; the ID token describes an authentication event for the client.
- **JWT:** signed/encrypted token container format—not a login or authorization system.
- **mTLS:** both endpoints authenticate at the transport layer; workload identity still needs authorization.

## How it works

For browser/mobile user login, Authorization Code + PKCE sends the user to the authorization server; the client exchanges a one-time code/verifier and receives an ID token for the client plus access token for the API. The API validates access-token issuer, audience, signature or introspection, lifetime, and scope. Refresh tokens rotate and are protected. Workloads use managed workload identity/mTLS or client credentials, not shared user tokens.

## Concrete example and detailed dry run

Client creates `code_verifier` and challenge, redirects to the IdP, checks returned `state` and OIDC `nonce`, then exchanges the code with verifier. API receives the access token, fetches cached issuer keys, validates algorithm/signature/issuer/audience/expiry, then maps scopes to a preliminary permission. Order ownership is still checked by [[Authentication and Authorization]].

## Success scenario

Tokens are short-lived and audience-bound, authorization code is unusable without PKCE verifier, redirect URI is exact, refresh reuse is detected, and APIs do not accept ID tokens as access tokens.

## Failure scenario

A service accepts any correctly signed JWT without checking audience/issuer, so a token minted for another API is replayed. Correct validation rejects it. A leaked bearer token remains usable until expiry unless sender-constrained; use short lifetime and, where warranted, mTLS/DPoP-style binding.

## Scaling considerations

Cache discovery/signing keys with rotation handling; avoid per-request identity-provider calls for JWT access tokens; design introspection availability for opaque tokens; distribute trust bundles safely; automate certificate issuance/rotation.

## Production technology choices

Standards-compliant OIDC provider; OAuth Authorization Code + PKCE; opaque or JWT access tokens according to revocation/privacy needs; SPIFFE/SPIRE or mesh certificates for workload mTLS. Verify supported algorithms and profiles.

## Trade-offs

JWTs are locally verifiable but hard to revoke and expose claims; opaque tokens centralize control but require introspection/cache. mTLS authenticates workloads strongly but adds certificate lifecycle and proxy complexity.

## When not to use it

Do not build a custom OAuth/OIDC server casually, put secrets/PII in readable JWT claims, use implicit/password grants for new designs, or treat mTLS as resource authorization.

## Common interview mistakes

Using ID token at API; saying JWT is encrypted by default; no issuer/audience/algorithm checks; long-lived bearer access tokens; missing PKCE/state/nonce; shared certificates with no rotation.

## Interview questions and follow-ups

Access token versus ID token? JWT versus opaque? How does revocation work? What does PKCE stop? What identity does mTLS authenticate?

## Five-minute recall

OAuth delegates; OIDC authenticates client session; JWT is format; mTLS authenticates transport peers. Code+PKCE, exact redirects, state/nonce, short audience-bound access token, rotate refresh/certs, resource authorization remains separate.

## Related notes

[[Authentication and Authorization]] · [[API Security]] · [[Stateless and Stateful Services]]

## Source metadata

Based on the extracted security conversation, OIDC Core, and OAuth Security BCP RFC 9700. Deployment recommendations remain subject to current provider/spec verification.

