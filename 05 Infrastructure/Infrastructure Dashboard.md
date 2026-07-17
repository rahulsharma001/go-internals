---
type: dashboard
domain: infrastructure
status: active
---

# Infrastructure Dashboard

Use this dashboard to move from request flow to failure diagnosis and interview recall. The canonical owner explains the concept; runbooks diagnose; labs create implementation evidence; revisions test retrieval. Content creation is not evidence of interview readiness.

## Start here

1. [[Client to Pod Request Flow]] — full EKS request and service-to-service path.
2. [[Kubernetes Production Failures]] — fifteen production diagnostic scenarios.
3. [[AWS Architecture Selection Guide]] — connected REST, asynchronous and WebSocket designs.
4. [[Network Troubleshooting]] and [[Linux Production Debugging]] — host/packet diagnostic ladders.
5. [[Minikube Practical Labs]] — ordered executable practice; status remains not-attempted.
6. [[Incident Investigation]] — stabilization through prevention.

## Kubernetes

- [[Autoscaling HPA VPA and Cluster Autoscaler]]
- [[Client to Pod Request Flow]]
- [[ConfigMaps Secrets and Configuration]]
- [[EKS Architecture]]
- [[Ingress and AWS Load Balancers]]
- [[Kubernetes Architecture]]
- [[Kubernetes Mental Model]]
- [[Kubernetes Networking CNI and kube-proxy]]
- [[Kubernetes Observability]]
- [[Kubernetes Production Failures]]
- [[Minikube Practical Labs]]
- [[Network Policies]]
- [[Pod Disruption Budgets]]
- [[Pods Deployments and ReplicaSets]]
- [[Probes and Application Health]]
- [[RBAC and Service Accounts]]
- [[Requests Limits and QoS]]
- [[Rolling Deployments and Rollbacks]]
- [[Service to Service Communication]]
- [[Services and Service Discovery]]
- [[StatefulSets and Persistent Storage]]

## AWS

- [[API Gateway WebSockets]]
- [[API Gateway]]
- [[AWS Architecture Selection Guide]]
- [[AWS Cost and Scaling Trade-offs]]
- [[AWS Reliability and Multi AZ]]
- [[CloudWatch and X-Ray]]
- [[ECS and Fargate]]
- [[EKS]]
- [[ElastiCache Redis]]
- [[IAM Roles and Policies]]
- [[Lambda]]
- [[MSK and Kafka on AWS]]
- [[RDS Aurora and DynamoDB]]
- [[S3 and CloudFront]]
- [[SQS SNS and EventBridge]]
- [[Step Functions]]
- [[VPC Subnets Routing and Security Groups]]

## Docker

- [[Container Networking]]
- [[Container Security]]
- [[Containers and Images]]
- [[Docker Layers and Build Cache]]
- [[Docker Production Failures]]
- [[Multi Stage Builds for Go]]
- [[Volumes and Persistence]]

## Linux

- [[CPU Memory and IO Troubleshooting]]
- [[File Descriptors]]
- [[Linux Memory and Virtual Memory]]
- [[Linux Networking Tools]]
- [[Linux Production Debugging]]
- [[Processes Threads and Signals]]
- [[System Calls and Context Switching]]

## Networking

- [[Connection Pooling]]
- [[DNS]]
- [[HTTP 1 2 and 3]]
- [[IPsec and VTI]]
- [[Network Troubleshooting]]
- [[OSPF Fundamentals]]
- [[Proxies Load Balancers and NAT]]
- [[SNMP and Traps]]
- [[TCP Connection Lifecycle]]
- [[TCP and UDP]]
- [[TLS and mTLS]]
- [[WebSocket Polling Webhook and SSE]]

## Terraform

- [[Modules]]
- [[Plan Apply and Drift]]
- [[Providers Resources and Data Sources]]
- [[State Locking]]
- [[State and Remote Backends]]
- [[Terraform Mental Model]]
- [[Terraform Production Practices]]
- [[Terraform with AWS and EKS]]

## Observability

- [[Alert Design]]
- [[Datadog and APM]]
- [[ELK and Kibana]]
- [[Incident Investigation]]
- [[Logs Metrics and Traces]]
- [[OpenTelemetry]]
- [[Prometheus and Grafana]]
- [[SLI SLO and Error Budgets]]

## Quick Revision

- [[AWS Interview Revision]]
- [[Docker Interview Revision]]
- [[Kubernetes Interview Revision]]
- [[Linux Interview Revision]]
- [[Networking Interview Revision]]
- [[Observability Interview Revision]]
- [[Terraform Interview Revision]]

## Learning lifecycle

Learn a canonical → draw the flow from memory → run a lab or diagnostic drill → explain the failure and trade-off → use the revision card → record an actual mistake only if observed → schedule a re-test.

## Verification boundary

Cloud/Kubernetes/vendor details change. Notes mark version, controller, region, quota, price and policy-dependent claims as `needs-verification`. Use official documentation and deployed configuration before production action. No personal production ownership, scale, incident or metric is asserted.

Home index: [[Infrastructure Map of Content]] · Revisions: [[Quick Revision Index]]
