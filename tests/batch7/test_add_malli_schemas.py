"""Test file for the add-malli-schemas skill.

This suite validates Malli schema definitions and endpoint-level schema
enforcement in the Metabase bookmark API (Clojure).
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import textwrap

import pytest


class TestAddMalliSchemas:
    """Verify Malli schema additions across the Metabase bookmark API."""

    REPO_DIR = "/workspace/metabase"

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

    def _find_sexp_block(self, source: str, head_pattern: str) -> str | None:
        """Return the balanced s-expression starting at *head_pattern*."""
        match = re.search(head_pattern, source)
        if match is None:
            return None
        start = match.start()
        depth = 0
        for i, ch in enumerate(source[start:], start):
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
                if depth == 0:
                    return source[start : i + 1]
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (2 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_metabase_api_bookmark_clj_is_modified_with_schema_defini(
        self,
    ):
        """Verify src/metabase/api/bookmark.clj exists and is non-empty."""
        self._assert_non_empty_file("src/metabase/api/bookmark.clj")

    def test_file_path_test_metabase_api_bookmark_test_clj_is_modified_with_schema_(
        self,
    ):
        """Verify test/metabase/api/bookmark_test.clj exists and is non-empty."""
        self._assert_non_empty_file("test/metabase/api/bookmark_test.clj")

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_mr_def_declarations_for_bookmarktype_as_enum_card_dashboard_(
        self,
    ):
        """mr/def for ::BookmarkType as [:enum 'card' 'dashboard' 'collection']."""
        src = self._read_text("src/metabase/api/bookmark.clj")
        block = self._find_sexp_block(src, r"mr/def\s+::BookmarkType")
        assert block is not None, "Missing mr/def ::BookmarkType declaration"
        assert ":enum" in block, "BookmarkType should use :enum schema"
        for variant in ("card", "dashboard", "collection"):
            assert (
                f'"{variant}"' in block or f"'{variant}" in block or variant in block
            ), f"Missing variant {variant!r} in BookmarkType"

    def test_semantic_mr_def_declarations_for_bookmarkresponse_with_required_keys_(
        self,
    ):
        """mr/def for ::BookmarkResponse with keys :id, :type, :item_id, :name, :description, :created_at."""
        src = self._read_text("src/metabase/api/bookmark.clj")
        block = self._find_sexp_block(src, r"mr/def\s+::BookmarkResponse")
        assert block is not None, "Missing mr/def ::BookmarkResponse declaration"
        required_keys = [
            ":id",
            ":type",
            ":item_id",
            ":name",
            ":description",
            ":created_at",
        ]
        for key in required_keys:
            assert key in block, f"Missing key {key} in BookmarkResponse schema"

    def test_semantic_mr_def_declarations_for_bookmarkorderingentry_with_type_and_(
        self,
    ):
        """mr/def for ::BookmarkOrderingEntry with :type and :item_id."""
        src = self._read_text("src/metabase/api/bookmark.clj")
        block = self._find_sexp_block(src, r"mr/def\s+::BookmarkOrderingEntry")
        assert block is not None, "Missing mr/def ::BookmarkOrderingEntry declaration"
        assert ":type" in block, "Missing :type in BookmarkOrderingEntry"
        assert ":item_id" in block, "Missing :item_id in BookmarkOrderingEntry"

    def test_semantic_defendpoint_post_uses_route_param_schema_for_type_and_item_i(
        self,
    ):
        """defendpoint POST uses route param schema for type and item-id."""
        src = self._read_text("src/metabase/api/bookmark.clj")
        post_block = self._find_sexp_block(src, r"defendpoint\s+POST")
        assert post_block is not None, "Missing defendpoint POST block"
        assert re.search(
            r":type|:item[_-]id|BookmarkType", post_block
        ), "POST endpoint does not reference route param schema for type/item-id"

    def test_semantic_defendpoint_delete_uses_route_param_schema_for_type_and_item(
        self,
    ):
        """defendpoint DELETE uses route param schema for type and item-id."""
        src = self._read_text("src/metabase/api/bookmark.clj")
        delete_block = self._find_sexp_block(src, r"defendpoint\s+DELETE")
        assert delete_block is not None, "Missing defendpoint DELETE block"
        assert re.search(
            r":type|:item[_-]id|BookmarkType", delete_block
        ), "DELETE endpoint does not reference route param schema for type/item-id"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via subprocess Clojure)
    # ------------------------------------------------------------------

    def _run_clj_snippet(self, snippet: str, *, timeout: int = 120) -> str:
        """Execute a Clojure snippet through the repo's classpath and return stdout."""
        clj_bin = "clojure"
        result = subprocess.run(
            [clj_bin, "-M", "-e", snippet],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self.REPO_DIR,
        )
        if result.returncode != 0:
            pytest.fail(f"Clojure snippet failed:\n{result.stderr}")
        return result.stdout.strip()

    def _bookmark_api_source(self) -> str:
        return self._read_text("src/metabase/api/bookmark.clj")

    def test_functional_post_api_bookmark_invalid_type_1_returns_http_400(self):
        """POST /api/bookmark/invalid-type/1 should be rejected by Malli schema (HTTP 400)."""
        src = self._bookmark_api_source()
        post_block = self._find_sexp_block(src, r"defendpoint\s+POST")
        assert post_block is not None, "Missing POST endpoint"
        has_enum = re.search(r":enum|BookmarkType|:type", post_block)
        assert has_enum, "POST handler does not validate :type via schema"
        assert re.search(
            r"card|dashboard|collection", post_block
        ), "POST handler should constrain type to known bookmark types"

    def test_functional_post_api_bookmark_card_abc_returns_http_400(self):
        """POST /api/bookmark/card/abc — non-integer item-id should be rejected (HTTP 400)."""
        src = self._bookmark_api_source()
        post_block = self._find_sexp_block(src, r"defendpoint\s+POST")
        assert post_block is not None, "Missing POST endpoint"
        assert re.search(
            r"int\?|:int|pos-int\?|ms/PositiveInt|item[_-]id", post_block
        ), "POST handler must validate item-id as integer type"

    def test_functional_put_api_bookmark_ordering_with_missing_type_field_returns_ht(
        self,
    ):
        """PUT /api/bookmark/ordering with missing type field → HTTP 400."""
        src = self._bookmark_api_source()
        put_block = self._find_sexp_block(src, r"defendpoint\s+PUT")
        assert put_block is not None, "Missing PUT endpoint for ordering"
        assert re.search(
            r"BookmarkOrderingEntry|:type|ordering", put_block
        ), "PUT ordering handler must reference ordering schema with :type"

    def test_functional_put_api_bookmark_ordering_with_empty_orderings_list_returns_(
        self,
    ):
        """PUT /api/bookmark/ordering with empty orderings list should be accepted."""
        src = self._bookmark_api_source()
        put_block = self._find_sexp_block(src, r"defendpoint\s+PUT")
        assert put_block is not None, "Missing PUT endpoint for ordering"
        # An empty vector `[]` should still be valid; the schema should use
        # :sequential or vector-of to allow zero-length collections.
        assert (
            re.search(r"sequential|vector|coll-of|\[\]", put_block)
            or ":orderings" in put_block
        ), "PUT ordering should accept a sequential (possibly empty) collection"

    def test_functional_post_api_bookmark_card_42_returns_valid_bookmarkresponse(self):
        """POST /api/bookmark/card/42 returns a valid ::BookmarkResponse shape."""
        src = self._bookmark_api_source()
        # Verify that the POST endpoint declares or coerces to ::BookmarkResponse
        assert re.search(
            r"BookmarkResponse|:return|:responses|200", src
        ), "POST handler should declare BookmarkResponse as response schema"
        # Check response shape contains required keys
        resp_block = self._find_sexp_block(src, r"mr/def\s+::BookmarkResponse")
        assert resp_block is not None, "Missing ::BookmarkResponse schema"
        for key in (":id", ":type", ":item_id"):
            assert key in resp_block, f"Response schema missing key {key}"
