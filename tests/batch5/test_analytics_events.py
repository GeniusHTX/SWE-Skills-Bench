"""
Test for 'analytics-events' skill — Metabase Dashboard Analytics Events
Validates TypeScript analytics event interfaces, hooks, and tracking
for dashboard resize, share, and related interactions.
"""

import os
import re

import pytest


class TestAnalyticsEvents:
    """Verify Metabase dashboard analytics event implementation."""

    REPO_DIR = "/workspace/metabase"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_analytics_source_files_exist(self):
        """Verify at least 3 analytics TS files exist."""
        frontend = os.path.join(self.REPO_DIR, "frontend", "src")
        if not os.path.isdir(frontend):
            pytest.skip("frontend/src directory not found")
        ts_analytics = []
        for dirpath, _, fnames in os.walk(frontend):
            for f in fnames:
                if (
                    f.endswith(".ts") or f.endswith(".tsx")
                ) and "analytics" in f.lower():
                    ts_analytics.append(os.path.join(dirpath, f))
        assert (
            len(ts_analytics) >= 3
        ), f"Expected ≥3 analytics TS files, found {len(ts_analytics)}"

    def test_analytics_spec_file_exists(self):
        """Verify at least one analytics test/spec file exists."""
        frontend = os.path.join(self.REPO_DIR, "frontend")
        if not os.path.isdir(frontend):
            pytest.skip("frontend/ not found")
        found = False
        for dirpath, _, fnames in os.walk(frontend):
            for f in fnames:
                if (
                    "analytics" in f.lower()
                    and ("spec" in f.lower() or "test" in f.lower())
                    and (f.endswith(".ts") or f.endswith(".tsx"))
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No analytics spec/test file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_event_interfaces_defined(self):
        """Verify at least 4 TypeScript event interfaces are defined."""
        files = self._find_analytics_files()
        assert files, "No analytics files found"
        interface_count = 0
        for fpath in files:
            content = self._read(fpath)
            interface_count += len(re.findall(r"\binterface\s+\w+", content))
            interface_count += len(re.findall(r"\btype\s+\w+\s*=", content))
        assert (
            interface_count >= 4
        ), f"Expected ≥4 event type definitions, found {interface_count}"

    def test_use_dashboard_analytics_hook(self):
        """Verify a useDashboardAnalytics hook is defined."""
        files = self._find_analytics_files()
        assert files, "No analytics files found"
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"(useDashboardAnalytics|use\w*Analytics)", content):
                return  # pass
        pytest.fail("No useDashboardAnalytics hook found")

    def test_resize_event_has_size_fields(self):
        """Verify resize event includes old_size and new_size fields."""
        files = self._find_analytics_files()
        assert files, "No analytics files found"
        for fpath in files:
            content = self._read(fpath)
            if "old_size" in content and "new_size" in content:
                return
            if "oldSize" in content and "newSize" in content:
                return
        pytest.fail("No resize event with old_size/new_size fields found")

    def test_share_event_has_share_type(self):
        """Verify share event includes a share_type field."""
        files = self._find_analytics_files()
        assert files, "No analytics files found"
        for fpath in files:
            content = self._read(fpath)
            if "share_type" in content or "shareType" in content:
                return
        pytest.fail("No share event with share_type field found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_analytics_files_valid_typescript_syntax(self):
        """Verify TS analytics files have balanced braces."""
        files = self._find_analytics_files()
        assert files, "No analytics files found"
        for fpath in files:
            content = self._read(fpath)
            opens = content.count("{")
            closes = content.count("}")
            assert opens == closes, f"Unbalanced braces in {os.path.basename(fpath)}"

    def test_analytics_files_have_exports(self):
        """Verify analytics modules export their interfaces/functions."""
        files = self._find_analytics_files()
        assert files, "No analytics files found"
        exported = False
        for fpath in files:
            content = self._read(fpath)
            if "export " in content:
                exported = True
                break
        assert exported, "No analytics file exports any symbol"

    def test_spec_file_has_test_cases(self):
        """Verify spec file contains actual test cases."""
        frontend = os.path.join(self.REPO_DIR, "frontend")
        if not os.path.isdir(frontend):
            pytest.skip("frontend/ not found")
        for dirpath, _, fnames in os.walk(frontend):
            for f in fnames:
                if "analytics" in f.lower() and (
                    "spec" in f.lower() or "test" in f.lower()
                ):
                    fpath = os.path.join(dirpath, f)
                    content = self._read(fpath)
                    if re.search(r"\b(it|test|describe)\s*\(", content):
                        return  # pass
        pytest.fail("No test cases found in analytics spec file")

    def test_resize_noop_guard(self):
        """Verify resize logic guards against no-op (same size) events."""
        files = self._find_analytics_files()
        assert files, "No analytics files found"
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"old.?size.*===?\s*new.?size|no.?op|same.?size", content, re.IGNORECASE
            ):
                return
            if re.search(r"if\s*\(.*old.*new.*\)", content):
                return
        # Also check spec files
        for dirpath, _, fnames in os.walk(os.path.join(self.REPO_DIR, "frontend")):
            for f in fnames:
                if "analytics" in f.lower() and (
                    "spec" in f.lower() or "test" in f.lower()
                ):
                    content = self._read(os.path.join(dirpath, f))
                    if "no" in content.lower() and "op" in content.lower():
                        return
                    if "same" in content.lower() and "size" in content.lower():
                        return
        pytest.fail("No resize no-op guard found in analytics code or tests")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_analytics_files(self):
        frontend = os.path.join(self.REPO_DIR, "frontend", "src")
        if not os.path.isdir(frontend):
            return []
        results = []
        for dirpath, _, fnames in os.walk(frontend):
            for f in fnames:
                if (
                    f.endswith(".ts") or f.endswith(".tsx")
                ) and "analytics" in f.lower():
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
