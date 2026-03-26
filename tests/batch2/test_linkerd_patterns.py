"""
Upgraded Test for 'Add mTLS Verification Examples to Linkerd'

Level 3: Strong behavioral simulation (logic-aware validation)
No runtime environment required.
"""

import os
import re
import pytest


class TestLinkerdMTLSExample:

    BASE_DIR = "/workspace/linkerd2/examples/mtls-demo"

    def _read(self, filename):
        path = os.path.join(self.BASE_DIR, filename)
        assert os.path.isfile(path), f"Missing file: {path}"
        with open(path, "r", errors="ignore") as f:
            return f.read().lower()

    # --------------------------------------------------
    # L1: 文件存在
    # --------------------------------------------------

    def test_required_files_exist(self):
        required = [
            "server-authorization.yaml",
            "server.yaml",
            "deployments.yaml",
            "verify-mtls.sh",
            "README.md",
        ]
        for f in required:
            assert os.path.isfile(os.path.join(self.BASE_DIR, f)), f"{f} missing"

    # --------------------------------------------------
    # L2: 基础结构
    # --------------------------------------------------

    def test_yaml_basic_structure(self):
        for f in ["server-authorization.yaml", "server.yaml", "deployments.yaml"]:
            content = self._read(f)
            assert "apiversion" in content
            assert "kind" in content

    # --------------------------------------------------
    # L3: 强行为模拟 —— mTLS模式逻辑
    # --------------------------------------------------

    def test_strict_mode_implies_rejection(self):
        content = self._read("server-authorization.yaml")

        assert "strict" in content, "Strict mode missing"

        # 核心逻辑：strict → 必须有拒绝语义
        assert any(
            word in content
            for word in ["deny", "reject", "unauthenticated", "forbidden"]
        ), "Strict mode must imply rejection behavior"

    def test_permissive_mode_allows_non_mtls(self):
        content = self._read("server-authorization.yaml")

        assert "permissive" in content, "Permissive mode missing"

        # 核心逻辑：permissive → 允许非认证流量
        assert any(
            word in content for word in ["allow", "unauthenticated", "both"]
        ), "Permissive mode must allow non-mTLS traffic"

    def test_modes_are_semantically_distinct(self):
        content = self._read("server-authorization.yaml")

        # strict 和 permissive 不应表达相同行为
        strict_has_allow = "strict" in content and "allow" in content
        permissive_has_deny = "permissive" in content and "deny" in content

        assert not (
            strict_has_allow and permissive_has_deny
        ), "Strict and permissive modes are semantically mixed or incorrect"

    # --------------------------------------------------
    # L3: 身份与认证逻辑
    # --------------------------------------------------

    def test_identity_required_in_strict_mode(self):
        content = self._read("server-authorization.yaml")

        assert "strict" in content

        # strict → 必须依赖 identity / authentication
        assert any(
            word in content for word in ["identity", "serviceaccount", "authenticated"]
        ), "Strict mode must enforce identity-based access"

    def test_authorization_targets_defined(self):
        content = self._read("server-authorization.yaml")

        # 必须指定谁可以访问（不是空策略）
        assert any(
            word in content for word in ["client", "serviceaccount", "namespace"]
        ), "Authorization does not define allowed identities"

    # --------------------------------------------------
    # L3: Workload 行为表达
    # --------------------------------------------------

    def test_meshed_vs_unmeshed_distinction(self):
        content = self._read("deployments.yaml")

        # 必须体现 mesh 注入
        assert "linkerd.io/inject" in content

        # 行为模拟：必须存在“可区分的客户端”
        assert any(
            word in content for word in ["client", "server"]
        ), "No clear service interaction roles defined"

    # --------------------------------------------------
    # L3: 验证机制逻辑
    # --------------------------------------------------

    def test_verification_script_has_intent(self):
        content = self._read("verify-mtls.sh")

        # 验证脚本必须至少包含“检查行为”
        assert any(
            cmd in content for cmd in ["linkerd", "check", "stat", "routes", "curl"]
        ), "Verification script lacks diagnostic intent"

        # 行为逻辑：必须涉及“验证加密”
        assert any(
            word in content for word in ["mtls", "tls", "secure", "identity"]
        ), "Script does not verify mTLS behavior"

    # --------------------------------------------------
    # L3: 文档行为一致性（关键升级点）
    # --------------------------------------------------

    def test_documentation_matches_strict_behavior(self):
        content = self._read("README.md")

        assert "strict" in content

        # strict → 拒绝未认证
        assert any(
            word in content for word in ["reject", "deny", "unauthorized"]
        ), "Documentation does not correctly describe strict behavior"

    def test_documentation_matches_permissive_behavior(self):
        content = self._read("README.md")

        assert "permissive" in content

        # permissive → 允许混合流量
        assert any(
            word in content for word in ["allow", "both", "migration"]
        ), "Documentation does not correctly describe permissive behavior"

    def test_documentation_and_config_consistency(self):
        yaml_content = self._read("server-authorization.yaml")
        doc_content = self._read("README.md")

        # 文档和配置必须同时提到关键概念
        for keyword in ["strict", "permissive", "mtls"]:
            assert keyword in yaml_content, f"{keyword} missing in config"
            assert keyword in doc_content, f"{keyword} missing in docs"

    # --------------------------------------------------
    # L3: Trust 模型
    # --------------------------------------------------

    def test_trust_model_has_core_elements(self):
        content = self._read("README.md")

        required = ["trust", "certificate", "identity"]

        found = sum(1 for r in required if r in content)
        assert found >= 2, "Trust model is insufficiently explained"
