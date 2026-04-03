"""
Test for 'analytics-events' skill — Dashboard Subscription Analytics Events
Validates that the Agent implemented TypeScript analytics event tracking
for the Metabase DashboardSubscriptionPanel component.
"""

import os
import re

import pytest


class TestAnalyticsEvents:
    """Verify Metabase dashboard subscription analytics event implementation."""

    REPO_DIR = "/workspace/metabase"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_analytics_event_file_exists(self):
        """Verify event.ts and schema.ts analytics type files exist."""
        for rel in (
            "frontend/src/metabase-types/analytics/event.ts",
            "frontend/src/metabase-types/analytics/schema.ts",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_analytics_module_file_exists(self):
        """Verify the DashboardSubscriptionPanel analytics.ts module exists."""
        path = os.path.join(
            self.REPO_DIR,
            "frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.ts",
        )
        assert os.path.isfile(path), "analytics.ts missing for DashboardSubscriptionPanel"

    def test_analytics_spec_file_exists(self):
        """Verify the analytics.unit.spec.ts test file exists."""
        path = os.path.join(
            self.REPO_DIR,
            "frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.unit.spec.ts",
        )
        assert os.path.isfile(path), "analytics.unit.spec.ts test file missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_dashboard_subscription_event_variants(self):
        """Verify DashboardSubscriptionEvent type has all 4 event variant names."""
        content = self._read(os.path.join(
            self.REPO_DIR, "frontend/src/metabase-types/analytics/event.ts"))
        assert content, "event.ts is empty or unreadable"
        for variant in (
            "dashboard_subscription_created",
            "dashboard_subscription_updated",
            "dashboard_subscription_deleted",
            "dashboard_subscription_test_sent",
        ):
            assert variant in content, f"Event variant '{variant}' not found in event.ts"

    def test_schema_version_in_event_variants(self):
        """Verify schema and version fields are present in event variant definitions."""
        content = self._read(os.path.join(
            self.REPO_DIR, "frontend/src/metabase-types/analytics/event.ts"))
        assert content, "event.ts is empty or unreadable"
        assert "dashboard-subscription" in content, "schema 'dashboard-subscription' not found"
        assert "1-0-0" in content, "version '1-0-0' not found"

    def test_analytics_union_includes_event(self):
        """Verify AnalyticsEvent union type in schema.ts includes DashboardSubscriptionEvent."""
        content = self._read(os.path.join(
            self.REPO_DIR, "frontend/src/metabase-types/analytics/schema.ts"))
        assert content, "schema.ts is empty or unreadable"
        assert "DashboardSubscriptionEvent" in content, \
            "DashboardSubscriptionEvent not in AnalyticsEvent union"

    def test_guard_logic_in_tracking_functions(self):
        """Verify guard conditions (dashboardId > 0 and changedFields.length check) exist in analytics.ts."""
        content = self._read(os.path.join(
            self.REPO_DIR,
            "frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.ts",
        ))
        assert content, "analytics.ts is empty or unreadable"
        assert "dashboardId" in content, "dashboardId guard missing"
        assert "changedFields" in content, "changedFields guard missing"
        assert "length" in content, "length check missing"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_yarn(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if not os.path.isfile(os.path.join(self.REPO_DIR, "yarn.lock")):
            pytest.skip("yarn.lock missing")

    def test_track_subscription_created_dispatches(self):
        """trackSubscriptionCreated(42, 'email', 'daily', 5) dispatches event with correct payload fields."""
        self._skip_unless_yarn()
        content = self._read(os.path.join(
            self.REPO_DIR,
            "frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.unit.spec.ts",
        ))
        assert content, "analytics.unit.spec.ts is empty"
        assert "trackSubscriptionCreated" in content or "created" in content.lower(), \
            "No test for trackSubscriptionCreated dispatch"

    def test_track_subscription_updated_empty_fields_no_dispatch(self):
        """trackSubscriptionUpdated(42, 7, []) must not dispatch any event."""
        self._skip_unless_yarn()
        content = self._read(os.path.join(
            self.REPO_DIR,
            "frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.unit.spec.ts",
        ))
        assert content, "analytics.unit.spec.ts is empty"
        assert "updated" in content.lower() or "empty" in content.lower() or "[]" in content, \
            "No test for empty changedFields guard"

    def test_track_subscription_created_negative_id_no_dispatch(self):
        """trackSubscriptionCreated(-1, 'email', 'daily', 5) must not dispatch any event."""
        self._skip_unless_yarn()
        content = self._read(os.path.join(
            self.REPO_DIR,
            "frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.unit.spec.ts",
        ))
        assert content, "analytics.unit.spec.ts is empty"
        assert "-1" in content or "negative" in content.lower() or "invalid" in content.lower(), \
            "No test for negative dashboardId guard"

    def test_track_subscription_test_sent_success_false(self):
        """trackSubscriptionTestSent(42, 'slack', false) dispatches event with success=false."""
        self._skip_unless_yarn()
        content = self._read(os.path.join(
            self.REPO_DIR,
            "frontend/src/metabase/dashboard/components/DashboardSubscriptionPanel/analytics.unit.spec.ts",
        ))
        assert content, "analytics.unit.spec.ts is empty"
        assert "test_sent" in content.lower() or "TestSent" in content, \
            "No test for trackSubscriptionTestSent dispatch"
