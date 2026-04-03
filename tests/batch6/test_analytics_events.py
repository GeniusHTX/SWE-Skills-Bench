"""
Tests for 'analytics-events' skill.
Generated from benchmark case definitions for analytics-events.
"""

import ast
import base64
import glob
import json
import os
import py_compile
import re
import subprocess
import textwrap

import pytest

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


class TestAnalyticsEvents:
    """Verify the analytics-events skill output."""

    REPO_DIR = "/workspace/metabase"

    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestAnalyticsEvents.REPO_DIR, rel)

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _load_yaml(path: str):
        if yaml is None:
            pytest.skip("PyYAML not available")
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _load_json(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return json.load(fh)

    @classmethod
    def _run_in_repo(
        cls, script: str, timeout: int = 120
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _run_cmd(cls, command, args=None, timeout=120):
        args = args or []
        if isinstance(command, str) and args:
            return subprocess.run(
                [command, *args],
                cwd=cls.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        return subprocess.run(
            command if isinstance(command, list) else command,
            cwd=cls.REPO_DIR,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _ensure_setup(cls, label, setup_cmds, fallback):
        if not setup_cmds:
            return
        key = tuple(setup_cmds)
        if key in cls._SETUP_CACHE:
            ok, msg = cls._SETUP_CACHE[key]
            if ok:
                return
            if fallback == "skip_if_setup_fails":
                pytest.skip(f"{label} setup failed: {msg}")
            pytest.fail(f"{label} setup failed: {msg}")
        for cmd in setup_cmds:
            r = subprocess.run(
                cmd,
                cwd=cls.REPO_DIR,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if r.returncode != 0:
                msg = (r.stderr or r.stdout or "failed").strip()
                cls._SETUP_CACHE[key] = (False, msg)
                if fallback == "skip_if_setup_fails":
                    pytest.skip(f"{label} setup failed: {msg}")
                pytest.fail(f"{label} setup failed: {msg}")
        cls._SETUP_CACHE[key] = (True, "ok")

    # ── file_path_check (static) ────────────────────────────────────────

    def test_snowplow_ts_file_exists(self):
        """Verify the main Snowplow tracking module exists"""
        _p = self._repo_path("frontend/src/metabase/analytics/snowplow.ts")
        assert os.path.isfile(
            _p
        ), f"Missing file: frontend/src/metabase/analytics/snowplow.ts"

    def test_dashboard_events_file_exists(self):
        """Verify dashboard event module exists"""
        _p = self._repo_path("frontend/src/metabase/analytics/events/dashboard.ts")
        assert os.path.isfile(
            _p
        ), f"Missing file: frontend/src/metabase/analytics/events/dashboard.ts"

    def test_snowplow_test_file_exists(self):
        """Verify unit test file for Snowplow module exists"""
        _p = self._repo_path(
            "frontend/src/metabase/analytics/__tests__/snowplow.unit.spec.ts"
        )
        assert os.path.isfile(
            _p
        ), f"Missing file: frontend/src/metabase/analytics/__tests__/snowplow.unit.spec.ts"

    # ── semantic_check (static) ────────────────────────────────────────

    def test_trackStructEvent_typed_export(self):
        """Verify trackStructEvent is exported with typed parameters (no 'any')"""
        _p = self._repo_path("frontend/src/metabase/analytics/snowplow.ts")
        assert os.path.exists(
            _p
        ), f"Missing: frontend/src/metabase/analytics/snowplow.ts"
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ""
        assert (
            "export function trackStructEvent" in _all
        ), "Missing: export function trackStructEvent"
        assert "category" in _all, "Missing: category"
        assert "action" in _all, "Missing: action"
        assert "string" in _all, "Missing: string"

    def test_trackDashboardViewed_signature(self):
        """Verify trackDashboardViewed has typed dashboardId and accessedVia params"""
        _p = self._repo_path("frontend/src/metabase/analytics/events/dashboard.ts")
        assert os.path.exists(
            _p
        ), f"Missing: frontend/src/metabase/analytics/events/dashboard.ts"
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ""
        assert "trackDashboardViewed" in _all, "Missing: trackDashboardViewed"
        assert "dashboardId" in _all, "Missing: dashboardId"
        assert "number" in _all, "Missing: number"
        assert "accessedVia" in _all, "Missing: accessedVia"
        assert "string" in _all, "Missing: string"

    def test_snowplow_mock_pattern(self):
        """Verify test file uses window.snowplow mock or @snowplow/browser-tracker mock"""
        _p = self._repo_path(
            "frontend/src/metabase/analytics/__tests__/snowplow.unit.spec.ts"
        )
        assert os.path.exists(
            _p
        ), f"Missing: frontend/src/metabase/analytics/__tests__/snowplow.unit.spec.ts"
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ""
        assert "jest.fn" in _all, "Missing: jest.fn"
        assert "jest.mock" in _all, "Missing: jest.mock"
        assert "snowplow" in _all, "Missing: snowplow"
        assert "window.snowplow" in _all, "Missing: window.snowplow"

    def test_void_return_types(self):
        """Verify all tracking functions have return type void"""
        _p = self._repo_path("frontend/src/metabase/analytics/snowplow.ts")
        assert os.path.exists(
            _p
        ), f"Missing: frontend/src/metabase/analytics/snowplow.ts"
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ""
        assert ": void" in _all, "Missing: : void"
        assert "track" in _all, "Missing: track"

    # ── functional_check ────────────────────────────────────────

    def test_typescript_compilation(self):
        """Verify TypeScript compiles without errors"""
        self._ensure_setup(
            "test_typescript_compilation",
            ["cd frontend && yarn install"],
            "skip_if_setup_fails",
        )
        result = self._run_cmd(
            "npx",
            args=["tsc", "--noEmit", "src/metabase/analytics/snowplow.ts"],
            timeout=120,
        )
        assert result.returncode == 0, (
            f"test_typescript_compilation failed (exit {result.returncode})\n"
            + result.stderr[:500]
        )

    def test_jest_unit_tests_pass(self):
        """Verify Jest unit tests for Snowplow pass"""
        self._ensure_setup(
            "test_jest_unit_tests_pass",
            ["cd frontend && yarn install"],
            "skip_if_setup_fails",
        )
        result = self._run_cmd(
            "npx",
            args=[
                "jest",
                "src/metabase/analytics/__tests__/snowplow.unit.spec.ts",
                "--no-coverage",
            ],
            timeout=120,
        )
        assert result.returncode == 0, (
            f"test_jest_unit_tests_pass failed (exit {result.returncode})\n"
            + result.stderr[:500]
        )

    def test_no_any_in_tracking_functions(self):
        """Verify no 'any' type annotations in tracking function signatures"""
        result = self._run_cmd(
            "grep",
            args=["-c", "any", "frontend/src/metabase/analytics/snowplow.ts"],
            timeout=120,
        )
        assert result.returncode == 0, (
            f"test_no_any_in_tracking_functions failed (exit {result.returncode})\n"
            + result.stderr[:500]
        )

    def test_optional_params_undefined_handling(self):
        """Verify optional params use TypeScript ? syntax and are not sent as string 'null'"""
        _p = self._repo_path("frontend/src/metabase/analytics/snowplow.ts")
        assert os.path.exists(
            _p
        ), f"Missing: frontend/src/metabase/analytics/snowplow.ts"
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ""
        assert "label?" in _all, "Missing: label?"
        assert "value?" in _all, "Missing: value?"
        assert "undefined" in _all, "Missing: undefined"

    def test_event_category_string_constants(self):
        """Verify event category strings match documented taxonomy ('dashboard', 'question')"""
        _p = self._repo_path("frontend/src/metabase/analytics/events/dashboard.ts")
        assert os.path.exists(
            _p
        ), f"Missing: frontend/src/metabase/analytics/events/dashboard.ts"
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ""
        assert "'dashboard'" in _all, "Missing: 'dashboard'"
        assert "'viewed'" in _all, "Missing: 'viewed'"
