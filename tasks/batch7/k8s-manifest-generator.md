# Task: Add a Helm Chart Values Generator to Kustomize

## Background

Kustomize (https://github.com/kubernetes-sigs/kustomize) is a Kubernetes configuration management tool. The task is to implement a Kustomize transformer plugin that generates Kubernetes `Deployment`, `Service`, `HorizontalPodAutoscaler`, and `ConfigMap` resources from a concise declarative specification, similar to how Helm charts produce resources from `values.yaml` — but as a native Kustomize plugin without requiring Helm.

## Files to Create/Modify

- `plugin/builtin/applicationgenerator/ApplicationGenerator.go` (create) — Kustomize generator plugin that produces Deployment, Service, HPA, and ConfigMap from an `ApplicationSpec`
- `plugin/builtin/applicationgenerator/ApplicationGenerator_test.go` (create) — Unit tests for the generator
- `api/types/applicationspec.go` (create) — Go types for the `ApplicationSpec` configuration
- `api/types/applicationspec_test.go` (create) — Unit tests for type validation

## Requirements

### `ApplicationSpec` Types (`applicationspec.go`)

```go
type ApplicationSpec struct {
    APIVersion string `json:"apiVersion" yaml:"apiVersion"`
    Kind       string `json:"kind" yaml:"kind"`
    Metadata   ApplicationMetadata `json:"metadata" yaml:"metadata"`
    Spec       ApplicationConfig   `json:"spec" yaml:"spec"`
}

type ApplicationMetadata struct {
    Name      string            `json:"name" yaml:"name"`
    Namespace string            `json:"namespace,omitempty" yaml:"namespace,omitempty"`
    Labels    map[string]string `json:"labels,omitempty" yaml:"labels,omitempty"`
}

type ApplicationConfig struct {
    Image       ImageSpec           `json:"image" yaml:"image"`
    Replicas    int32               `json:"replicas" yaml:"replicas"`
    Port        int32               `json:"port" yaml:"port"`
    Env         []EnvVar            `json:"env,omitempty" yaml:"env,omitempty"`
    Resources   ResourceSpec        `json:"resources,omitempty" yaml:"resources,omitempty"`
    Health      HealthSpec          `json:"health,omitempty" yaml:"health,omitempty"`
    Autoscaling *AutoscalingSpec    `json:"autoscaling,omitempty" yaml:"autoscaling,omitempty"`
    Config      map[string]string   `json:"config,omitempty" yaml:"config,omitempty"`
    ServiceType string              `json:"serviceType,omitempty" yaml:"serviceType,omitempty"` // ClusterIP, NodePort, LoadBalancer
}

type ImageSpec struct {
    Repository string `json:"repository" yaml:"repository"`
    Tag        string `json:"tag" yaml:"tag"`
    PullPolicy string `json:"pullPolicy,omitempty" yaml:"pullPolicy,omitempty"` // Always, IfNotPresent, Never
}

type EnvVar struct {
    Name  string `json:"name" yaml:"name"`
    Value string `json:"value,omitempty" yaml:"value,omitempty"`
    ValueFrom *EnvVarSource `json:"valueFrom,omitempty" yaml:"valueFrom,omitempty"`
}

type EnvVarSource struct {
    SecretKeyRef    *KeyRef `json:"secretKeyRef,omitempty" yaml:"secretKeyRef,omitempty"`
    ConfigMapKeyRef *KeyRef `json:"configMapKeyRef,omitempty" yaml:"configMapKeyRef,omitempty"`
}

type KeyRef struct {
    Name string `json:"name" yaml:"name"`
    Key  string `json:"key" yaml:"key"`
}

type ResourceSpec struct {
    Requests ResourceValues `json:"requests,omitempty" yaml:"requests,omitempty"`
    Limits   ResourceValues `json:"limits,omitempty" yaml:"limits,omitempty"`
}

type ResourceValues struct {
    CPU    string `json:"cpu,omitempty" yaml:"cpu,omitempty"`
    Memory string `json:"memory,omitempty" yaml:"memory,omitempty"`
}

type HealthSpec struct {
    LivenessPath  string `json:"livenessPath,omitempty" yaml:"livenessPath,omitempty"`
    ReadinessPath string `json:"readinessPath,omitempty" yaml:"readinessPath,omitempty"`
    Port          int32  `json:"port,omitempty" yaml:"port,omitempty"`
}

type AutoscalingSpec struct {
    MinReplicas    int32 `json:"minReplicas" yaml:"minReplicas"`
    MaxReplicas    int32 `json:"maxReplicas" yaml:"maxReplicas"`
    TargetCPU      int32 `json:"targetCPU,omitempty" yaml:"targetCPU,omitempty"`       // Target CPU utilization percentage
    TargetMemory   int32 `json:"targetMemory,omitempty" yaml:"targetMemory,omitempty"` // Target memory utilization percentage
}
```

### `ApplicationGenerator` Plugin (`ApplicationGenerator.go`)

Implements the `resmap.GeneratorPlugin` interface.

#### `Generate() (resmap.ResMap, error)`

Given an `ApplicationSpec`, generate the following Kubernetes resources:

1. **Deployment** (`apps/v1`):
   - Name: `spec.metadata.name`
   - Namespace: `spec.metadata.namespace`
   - Labels: `app.kubernetes.io/name: <name>`, `app.kubernetes.io/managed-by: kustomize-appgen`, plus any labels from `spec.metadata.labels`
   - Replicas: `spec.spec.replicas` (omit if autoscaling is configured)
   - Container image: `spec.spec.image.repository:spec.spec.image.tag`
   - Container port: `spec.spec.port`
   - Environment variables from `spec.spec.env`, plus inject `CONFIG_PATH` pointing to the ConfigMap mount (if config is present)
   - Resource requests/limits from `spec.spec.resources`
   - Liveness probe: HTTP GET on `spec.spec.health.livenessPath` at `spec.spec.health.port` (default: `spec.spec.port`)
   - Readiness probe: HTTP GET on `spec.spec.health.readinessPath` at the health port
   - If `spec.spec.config` is non-empty, mount the generated ConfigMap as a volume at `/etc/config`

2. **Service** (`v1`):
   - Name: `<metadata.name>-svc`
   - Type: `spec.spec.serviceType` (default: `ClusterIP`)
   - Selector: matches the Deployment's pod labels
   - Port: `spec.spec.port` → target port `spec.spec.port`

3. **ConfigMap** (`v1`) — only if `spec.spec.config` is non-empty:
   - Name: `<metadata.name>-config`
   - Data: key-value pairs from `spec.spec.config`

4. **HorizontalPodAutoscaler** (`autoscaling/v2`) — only if `spec.spec.autoscaling` is set:
   - Name: `<metadata.name>-hpa`
   - ScaleTargetRef: the generated Deployment
   - MinReplicas: `spec.spec.autoscaling.minReplicas`
   - MaxReplicas: `spec.spec.autoscaling.maxReplicas`
   - Metrics: CPU utilization at `targetCPU`% and/or memory at `targetMemory`%

#### Validation

- `image.repository` is required (non-empty)
- `image.tag` is required (non-empty)
- `port` must be between 1 and 65535
- `replicas` must be ≥ 0
- If autoscaling is set: `minReplicas` ≤ `maxReplicas`, both > 0, at least one target metric must be defined
- `serviceType` must be one of `"ClusterIP"`, `"NodePort"`, `"LoadBalancer"`, or empty (defaults to `ClusterIP`)

## Expected Functionality

Given this input:
```yaml
apiVersion: kustomize.config.k8s.io/v1
kind: ApplicationSpec
metadata:
  name: myapp
  namespace: production
spec:
  image:
    repository: myorg/myapp
    tag: "1.5.0"
  replicas: 3
  port: 8080
  env:
    - name: DB_HOST
      value: "postgres.production"
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "512Mi"
  health:
    livenessPath: /healthz
    readinessPath: /ready
  autoscaling:
    minReplicas: 2
    maxReplicas: 10
    targetCPU: 70
  config:
    LOG_LEVEL: info
    FEATURE_X: enabled
```

The generator produces 4 resources: Deployment (no replicas field since autoscaling is set), Service (ClusterIP on port 8080), ConfigMap with LOG_LEVEL and FEATURE_X, and HPA targeting 70% CPU.

## Acceptance Criteria

- Generator produces valid Deployment, Service, ConfigMap, and HPA resources
- Deployment omits `replicas` field when autoscaling is configured
- ConfigMap is only generated when `config` contains entries
- HPA is only generated when `autoscaling` is specified
- Health probes are configured on the Deployment container when health paths are specified
- All resources share consistent labels and namespace
- Validation rejects invalid port ranges, negative replicas, mismatched autoscaling min/max
- Generated YAML is valid and can be applied to a Kubernetes cluster
- All unit tests pass covering generation with various spec combinations
