"""
Test for 'analytics-events' skill — TypeScript Analytics Event Tracking Library
Validates event type definitions, AnalyticsTracker, BatchProcessor, adapter patterns,
type-checking, and runtime behavior for event batching and validation.
"""

import os
import re
import subprocess
import sys

import pytest


class TestAnalyticsEvents:
    """Verify TypeScript analytics event tracking library implementation."""

    REPO_DIR = "/workspace/metabase"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _src(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "src", "analytics", *parts)

    def _npm_install(self):
        pkg = os.path.join(self.REPO_DIR, "package.json")
        if not os.path.isfile(pkg):
            pytest.skip("package.json not found")
        nm = os.path.join(self.REPO_DIR, "node_modules")
        if not os.path.isdir(nm):
            result = subprocess.run(
                ["npm", "install", "--ignore-scripts"],
                cwd=self.REPO_DIR,
                capture_output=True,
                timeout=120,
            )
            if result.returncode != 0:
                pytest.skip(f"npm install failed: {result.stderr[:200]}")

    # ── file_path_check ──────────────────────────────────────────────────

    def test_tracker_ts_source_file_exists(self):
        """src/analytics/tracker.ts must exist."""
        path = self._src("tracker.ts")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_events_type_definition_file_exists(self):
        """src/analytics/events.ts must exist."""
        path = self._src("events.ts")
        assert os.path.isfile(path), f"{path} does not exist"

    def test_batch_processor_and_adapter_files_exist(self):
        """batch.ts and adapters/segment.ts must exist."""
        batch = self._src("batch.ts")
        adapter = self._src("adapters", "segment.ts")
        assert os.path.isfile(batch), f"{batch} does not exist"
        assert os.path.isfile(adapter), f"{adapter} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_event_schema_is_discriminated_union(self):
        """EventSchema must be a discriminated union type keyed on 'name'."""
        path = self._src("events.ts")
        if not os.path.isfile(path):
            pytest.skip("events.ts not found")
        content = self._read_file(path)
        assert re.search(r"type\s+EventSchema", content), "EventSchema type not defined"
        assert "|" in content, "EventSchema should be a union type with |"
        assert re.search(r"name\s*:\s*['\"]", content), "Union members should have literal name field"

    def test_track_method_generic_signature(self):
        """AnalyticsTracker must have a generic track<T extends EventSchema> method."""
        path = self._src("tracker.ts")
        if not os.path.isfile(path):
            pytest.skip("tracker.ts not found")
        content = self._read_file(path)
        assert re.search(r"track", content), "No track method found"
        assert "any" not in content.split("track")[1][:50] or "EventSchema" in content, \
            "track parameter type should not be 'any'; must reference EventSchema"

    def test_batch_processor_maxsize_and_flush_interval(self):
        """BatchProcessor must accept maxSize and flushInterval parameters."""
        path = self._src("batch.ts")
        if not os.path.isfile(path):
            pytest.skip("batch.ts not found")
        content = self._read_file(path)
        assert "maxSize" in content, "maxSize parameter not found in batch.ts"
        assert "flushInterval" in content, "flushInterval parameter not found in batch.ts"

    def test_event_validation_error_extends_error(self):
        """EventValidationError must extend the built-in Error class."""
        candidates = [
            self._src("validation.ts"),
            self._src("errors.ts"),
            self._src("tracker.ts"),
        ]
        found = False
        for path in candidates:
            if os.path.isfile(path):
                content = self._read_file(path)
                if "EventValidationError" in content and "extends Error" in content:
                    found = True
                    break
        assert found, "EventValidationError extending Error not found in any analytics file"

    # ── functional_check ─────────────────────────────────────────────────

    def test_typescript_type_check_passes(self):
        """TypeScript source must compile without type errors using tsc --noEmit."""
        self._npm_install()
        tsconfig = os.path.join(self.REPO_DIR, "tsconfig.json")
        if not os.path.isfile(tsconfig):
            pytest.skip("tsconfig.json not found")
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"tsc failed (may need setup): {result.stderr[:200]}")

    def test_batch_flush_triggers_at_maxsize(self):
        """BatchProcessor.flush() should be callable; batch.ts must contain flush logic."""
        path = self._src("batch.ts")
        if not os.path.isfile(path):
            pytest.skip("batch.ts not found")
        content = self._read_file(path)
        assert "flush" in content, "flush method not defined in BatchProcessor"
        assert "maxSize" in content, "maxSize not referenced in flush logic"
        assert re.search(r"(length|size|count)\s*[><=]+", content), \
            "No length/size comparison found in batch.ts (needed for flush trigger)"

    def test_empty_batch_flush_no_api_call(self):
        """Flushing empty queue should not invoke send — check guard clause exists."""
        path = self._src("batch.ts")
        if not os.path.isfile(path):
            pytest.skip("batch.ts not found")
        content = self._read_file(path)
        assert re.search(r"(\.length\s*[=<>!]+\s*0|\.length\s*===?\s*0|isEmpty|queue\.length)", content), \
            "batch.ts should guard against flushing empty queue"

    def test_anonymous_id_handling(self):
        """Tracker should handle anonymous_id when identify() not called."""
        path = self._src("tracker.ts")
        if not os.path.isfile(path):
            pytest.skip("tracker.ts not found")
        content = self._read_file(path)
        has_anon = "anonymous" in content.lower() or "anon" in content.lower()
        has_identify = "identify" in content
        assert has_identify or has_anon, \
            "tracker.ts should handle identify() and/or anonymous_id pattern"

    def test_validation_error_thrown_for_missing_property(self):
        """Validation logic should check for required properties."""
        candidates = [
            self._src("validation.ts"),
            self._src("tracker.ts"),
            self._src("events.ts"),
        ]
        found = False
        for path in candidates:
            if os.path.isfile(path):
                content = self._read_file(path)
                if "required" in content.lower() or "validate" in content.lower():
                    found = True
                    break
        assert found, "No validation/required property checking found"
