# Task: Add Flux GitOps Demo Configuration and Verification Script

## Background
   在 Flux CD 仓库中新增一个完整的 GitOps 配置示例，展示 Flux 部署清单和 Kustomize Overlay 结构，并编写一个验证脚本来检查配置的正确性。

## Files to Create/Modify
   - `hack/gitops-demo/clusters/dev/flux-system/gotk-components.yaml` (Flux bootstrap 组件)
   - `hack/gitops-demo/clusters/dev/flux-system/kustomization.yaml` (Flux kustomization)
   - `hack/gitops-demo/apps/base/deployment.yaml` (基础 Deployment)
   - `hack/gitops-demo/apps/base/service.yaml` (基础 Service)
   - `hack/gitops-demo/apps/base/kustomization.yaml` (基础 kustomization)
   - `hack/gitops-demo/apps/overlays/dev/kustomization.yaml` (dev overlay)
   - `hack/gitops-demo/apps/overlays/dev/patch-replicas.yaml` (replicas patch)
   - `hack/verify-gitops-demo.sh` (验证脚本)

## Requirements

   ### 目录结构
   ```
   hack/
   ├── gitops-demo/
   │   ├── clusters/
   │   │   └── dev/
   │   │       └── flux-system/
   │   │           ├── gotk-components.yaml
   │   │           └── kustomization.yaml
   │   └── apps/
   │       ├── base/
   │       │   ├── deployment.yaml
   │       │   ├── service.yaml
   │       │   └── kustomization.yaml
   │       └── overlays/
   │           └── dev/
   │               ├── kustomization.yaml
   │               └── patch-replicas.yaml
   └── verify-gitops-demo.sh
   ```

   ### Kustomize 配置要求
   - base/deployment.yaml: 包含完整的 Kubernetes Deployment (apiVersion, kind, metadata.name, spec.replicas, spec.template)
   - base/service.yaml: 包含完整的 Kubernetes Service 暴露端口
   - base/kustomization.yaml: 引用 deployment.yaml 和 service.yaml
   - overlays/dev/kustomization.yaml: 基于 ../../base，应用 patch-replicas.yaml 补丁
   - overlays/dev/patch-replicas.yaml: Strategic Merge Patch，将 replicas 修改为 dev 环境值

   ### 验证脚本要求 (hack/verify-gitops-demo.sh)
   - 脚本必须可执行 (`chmod +x`)
   - 检查 `hack/gitops-demo/` 下所有必要文件存在
   - 使用 `kustomize build hack/gitops-demo/apps/overlays/dev` 验证 Kustomize 构建成功
   - 验证生成的 manifest 包含 Deployment 和 Service 资源
   - 验证 overlay patch 已正确应用
   - 所有检查通过时以退出码 0 退出，任何检查失败以非零退出码退出

## Acceptance Criteria
   - `kustomize build hack/gitops-demo/apps/overlays/dev` 退出码为 0
   - 生成的 manifest 包含 deployment 和 service
   - Overlay patches 正确应用
   - `bash hack/verify-gitops-demo.sh` 退出码为 0
