---
type: practical-lab
domain: infrastructure
topic: minikube-go-api
status: not-attempted
---

# Minikube Practical Labs

## Goal and evidence contract

Build one Go API through twelve ordered changes. Run each command, record the date/result/mistake, and schedule a re-test; reading the manifests is not completion. Prerequisites: `go`, a container builder, `minikube`, and `kubectl`. Commands assume a disposable local cluster and namespace `infra-lab`.

## Lab application

Create a fresh directory outside the vault for executable files. `main.go`:

```go
package main

import (
    "fmt"
    "log"
    "net/http"
    "os"
    "sync/atomic"
    "time"
)

var ready atomic.Bool

func main() {
    ready.Store(os.Getenv("BROKEN_READINESS") != "true")
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "text/plain")
        fmt.Fprintf(w, "hello from %s message=%s\n", os.Getenv("HOSTNAME"), os.Getenv("MESSAGE"))
    })
    mux.HandleFunc("/live", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusNoContent) })
    mux.HandleFunc("/ready", func(w http.ResponseWriter, _ *http.Request) {
        if !ready.Load() { http.Error(w, "not ready", http.StatusServiceUnavailable); return }
        w.WriteHeader(http.StatusNoContent)
    })
    mux.HandleFunc("/metrics", func(w http.ResponseWriter, _ *http.Request) {
        fmt.Fprintln(w, "# HELP lab_up Whether the lab API is running.")
        fmt.Fprintln(w, "# TYPE lab_up gauge")
        fmt.Fprintln(w, "lab_up 1")
    })
    s := &http.Server{Addr: ":8080", Handler: mux, ReadHeaderTimeout: 3 * time.Second, IdleTimeout: 30 * time.Second}
    log.Fatal(s.ListenAndServe())
}
```

`go.mod`:

```go
module example.com/infra-lab

go 1.23
```

`Dockerfile`:

```dockerfile
FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags='-s -w' -o /out/api ./main.go

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/api /api
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/api"]
```

Start and build into Minikube: `minikube start`; `minikube image build -t infra-lab:v1 .`; `kubectl create namespace infra-lab`.

## Base manifest

Save as `app.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: {name: api, namespace: infra-lab}
spec:
  replicas: 2
  strategy: {type: RollingUpdate, rollingUpdate: {maxUnavailable: 0, maxSurge: 1}}
  selector: {matchLabels: {app: api}}
  template:
    metadata: {labels: {app: api}}
    spec:
      containers:
        - name: api
          image: infra-lab:v1
          imagePullPolicy: IfNotPresent
          ports: [{name: http, containerPort: 8080}]
          env:
            - {name: MESSAGE, valueFrom: {configMapKeyRef: {name: api-config, key: MESSAGE}}}
          readinessProbe: {httpGet: {path: /ready, port: http}, periodSeconds: 3, failureThreshold: 2}
          livenessProbe: {httpGet: {path: /live, port: http}, periodSeconds: 5, failureThreshold: 3}
          resources:
            requests: {cpu: 50m, memory: 32Mi}
            limits: {cpu: 250m, memory: 64Mi}
---
apiVersion: v1
kind: ConfigMap
metadata: {name: api-config, namespace: infra-lab}
data: {MESSAGE: "configured-v1"}
---
apiVersion: v1
kind: Service
metadata: {name: api, namespace: infra-lab}
spec:
  type: ClusterIP
  selector: {app: api}
  ports: [{name: http, port: 80, targetPort: http}]
```

## Ordered labs

### 1. Deploy a simple Go API

`kubectl apply -f app.yaml`; `kubectl -n infra-lab rollout status deploy/api`; verify two Ready Pods. Explain which controller created each object.

### 2. Expose with ClusterIP

`kubectl -n infra-lab get svc api -o wide`; inspect `kubectl -n infra-lab get endpointslice -l kubernetes.io/service-name=api -o yaml`. Confirm both ready Pod IPs appear.

