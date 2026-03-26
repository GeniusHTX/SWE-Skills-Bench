# Task: Add Linkerd mTLS Verification Example

## Background

Add a complete mTLS (mutual TLS) verification example for Linkerd2, demonstrating how to validate that service-to-service communication is encrypted and identities are properly verified within the mesh.

## Files to Create/Modify

- `examples/mtls-demo/deployments.yaml` - Sample client and server deployments with Linkerd annotations
- `examples/mtls-demo/service.yaml` - Kubernetes Service definitions
- `examples/mtls-demo/server-policy.yaml` - Linkerd Server and ServerAuthorization CRDs
- `examples/mtls-demo/README.md` - Setup documentation
- `bin/check-mtls-demo.sh` - Verification script

## Requirements

### Kubernetes Manifests
- Client deployment with `linkerd.io/inject: enabled` annotation
- Server deployment with `linkerd.io/inject: enabled` annotation
- Service exposing the server

### Server Policy (server-policy.yaml)
- `Server` CRD selecting the server pods
- `ServerAuthorization` CRD requiring mTLS identity
- Restrict access to only the client's ServiceAccount identity

### Verification Script (bin/check-mtls-demo.sh)
- Validate all YAML files are syntactically valid
- Check that Server and ServerAuthorization resources are present
- Verify the `linkerd.io/inject` annotation exists on both deployments
- Confirm the ServerAuthorization references a valid mTLS identity

## Acceptance Criteria

- `kubectl apply --dry-run=client -f examples/mtls-demo/` succeeds
- `bash bin/check-mtls-demo.sh` passes all checks
- Server policy enforces mTLS identity verification
