---
type: runbook
domain: infrastructure
topic: production-failures
status: learning
source_conversations:
  - "Kubernetes for Backend Interviews | 2026-07-07 | 6a4cf217-e6dc-83e8-b416-156a8354a76b"
  - "AWS EKS App Deployment | 2026-06-25 | 6a3ce123-1794-83e8-83ea-0c20e4b4424c"
  - "Kafka Deep Dive Guide | 2026-06-28 | 6a4107d3-19ac-83ee-a716-51fdbc569f3e"
  - "PostgreSQL for Production Systems | 2026-06-28 | 6a41070b-052c-83ee-bf6b-ceb1d4910e0e"
  - "AWS WebSocket Architecture Overview | 2025-06-09 | 6846e928-6bfc-8013-8fb6-6961d4da1540"
---

# Kubernetes Production Failures

## How a senior engineer uses this runbook

Stabilize users first, preserve evidence, and change one variable at a time. Establish the blast radius, start from the failed user journey, compare healthy and unhealthy dimensions, and follow the request/event path. Commands are examples: use the correct namespace/context and least-privilege access; never paste secrets or customer payloads into tickets.

## 1. Pod is Running but receives no traffic

### Symptoms

Pod phase is Running; direct process may be alive, but Service/Ingress requests time out or hit other replicas.

### Likely causes

readiness false; selector/label mismatch; wrong `port`/`targetPort`; process bound to localhost; empty/stale EndpointSlice; NetworkPolicy; ALB target unhealthy; CNI or node path fault.

### Investigation order

Check readiness and container listening socket → Service selector/ports → EndpointSlice ready address → direct Pod-IP call → ClusterIP call from a debug Pod → Ingress/target health → policy/CNI.

### Useful commands

`kubectl get pod -o wide`; `kubectl describe pod <pod>`; `kubectl get svc <svc> -o yaml`; `kubectl get endpointslice -l kubernetes.io/service-name=<svc> -o yaml`; `kubectl exec <pod> -- ss -lnt`; `curl -v http://<pod-ip>:<port>/ready`.

### Metrics and logs

readiness result, EndpointSlice ready count, ALB healthy targets, ingress upstream errors, NetworkPolicy/CNI drops, application accept/request count.

### Immediate mitigation

Correct label/port or readiness configuration; route traffic to known healthy replicas; roll back the last routing/config change.

### Permanent fix

Use consistent app labels, named ports, contract tests for manifests, and a readiness endpoint that proves the serving path.

### Prevention

Admission/schema checks, pre-production smoke test through Service and Ingress, alert on zero ready endpoints.

### Senior-level trade-offs

Bypassing readiness restores traffic quickly but may send users to a broken dependency; prefer rollback or a deliberately degraded mode.

## 2. Readiness probe failing

### Symptoms

Pod stays Running but `Ready=False`; Deployment stalls and Service endpoints shrink; events show probe failures.

### Likely causes

wrong path/port/scheme; slow startup; handler depends on optional/shared dependency; CPU starvation; deadlock; timeout too strict; auth or mesh interception.

### Investigation order

Read event message → execute the exact probe inside Pod → inspect startup timing and logs → compare CPU throttling/pool saturation → decide whether application or probe contract is wrong.

### Useful commands

`kubectl describe pod <pod>`; `kubectl exec <pod> -- wget -S -O- http://127.0.0.1:<port>/ready`; `kubectl top pod <pod>`; inspect Deployment probe fields.

### Metrics and logs

probe latency/failures, ready replicas, CPU throttled seconds, goroutines, DB pool wait, dependency latency.

### Immediate mitigation

Roll back a bad probe; increase startup protection only with evidence; temporarily shed load or restore dependency.

### Permanent fix

Separate startup/readiness/liveness; make readiness cheap and bounded; expose reason-coded internal metrics without leaking details publicly.

### Prevention

Test probe from the same network namespace in CI/minikube and alert before ready replicas reach zero.

### Senior-level trade-offs

A broad readiness check protects correctness but can cause total outage during a dependency failure; model degraded service explicitly.

## 3. CrashLoopBackOff

### Symptoms

Restart count rises and Pod cycles through waiting/backoff; current logs may be empty because the useful log is from the previous container.

### Likely causes

startup panic; missing configuration; command/permission error; failed migration; dependency exit policy; OOM; liveness killing slow startup.

### Investigation order

Get termination reason/exit code → previous logs → events → config/image/command diff → resource and node evidence → reproduce with the same image/config.

### Useful commands

`kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[*].lastState}'`; `kubectl logs <pod> --previous`; `kubectl describe pod <pod>`; `kubectl get rs`.

### Metrics and logs

restart rate, termination reasons, rollout version, OOM events, startup duration, dependency failure class.

### Immediate mitigation

Roll back; restore required config; stop a dangerous rollout. Do not repeatedly delete the Pod—it destroys evidence and the controller recreates it.

### Permanent fix

Fail startup with actionable errors, validate config before deploy, add startup probe, make migrations separate/idempotent.

### Prevention

Canary, immutable image digest, manifest validation, startup integration test, alert on restart rate by version.

### Senior-level trade-offs

Keeping a failed Pod for debugging reduces capacity; capture evidence first, then scale/rollback safely.

## 4. OOMKilled

### Symptoms

Container terminates with reason OOMKilled/exit 137; latency and GC CPU may rise first; node may also show memory pressure.

### Likely causes

memory limit below workload; unbounded cache/queue/goroutines; large request buffers; retained objects; burst plus insufficient headroom; sidecar or node pressure.

### Investigation order

Distinguish container-limit OOM from node eviction → correlate RSS/working set, Go heap/live objects, allocation rate, goroutines and traffic → capture profiles before restart if safe → inspect recent limit/config changes.

### Useful commands

`kubectl describe pod <pod>`; `kubectl top pod --containers`; inspect `/sys/fs/cgroup` from an approved debug path; collect `pprof/heap` securely.

### Metrics and logs

working set/RSS, cgroup OOM events, Go heap goal/live, alloc rate, GC CPU, goroutine count, request size, queue depth.

### Immediate mitigation

Rollback leak; cap request/queue/cache; shed load; raise limit only when node capacity and evidence support it.

### Permanent fix

Remove unintended retention, stream large payloads, bound concurrency, load-test with realistic cgroup limits, set Go memory guidance with headroom.

### Prevention

Alert on memory slope and headroom, profile periodically, enforce body/queue limits, test failure near limit.

### Senior-level trade-offs

Higher limits reduce kills but lower bin packing and can move failure to node level; aggressive GC saves memory at CPU/latency cost.

## 5. CPU throttling

### Symptoms

High p95/p99 latency despite moderate CPU usage; cgroup throttled periods rise; Go work progresses in bursts.

### Likely causes

CPU limit too low; bursty handler/JSON/crypto/GC; noisy node; excessive runnable goroutines; mismatch between runtime parallelism and quota.

### Investigation order

Correlate latency with throttled seconds/periods → compare request vs limit and node saturation → inspect CPU profile/GC → test one replica with corrected resources.

### Useful commands

`kubectl top pod`; `kubectl describe pod`; inspect cgroup `cpu.stat`; capture `pprof/profile`; check node CPU and scheduler events.

### Metrics and logs

CPU usage, throttled seconds/period ratio, run queue, Go scheduler latency, GC CPU, request latency and saturation.

### Immediate mitigation

Scale out, remove or raise an unjustified CPU limit with capacity controls, reduce expensive work, or route traffic away.

### Permanent fix

Right-size requests from measurements; decide limit policy deliberately; bound concurrency; optimize profiled hot paths; verify container-aware runtime settings for the deployed Go version.

### Prevention

Load-test under quotas, alert on throttling plus user latency, review HPA signal and scale-up delay.

### Senior-level trade-offs

Limits contain noisy neighbors but can create tail latency; no limit improves bursting but needs strong requests, quotas and node capacity.

## 6. DNS resolution failure

### Symptoms

`no such host`, resolver timeout, intermittent 5xx, or only some nodes/Pods fail; direct IP succeeds.

### Likely causes

wrong Service/namespace name; CoreDNS unavailable/overloaded; blocked UDP/TCP 53; bad search path/`ndots`; node resolver issue; stale negative cache; CNI path fault.

### Investigation order

Resolve FQDN and short name from affected Pod → inspect `/etc/resolv.conf` → check Service and CoreDNS endpoints → compare nodes → test UDP and TCP DNS → inspect policies and CoreDNS logs/latency.

### Useful commands

`kubectl exec <pod> -- cat /etc/resolv.conf`; `nslookup svc.ns.svc.cluster.local`; `kubectl -n kube-system get pod,svc,endpointslice -l k8s-app=kube-dns`; `kubectl logs -n kube-system deploy/coredns`.

### Metrics and logs

DNS request latency/error/response codes, CoreDNS CPU, cache hit/miss, dropped packets, affected node count.

### Immediate mitigation

