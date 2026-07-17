---
type: canonical
domain: infrastructure
topic: kubernetes-client-to-pod-flow
status: learning
source_conversations:
  - "Kubernetes for Backend Interviews | 2026-07-07 | 6a4cf217-e6dc-83e8-b416-156a8354a76b"
  - "AWS EKS App Deployment | 2026-06-25 | 6a3ce123-1794-83e8-83ea-0c20e4b4424c"
verification_needed: cluster version, controller mode, CNI, and load-balancer target type
---

# Client to Pod Request Flow

## Problem it solves

This note answers the production question: **how does one client request reach a healthy Go container on EKS, and at which boundary can it fail?** Kubernetes objects express desired state; the live request travels through AWS and node networking. Do not confuse the configuration path with the packet path.

## The complete flow

Client → recursive DNS → Route 53 authoritative DNS → public ALB or NLB → Kubernetes Ingress or `LoadBalancer` Service → AWS Load Balancer Controller-managed listener/target group → Kubernetes Service → EndpointSlice → kube-proxy rules or an eBPF service data path → Pod IP → container port → Go HTTP handler → downstream Service/database → response.

An implementation can skip or merge hops. With an ALB Ingress using IP targets, the ALB can target Pod IPs directly; with instance targets it reaches a node port before Service routing. An NLB normally handles L4 TCP/UDP. Confirm the installed controller and target type instead of memorizing one universal route.

## Control plane versus data plane

| Plane | Purpose | Main actors | On every request? |
| --- | --- | --- | --- |
| Control plane | Stores desired state and reconciles actual state | API server, etcd, scheduler, controllers, AWS Load Balancer Controller | No |
| Node/application data plane | Moves bytes to a selected healthy backend | ALB/NLB, VPC routing, CNI, kube-proxy/eBPF, Pod network, Go process | Yes |

`kubectl apply` sends an authenticated and authorized API request to the API server. Admission validates/mutates it; the API server persists the object in etcd. Controllers notice desired/actual differences. The Deployment controller creates a ReplicaSet; the scheduler binds pending Pods to suitable nodes; the kubelet asks the CRI-compatible container runtime to pull the image and start containers; the CNI plugin attaches Pod networking. These actions prepare the data plane but are not synchronous steps in a user request.

## External request: hop-by-hop

1. **DNS.** The client resolver checks caches, then a recursive resolver obtains the Route 53 record. TTL controls how quickly a changed load-balancer name or failover record is observed. Diagnose with `dig +trace api.example.com` and compare answers from several resolvers.
2. **AWS edge/load balancer.** A security group and listener admit the connection. TLS may terminate here or pass through. An ALB evaluates host/path rules and target-group health; an NLB forwards the TCP/UDP flow. WAF, CloudFront, or API Gateway may precede this hop when required.
3. **Ingress and Ingress controller.** Ingress is desired L7 routing configuration, not a proxy process by itself. An Ingress controller implements that configuration. The AWS Load Balancer Controller watches Ingress/Service resources and configures AWS ALB/NLB resources. NGINX/Envoy ingress instead runs proxy Pods behind a load balancer.
4. **Service.** A Service gives a stable virtual IP and port. Its selector normally identifies Pods. The EndpointSlice controller publishes matching backend IPs plus readiness/serving/terminating conditions.
5. **Endpoint choice.** kube-proxy programs node rules (implementation depends on cluster mode) or an eBPF CNI implements Service translation. The packet is DNATed/routed to one eligible Pod IP. In EKS VPC CNI mode, Pod IPs are drawn from VPC-addressable ranges; alternative CNIs differ.
6. **Pod and container.** The CNI path delivers to the Pod network namespace. The container must listen on the address and `targetPort` expected by the Service. `containerPort` is metadata; it does not make an application listen.
7. **Go handler.** `net/http` or a framework accepts the socket. Server read-header/read/write/idle timeouts, maximum body size, request context, authentication, and bounded concurrency protect the process. The handler should propagate `context.Context` to downstream work.
8. **Downstream.** A service call repeats CoreDNS → Service → EndpointSlice → Pod flow. A database call uses a connection pool and VPC/DNS/TLS path. Timeouts must fit inside the caller deadline; unsafe retries can duplicate work.
9. **Response.** Bytes travel back through the established connection and reverse NAT/load-balancer state. Logs and trace spans should preserve a request/trace ID; metrics record outcome and duration without unbounded labels.

