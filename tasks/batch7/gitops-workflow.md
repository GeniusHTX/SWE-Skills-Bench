# Task: Implement a Multi-Tenant GitOps Reconciliation Controller in Flux2

## Background

Flux2 (https://github.com/fluxcd/flux2) is a GitOps toolkit for Kubernetes. The task is to implement a multi-tenant reconciliation controller that manages `TenantConfig` custom resources, each representing a tenant's GitOps configuration with a dedicated Git source, Kustomization, and namespace. The controller reconciles tenant configurations by creating and managing the underlying Flux resources.

## Files to Create/Modify

- `internal/controller/tenant_controller.go` (create) — `TenantReconciler` that watches `TenantConfig` CRs and reconciles underlying Flux `GitRepository` and `Kustomization` resources
- `api/v1alpha1/tenantconfig_types.go` (create) — CRD type definitions for `TenantConfig`
- `api/v1alpha1/zz_generated.deepcopy.go` (modify or create) — DeepCopy methods for the new types
- `internal/controller/tenant_controller_test.go` (create) — Unit tests for the reconciliation logic
- `api/v1alpha1/tenantconfig_types_test.go` (create) — Unit tests for type validation

## Requirements

### CRD Types (`tenantconfig_types.go`)

#### `TenantConfig` spec
```go
type TenantConfigSpec struct {
    // TenantName is the display name of the tenant
    TenantName string `json:"tenantName"`

    // GitSource configures the Git repository for this tenant
    GitSource GitSourceSpec `json:"gitSource"`

    // TargetNamespace is the namespace where tenant resources are deployed
    TargetNamespace string `json:"targetNamespace"`

    // Path is the directory in the Git repo containing the tenant's manifests
    Path string `json:"path"`

    // Interval is the reconciliation interval (e.g., "5m")
    Interval metav1.Duration `json:"interval"`

    // Suspend pauses reconciliation when true
    Suspend bool `json:"suspend,omitempty"`

    // ServiceAccountName is the SA used for impersonation in the target namespace
    ServiceAccountName string `json:"serviceAccountName,omitempty"`

    // ResourceQuota defines resource limits for the tenant namespace
    ResourceQuota *ResourceQuotaSpec `json:"resourceQuota,omitempty"`
}

type GitSourceSpec struct {
    URL    string `json:"url"`
    Branch string `json:"branch"`
    // SecretRef references a Secret containing Git credentials
    SecretRef *corev1.LocalObjectReference `json:"secretRef,omitempty"`
}

type ResourceQuotaSpec struct {
    CPULimit    string `json:"cpuLimit,omitempty"`    // e.g., "4"
    MemoryLimit string `json:"memoryLimit,omitempty"` // e.g., "8Gi"
    PodCount    int32  `json:"podCount,omitempty"`    // e.g., 50
}
```

#### `TenantConfig` status
```go
type TenantConfigStatus struct {
    // Conditions holds the conditions for the TenantConfig
    Conditions []metav1.Condition `json:"conditions,omitempty"`

    // NamespaceReady indicates the target namespace exists
    NamespaceReady bool `json:"namespaceReady,omitempty"`

    // GitRepositoryReady indicates the Flux GitRepository is ready
    GitRepositoryReady bool `json:"gitRepositoryReady,omitempty"`

    // KustomizationReady indicates the Flux Kustomization is ready
    KustomizationReady bool `json:"kustomizationReady,omitempty"`

    // LastReconcileTime is the timestamp of the last successful reconciliation
    LastReconcileTime *metav1.Time `json:"lastReconcileTime,omitempty"`

    // ObservedGeneration is the last observed generation of the TenantConfig
    ObservedGeneration int64 `json:"observedGeneration,omitempty"`
}
```

### Reconciliation Controller (`tenant_controller.go`)

Implements `reconcile.Reconciler` interface.

#### `Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error)`

The reconciliation loop performs these steps in order:

1. **Fetch the TenantConfig** — Get the CR from the API server; if not found, return (deleted)
2. **Handle suspension** — If `spec.suspend` is true, set a `Suspended` condition and return without requeuing
3. **Ensure target namespace** — Create the namespace `spec.targetNamespace` if it doesn't exist; set owner reference to the `TenantConfig` so it's garbage collected on deletion; set `namespaceReady` status
4. **Apply resource quota** — If `spec.resourceQuota` is set, create or update a `ResourceQuota` in the target namespace with the specified limits
5. **Create/update GitRepository** — Create a Flux `GitRepository` CR in the same namespace as the `TenantConfig` with:
   - Name: `{tenantconfig-name}-source`
   - URL: `spec.gitSource.url`
   - Branch: `spec.gitSource.branch`
   - Interval: `spec.interval`
   - SecretRef: `spec.gitSource.secretRef` (if set)
   - Set owner reference to the `TenantConfig`
6. **Create/update Kustomization** — Create a Flux `Kustomization` CR with:
   - Name: `{tenantconfig-name}-sync`
   - SourceRef: pointing to the GitRepository created in step 5
   - Path: `spec.path`
   - TargetNamespace: `spec.targetNamespace`
   - Interval: `spec.interval`
   - ServiceAccountName: `spec.serviceAccountName` (if set)
   - Prune: `true`
   - Set owner reference to the `TenantConfig`
7. **Update status** — Set `gitRepositoryReady` and `kustomizationReady` based on the current conditions of the child resources; update `lastReconcileTime`; set `observedGeneration`
8. **Set ready condition** — If all sub-resources are ready, set a `Ready: True` condition; otherwise `Ready: False` with a message indicating which sub-resource is not ready
9. **Requeue** — Return `ctrl.Result{RequeueAfter: spec.interval.Duration}`

#### Deletion Handling

- Add a finalizer `tenantconfig.fluxcd.io/finalizer` on creation
- On deletion (DeletionTimestamp set):
  1. Delete the Kustomization CR
  2. Delete the GitRepository CR
  3. Delete the target namespace (only if the TenantConfig owns it)
  4. Remove the finalizer

#### Error Handling
- If namespace creation fails, set condition `NamespaceReady: False` with error message and requeue after 30 seconds
- If GitRepository or Kustomization creation fails, set the respective ready flag to false and requeue

### RBAC

The controller needs permissions:
- `TenantConfig`: get, list, watch, create, update, patch, delete
- `Namespace`: get, list, watch, create, delete
- `ResourceQuota`: get, list, watch, create, update, patch
- `GitRepository` (source.toolkit.fluxcd.io): get, list, watch, create, update, patch, delete
- `Kustomization` (kustomize.toolkit.fluxcd.io): get, list, watch, create, update, patch, delete

## Expected Functionality

- Creating a `TenantConfig` with `targetNamespace: "team-alpha"`, `gitSource.url: "https://github.com/org/team-alpha-config"`, `path: "./k8s"`:
  1. Creates namespace `team-alpha`
  2. Creates `GitRepository` `<name>-source` pointing to the repo/branch
  3. Creates `Kustomization` `<name>-sync` pointing to `./k8s` in the GitRepository
  4. Status shows all three ready flags as true

- Setting `suspend: true` stops reconciliation and sets the Suspended condition
- Deleting the `TenantConfig` cleans up the namespace, GitRepository, and Kustomization

## Acceptance Criteria

- `TenantConfig` CRD types compile and have proper JSON tags and DeepCopy methods
- Reconciler creates namespace, GitRepository, and Kustomization with correct owner references
- Resource quotas are applied to the target namespace when specified
- Status accurately reflects the readiness of each sub-resource
- Suspension stops reconciliation without deleting resources
- Deletion cleans up all owned resources via the finalizer
- Controller requeues at the configured interval
- All test cases cover: creation, update, suspension, deletion, and error scenarios
