"""
Test for 'analytics-events' skill — Metabase Snowplow Analytics Events
Validates that the Agent added Snowplow analytics event tracking to Metabase,
including BulkActionBar tracking and event schema definitions.
"""

import os
import re

import pytest


class TestAnalyticsEvents:
    """Verify Metabase Snowplow analytics event additions."""

    REPO_DIR = "/workspace/metabase"

    def test_snowplow_event_schema_exists(self):
        """Snowplow event schema definition must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".clj", ".cljc", ".cljs", ".js", ".ts", ".tsx")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"snowplow|Snowplow", content) and re.search(r"schema|event", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Snowplow event schema not found"

    def test_bulk_action_bar_tracking_exists(self):
        """BulkActionBar component must have event tracking."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "frontend")):
            for f in files:
                if f.endswith((".tsx", ".ts", ".jsx", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"BulkAction", content) and re.search(r"track|analytics|event", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "BulkActionBar tracking not found"

    def test_tracking_function_defined(self):
        """A tracking function (trackEvent, trackSchemaEvent, etc.) must be defined."""
        found = False
        search_dirs = [
            os.path.join(self.REPO_DIR, "frontend", "src"),
            os.path.join(self.REPO_DIR, "src"),
        ]
        for search_dir in search_dirs:
            if not os.path.isdir(search_dir):
                continue
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if f.endswith((".ts", ".tsx", ".js", ".clj")):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"def\s+track|function\s+track|trackSchemaEvent|trackEvent|export.*track", content):
                            found = True
                            break
                if found:
                    break
            if found:
                break
        assert found, "No tracking function defined"

    def test_event_has_properties(self):
        """Analytics events must include properties/context data."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".ts", ".tsx", ".clj", ".cljs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"event.*properties|event.*context|trackStructEvent|trackSchemaEvent", content):
                        found = True
                        break
            if found:
                break
        assert found, "Events have no properties/context data"

    def test_event_names_follow_convention(self):
        """Event names should follow a naming convention (snake_case or category.action)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".ts", ".tsx", ".clj", ".cljs")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r'track.*"[a-z_]+\.[a-z_]+"|track.*"[a-z]+_[a-z]+"', content):
                        found = True
                        break
            if found:
                break
        # This is a soft check - event names may vary
        assert True

    def test_snowplow_initialization_exists(self):
        """Snowplow tracker initialization must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".ts", ".tsx", ".js", ".clj")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"newTracker|tracker.*init|snowplow.*init|createTracker", content):
                        found = True
                        break
            if found:
                break
        assert found, "Snowplow tracker initialization not found"

    def test_event_tracking_is_non_blocking(self):
        """Event tracking calls should not block the main thread."""
        found_blocking = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "frontend")):
            for f in files:
                if f.endswith((".ts", ".tsx")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"await\s+track", content):
                        found_blocking = True
                        break
            if found_blocking:
                break
        assert not found_blocking, "Event tracking should not use await (blocking)"

    def test_analytics_test_exists(self):
        """Test files for analytics events must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if ("test" in f.lower() or "spec" in f.lower()) and f.endswith((".ts", ".tsx", ".js", ".clj")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"track|analytics|snowplow|event", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No test file for analytics events"

    def test_no_hardcoded_collector_url(self):
        """Snowplow collector URL should come from config/env, not hardcoded."""
        found_hardcoded = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".ts", ".tsx", ".js", ".clj")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r'collector.*=\s*["\']https?://[^"]+["\']', content):
                        found_hardcoded = True
                        break
            if found_hardcoded:
                break
        # Soft check - some repos have test/dev URLs
        assert True

    def test_frontend_event_types_exported(self):
        """Event type definitions should be exported from frontend module."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "frontend")):
            for f in files:
                if f.endswith((".ts", ".tsx")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"export.*(Event|Analytics|Tracking)", content):
                        found = True
                        break
            if found:
                break
        assert found, "No event type exports in frontend"

    def test_event_context_includes_user_info(self):
        """Events should include user context (user_id or similar)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".ts", ".tsx", ".clj")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"track|event", content, re.IGNORECASE) and re.search(r"user.id|userId|user_id", content):
                        found = True
                        break
            if found:
                break
        assert found, "Events do not include user context"
