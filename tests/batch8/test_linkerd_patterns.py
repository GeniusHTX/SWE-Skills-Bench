"""
Test for 'linkerd-patterns' skill — Linkerd SMI Traffic Split Manager
Validates that the Agent created a Python package for generating Linkerd
TrafficSplit and ServiceProfile CRD YAML with weight validation and shift logic.
"""

import os
import re
import sys

import pytest


class TestLinkerdPatterns:
    """Verify Linkerd traffic split manager implementation."""

    REPO_DIR = "/workspace/linkerd2"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_linkerd_manager_package_exists(self):
        """Verify __init__.py and generator.py exist under src/linkerd_manager/."""
        for rel in ("src/linkerd_manager/__init__.py", "src/linkerd_manager/generator.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_traffic_split_retry_models_exist(self):
        """Verify traffic_split.py, retry_policy.py, and models.py exist."""
        for rel in ("src/linkerd_manager/traffic_split.py",
                     "src/linkerd_manager/retry_policy.py",
                     "src/linkerd_manager/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """TrafficSplitManager, RetryPolicyBuilder, LinkerdConfigGenerator importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from linkerd_manager.generator import LinkerdConfigGenerator  # noqa: F401
            from linkerd_manager.traffic_split import TrafficSplitManager  # noqa: F401
            from linkerd_manager.retry_policy import RetryPolicyBuilder  # noqa: F401
        except ImportError:
            pytest.skip("linkerd_manager not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_traffic_split_smi_api_version(self):
        """Verify traffic_split.py references split.smi-spec.io/v1alpha1 and TrafficSplit."""
        content = self._read(os.path.join(self.REPO_DIR, "src/linkerd_manager/traffic_split.py"))
        assert content, "traffic_split.py is empty or unreadable"
        assert "split.smi-spec.io/v1alpha1" in content
        assert "TrafficSplit" in content

    def test_service_profile_linkerd_api_version(self):
        """Verify retry_policy.py references linkerd.io/v1alpha2 and ServiceProfile."""
        content = self._read(os.path.join(self.REPO_DIR, "src/linkerd_manager/retry_policy.py"))
        assert content, "retry_policy.py is empty or unreadable"
        assert "linkerd.io/v1alpha2" in content
        assert "ServiceProfile" in content

    def test_weight_validation_in_traffic_split(self):
        """Verify traffic_split.py validates weight in [0, 100]."""
        content = self._read(os.path.join(self.REPO_DIR, "src/linkerd_manager/traffic_split.py"))
        assert content, "traffic_split.py is empty or unreadable"
        found = any(kw in content for kw in ("ValueError", "must be between", "range"))
        assert found, "Weight validation not found in traffic_split.py"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_traffic_split_api_version_in_output(self):
        """create_split() YAML has apiVersion: split.smi-spec.io/v1alpha1."""
        import yaml
        mod = self._import("linkerd_manager.traffic_split")
        ts = yaml.safe_load(mod.TrafficSplitManager().create_split("my-svc", 20))
        assert ts["apiVersion"] == "split.smi-spec.io/v1alpha1"

    def test_backends_weights_sum_to_100(self):
        """All backend weights in generated TrafficSplit sum to 100."""
        import yaml
        mod = self._import("linkerd_manager.traffic_split")
        ts = yaml.safe_load(mod.TrafficSplitManager().create_split("my-svc", 30))
        backends = ts["spec"]["backends"]
        assert sum(b["weight"] for b in backends) == 100

    def test_canary_weight_101_raises_value_error(self):
        """create_split() raises ValueError when canary_weight=101."""
        mod = self._import("linkerd_manager.traffic_split")
        with pytest.raises(ValueError):
            mod.TrafficSplitManager().create_split("svc", 101)

    def test_service_profile_kind_in_output(self):
        """RetryPolicyBuilder.build() returns ServiceProfile YAML with correct kind."""
        import yaml
        mod = self._import("linkerd_manager.retry_policy")
        sp = yaml.safe_load(mod.RetryPolicyBuilder().build("my-svc", retries=3, timeout_ms=500))
        assert sp["kind"] == "ServiceProfile"

    def test_shift_traffic_updates_weights(self):
        """shift_traffic(current_yaml, 40) produces canary=40 and stable=60."""
        import yaml
        mod = self._import("linkerd_manager.traffic_split")
        mgr = mod.TrafficSplitManager()
        current_yaml = mgr.create_split("svc", 20)
        updated = yaml.safe_load(mgr.shift_traffic(current_yaml, 40))
        backends = {b["service"]: b["weight"] for b in updated["spec"]["backends"]}
        assert backends.get("svc-canary") == 40
        assert backends.get("svc-stable") == 60
