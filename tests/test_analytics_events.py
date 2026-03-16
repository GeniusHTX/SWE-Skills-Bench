"""
Test for 'analytics-events' skill — Metabase Analytics Event Definitions
Validates that the Agent created TypeScript analytics event interfaces with
proper typing, naming conventions, and event schema validation.
"""

import os
import pytest


class TestAnalyticsEvents:
    """Verify analytics event definitions in Metabase."""

    REPO_DIR = "/workspace/metabase"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_event_definition_file_exists(self):
        """A TypeScript analytics event file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("analytics" in f.lower() or "event" in f.lower())
                    and f.endswith((".ts", ".tsx"))
                    and "node_modules" not in root
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No analytics event TypeScript file found"

    def test_test_file_exists(self):
        """Test file for analytics events must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("analytics" in f.lower() or "event" in f.lower())
                    and ("test" in f.lower() or "spec" in f.lower())
                    and f.endswith((".ts", ".tsx", ".js"))
                    and "node_modules" not in root
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No analytics event test file found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_event_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    ("analytics" in f.lower() or "event" in f.lower())
                    and f.endswith((".ts", ".tsx"))
                    and "node_modules" not in root
                ):
                    found.append(os.path.join(root, f))
        return found

    def _read_all_events(self):
        content = ""
        for fpath in self._find_event_files():
            try:
                with open(fpath, "r", errors="ignore") as f:
                    content += f.read() + "\n"
            except OSError:
                pass
        return content

    def test_interface_or_type_definitions(self):
        """Must define TypeScript interfaces or types for events."""
        content = self._read_all_events()
        ts_patterns = ["interface ", "type ", "Event", "Schema"]
        found = sum(1 for p in ts_patterns if p in content)
        assert found >= 2, "Insufficient TypeScript type definitions"

    def test_snake_case_event_names(self):
        """Event names should use snake_case convention."""
        import re

        content = self._read_all_events()
        # Look for string literals with underscores (snake_case event names)
        snake_events = re.findall(r'["\']([a-z]+_[a-z_]+)["\']', content)
        assert (
            len(snake_events) >= 3
        ), f"Only {len(snake_events)} snake_case event names; need >= 3"

    def test_event_has_properties(self):
        """Events must define properties/payload."""
        content = self._read_all_events()
        prop_patterns = [
            "properties",
            "payload",
            "data:",
            "params",
            "event_name",
            "event_type",
        ]
        found = sum(1 for p in prop_patterns if p in content)
        assert found >= 2, "Events missing properties definition"

    def test_event_categories(self):
        """Events should cover multiple categories."""
        content = self._read_all_events()
        categories = [
            "dashboard",
            "question",
            "model",
            "collection",
            "search",
            "admin",
            "auth",
            "navigation",
        ]
        found = sum(1 for c in categories if c in content.lower())
        assert found >= 2, f"Only {found} event categories found"

    def test_export_statements(self):
        """Event definitions must be exported."""
        content = self._read_all_events()
        export_patterns = ["export ", "export default", "module.exports"]
        found = any(p in content for p in export_patterns)
        assert found, "No export statements found"

    def test_timestamp_or_metadata(self):
        """Events should include timestamp or metadata fields."""
        content = self._read_all_events()
        meta_patterns = [
            "timestamp",
            "created_at",
            "user_id",
            "session_id",
            "metadata",
            "context",
        ]
        found = any(p in content for p in meta_patterns)
        assert found, "No timestamp/metadata fields found"

    def test_validation_logic(self):
        """Event schema should have validation logic."""
        content = self._read_all_events()
        validation_patterns = [
            "validate",
            "required",
            "z.object",
            "yup.",
            "joi.",
            "assert",
            "check",
        ]
        found = any(p in content for p in validation_patterns)
        # Also check test files for validation coverage
        if not found:
            for root, dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if ("analytics" in f.lower() or "event" in f.lower()) and (
                        "test" in f.lower() or "spec" in f.lower()
                    ):
                        fpath = os.path.join(root, f)
                        with open(fpath, "r", errors="ignore") as fh:
                            test_content = fh.read()
                        if any(p in test_content for p in validation_patterns):
                            found = True
                            break
                if found:
                    break
        assert found, "No validation logic found for events"

    def test_at_least_5_event_types(self):
        """Must define at least 5 distinct event types."""
        import re

        content = self._read_all_events()
        # Count unique snake_case strings that look like event names
        event_names = set(re.findall(r'["\']([a-z][a-z_]*_[a-z_]+)["\']', content))
        assert (
            len(event_names) >= 5
        ), f"Only {len(event_names)} event types found, need >= 5"
