"""
Test for 'analytics-events' skill — User Behavior Analytics Events
Validates that the Agent added three analytics event type definitions and
tracking functions to Metabase's frontend TypeScript codebase.
"""

import os
import re
import subprocess

import pytest


class TestAnalyticsEvents:
    """Verify analytics event definitions and tracking functions."""

    REPO_DIR = "/workspace/metabase"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_events_ts_exists(self):
        """events.ts must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, "frontend/src/metabase-types/analytics/events.ts"
            )
        )

    def test_tracking_ts_exists(self):
        """tracking.ts must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "frontend/src/metabase/analytics/tracking.ts")
        )

    # ------------------------------------------------------------------
    # L1: Event type definitions
    # ------------------------------------------------------------------

    def test_feature_discovery_event_defined(self):
        """feature_discovery_triggered event type must be defined."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        assert re.search(
            r"feature_discovery_triggered", content
        ), "feature_discovery_triggered event not defined"

    def test_navigation_tab_event_defined(self):
        """navigation_tab_clicked event type must be defined."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        assert re.search(
            r"navigation_tab_clicked", content
        ), "navigation_tab_clicked event not defined"

    def test_content_created_event_defined(self):
        """content_created event type must be defined."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        assert re.search(
            r"content_created", content
        ), "content_created event not defined"

    # ------------------------------------------------------------------
    # L2: Event payload types
    # ------------------------------------------------------------------

    def test_feature_discovery_has_payload(self):
        """feature_discovery event must carry feature_name and source."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        assert re.search(
            r"feature_name", content
        ), "feature_discovery missing feature_name field"
        assert re.search(r"source", content), "feature_discovery missing source field"

    def test_navigation_tab_has_payload(self):
        """navigation_tab event must carry tab_name and previous_tab."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        assert re.search(r"tab_name", content), "navigation_tab missing tab_name field"
        assert re.search(
            r"previous_tab", content
        ), "navigation_tab missing previous_tab field"

    def test_content_created_has_payload(self):
        """content_created event must carry content_type and content_id."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        assert re.search(
            r"content_type", content
        ), "content_created missing content_type field"
        assert re.search(
            r"content_id", content
        ), "content_created missing content_id field"

    def test_content_type_is_union(self):
        """content_type should be a union of question/dashboard/model."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        patterns = [
            r'"question"\s*\|\s*"dashboard"\s*\|\s*"model"',
            r'"dashboard"\s*\|\s*"question"\s*\|\s*"model"',
            r'"model"\s*\|\s*"question"\s*\|\s*"dashboard"',
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "content_type is not a union of question|dashboard|model"

    def test_events_use_snake_case(self):
        """Event names must follow snake_case convention."""
        content = self._read("frontend/src/metabase-types/analytics/events.ts")
        event_names = re.findall(r'["\'](\w+_\w+)["\']', content)
        for name in event_names:
            assert name == name.lower(), f"Event name '{name}' is not snake_case"

    # ------------------------------------------------------------------
    # L2: Tracking functions
    # ------------------------------------------------------------------

    def test_track_feature_discovery_function(self):
        """trackFeatureDiscovery function must exist."""
        content = self._read("frontend/src/metabase/analytics/tracking.ts")
        assert re.search(
            r"trackFeatureDiscovery", content
        ), "trackFeatureDiscovery function not found"

    def test_track_navigation_action_function(self):
        """trackNavigationAction function must exist."""
        content = self._read("frontend/src/metabase/analytics/tracking.ts")
        assert re.search(
            r"trackNavigationAction", content
        ), "trackNavigationAction function not found"

    def test_track_content_creation_function(self):
        """trackContentCreation function must exist."""
        content = self._read("frontend/src/metabase/analytics/tracking.ts")
        assert re.search(
            r"trackContentCreation", content
        ), "trackContentCreation function not found"

    def test_tracking_uses_core_utility(self):
        """Tracking functions must use the project's core tracking utility."""
        content = self._read("frontend/src/metabase/analytics/tracking.ts")
        patterns = [
            r"trackEvent",
            r"trackStructEvent",
            r"trackSchemaEvent",
            r"dispatch",
            r"sendEvent",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Tracking functions do not use core tracking utility"
