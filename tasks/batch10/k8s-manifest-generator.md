# Task: Implement Kubernetes Manifest Generator with Validation and Security Context Enforcement

## Background

The Kustomize project (`kubernetes-sigs/kustomize`) needs a manifest generator library within the `api/` package that programmatically creates production-ready Kubernetes Deployment, Service, ConfigMap, and Secret manifests. The generator must enforce security best practices (non-root containers, resource limits, health probes) and produce valid YAML that integrates with the existing `kyaml/` YAML processing pipeline. The output must follow Kubernetes labeling conventions and support multi-environment overlays.

## Files to Create/Modify

- `api/manifest/generator.go` — Core manifest generator with builder API for Deployment, Service, ConfigMap, Secret, and PVC resources (new)
- `api/manifest/generator_test.go` — Unit tests for the manifest generator (new)
- `api/manifest/security.go` — Security context validator and enforcer (new)
- `api/manifest/security_test.go` — Unit tests for security enforcement (new)
- `api/manifest/labels.go` — Kubernetes standard label generator and validator (new)
- `api/manifest/labels_test.go` — Unit tests for label generation (new)

## Requirements

### Manifest Generator API

- `NewDeployment(name, namespace, image string)` returns a `DeploymentBuilder` with chainable methods:
  - `WithReplicas(n int32)` — set replica count; must be >= 1
  - `WithPort(name string, containerPort int32)` — add a named port; reject port numbers outside 1–65535 and duplicate port names
  - `WithResources(requests, limits ResourceSpec)` — set CPU/memory; `ResourceSpec` has `CPU string`, `Memory string`; reject if limits are lower than requests
  - `WithProbe(probeType string, path string, port string, initialDelay, period int32)` — probeType is `liveness` or `readiness`; reject unknown types
  - `WithEnv(key, value string)` — add an environment variable
  - `WithEnvFrom(configMapName string)` and `WithSecretRef(secretName string)` — reference external config
  - `WithSecurityContext(sc SecurityContext)` — applied at pod and container level
  - `Build()` returns `(*yaml.RNode, error)` using the kyaml `yaml.RNode` type; returns error if name is empty, image is empty, or image uses `:latest` tag
- `NewService(name, namespace string, serviceType string)` returns a `ServiceBuilder`:
  - `WithSelector(labels map[string]string)` — pod selector
  - `WithPort(name string, port, targetPort int32)` — add port mapping; reject if port ≤ 0
  - `Build()` returns `(*yaml.RNode, error)`; rejects unknown serviceType values (only `ClusterIP`, `NodePort`, `LoadBalancer` allowed)
- `NewConfigMap(name, namespace string)` returns a `ConfigMapBuilder`:
  - `WithData(key, value string)` — add key-value pair
  - `WithFileData(key, content string)` — add file-style entry; reject keys containing `..` or `/`
  - `Build()` returns `(*yaml.RNode, error)`
- `NewSecret(name, namespace string)` returns a `SecretBuilder`:
  - `WithStringData(key, value string)` — add a stringData entry
  - `WithType(secretType string)` — set type (`Opaque`, `kubernetes.io/tls`, `kubernetes.io/dockerconfigjson`)
  - `Build()` returns `(*yaml.RNode, error)`; rejects `kubernetes.io/tls` type unless both `tls.crt` and `tls.key` keys are present

### Security Context Enforcement

- Define `SecurityContext` struct: `RunAsNonRoot bool`, `RunAsUser int64`, `ReadOnlyRootFilesystem bool`, `DropCapabilities []string`, `AllowPrivilegeEscalation bool`
- `EnforceSecurityPolicy(deployment *yaml.RNode)` scans the deployment and returns a list of `SecurityViolation` (field string + message):
  - Violation if `RunAsNonRoot` is false or absent
  - Violation if `AllowPrivilegeEscalation` is true or absent
  - Violation if `ReadOnlyRootFilesystem` is false or absent
  - Violation if capabilities do not include `DROP ALL`
  - Violation if `RunAsUser` is 0 (root)
- `ApplySecurityDefaults(deployment *yaml.RNode)` applies secure defaults: `RunAsNonRoot: true`, `RunAsUser: 1000`, `ReadOnlyRootFilesystem: true`, `AllowPrivilegeEscalation: false`, `DropCapabilities: ["ALL"]`

### Label Management

- `StandardLabels(name, version, component, partOf string)` returns a `map[string]string` with keys: `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/component`, `app.kubernetes.io/part-of`, `app.kubernetes.io/managed-by` (set to `kustomize`)
- `ValidateLabels(labels map[string]string)` returns errors for: keys longer than 253 characters in prefix, values longer than 63 characters, values containing characters outside `[a-zA-Z0-9_.-]`, empty key names

### Expected Functionality

- `NewDeployment("api", "production", "myregistry/api:v1.2.3").WithReplicas(3).WithPort("http", 8080).WithResources(ResourceSpec{"250m","256Mi"}, ResourceSpec{"500m","512Mi"}).Build()` → valid YAML with 3 replicas, port 8080, resource limits
- `NewDeployment("api", "prod", "myregistry/api:latest").Build()` → error containing "latest tag"
- `NewDeployment("", "prod", "myregistry/api:v1").Build()` → error containing "name is required"
- `NewDeployment("api", "prod", "img:v1").WithResources(ResourceSpec{"500m","512Mi"}, ResourceSpec{"250m","256Mi"}).Build()` → error containing "limits must be >= requests"
- `NewService("api", "prod", "Ingress").Build()` → error containing "unsupported service type"
- `NewSecret("tls-cert", "prod").WithType("kubernetes.io/tls").WithStringData("tls.crt","...").Build()` → error containing "tls.key" (missing key)
- `NewConfigMap("cfg","ns").WithFileData("../etc/passwd","data").Build()` → error containing "invalid key"
- `EnforceSecurityPolicy` on a deployment with `RunAsUser: 0` → returns violation mentioning "root"
- `ApplySecurityDefaults` on a bare deployment → resulting YAML contains `runAsNonRoot: true` and `drop: ["ALL"]`
- `ValidateLabels(map[string]string{"app.kubernetes.io/name": "value with spaces"})` → error about invalid characters

## Acceptance Criteria

- `go test ./api/manifest/ -run TestDeployment -v` passes — deployments generate valid YAML with correct apiVersion, kind, metadata, and spec
- `go test ./api/manifest/ -run TestService -v` passes — services enforce valid type and port constraints
- `go test ./api/manifest/ -run TestConfigMap -v` passes — config maps reject path traversal keys
- `go test ./api/manifest/ -run TestSecret -v` passes — secrets enforce type-specific key requirements
- `go test ./api/manifest/ -run TestSecurity -v` passes — security violations detected and defaults applied correctly
- `go test ./api/manifest/ -run TestLabels -v` passes — labels conform to Kubernetes conventions
- `:latest` image tags are rejected at build time
- Resource limit/request validation prevents limits < requests
- TLS secrets require both `tls.crt` and `tls.key` data keys
- Security defaults produce a container spec that passes `EnforceSecurityPolicy` with zero violations
