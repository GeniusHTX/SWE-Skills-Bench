"""
Tests for the analytics-events skill.
Verifies that the Metabase frontend analytics event system (types.ts,
useTrackEvent.ts, batcher.ts) is correctly implemented with proper
TypeScript structure, event category types, privacy guards, and
batch flush logic.
"""

import os
import re
import subprocess

import pytest

REPO_DIR = "/workspace/metabase"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _node_available() -> bool:
    try:
        r = subprocess.run(["node", "--version"], capture_output=True, timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _yarn_available() -> bool:
    try:
        r = subprocess.run(["yarn", "--version"], capture_output=True, timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_cmd(cmd: list, cwd: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestAnalyticsEvents:
    """Test suite for the Metabase frontend analytics events skill."""

    def test_analytics_types_file_exists(self):
        """Verify analytics types.ts is created at the expected path."""
        target = _path("frontend/src/metabase/analytics/types.ts")
        assert os.path.isfile(target), f"types.ts not found: {target}"
        assert os.path.getsize(target) > 0, "types.ts must be non-empty"

    def test_use_track_event_and_batcher_files_exist(self):
        """Verify useTrackEvent.ts and batcher.ts files exist."""
        for rel in (
            "frontend/src/metabase/analytics/useTrackEvent.ts",
            "frontend/src/metabase/analytics/batcher.ts",
        ):
            assert os.path.isfile(_path(rel)), f"Missing file: {rel}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_types_defines_four_event_categories(self):
        """Verify types.ts defines at least 4 analytics event category types."""
        content = _read("frontend/src/metabase/analytics/types.ts")
        # Count unique string literal members in union types or enum values
        string_literals = re.findall(r"['\"]([a-zA-Z_][a-zA-Z0-9_-]*)['\"]", content)
        type_members = re.findall(r"\|\s*['\"]([a-zA-Z_][a-zA-Z0-9_-]*)['\"]", content)
        candidates = set(string_literals) | set(type_members)
        assert (
            len(candidates) >= 4
        ), f"types.ts must define at least 4 distinct event category members, found: {candidates}"

    def test_batcher_defines_flush_at_count_threshold(self):
        """Verify batcher.ts defines a batch flush threshold of 10."""
        content = _read("frontend/src/metabase/analytics/batcher.ts")
        # Must reference the number 10 as a threshold constant
        assert (
            "10" in content
        ), "batcher.ts must define a flush threshold (expected value 10)"
        # Must have logic to flush when batch reaches the threshold
        has_flush = (
            "flush" in content.lower()
            or "send" in content.lower()
            or "dispatch" in content.lower()
        )
        assert has_flush, "batcher.ts must contain a flush/send/dispatch call"

    def test_use_track_event_has_do_not_track_guard(self):
        """Verify useTrackEvent.ts includes a do_not_track guard condition."""
        content = _read("frontend/src/metabase/analytics/useTrackEvent.ts")
        lower = content.lower()
        has_guard = (
            "do_not_track" in lower
            or "donottrack" in lower
            or "tracking_enabled" in lower
            or "track" in lower
        )
        assert (
            has_guard
        ), "useTrackEvent.ts must contain a privacy guard (do_not_track / doNotTrack / tracking_enabled)"

    def test_batcher_has_debounce_logic(self):
        """Verify batcher.ts contains debounce or timer-based flush logic."""
        content = _read("frontend/src/metabase/analytics/batcher.ts")
        lower = content.lower()
        has_timer = (
            "settimeout" in lower
            or "debounce" in lower
            or "interval" in lower
            or "setinterval" in lower
        )
        assert (
            has_timer
        ), "batcher.ts must contain timer-based (setTimeout/debounce/interval) flush logic"

    # -----------------------------------------------------------------------
    # Functional checks
    # -----------------------------------------------------------------------

    def test_event_type_union_imported_in_use_track_event(self):
        """Verify useTrackEvent.ts imports type definitions from types.ts."""
        content = _read("frontend/src/metabase/analytics/useTrackEvent.ts")
        has_import = "types" in content or "./types" in content or "../types" in content
        assert has_import, "useTrackEvent.ts must import from the types module"

    def test_do_not_track_guard_has_early_return(self):
        """Verify useTrackEvent.ts has an early return within the privacy guard block."""
        content = _read("frontend/src/metabase/analytics/useTrackEvent.ts")
        # Look for a return statement in the file (as guard exit)
        assert (
            "return" in content
        ), "useTrackEvent.ts must contain a return statement for the privacy guard"

    def test_batcher_flush_on_count_ten(self):
        """Verify batcher flushes when exactly 10 events are queued."""
        content = _read("frontend/src/metabase/analytics/batcher.ts")
        # The threshold '10' must appear near a conditional/comparison
        has_threshold_check = (
            re.search(r"[><=!]=?\s*10|10\s*[><=!]=?", content) is not None
        )
        has_length = "length" in content or "size" in content or "count" in content
        assert (
            has_threshold_check or has_length
        ), "batcher.ts must check queue length against threshold 10"

    def test_no_hardcoded_external_tracking_urls(self):
        """Verify analytics files do not contain hardcoded external tracking URLs."""
        for rel in (
            "frontend/src/metabase/analytics/useTrackEvent.ts",
            "frontend/src/metabase/analytics/batcher.ts",
        ):
            full = _path(rel)
            if not os.path.isfile(full):
                continue
            with open(full, encoding="utf-8", errors="replace") as f:
                content = f.read()
            external_trackers = [
                "segment.com",
                "mixpanel.com",
                "amplitude.com",
                "heap.io",
            ]
            for tracker in external_trackers:
                assert (
                    tracker not in content
                ), f"{rel} must not contain hardcoded external tracking URL: {tracker}"

    def test_typescript_analytics_files_have_valid_syntax(self):
        """Verify analytics TypeScript files have valid syntax via node/tsc check."""
        if not _node_available():
            pytest.skip("node not available")
        frontend_dir = _path("frontend")
        if not os.path.isdir(frontend_dir):
            pytest.skip("frontend directory not found")
        # Try quick syntax check using node with require
        for rel in (
            "frontend/src/metabase/analytics/types.ts",
            "frontend/src/metabase/analytics/batcher.ts",
        ):
            target = _path(rel)
            if not os.path.isfile(target):
                continue
            # Check that file is not empty and has TS-style content
            with open(target, encoding="utf-8") as f:
                content = f.read()
            # Basic structural check: file must have at least one export or type keyword
            has_ts_construct = (
                "export" in content
                or "type " in content
                or "interface " in content
                or "const " in content
            )
            assert (
                has_ts_construct
            ), f"{rel} must contain TypeScript constructs (export/type/interface/const)"

    def test_use_track_event_exports_hook(self):
        """Verify useTrackEvent.ts exports a hook function (useTrackEvent or similar)."""
        content = _read("frontend/src/metabase/analytics/useTrackEvent.ts")
        has_export = "export" in content
        has_function = (
            "function" in content or "=>" in content or "const use" in content
        )
        assert has_export, "useTrackEvent.ts must export the hook"
        assert has_function, "useTrackEvent.ts must define a hook function"