Use the correct FQDN; restore/scale CoreDNS; move affected Pods; fix policy. Do not hard-code transient Pod IPs.

### Permanent fix

Capacity and topology for DNS, NodeLocal cache when justified, sane search use, explicit egress policy, application resolver timeouts.

### Prevention

Synthetic Service lookup from each zone/node pool and alert on DNS latency before application error rate.

### Senior-level trade-offs

Long caching reduces DNS load but delays endpoint/failover changes; aggressive retries can overload DNS.

## 7. Service has no endpoints

### Symptoms

Service exists but EndpointSlice has no addresses; clients see connection refused/timeout or ingress `no upstream`.

### Likely causes

selector mismatch; Pods not ready; wrong namespace; headless/manual Service misconfigured; terminating Pods only; controller lag.

### Investigation order

Compare Service selector with Pod labels → inspect readiness → list EndpointSlices → confirm namespace and owner references → inspect events/controller health.

### Useful commands

`kubectl get svc <svc> -o yaml`; `kubectl get pod -l '<selector>' --show-labels`; `kubectl get endpointslice -l kubernetes.io/service-name=<svc> -o wide`; `kubectl describe deploy <name>`.

### Metrics and logs

ready replicas, ready endpoint count, selector match count, rollout availability, controller errors.

### Immediate mitigation

Fix selector/readiness or roll back; scale a known-good ReplicaSet.

### Permanent fix

Use one label contract across Deployment and Service, named ports, deployment smoke tests, zero-endpoint alert.

### Prevention

Policy tests assert every selected Service has intended ready backends in staging and during rollout.

### Senior-level trade-offs

Relaxing readiness can repopulate endpoints but may violate correctness; treat endpoint absence as a symptom, not the root cause.

## 8. Ingress returns 502 or 504

### Symptoms

502 indicates failed/invalid upstream response; 504 usually indicates upstream timeout. ALB/ingress works for some paths or versions.

### Likely causes

no healthy targets; port/protocol mismatch; Pod closes/reset; readiness/target health race; upstream slower than timeout; security group/policy; idle timeout mismatch.

### Investigation order

Check load-balancer/ingress access log and target health → EndpointSlice → direct Pod then Service request → controller config/logs → timeout chain and application/downstream trace.

### Useful commands

`kubectl describe ingress`; `kubectl logs -n <controller-ns> deploy/<controller>`; `kubectl get endpointslice`; `curl -v` from inside cluster; inspect AWS target health.

### Metrics and logs

ALB 5xx vs target 5xx, target response time, upstream connect time, reset count, ready endpoints, app latency, DB/pool waits.

### Immediate mitigation

Rollback routing/version; restore healthy targets; increase timeout only for a known legitimate operation while protecting capacity.

### Permanent fix

Align protocols/ports/health checks; enforce end-to-end deadlines; make slow work asynchronous; drain correctly.

### Prevention

Canary through public path, target-health alarms, timeout budget documentation, error classification dashboards.

### Senior-level trade-offs

Longer timeouts reduce 504s but hold connections and hide overload; retries at ingress may duplicate or amplify work.

## 9. Node becomes NotReady

### Symptoms

Node condition NotReady/Unknown; many Pods become unreachable; connections drop and replacements may remain Pending.

### Likely causes

kubelet stopped; network partition; disk/memory/PID pressure; container runtime failure; expired credentials/cert; instance/AZ failure; CNI failure.

### Investigation order

Assess blast radius and endpoint removal → Node conditions/events/leases → instance and network health → kubelet/runtime/system logs → capacity for rescheduling → volume/topology constraints.

### Useful commands

`kubectl describe node <node>`; `kubectl get lease -n kube-node-lease`; `kubectl get pod -A --field-selector spec.nodeName=<node>`; approved `journalctl -u kubelet`; cloud instance status.

### Metrics and logs

node heartbeat age, ready endpoints, unschedulable Pods, pressure conditions, disk/inodes, CNI/runtime errors, zone capacity.

### Immediate mitigation

Cordon; drain only if node responds and disruption policy/capacity permit; replace instance; add capacity in healthy zones.

### Permanent fix

Repair bootstrap/runtime/network; use managed immutable node groups, multi-AZ topology spread, capacity headroom and tested replacement.

### Prevention

Node health monitoring, AMI rollout canary, disk/PID alerts, autoscaler capacity and disruption drills.

### Senior-level trade-offs

Fast eviction improves recovery but risks duplicate stateful work and overload; conservative timers preserve transient nodes but extend impact.

## 10. Rolling deployment causes errors

### Symptoms

