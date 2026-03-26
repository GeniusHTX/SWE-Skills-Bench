# Task: Implement Kubernetes Manifest Generator with Resource Policies for Kustomize

## Background

Kustomize (https://github.com/kubernetes-sigs/kustomize) is a Kubernetes configuration management tool. The project needs a manifest generator component that creates secure, production-ready Kubernetes resource manifests (Deployments, Services, ConfigMaps, NetworkPolicies) with proper resource limits, health probes, security contexts, and network policies. This should be implemented within the `api/` package structure.

## Files to Create/Modify

- `api/manifest/deployment_generator.go` (create) — Deployment manifest generator with resource limits, probes, and security contexts
- `api/manifest/network_policy_generator.go` (create) — NetworkPolicy generator for namespace isolation
- `api/manifest/configmap_generator.go` (create) — ConfigMap and Secret manifest generator with data validation
- `api/manifest/deployment_generator_test.go` (create) — Tests for Deployment generation
- `api/manifest/network_policy_generator_test.go` (create) — Tests for NetworkPolicy generation

## Requirements

### Deployment Generator

- Implement a `DeploymentGenerator` that creates Kubernetes Deployment manifests with:
  - `replicas` (int, default 2, must be ≥ 1)
  - Container `image` (string, required, must include a tag or digest — bare image names like `nginx` are rejected)
  - Resource `requests` and `limits` for CPU and memory (required; requests must be ≤ limits)
  - Liveness probe: HTTP GET on a configurable path and port, with `initialDelaySeconds`, `periodSeconds`, `failureThreshold`
  - Readiness probe: HTTP GET with separate configuration from liveness
  - Security context: `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, `capabilities.drop: ["ALL"]`
- Validate: CPU requests/limits must be in valid Kubernetes format (e.g., `"100m"`, `"1"`, `"2.5"`); memory must include units (`"128Mi"`, `"1Gi"`)
- Validate: if memory request > memory limit, return error with specific message
- Generate labels: `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/managed-by: kustomize`
- Generate YAML output with `apiVersion: apps/v1`, `kind: Deployment`

### NetworkPolicy Generator

- Implement a `NetworkPolicyGenerator` that creates namespace isolation policies:
  - **Default deny ingress**: deny all incoming traffic to a namespace except explicitly allowed
  - **Allow from namespaces**: allow ingress from specified namespaces by label selector
  - **Allow specific ports**: restrict allowed traffic to specific TCP ports
  - **Egress rules**: allow egress to specific CIDR blocks and deny egress to metadata service (169.254.169.254/32)
- Each policy has `apiVersion: networking.k8s.io/v1` and `kind: NetworkPolicy`
- Validate: port numbers must be 1–65535; CIDR blocks must be valid (parse and verify)

### ConfigMap and Secret Generator

- Implement a `ConfigMapGenerator` that creates ConfigMaps from:
  - Key-value pairs (map[string]string)
  - File contents (map[string][]byte for binary data support)
- Validate: ConfigMap data total size must not exceed 1 MiB (Kubernetes limit); return error if exceeded
- Validate: key names must conform to Kubernetes naming: alphanumeric, `-`, `_`, `.` only
- For Secrets: same structure but `kind: Secret`, with values base64-encoded in the output, and `type` field (default: `Opaque`)

### Expected Functionality

- A Deployment for image `nginx:1.25` with CPU request `100m`, limit `500m`, memory request `128Mi`, limit `256Mi` produces correct YAML with security context
- An image name `nginx` (no tag) is rejected with error "image must include a tag or digest"
- Memory request `512Mi` with limit `256Mi` is rejected with error about request exceeding limit
- Default deny ingress policy for namespace `production` produces a NetworkPolicy that selects all pods and has empty ingress rules
- A ConfigMap with 2 MiB of data is rejected with error about exceeding the 1 MiB limit
- A Secret manifest has values base64-encoded in the YAML output

## Acceptance Criteria

- Deployment manifests include correct resource requests/limits, probes, and security context
- Image names without tags or digests are rejected
- Resource validation catches requests exceeding limits with specific messages
- Security context enforces `runAsNonRoot`, `readOnlyRootFilesystem`, drop all capabilities
- NetworkPolicies correctly implement deny-all ingress, namespace-based allow rules, and port restrictions
- Egress rules block metadata service CIDR
- ConfigMaps validate size limits and key naming conventions
- Secrets produce base64-encoded values in YAML output
- All manifests have correct apiVersion, kind, and standard Kubernetes labels
- Tests cover valid manifests, validation errors, edge cases, and YAML output correctness
