---
status: learning
type: canonical
area: system-design
sources:
  - "ChatGPT: Logging Monitoring Alerting BFF (2025-01-24, 6793a2b8-aacc-8013-a770-860633f9d45e)"
  - "Google SRE Workbook: Monitoring"
---

# Alerting Strategy

## Problem it solves

Operators need timely, actionable notification of customer impact without fatigue from transient or redundant signals.

## Mental model

Page for urgent user-impacting action; ticket for slower risk; dashboard/log for investigation. An alert is a routed decision, not merely a threshold.

## How it works

Start with [[SLI SLO and Error Budgets|SLO]] burn, availability, latency, correctness, and critical backlog age. Add dependency/capacity alerts only when they predict impact and have an action. Every alert includes owner, severity, scope, current value, links, likely causes, runbook, and resolution signal. Group, deduplicate, inhibit downstream symptoms, and test routes.

## Concrete example and detailed dry run

Checkout error-budget burn rises across fast and long windows in one region. Alert manager groups instances by service/region, inhibits derivative payment queue alerts, and pages checkout on-call with trace/dashboard/runbook. After traffic moves and burn falls for the recovery window, it resolves; a ticket tracks remaining capacity risk.

## Success scenario

The right responder receives one actionable notification early enough to protect the objective and can verify recovery.

## Failure scenario

A fixed CPU threshold pages repeatedly although customers are healthy. Responders ignore alerts; a real incident is missed. Remove/demote the unactionable alert and connect saturation to user or imminent-capacity impact.

## Scaling considerations

Aggregate high-cardinality instances, route by service/tenant/region, protect the notification channel from storms, maintain redundant evaluators with dedupe, and monitor rule-evaluation and delivery health.

## Production technology choices

Prometheus-compatible rules, Alertmanager grouping/inhibition/silences, PagerDuty/Opsgenie-like paging, chat/email for non-urgent notifications, runbooks in version control.

## Trade-offs

Sensitive alerts detect sooner but page on noise; longer windows reduce noise but delay action. Symptom alerts are actionable but may lag leading capacity signals.

## When not to use it

Do not page on informational logs, single-instance failure behind healthy redundancy, or conditions with no urgent human action.

## Common interview mistakes

“Alert on CPU”; no severity/owner/runbook; every replica pages; no missing-data rule; no dead-man/external check; no post-incident tuning.

## Interview questions and follow-ups

Why page instead of ticket? What action follows? How are alert storms controlled? How is the monitoring system itself monitored?

## Five-minute recall

Page on urgent symptoms/burn; ticket on slow risk; group/dedupe/inhibit; include context + owner + action + recovery; test routes and dead-man signal.

## Related notes

[[SLI SLO and Error Budgets]] · [[Logs Metrics and Traces]] · [[Monitoring System]] · [[Failure Handling Strategy]]

## Source metadata

Based on the extracted logging/monitoring conversation and Google SRE monitoring guidance. Thresholds and ownership are `status: needs-verification`.
