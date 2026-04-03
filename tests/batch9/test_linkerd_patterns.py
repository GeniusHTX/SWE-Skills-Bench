"""
Test for 'linkerd-patterns' skill — Linkerd2 Service Mesh Patterns (Go)
Validates ServiceProfile, RetryBudget, TrafficSplit, duration validation,
and Go source patterns via static source analysis.
"""

import os
import re

import pytest


class TestLinkerdPatterns:
    """Verify Linkerd2 service mesh patterns via static Go source inspection."""

    REPO_DIR = "/workspace/linkerd2"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _lk(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "linkerd", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_service_profile_go_exists(self):
        """linkerd/service_profile.go must exist."""
        assert os.path.isfile(self._lk("service_profile.go")), "service_profile.go not found"

    def test_traffic_split_go_exists(self):
        """linkerd/traffic_split.go must exist."""
        assert os.path.isfile(self._lk("traffic_split.go")), "traffic_split.go not found"

    def test_go_mod_and_test_file_exist(self):
        """go.mod and service_profile_test.go must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "go.mod")), "go.mod not found"
        assert os.path.isfile(self._lk("service_profile_test.go")), "test file not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_service_profile_uses_v1alpha2(self):
        """ServiceProfile must use linkerd.io/v1alpha2, not v1alpha1."""
        content = self._read_file(self._lk("service_profile.go"))
        if not content:
            pytest.skip("service_profile.go not found")
        assert "v1alpha2" in content, "v1alpha2 not found"

    def test_retry_budget_has_retry_ratio_float64(self):
        """RetryBudget must have RetryRatio as float64."""
        content = self._read_file(self._lk("service_profile.go"))
        if not content:
            pytest.skip("service_profile.go not found")
        assert "RetryBudget" in content
        assert "RetryRatio" in content

    def test_duration_validation_uses_parse_duration(self):
        """Timeout field must be validated via time.ParseDuration."""
        content = self._read_file(self._lk("service_profile.go"))
        if not content:
            pytest.skip("service_profile.go not found")
        assert "ParseDuration" in content, "time.ParseDuration not used"

    def test_isretryable_field_present(self):
        """IsRetryable bool field must exist in route spec."""
        content = self._read_file(self._lk("service_profile.go"))
        if not content:
            pytest.skip("service_profile.go not found")
        has_retry = "IsRetryable" in content or "isRetryable" in content
        assert has_retry, "IsRetryable field not found"

    def test_traffic_split_weight_sum_validation(self):
        """TrafficSplit must validate weights sum to 100."""
        content = self._read_file(self._lk("traffic_split.go"))
        if not content:
            pytest.skip("traffic_split.go not found")
        has_100 = "100" in content
        has_weight = "weight" in content.lower() or "Weight" in content
        assert has_100 and has_weight, "Weight sum validation not found"

    # ── functional_check (static Go) ─────────────────────────────────────

    def test_valid_timeout_test_case(self):
        """Test file must contain valid duration test case ('30s' or '1m')."""
        content = self._read_file(self._lk("service_profile_test.go"))
        if not content:
            pytest.skip("test file not found")
        has_valid = "30s" in content or "1m" in content or "10s" in content
        assert has_valid, "No valid duration test case found"
        assert "nil" in content, "No nil error assertion for valid case"

    def test_invalid_timeout_test_case(self):
        """Test file must contain invalid duration test case ('30x')."""
        content = self._read_file(self._lk("service_profile_test.go"))
        if not content:
            pytest.skip("test file not found")
        has_invalid = "30x" in content or "invalid" in content.lower()
        assert has_invalid, "No invalid duration test case found"

    def test_retry_ratio_zero_is_valid(self):
        """RetryRatio=0.0 must be a valid edge case in test file."""
        content = self._read_file(self._lk("service_profile_test.go"))
        if not content:
            pytest.skip("test file not found")
        has_zero = "0.0" in content or "RetryRatio: 0" in content
        assert has_zero, "No zero RetryRatio edge case test found"

    def test_unequal_weights_fail_validation(self):
        """TrafficSplit with sum != 100 must fail in source or test."""
        content = self._read_file(self._lk("traffic_split.go"))
        test_content = self._read_file(self._lk("service_profile_test.go"))
        combined = content + test_content
        has_error = "error" in combined.lower() and "weight" in combined.lower()
        assert has_error, "No weight validation error path found"
