> [!archive] Superseded on 2026-07-17 during the System Design rebuild. Replacement: [[Observability and SLOs]].

---
status: learning
type: canonical
area: system-design
sources:
  - "Google SRE Workbook: Implementing SLOs"
  - "Google SRE Workbook: Error Budget Policy"
---

# SLI SLO and Error Budgets

## Problem it solves

Teams need a user-centered reliability target and a rational way to balance reliability work against release velocity.

## Mental model

SLI is the measured user outcome; SLO is the target over a window; error budget is the allowed bad fraction. Policy says what changes when consumption is too fast.

## How it works

Define eligible events and good-event criteria close to the user. Example: `good checkout requests / eligible checkout requests`, where good means correct non-5xx completion under the latency threshold; exclude only explicitly invalid traffic. Select a rolling window and target from user/business needs. Track budget remaining and multi-window burn rate.

## Concrete example and detailed dry run

Suppose an explicitly agreed SLO is `99.9%` over 30 days (illustrative, not a recommendation). The budget is `0.1%` bad eligible events. A short incident burns at a high multiple of the sustainable rate, so a fast-window alert pages. A slow persistent regression burns a longer window and opens a ticket/page per policy. Release controls change only according to the agreed error-budget policy.

## Success scenario

The SLI reflects customer experience, alerts before the full budget is consumed, and the team can explain reliability using events—not host health averages.

## Failure scenario

The metric counts only successful requests in the denominator or excludes overload errors, making the service look healthy while users fail. Correct the eligibility definition, backtest with incidents, and treat missing telemetry explicitly.

## Scaling considerations

Compute aggregates efficiently with recording rules; preserve dimensions needed for diagnosis without fragmenting the SLO into tiny populations; define low-traffic alert handling; evaluate regional/tenant views alongside the global objective.

## Production technology choices

Prometheus-compatible counters/histograms and recording rules; SLO tooling such as Sloth/Pyrra/vendor platforms; dashboard plus alert routing. Tools do not decide the user promise.

## Trade-offs

A stricter SLO drives cost and slower change; a loose SLO permits poor experience. Event-based SLIs are precise but need good instrumentation; synthetic/probe SLIs see externally but cover limited journeys.

## When not to use it

Do not create an SLO for every internal metric. Internal components may have supporting objectives, but start with critical user journeys.

## Common interview mistakes

Confusing SLA and SLO; arbitrary `99.99`; average latency; alerting whenever one request fails; no denominator/exclusions/window/policy.

## Interview questions and follow-ups

What is an eligible event? Why this target/window? How is low traffic handled? What does the team do when budget is exhausted?

## Five-minute recall

User journey → eligible events → good criterion → window/target → budget → burn alerts → explicit policy. Backtest and revise.

## Related notes

[[Alerting Strategy]] · [[Logs Metrics and Traces]] · [[Graceful Degradation]] · [[System Design Interview Framework]]

## Source metadata

Based on Google SRE Workbook guidance. The numeric example is labelled illustrative; actual objectives require business agreement (`status: needs-verification`).