5xx/502 spike aligns with rollout; old and new Pods differ; errors may continue only on long-lived connections.

### Likely causes

readiness lies; SIGTERM/grace/drain race; incompatible API/schema; bad config; insufficient surge capacity; HPA interaction; DB connection surge; cached/sticky traffic.

### Investigation order

Pause rollout → compare errors by version/Pod → inspect rollout events, ready endpoints and target health → trace termination/startup timeline → check schema/config/pool capacity.

### Useful commands

`kubectl rollout status deploy/<name>`; `kubectl rollout pause deploy/<name>`; `kubectl rollout history`; `kubectl get rs,pod -l app=<name> -w`; `kubectl rollout undo` when safe.

### Metrics and logs

error/latency by version, ready/available replicas, termination duration, target deregistration, connection count, DB pool usage.

### Immediate mitigation

Pause/rollback; reduce traffic/canary weight; restore compatible config/schema; scale dependency capacity if safe.

### Permanent fix

Backward/forward-compatible changes, expand-migrate-contract schema rollout, truthful readiness, graceful drain, canary and automated analysis.

### Prevention

Public-path smoke test, PDB plus adequate surge/headroom, rollout SLO guard, connection-drain test.

### Senior-level trade-offs

Fast rollback minimizes impact but may be unsafe after irreversible data changes; design deployments so rollback remains possible.

## 11. Kafka consumer lag increases

### Symptoms

Offset/record lag and oldest-event age rise; business processing is delayed although producers succeed.

### Likely causes

producer rate exceeds service rate; slow dependency; partition skew/hot key; too few partitions/consumers; rebalance loop; poison record; GC/CPU throttling; broker issue.

### Investigation order

Confirm business age and per-partition lag → compare ingress vs processing throughput → find skew/stuck offset → inspect rebalances/errors → trace dependency and resource saturation → broker health.

### Useful commands

Use approved consumer-group describe tooling; `kubectl logs` consumer; inspect Pod throttling/restarts; sample one record metadata without exposing payload.

### Metrics and logs

lag/oldest age per partition, consume rate, processing latency, retries/DLQ, rebalance count, commit failures, CPU/GC, dependency latency.

### Immediate mitigation

Fix/route around dependency; scale consumers up to useful partition count; quarantine poison event; pause noncritical producers or shed optional work.

### Permanent fix

Choose partition key/partitions from concurrency needs, idempotent handler, bounded retry/DLQ, backpressure, batch/commit tuning from load tests.

### Prevention

Alert on lag age and recovery time, not lag count alone; capacity test; replay and poison-message drills.

### Senior-level trade-offs

More partitions increase parallelism but cost broker/controller/consumer overhead and weaken ordering scope; skipping a record protects flow but needs an explicit correctness policy.

## 12. Database connection pool exhaustion

### Symptoms

Requests wait for or time out acquiring a connection; DB CPU may be normal; scaling Pods makes the incident worse.

### Likely causes

pool maximum × replicas exceeds DB capacity; leaked rows/transactions; slow queries/locks; long transactions; retry storm; missing acquisition deadline; traffic burst.

### Investigation order

Measure pool wait and in-use/open counts → DB sessions by service → slow/blocked queries → transaction/rows closure → replica/HPA change → retry amplification.

### Useful commands

Expose Go `database/sql` Stats; inspect DB activity/locks with approved read-only queries; `kubectl get hpa,deploy`; correlate traces.

### Metrics and logs

open/in-use/idle, wait count/duration, query latency, lock waits, DB connections/CPU/IO, timeouts, retries.

### Immediate mitigation

Stop retry storm; shed/load-limit; terminate clearly orphaned sessions through approved procedure; reduce replicas/pool or add DB capacity only with analysis.

### Permanent fix

Global connection budget, bounded acquisition via context, close rows/transactions, query/index fixes, proxy/pooler where justified.

### Prevention

Load-test replica scaling, alert on wait duration and DB headroom, code review for lifecycle, per-query deadlines.

### Senior-level trade-offs

Large pools hide bursts but can collapse DB; small pools protect DB but require backpressure and may increase application wait.

## 13. Redis latency spike

### Symptoms

Cache/lock/session calls slow; application tail latency rises; hit rate may fall or timeouts/reconnects grow.

### Likely causes

hot key or large value; blocking command; eviction/fragmentation; failover; network/DNS; connection pool contention; command storm/cache miss stampede; persistence work.

### Investigation order

Separate network, pool wait and server command latency → inspect slow commands/hot keys/value sizes safely → CPU/memory/evictions → failover/events → callers and key cardinality.

