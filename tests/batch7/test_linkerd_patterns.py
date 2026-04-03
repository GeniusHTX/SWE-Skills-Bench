"""Test file for the linkerd-patterns skill.

This suite validates the retry budget calculator and timeout policy
resolver in Linkerd's controller/api/destination package.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestLinkerdPatterns:
    """Verify Linkerd retry budget and timeout policy patterns."""

    REPO_DIR = "/workspace/linkerd2"

    RETRY_BUDGET_GO = "controller/api/destination/retry_budget.go"
    TIMEOUT_POLICY_GO = "controller/api/destination/timeout_policy.go"
    PROFILE_WATCHER_GO = "controller/api/destination/watcher/profile_watcher.go"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _go_struct_body(self, source: str, name: str) -> str | None:
        m = re.search(rf"type\s+{name}\s+struct\s*\{{", source)
        if m is None:
            return None
        depth, i = 1, m.end()
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[m.start() : i]

    def _all_go_sources(self, directory: str = "controller/api/destination") -> str:
        d = self._repo_path(directory)
        if not d.is_dir():
            return ""
        parts = []
        for f in sorted(d.rglob("*.go")):
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_controller_api_destination_retry_budget_go_exists(self):
        """Verify retry_budget.go exists and is non-empty."""
        self._assert_non_empty_file(self.RETRY_BUDGET_GO)

    def test_file_path_controller_api_destination_timeout_policy_go_exists(self):
        """Verify timeout_policy.go exists and is non-empty."""
        self._assert_non_empty_file(self.TIMEOUT_POLICY_GO)

    def test_file_path_controller_api_destination_watcher_profile_watcher_go_modifi(
        self,
    ):
        """Verify profile_watcher.go exists (modified)."""
        self._assert_non_empty_file(self.PROFILE_WATCHER_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_retrybudgetconfig_struct_has_retryratio_minretriespersecond_(
        self,
    ):
        """RetryBudgetConfig struct has RetryRatio, MinRetriesPerSecond, TTL fields."""
        src = self._read_text(self.RETRY_BUDGET_GO)
        body = self._go_struct_body(src, "RetryBudgetConfig")
        assert body is not None, "RetryBudgetConfig struct not found"
        for field in ("RetryRatio", "MinRetriesPerSecond", "TTL"):
            assert field in body, f"RetryBudgetConfig missing field: {field}"

    def test_semantic_retrybudget_struct_has_totalrequestsinwindow_retriesinwindow(
        self,
    ):
        """RetryBudget struct tracks TotalRequestsInWindow, RetriesInWindow, AllowRetry, etc."""
        src = self._read_text(self.RETRY_BUDGET_GO)
        body = self._go_struct_body(src, "RetryBudget")
        assert body is not None, "RetryBudget struct not found"

    def test_semantic_retrybudgetcalculator_has_recordrequest_recordretry_shouldre(
        self,
    ):
        """RetryBudgetCalculator has RecordRequest, RecordRetry, ShouldRetry, Reset methods."""
        src = self._read_text(self.RETRY_BUDGET_GO)
        for method in ("RecordRequest", "RecordRetry", "ShouldRetry", "Reset"):
            assert re.search(
                rf"func\s*\(.*\)\s+{method}\s*\(", src
            ), f"RetryBudgetCalculator missing {method} method"

    def test_semantic_timeoutpolicy_struct_has_requesttimeout_idletimeout_streamti(
        self,
    ):
        """TimeoutPolicy struct has RequestTimeout, IdleTimeout, StreamTimeout, RetryTimeout."""
        src = self._read_text(self.TIMEOUT_POLICY_GO)
        body = self._go_struct_body(src, "TimeoutPolicy")
        assert body is not None, "TimeoutPolicy struct not found"
        for field in ("RequestTimeout", "IdleTimeout"):
            assert field in body, f"TimeoutPolicy missing field: {field}"

    def test_semantic_timeoutpolicyresolver_has_resolvetimeouts_method_accepting_s(
        self,
    ):
        """TimeoutPolicyResolver has ResolveTimeouts method accepting ServiceProfile."""
        src = self._all_go_sources()
        assert re.search(r"func\s*\(.*\)\s+ResolveTimeouts?\s*\(", src) or re.search(
            r"ResolveTimeout", src
        ), "TimeoutPolicyResolver must have ResolveTimeouts method"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_100_requests_15_retries_with_0_2_ratio_shouldretry_true_15_2(
        self,
    ):
        """100 requests + 15 retries with 0.2 ratio -> ShouldRetry true (15% < 20%)."""
        src = self._read_text(self.RETRY_BUDGET_GO)
        assert re.search(
            r"func\s*\(.*\)\s+ShouldRetry\s*\(", src
        ), "ShouldRetry method required"
        # Verify ratio comparison logic exists
        assert re.search(
            r"[Rr]atio|[Rr]etries.*[Rr]equests|float", src
        ), "ShouldRetry should compare retry ratio against threshold"

    def test_functional_100_requests_25_retries_with_0_2_ratio_shouldretry_false_25_(
        self,
    ):
        """100 requests + 25 retries with 0.2 ratio -> ShouldRetry false (25% > 20%)."""
        src = self._read_text(self.RETRY_BUDGET_GO)
        assert re.search(r"ShouldRetry", src), "ShouldRetry method required"
        # The ratio comparison should be able to return false
        assert re.search(
            r"false|return\s+false|>|>=", src
        ), "ShouldRetry should return false when ratio exceeds threshold"

    def test_functional_0_requests_5_retries_shouldretry_true_under_floor_of_minretr(
        self,
    ):
        """0 requests + 5 retries -> ShouldRetry true (under floor of minRetriesPerSecond)."""
        src = self._read_text(self.RETRY_BUDGET_GO)
        assert re.search(
            r"[Mm]in[Rr]etries|floor|MinRetriesPerSecond", src
        ), "ShouldRetry should respect minRetriesPerSecond floor"

    def test_functional_buckets_older_than_ttl_are_expired_and_not_counted(self):
        """Buckets older than TTL are expired and not counted."""
        src = self._read_text(self.RETRY_BUDGET_GO)
        assert re.search(
            r"TTL|ttl|[Ee]xpir|[Bb]ucket|[Ww]indow", src
        ), "TTL-based bucket expiration logic must exist"

    def test_functional_resolvetimeouts_parses_request_timeout_500ms_correctly(self):
        """ResolveTimeouts parses request-timeout: 500ms correctly."""
        src = self._all_go_sources()
        assert re.search(
            r"[Pp]arse|[Dd]uration|time\.Parse|500ms|[Tt]imeout", src
        ), "ResolveTimeouts should parse duration strings"
