"""
Test for 'analytics-events' skill — Metabase Collection Bookmark Analytics
Validates that the Agent created analytics event types and integrated tracking
for CollectionBookmark CRUD operations in the Metabase frontend.
"""

import os

import pytest


class TestAnalyticsEvents:
    """Verify Metabase collection bookmark analytics event implementation."""

    REPO_DIR = "/workspace/metabase"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _find_file(self, filename, start_dir=None):
        start = start_dir or self.REPO_DIR
        for root, _dirs, files in os.walk(start):
            if filename in files:
                return os.path.join(root, filename)
        return None

    # ---- file_path_check ----

    def test_frontend_src_exists(self):
        """Verifies frontend/src directory exists."""
        path = os.path.join(self.REPO_DIR, "frontend/src")
        assert os.path.exists(path), f"Expected path not found: {path}"

    def test_event_ts_exists(self):
        """Verifies metabase-types/analytics/event.ts exists."""
        path = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_analytics_ts_exists(self):
        """Verifies metabase/collections/analytics.ts exists."""
        path = os.path.join(self.REPO_DIR, "metabase/collections/analytics.ts")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_collection_bookmark_tsx_exists(self):
        """Verifies CollectionBookmark.tsx exists."""
        path = os.path.join(
            self.REPO_DIR,
            "metabase/collections/components/CollectionBookmark.tsx",
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    # ---- semantic_check ----

    def test_sem_event_ts_readable(self):
        """Reads event.ts file."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        assert len(event_text) > 0, "event.ts is empty"

    def test_sem_event_types_defined(self):
        """Verifies all bookmark event types are defined in event.ts."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        for etype in [
            "CollectionBookmarkCreatedEvent",
            "CollectionBookmarkRemovedEvent",
            "CollectionBookmarkReorderedEvent",
            "CollectionBookmarkItemClickedEvent",
        ]:
            assert etype in event_text, f"{etype} not found in event.ts"

    def test_sem_union_type(self):
        """Verifies CollectionBookmarkEvent union type (edge case)."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        assert (
            "CollectionBookmarkEvent" in event_text
        ), "CollectionBookmarkEvent union type missing"

    def test_sem_analytics_event_union(self):
        """Verifies events added to AnalyticsEvent union."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        assert (
            "AnalyticsEvent" in event_text
        ), "CollectionBookmarkEvent not added to AnalyticsEvent union"

    def test_sem_validate_event(self):
        """Verifies ValidateEvent used for new event types."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        assert (
            "ValidateEvent" in event_text
        ), "ValidateEvent not used for new event types"

    # ---- functional_check ----

    def test_func_bookmark_tsx_readable(self):
        """Reads CollectionBookmark.tsx file."""
        bookmark_tsx = os.path.join(
            self.REPO_DIR,
            "metabase/collections/components/CollectionBookmark.tsx",
        )
        bookmark_text = self._read(bookmark_tsx)
        assert len(bookmark_text) > 0, "CollectionBookmark.tsx is empty"

    def test_func_bookmark_created_tracking(self):
        """Verifies bookmark created tracking integrated."""
        bookmark_tsx = os.path.join(
            self.REPO_DIR,
            "metabase/collections/components/CollectionBookmark.tsx",
        )
        bookmark_text = self._read(bookmark_tsx)
        assert (
            "collection_bookmark_created" in bookmark_text
            or "trackCollectionBookmarkCreated" in bookmark_text
            or "analytics" in bookmark_text.lower()
        ), "Bookmark created tracking not integrated"

    def test_func_bookmark_removed_tracking(self):
        """Verifies bookmark removed tracking integrated."""
        bookmark_tsx = os.path.join(
            self.REPO_DIR,
            "metabase/collections/components/CollectionBookmark.tsx",
        )
        bookmark_text = self._read(bookmark_tsx)
        assert (
            "collection_bookmark_removed" in bookmark_text
            or "trackCollectionBookmarkRemoved" in bookmark_text
        ), "Bookmark removed tracking not integrated"

    def test_func_bookmark_list_readable(self):
        """Reads BookmarkList component file."""
        # Try to find BookmarkList.tsx
        bookmark_list = self._find_file("BookmarkList.tsx")
        assert bookmark_list is not None, "BookmarkList.tsx not found"
        list_text = self._read(bookmark_list)
        assert len(list_text) > 0, "BookmarkList.tsx is empty"

    def test_func_reorder_tracking(self):
        """Verifies reorder tracking in BookmarkList."""
        bookmark_list = self._find_file("BookmarkList.tsx")
        assert bookmark_list is not None, "BookmarkList.tsx not found"
        list_text = self._read(bookmark_list)
        assert (
            "collection_bookmark_reordered" in list_text
            or "trackCollectionBookmarkReordered" in list_text
            or "reorder" in list_text.lower()
        ), "Reorder tracking not in BookmarkList.tsx"

    def test_func_item_clicked_tracking(self):
        """Verifies item clicked tracking in BookmarkList."""
        bookmark_list = self._find_file("BookmarkList.tsx")
        assert bookmark_list is not None, "BookmarkList.tsx not found"
        list_text = self._read(bookmark_list)
        assert (
            "collection_bookmark_item_clicked" in list_text
            or "trackCollectionBookmarkItemClicked" in list_text
        ), "Item clicked tracking not in BookmarkList.tsx"

    def test_func_triggered_from_literals(self):
        """Verifies triggered_from literal values in event.ts."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        assert (
            "'collection-header'" in event_text or '"collection-header"' in event_text
        ), "triggered_from literal values missing"

    def test_func_event_detail_moved_up(self):
        """Verifies event_detail moved-up literal in event.ts."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        assert (
            "'moved-up'" in event_text or '"moved-up"' in event_text
        ), "event_detail moved-up literal missing"

    def test_func_failure_missing_event_type(self):
        """Failure case: all event types must be present for TS compilation."""
        event_ts = os.path.join(self.REPO_DIR, "metabase-types/analytics/event.ts")
        event_text = self._read(event_ts)
        required = [
            "CollectionBookmarkCreatedEvent",
            "CollectionBookmarkRemovedEvent",
            "CollectionBookmarkReorderedEvent",
            "CollectionBookmarkItemClickedEvent",
        ]
        missing = [e for e in required if e not in event_text]
        assert len(missing) == 0, f"Missing event types: {missing}"
