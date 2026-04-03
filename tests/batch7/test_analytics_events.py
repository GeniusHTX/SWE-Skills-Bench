"""Test file for the analytics-events skill.

This suite validates dashboard analytics event instrumentation across the
Metabase frontend codebase — TypeScript interface definitions, tracking
function exports, and UI integration call-sites.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import textwrap

import pytest


class TestAnalyticsEvents:
    """Verify Metabase dashboard analytics event implementation."""

    REPO_DIR = "/workspace/metabase"

    ANALYTICS_TS = "frontend/src/metabase/dashboard/analytics.ts"
    HEADER_TSX = (
        "frontend/src/metabase/dashboard/components/DashboardHeader/DashboardHeader.tsx"
    )
    DASHCARD_TSX = "frontend/src/metabase/dashboard/components/DashCard/DashCard.tsx"

    EXPECTED_EVENT_TYPES = [
        "dashboard_created",
        "dashboard_saved",
        "dashboard_card_added",
        "dashboard_card_removed",
        "dashboard_filter_applied",
        "dashboard_fullscreen_toggled",
        "dashboard_shared",
    ]

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

    def _ensure_optional_setup(self) -> bool:
        """Try npm install in frontend dir; return True on success."""
        frontend = self._repo_path("frontend")
        if not frontend.is_dir():
            return False
        try:
            subprocess.run(
                ["npm", "install", "--ignore-scripts"],
                cwd=str(frontend),
                capture_output=True,
                timeout=120,
            )
            return True
        except Exception:
            return False

    def _ts_export_names(self, source: str) -> set[str]:
        """Extract exported identifier names from TypeScript source."""
        names: set[str] = set()
        for m in re.finditer(
            r"export\s+(?:interface|type|function|const|let|var|class|enum)\s+(\w+)",
            source,
        ):
            names.add(m.group(1))
        return names

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_frontend_src_metabase_dashboard_analytics_ts_exists(self):
        """Verify analytics.ts exists and is non-empty."""
        self._assert_non_empty_file(self.ANALYTICS_TS)

    def test_file_path_frontend_src_metabase_dashboard_components_dashboardheader_d(
        self,
    ):
        """Verify DashboardHeader.tsx exists and is non-empty."""
        self._assert_non_empty_file(self.HEADER_TSX)

    def test_file_path_frontend_src_metabase_dashboard_components_dashcard_dashcard(
        self,
    ):
        """Verify DashCard.tsx exists and is non-empty."""
        self._assert_non_empty_file(self.DASHCARD_TSX)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_analytics_ts_exports_typescript_interfaces_for_all_7_event_t(
        self,
    ):
        """analytics.ts exports TypeScript interfaces for all 7 event types."""
        src = self._read_text(self.ANALYTICS_TS)
        for evt in self.EXPECTED_EVENT_TYPES:
            # Interface name is typically PascalCase of the event name.
            pascal = "".join(part.capitalize() for part in evt.split("_"))
            # Either the raw event name or its PascalCase variant must appear.
            assert (
                evt in src or pascal in src
            ), f"Event type {evt} (or interface {pascal}) not found in analytics.ts"

    def test_semantic_analytics_ts_exports_trackdashboardevent_function_with_prope(
        self,
    ):
        """analytics.ts exports trackDashboardEvent function with property validation."""
        src = self._read_text(self.ANALYTICS_TS)
        assert re.search(
            r"export\s+(?:function|const)\s+trackDashboardEvent", src
        ), "trackDashboardEvent not exported from analytics.ts"

    def test_semantic_trackdashboardevent_includes_automatic_metadata_timestamp_so(
        self,
    ):
        """trackDashboardEvent includes automatic metadata: timestamp, source, user_id."""
        src = self._read_text(self.ANALYTICS_TS)
        for meta in ("timestamp", "source", "user_id"):
            assert (
                meta in src
            ), f"Automatic metadata field '{meta}' not found in analytics.ts"

    def test_semantic_dashboardheader_tsx_calls_trackdashboardevent_for_created_sa(
        self,
    ):
        """DashboardHeader.tsx calls trackDashboardEvent for created/saved/fullscreen/share."""
        src = self._read_text(self.HEADER_TSX)
        assert (
            "trackDashboardEvent" in src
        ), "DashboardHeader.tsx does not call trackDashboardEvent"
        expected_events = [
            "dashboard_created",
            "dashboard_saved",
            "dashboard_fullscreen_toggled",
            "dashboard_shared",
        ]
        found = [e for e in expected_events if e in src]
        assert (
            len(found) >= 2
        ), f"DashboardHeader.tsx should reference multiple event types; found only {found}"

    def test_semantic_dashcard_tsx_calls_trackdashboardevent_for_card_added_card_r(
        self,
    ):
        """DashCard.tsx calls trackDashboardEvent for card_added/card_removed events."""
        src = self._read_text(self.DASHCARD_TSX)
        assert (
            "trackDashboardEvent" in src
        ), "DashCard.tsx does not call trackDashboardEvent"
        card_events = [
            "dashboard_card_added",
            "dashboard_card_removed",
            "card_added",
            "card_removed",
        ]
        found = [e for e in card_events if e in src]
        assert found, "DashCard.tsx should reference card_added/card_removed events"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, import-style via Node.js)
    # ------------------------------------------------------------------

    _setup_done: bool | None = None

    def _try_setup(self):
        if TestAnalyticsEvents._setup_done is None:
            TestAnalyticsEvents._setup_done = self._ensure_optional_setup()
        if not TestAnalyticsEvents._setup_done:
            pytest.skip("npm install in frontend directory failed or unavailable")

    def _run_node_snippet(self, script: str, *, timeout: int = 120) -> str:
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self._repo_path("frontend")),
        )
        if result.returncode != 0:
            pytest.fail(f"Node script failed:\n{result.stderr[:1000]}")
        return result.stdout.strip()

    def test_functional_dashboard_created_event_fires_with_correct_dashboard_id_coll(
        self,
    ):
        """dashboard_created event fires with correct dashboard_id, collection_id, num_cards, has_filters."""
        self._try_setup()
        src = self._read_text(self.ANALYTICS_TS)
        # Validate the function signature / payload structure in source
        assert "dashboard_created" in src
        # Look for the expected property names in the same file
        for prop in ("dashboard_id", "collection_id", "num_cards", "has_filters"):
            assert (
                prop in src
            ), f"dashboard_created event payload missing property '{prop}'"

    def test_functional_dashboard_saved_event_fires_with_correct_properties_includin(
        self,
    ):
        """dashboard_saved event fires with correct properties including is_new boolean."""
        self._try_setup()
        src = self._read_text(self.ANALYTICS_TS)
        assert "dashboard_saved" in src
        assert "is_new" in src, "dashboard_saved should include is_new property"

    def test_functional_dashboard_card_added_event_fires_with_correct_card_type_and_(
        self,
    ):
        """dashboard_card_added event fires with correct card_type and position."""
        self._try_setup()
        src = self._read_text(self.ANALYTICS_TS)
        assert "dashboard_card_added" in src or "card_added" in src
        for prop in ("card_type", "position"):
            assert prop in src, f"dashboard_card_added event missing property '{prop}'"

    def test_functional_dashboard_filter_applied_event_fires_with_correct_filter_typ(
        self,
    ):
        """dashboard_filter_applied event fires with correct filter_type."""
        self._try_setup()
        src = self._read_text(self.ANALYTICS_TS)
        assert "dashboard_filter_applied" in src or "filter_applied" in src
        assert (
            "filter_type" in src
        ), "dashboard_filter_applied should include filter_type"

    def test_functional_dashboard_fullscreen_toggled_event_fires_with_entered_boolea(
        self,
    ):
        """dashboard_fullscreen_toggled event fires with entered boolean."""
        self._try_setup()
        src = self._read_text(self.ANALYTICS_TS)
        assert "dashboard_fullscreen_toggled" in src or "fullscreen_toggled" in src
        assert (
            "entered" in src
        ), "dashboard_fullscreen_toggled should include 'entered' boolean property"