## Readiness and traffic eligibility

A readiness probe answers **may this instance receive new traffic?** A failed readiness probe makes the Pod not ready; EndpointSlice readiness changes and Service-aware paths stop selecting it after propagation. Existing connections may continue, and an external target group can have a separate health-check convergence delay. Liveness answers **should kubelet restart this container?** Startup probes protect slow startup from premature liveness failures.

Readiness should verify the minimum ability to serve, not every optional dependency. If all Pods report unready because one shared dependency fails, the system converts a partial dependency failure into total unavailability. Prefer truthful degraded responses when safe.

## What changes during a deployment

1. Deployment creates a new ReplicaSet and new Pods according to `maxSurge`/`maxUnavailable`.
2. Scheduler selects nodes; kubelet/runtime/CNI create the Pods.
3. Startup and readiness must pass before new endpoints become eligible.
4. Old Pods receive termination: endpoint state changes, `preStop` may run, and the process receives SIGTERM.
5. A Go server should fail readiness, stop accepting new work, call graceful shutdown with a deadline, finish bounded in-flight requests, then exit before `terminationGracePeriodSeconds`.
6. When availability is stable, old ReplicaSet count reaches zero. `kubectl rollout status`, events, EndpointSlices, target health, HTTP error ratio, and latency verify the rollout.

A rolling update can still fail through a bad readiness check, too-small grace period, long-lived WebSockets, connection draining mismatch, schema incompatibility, or a surge that exhausts database connections.

## Failure behavior

### Pod crashes

The runtime reports exit; kubelet restarts the container according to policy and records restart/backoff state. Readiness removes it from new Service traffic. The ReplicaSet replaces a lost Pod object, but repeated process crashes become `CrashLoopBackOff`. Inspect the previous container log and termination reason before restarting manually.

### Node dies

Node heartbeats stop; the node becomes `NotReady`. Endpoint readiness and load-balancer target health should stop new traffic. Controllers eventually create replacement Pods on healthy nodes, subject to capacity, topology, volumes, taints, and disruption constraints. Existing connections to the dead node are lost. Multi-AZ nodes and spare capacity matter; Kubernetes cannot schedule onto capacity that does not exist.

### Control plane unavailable

Existing data-plane traffic can often continue because node and load-balancer rules already exist, but new scheduling, reconciliation, configuration changes, and some endpoint updates stall. EKS manages control-plane availability; the workload team still owns node capacity and application design.

## Internal service-to-service flow

`orders` calls `http://payments.payments.svc.cluster.local:8080/authorize`:

1. The Go resolver asks the Pod's configured DNS service; CoreDNS returns the payments Service ClusterIP (or headless Pod records).
2. The client opens/reuses a TCP connection. NetworkPolicy and security-group/VPC rules must permit both directions as applicable.
3. The Service virtual IP is translated by kube-proxy/eBPF to a ready payments endpoint from EndpointSlice.
4. The packet routes via the CNI to the destination Pod IP, possibly on another node.
5. Payments handles the deadline/idempotency key, queries RDS through `database/sql`, and returns.
6. The orders client reuses the connection only when response bodies are closed and pool settings permit it.

Internal traffic normally does not traverse public ALB/Ingress. Use Ingress/Gateway only when L7 policy, cross-cluster entry, or external exposure requires it. A service mesh adds sidecar/ambient proxies, mTLS, and another failure/telemetry layer.

## Observability: where evidence appears

- **Client/DNS:** DNS response, TTL, resolver latency, TLS/connect error.
- **ALB/NLB:** target health, connection/request counts, ALB access logs, 4xx/5xx, target response time.
- **Ingress/controller:** controller reconciliation events/logs, rejected config, proxy upstream timing.
- **Kubernetes:** Pod/Node conditions, events, Deployment status, EndpointSlices, probe results, restarts.
- **Node/network:** CNI logs/metrics, dropped packets, conntrack/NAT state, kube-proxy/eBPF maps, interface errors.
- **Go:** request rate, status/error class, latency histogram, saturation, goroutines, heap/GC, file descriptors, pool stats, structured logs, trace spans.
- **Downstream:** dependency spans, database pool wait time, Kafka lag, Redis/RDS latency.

