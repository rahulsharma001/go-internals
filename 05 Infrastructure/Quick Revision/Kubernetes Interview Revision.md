---
type: quick-revision
domain: infrastructure
status: active
---

# Kubernetes Interview Revision

## 60-second model

Kubernetes reconciles desired objects. API server is the API boundary, etcd stores state, controllers reconcile, scheduler binds Pods, kubelet/runtime/CNI start them. User traffic uses the data plane, not the scheduler/API server.

## Request flow

Client → DNS/Route 53 → ALB/NLB → Ingress/controller-managed config → Service → ready EndpointSlice → kube-proxy/eBPF → CNI/Pod IP → container port → Go handler → downstream → response. Internal call starts with CoreDNS and normally stays on ClusterIP.

## Health and rollout

- Startup protects slow initialization; readiness controls new traffic; liveness restarts.

- Deployment creates new ReplicaSet; new Pod becomes ready; old Pod is removed/drained, receives SIGTERM, and Go performs bounded graceful shutdown.

- Pod crash: kubelet restart/backoff. Node death: connections fail, endpoints withdraw, controller reschedules if capacity exists.

## Troubleshooting order

Reproduce → LB target/access log → Ingress → Service ports/selectors → EndpointSlice ready addresses → DNS/ClusterIP → direct Pod → probe/log/events → node/CNI/policy. Commands: `kubectl get deploy,rs,pod,svc,ingress,endpointslice`; `describe`; `logs --previous`; events; `rollout status`; in-Pod `nslookup`/`curl`.

## Resource/security traps

Requests schedule; CPU limits throttle; memory limits OOM. HPA needs meaningful signals and cannot scale a DB. Use RBAC plus workload IAM, default-deny policies, non-root images and approved secret management.

## Interview checks

Running ≠ Ready; Ingress without controller does nothing; Service with no endpoints cannot route; PDB protects voluntary disruption only; EKS manages control plane, not app/nodes/add-ons.

## Related

[[Client to Pod Request Flow]] · [[Kubernetes Production Failures]]

Return: [[Infrastructure Dashboard]]