### 3. Access through port-forward

`kubectl -n infra-lab port-forward svc/api 8080:80`; in another shell run `curl -i http://127.0.0.1:8080/`. Record the complete route and why port-forward is not production ingress.

### 4. Add readiness and liveness probes

They are present in the base manifest. Run `kubectl -n infra-lab describe pod <pod>` and `curl -i http://127.0.0.1:8080/ready`. Change `/live` to `/missing`, apply, observe restarts, then restore it. This intentionally demonstrates liveness—not application crashes.

### 5. Configure requests and limits

Inspect `kubectl -n infra-lab describe pod <pod>` and `kubectl -n infra-lab top pod` if Metrics Server is available (`minikube addons enable metrics-server`). Explain scheduling request versus cgroup limit and why the numbers are illustrative.

### 6. Perform a rolling update

Change response text, build `infra-lab:v2`, then run `kubectl -n infra-lab set image deploy/api api=infra-lab:v2`; watch `kubectl -n infra-lab get pod -w` and `kubectl -n infra-lab rollout status deploy/api`. Repeatedly curl during rollout.

### 7. Break readiness intentionally

`kubectl -n infra-lab set env deploy/api BROKEN_READINESS=true`; watch Pods become unready and EndpointSlice ready conditions change. Restore with `kubectl -n infra-lab set env deploy/api BROKEN_READINESS-`. Explain why containers did not restart.

### 8. Observe a Pod restart

Use the temporary broken liveness path from Lab 4, or run `kubectl -n infra-lab exec <pod> -- kill 1` only in this disposable lab if the image permits it. Record last state, restart count, `kubectl logs --previous`, and events. Restore the valid manifest.

### 9. Add ConfigMap

Update `MESSAGE`, `kubectl apply -f app.yaml`, then restart with `kubectl -n infra-lab rollout restart deploy/api` because environment-variable projections are read at process start. Contrast this with mounted-file update behavior.

### 10. Inspect logs and events

`kubectl -n infra-lab logs -l app=api --prefix --tail=50`; `kubectl -n infra-lab get events --sort-by=.metadata.creationTimestamp`; `kubectl -n infra-lab describe deploy/api`. Identify desired state, status, and evidence.

### 11. Test service-to-service communication

`kubectl -n infra-lab run caller --image=curlimages/curl --restart=Never --command -- sleep 3600`; `kubectl -n infra-lab exec caller -- curl -i http://api/`; `kubectl -n infra-lab exec caller -- nslookup api.infra-lab.svc.cluster.local`. Delete the caller after the lab.

### 12. Add basic metrics

`kubectl -n infra-lab port-forward svc/api 8080:80`; `curl http://127.0.0.1:8080/metrics`. Then enable Prometheus only if you want the optional extension: add scrape annotations or a ServiceMonitor matching the installed operator. Do not claim collection until a Prometheus query returns `lab_up`.

## Failure drills and cleanup

Repeat with a wrong Service selector, wrong `targetPort`, missing ConfigMap, memory pressure, and a bad image tag. Before every fix, predict which evidence changes. Cleanup: `kubectl delete namespace infra-lab`; optionally `minikube stop`. The namespace deletion is scoped to this disposable lab.

## Attempt and re-test record

| Date | Labs completed cold | Commands/errors preserved | Fix explained | Next re-test |
| --- | --- | --- | --- | --- |
| pending | 0/12 | pending | pending | schedule after first attempt |

## Related notes

[[Kubernetes Mental Model]] · [[Client to Pod Request Flow]] · [[Probes and Application Health]] · [[Requests Limits and QoS]] · [[Rolling Deployments and Rollbacks]] · [[Kubernetes Production Failures]]

## Source metadata

Curated from *Kubernetes for Backend Interviews* (2026-07-07, `6a4cf217-e6dc-83e8-b416-156a8354a76b`) and official Kubernetes tutorials. Image tags/tool versions are illustrative and must be verified locally (`status: needs-verification`).