Trace context should cross HTTP headers and message metadata. Telemetry export must be bounded and should not block the request path.

## Senior diagnostic order

Start outside-in, then compare control-plane intent with data-plane evidence:

1. Reproduce one request with DNS/connect/TLS/HTTP timings and a correlation ID.
2. Check load-balancer listener, target health, and access log.
3. Check Ingress/Service ports and selectors.
4. Inspect EndpointSlices; no ready address means routing cannot succeed.
5. Test Service DNS and ClusterIP from a debug Pod, then call one Pod IP directly.
6. Check readiness, logs, events, previous termination, and node condition.
7. Inspect NetworkPolicy, security groups, routes, CNI, kube-proxy/eBPF, and conntrack only after narrowing the failed hop.
8. Correlate application latency with CPU throttling, memory/GC, file descriptors, downstream pool wait, and trace spans.

Useful commands: `kubectl get deploy,rs,pod,svc,ingress,endpointslice -A`; `kubectl describe pod <pod>`; `kubectl logs <pod> --previous`; `kubectl get events --sort-by=.metadata.creationTimestamp`; `kubectl rollout status deploy/<name>`; `kubectl exec <debug-pod> -- nslookup <service>`; `curl -v --connect-timeout 2 http://<service>:<port>/ready`; `ss -s`; `ip route`; `tcpdump` only with appropriate access and data-handling controls.

## Security and trade-offs

Use least-privilege IAM and RBAC, private nodes where practical, workload identity for AWS calls, TLS at external boundaries, optional mTLS internally, default-deny NetworkPolicies with explicit egress, image provenance/scanning, non-root/read-only containers, and secrets from an approved manager/CSI path. Never place credentials in manifests or logs.

ALB provides rich HTTP routing but adds L7 cost and controller/AWS reconciliation. NLB is lower-level and suits TCP/UDP/source-IP requirements. IP targets shorten the route but consume VPC addresses and expose Pod lifecycle directly to target health. Instance targets add a node/Service hop. eBPF can improve observability and routing efficiency but increases platform-specific operational knowledge.

## Interview prompts

- Why can a Running Pod receive no traffic?
- What is stored in EndpointSlice, and how does readiness affect it?
- Which parts are control plane and which execute per request?
- How do ALB IP and instance target modes change the path?
- What happens to in-flight traffic during SIGTERM and endpoint removal?

## Five-minute revision

Desired state travels through API server → etcd → controllers/scheduler → kubelet/runtime/CNI. User bytes travel DNS → ALB/NLB → Ingress/controller configuration → Service → ready EndpointSlice → kube-proxy/eBPF → Pod IP → Go handler → dependency. Readiness controls new eligibility; liveness restarts; node death breaks connections and triggers rescheduling. Diagnose hop by hop with target health, EndpointSlices, events, direct calls, and correlated telemetry.

## Related notes

[[Kubernetes Architecture]] · [[Service to Service Communication]] · [[Services and Service Discovery]] · [[Ingress and AWS Load Balancers]] · [[Kubernetes Networking CNI and kube-proxy]] · [[Probes and Application Health]] · [[Rolling Deployments and Rollbacks]] · [[Kubernetes Production Failures]] · [[EKS Architecture]] · [[Context Cancellation]] · [[05 Infrastructure/Observability/Logs Metrics and Traces|Logs Metrics and Traces]]

## Source metadata

Curated from the two extracted conversations listed in frontmatter and verified against Kubernetes component/Service/EndpointSlice/probe documentation and AWS EKS load-balancing guidance on 2026-07-17. Exact behavior is `needs-verification` for the deployed Kubernetes version, AWS Load Balancer Controller version, CNI, Service implementation, and target type.

Official references: https://kubernetes.io/docs/concepts/overview/components/ · https://kubernetes.io/docs/concepts/services-networking/service/ · https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/ · https://kubernetes.io/docs/concepts/workloads/pods/probes/ · https://docs.aws.amazon.com/eks/latest/best-practices/load-balancing.html
