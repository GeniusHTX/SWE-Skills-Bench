# Task: Add mTLS Verification Examples to Linkerd

## Background

Linkerd (https://github.com/linkerd/linkerd2) is a lightweight Kubernetes service mesh. New example configurations are needed that demonstrate mutual TLS (mTLS) verification patterns, showing how to configure service-to-service authentication policies and verify that traffic between meshed services is encrypted.

## Files to Create

- `examples/mtls-demo/server-authorization.yaml` — ServerAuthorization resources for strict and permissive mTLS modes
- `examples/mtls-demo/server.yaml` — Server resource definitions for mTLS-enabled services
- `examples/mtls-demo/deployments.yaml` — Example workload Deployments for demonstrating mTLS behavior
- `examples/mtls-demo/verify-mtls.sh` — Script to verify mTLS status between meshed services
- `examples/mtls-demo/README.md` — Documentation explaining the trust hierarchy and verification steps

## Requirements

### mTLS Configuration

- Define ServiceProfile or Server/ServerAuthorization resources that enforce mTLS between specific services
- Include example policies for both permissive mode (allow unauthenticated alongside mTLS) and strict mode (require mTLS only)

### Verification

- Provide a verification script or commands that check whether mTLS is active between services
- Include example workload definitions (deployments) that can be used to demonstrate the mTLS behavior

### Documentation

- Explain the trust hierarchy and certificate management approach
- Document how to verify mTLS status using Linkerd's diagnostic tools

### Build

- All Go source files must compile as part of the Linkerd project
- YAML manifests must be syntactically valid

## Expected Functionality

- Deploying the example manifests configures mTLS between the sample services
- Strict mode rejects unauthenticated traffic
- Permissive mode allows both mTLS and plain connections during migration
- Verification commands confirm encryption status

## Acceptance Criteria

- The example demonstrates both permissive and strict mTLS authorization behavior for meshed services.
- Strict mode blocks unauthorized traffic while permissive mode allows a migration path that still admits non-mTLS traffic.
- The included workloads and policy resources are sufficient to understand how the authorization model is applied.
- Verification steps or scripts can confirm whether traffic is encrypted and whether the expected policy is active.
- The documentation explains the trust and certificate assumptions well enough for a reader to follow the example.
