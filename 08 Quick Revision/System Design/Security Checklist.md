---
type: quick-revision
domain: system-design
review_time: 4-minutes
---
# Security Checklist

- trust boundaries: client, edge, service, worker, third party
- authentication: who/what is the caller?
- authorization: which state owner decides access to this resource?
- transport and at-rest encryption; key/secret rotation
- PII/payment/content classification, minimization, retention, deletion, audit
- tenant-qualified keys, quotas, and isolation
- request/body/object size, decompression, parser, and egress limits
- rate limiting, spam/fraud/enumeration/hotlink defenses
- signed URLs with short expiry and narrow method/object scope
- abuse-review and business-level security signals

Security must modify the flow: show where identity is established, policy is checked, and untrusted bytes go. See [[Security Abuse and Privacy]].