### Useful commands

Use managed metrics; approved `SLOWLOG`/command statistics; inspect Go pool stats and traces; avoid broad key scans in production.

### Metrics and logs

p95/p99 command latency, connections/pool wait, CPU, memory/fragmentation, evictions, hit ratio, operations/sec, failover/reconnects.

### Immediate mitigation

Bypass noncritical cache, rate-limit hot caller, coalesce requests, remove blocking workload, scale/fail over per service procedure.

### Permanent fix

Bound values/TTLs, shard or replicate reads, single-flight/stampede control, separate workloads, connection timeouts and pool sizing.

### Prevention

Latency by command, hot-key/load tests, failover drills, max-value policy, cache-degradation behavior.

### Senior-level trade-offs

Fail-open preserves availability but increases DB load/staleness; fail-closed may be required for locks/security. Decide per use case.

## 14. WebSocket disconnections

### Symptoms

Reconnect rate spikes, clients miss/replay messages, one AZ/version loses sockets, or connections close at a regular idle interval.

### Likely causes

load-balancer/API Gateway idle or lifetime behavior; missing heartbeat; deploy without drain; NAT/mobile network; auth expiry; slow-client buffer; gateway OOM; Redis connection-map loss.

### Investigation order

Classify close code and client/network/version → compare LB/gateway logs → check heartbeat/idle timings → deploy/node events → gateway resources/buffers → registry and catch-up path.

### Useful commands

Inspect ALB/API Gateway and application connection logs; `kubectl get events`; Pod restarts/OOM; Redis mapping TTL; packet capture only in controlled reproduction.

### Metrics and logs

active/reconnect/disconnect by reason, connection age, heartbeat timeout, send-buffer depth, gateway CPU/memory/FDs, send-to-connection errors, catch-up gaps.

### Immediate mitigation

Stop bad rollout; extend/restore heartbeat within documented limits; move new connections; preserve durable messages and force cursor-based reconnect.

### Permanent fix

Jittered reconnect, durable sequence/cursor catch-up, TTL connection registry, graceful drain, bounded buffers, auth refresh and tested idle policy.

### Prevention

Soak test across deploys/AZ loss, synthetic long-lived clients, alert on reason-coded reconnects and message-gap recovery.

### Senior-level trade-offs

Frequent heartbeat detects failure sooner but costs battery/bandwidth; sticky routing helps local state but complicates rebalance and failure.

## 15. Sudden increase in HTTP latency

### Symptoms

p95/p99 rises suddenly, possibly without higher average or error rate; one route/zone/version/tenant may dominate.

### Likely causes

load change; CPU throttling/GC; downstream latency; pool exhaustion; DNS/connect/TLS; retries; locks/goroutine leak; large payload; node/network issue; telemetry exporter pressure.

### Investigation order

Define onset and affected dimensions → split queue/connect/TLS/server/downstream time via traces → saturation (CPU, memory, FDs, goroutines, pools) → deploy/config events → dependency and network evidence → controlled profile.

### Useful commands

Query SLO dashboard/traces; `kubectl top`; events/rollout history; Go pprof with bounded duration; `ss -s`; pool/runtime metrics.

### Metrics and logs

rate/errors/duration, histogram not average, in-flight/queue, throttling, GC, goroutines, FDs, pool waits, DNS/connect/TLS, downstream spans, retries.

### Immediate mitigation

Rollback, shed/rate-limit, scale the actual bottleneck, disable expensive optional work, apply circuit/bulkhead; do not blindly retry.

### Permanent fix

Remove profiled bottleneck, capacity model, deadline/retry budget, bounded concurrency/pools, cache/query/network correction.

### Prevention

Golden-signal and dependency dashboards, exemplars/traces, load/chaos tests, deploy annotations, saturation alerts tied to impact.

### Senior-level trade-offs

Scaling buys time but can overload DB/cache; aggressive timeouts reduce occupancy but cause false failure. State the protected resource and correctness cost.

## Related notes

[[Client to Pod Request Flow]] · [[Kubernetes Observability]] · [[Incident Investigation]] · [[CPU Memory and IO Troubleshooting]] · [[Network Troubleshooting]] · [[MSK and Kafka on AWS]] · [[RDS Aurora and DynamoDB]] · [[ElastiCache Redis]] · [[WebSocket Polling Webhook and SSE]]

## Source metadata

Curated from the extracted conversations listed in frontmatter and the existing system-design reliability canonicals. Commands and failure behavior require validation against the deployed versions, policies, managed-service configuration, and incident runbooks (`status: needs-verification`).
