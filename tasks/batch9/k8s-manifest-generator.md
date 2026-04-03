# Task: Build a Kubernetes Manifest Generator with Security Best Practices

## Background

Kustomize (https://github.com/kubernetes-sigs/kustomize) is a Kubernetes manifest management tool. A new Go package is needed that generates production-ready Kubernetes manifests (Deployment, Service, ConfigMap, Secret, HPA, PDB, NetworkPolicy) from a high-level application specification, enforcing security best practices: non-root security contexts, resource limits, read-only root filesystems, dropped capabilities, health checks, and Pod Disruption Budgets.

## Files to Create/Modify

- `cmd/manifest-gen/main.go` (create) — CLI that reads an application YAML spec and generates a directory of Kubernetes manifests
- `pkg/generator/deployment.go` (create) — Generates `Deployment` manifests with security contexts, resource limits, probes, and anti-affinity rules
- `pkg/generator/service.go` (create) — Generates `Service` and optional `Ingress` manifests
- `pkg/generator/config.go` (create) — Generates `ConfigMap` and `Secret` manifests from the app spec, with Secret data base64-encoded
- `pkg/generator/scaling.go` (create) — Generates `HorizontalPodAutoscaler` and `PodDisruptionBudget` manifests
- `pkg/generator/networkpolicy.go` (create) — Generates `NetworkPolicy` manifests allowing only specified ingress/egress traffic
- `pkg/generator/validator.go` (create) — Validates generated manifests against security rules (non-root, resource limits present, no `latest` tag)
- `pkg/generator/types.go` (create) — Input types: `AppSpec`, `ContainerSpec`, `ProbeSpec`, `ScalingSpec`, `NetworkSpec`
- `pkg/generator/generator_test.go` (create) — Unit tests for all generators

## Requirements

### Input Types (`types.go`)

- `AppSpec` struct: `Name`, `Namespace`, `Labels map[string]string`, `Containers []ContainerSpec`, `Replicas int`, `Scaling *ScalingSpec`, `Network *NetworkSpec`, `ConfigData map[string]string`, `SecretData map[string]string`
- `ContainerSpec` struct: `Name`, `Image` (must include tag, not `:latest`), `Port int`, `Env map[string]string`, `EnvFromSecret []string`, `Resources ResourceSpec`, `LivenessProbe *ProbeSpec`, `ReadinessProbe *ProbeSpec`, `VolumeMounts []VolumeMount`
- `ResourceSpec`: `RequestsCPU`, `RequestsMemory`, `LimitsCPU`, `LimitsMemory` (all strings like `"250m"`, `"512Mi"`)
- `ProbeSpec`: `Path string`, `Port int`, `InitialDelay int`, `Period int`
- `ScalingSpec`: `MinReplicas int`, `MaxReplicas int`, `TargetCPUPercent int`, `PDBMinAvailable string`
- `NetworkSpec`: `IngressPorts []int`, `IngressFrom []string` (namespace selectors), `EgressTo []string` (CIDR blocks), `DenyAll bool`

### Deployment Generator (`deployment.go`)

- Function `GenerateDeployment(spec AppSpec) (*appsv1.Deployment, error)`
- Security context at pod level:
  - `runAsNonRoot: true`
  - `runAsUser: 1000`
  - `runAsGroup: 1000`
  - `fsGroup: 1000`
  - `seccompProfile.type: RuntimeDefault`
- Security context at container level:
  - `allowPrivilegeEscalation: false`
  - `readOnlyRootFilesystem: true`
  - `capabilities.drop: ["ALL"]`
- Resource limits and requests from spec (error if not provided)
- Liveness and readiness probes from spec (warn if not provided, default to TCP check on container port)
- Pod anti-affinity: `preferredDuringSchedulingIgnoredDuringExecution` with topology key `kubernetes.io/hostname`
- Labels: include `app.kubernetes.io/name`, `app.kubernetes.io/version` (extracted from image tag), `app.kubernetes.io/managed-by: manifest-gen`
- Inject `envFrom` for ConfigMap and Secret references

### Service Generator (`service.go`)

- Function `GenerateService(spec AppSpec) (*corev1.Service, error)`
- Type `ClusterIP` by default
- Port mapping from container ports
- Selector from deployment labels
- Function `GenerateIngress(spec AppSpec, host string, tlsSecretName string) (*networkingv1.Ingress, error)` — Optional, called only when host is provided

### Config/Secret Generator (`config.go`)

- Function `GenerateConfigMap(spec AppSpec) (*corev1.ConfigMap, error)` — Only generated if `ConfigData` is non-empty
- Function `GenerateSecret(spec AppSpec) (*corev1.Secret, error)` — Only generated if `SecretData` is non-empty; values base64-encoded, type `Opaque`

### Scaling Generator (`scaling.go`)

- Function `GenerateHPA(spec AppSpec) (*autoscalingv2.HorizontalPodAutoscaler, error)` — Only generated if `Scaling` spec is present
  - `spec.metrics[0].type: Resource`, resource name `cpu`, `target.averageUtilization` from spec
- Function `GeneratePDB(spec AppSpec) (*policyv1.PodDisruptionBudget, error)`
  - `spec.minAvailable` from ScalingSpec.PDBMinAvailable (e.g., `"50%"` or `"2"`)

### Network Policy Generator (`networkpolicy.go`)

- Function `GenerateNetworkPolicy(spec AppSpec) (*networkingv1.NetworkPolicy, error)` — Only generated if `Network` spec is present
- If `DenyAll` is true: empty ingress and egress rules (deny all traffic)
- Otherwise: allow ingress on specified ports from specified namespaces, allow egress to specified CIDRs
- Always allow egress to kube-dns (UDP port 53) in `kube-system` namespace

### Validator (`validator.go`)

- Function `Validate(manifests []runtime.Object) []ValidationError`
- `ValidationError`: `Resource string`, `Field string`, `Message string`, `Severity string` (error/warning)
- Rules:
  - ERROR: container image uses `:latest` tag or no tag
  - ERROR: no resource limits defined
  - ERROR: `runAsNonRoot` is not true
  - ERROR: `allowPrivilegeEscalation` is not false
  - WARNING: no liveness probe defined
  - WARNING: no readiness probe defined
  - WARNING: no PDB defined when replicas > 1

### Expected Functionality

- Generating manifests for a 3-replica web app with image `nginx:1.25.3` produces a Deployment with non-root security context, resource limits, and anti-affinity
- Validator on a deployment with `:latest` tag returns an error for the image tag
- HPA with target CPU 80% and min/max 2/10 generates correct autoscaling resource
- NetworkPolicy with `DenyAll: false`, ingress on port 8080 from namespace "frontend" generates correct rules with kube-dns egress always allowed

## Acceptance Criteria

- All generated manifests are valid Kubernetes resource YAML
- Security contexts enforce non-root, read-only filesystem, and dropped capabilities on every deployment
- Resource limits are present on every container; validator catches missing limits
- HPA and PDB are correctly linked to the deployment via label selectors
- NetworkPolicy correctly restricts traffic to specified patterns with DNS egress exemption
- Validator catches all security anti-patterns (latest tag, privilege escalation, missing limits)
- `python -m pytest /workspace/tests/test_k8s_manifest_generator.py -v --tb=short` passes
