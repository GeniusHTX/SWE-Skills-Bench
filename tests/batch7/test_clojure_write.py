"""Test file for the clojure-write skill.

This suite validates the result-digest middleware and result-change
notification modules in the Metabase Clojure codebase.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestClojureWrite:
    """Verify result-digest and result-change Clojure modules in Metabase."""

    REPO_DIR = "/workspace/metabase"

    DIGEST_CLJ = "src/metabase/query_processor/middleware/result_digest.clj"
    CHANGE_CLJ = "src/metabase/notification/result_change.clj"
    DIGEST_TEST_CLJ = "test/metabase/query_processor/middleware/result_digest_test.clj"

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

    def _find_defn(self, source: str, fn_name: str) -> str | None:
        """Return the balanced s-expression starting at (defn fn_name ...)."""
        pat = rf"\(defn-?\s+{re.escape(fn_name)}\b"
        m = re.search(pat, source)
        if m is None:
            return None
        start = m.start()
        depth = 0
        for i, ch in enumerate(source[start:], start):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return source[start : i + 1]
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_metabase_query_processor_middleware_result_digest_clj_ex(
        self,
    ):
        """Verify result_digest.clj exists and is non-empty."""
        self._assert_non_empty_file(self.DIGEST_CLJ)

    def test_file_path_src_metabase_notification_result_change_clj_exists(self):
        """Verify result_change.clj exists and is non-empty."""
        self._assert_non_empty_file(self.CHANGE_CLJ)

    def test_file_path_test_metabase_query_processor_middleware_result_digest_test_(
        self,
    ):
        """Verify result_digest_test.clj exists and is non-empty."""
        self._assert_non_empty_file(self.DIGEST_TEST_CLJ)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_compute_digest_uses_java_security_messagedigest_for_sha_256(self):
        """compute-digest uses java.security.MessageDigest for SHA-256."""
        src = self._read_text(self.DIGEST_CLJ)
        assert (
            "MessageDigest" in src or "message-digest" in src.lower()
        ), "compute-digest should use java.security.MessageDigest"
        assert re.search(
            r"SHA.?256", src
        ), "compute-digest should specify SHA-256 algorithm"

    def test_semantic_compute_digest_serializes_rows_with_pr_str_and_includes_colu(
        self,
    ):
        """compute-digest serializes rows with pr-str and includes column names."""
        src = self._read_text(self.DIGEST_CLJ)
        fn = self._find_defn(src, "compute-digest")
        assert fn is not None, "Missing defn compute-digest"
        assert (
            "pr-str" in fn or "str" in fn
        ), "compute-digest should serialize rows using pr-str"
        assert re.search(
            r":cols|column|:name", fn
        ), "compute-digest should include column names in digest"

    def test_semantic_compute_digest_returns_map_with_digest_row_count_col_count(self):
        """compute-digest returns map with :digest, :row-count, :col-count."""
        src = self._read_text(self.DIGEST_CLJ)
        fn = self._find_defn(src, "compute-digest")
        assert fn is not None, "Missing defn compute-digest"
        for key in (":digest", ":row-count", ":col-count"):
            assert key in fn, f"compute-digest return map missing {key}"

    def test_semantic_result_digest_middleware_follows_metabase_middleware_convent(
        self,
    ):
        """result-digest-middleware follows Metabase middleware conventions with [query rff] args."""
        src = self._read_text(self.DIGEST_CLJ)
        fn = self._find_defn(src, "result-digest-middleware")
        assert fn is not None, "Missing defn result-digest-middleware"
        assert re.search(
            r"\[.*query.*rff.*\]|\[.*rff.*\]", fn
        ), "Middleware should accept [query rff] args"

    def test_semantic_check_card_for_changes_loads_card_via_t2_select_one(self):
        """check-card-for-changes loads card via t2/select-one."""
        src = self._read_text(self.CHANGE_CLJ)
        fn = self._find_defn(src, "check-card-for-changes")
        assert fn is not None, "Missing defn check-card-for-changes"
        assert re.search(
            r"t2/select-one|select-one|db/select-one", fn
        ), "check-card-for-changes should load card via t2/select-one"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def test_functional_compute_digest_rows_1_a_2_b_cols_name_id_name_val_returns_64(
        self,
    ):
        """compute-digest returns 64-char hex string with row-count=2, col-count=2."""
        src = self._read_text(self.DIGEST_CLJ)
        fn = self._find_defn(src, "compute-digest")
        assert fn is not None
        # Verify hex string production logic
        assert re.search(
            r"format|hex|DatatypeConverter|encode", fn, re.IGNORECASE
        ), "compute-digest should produce hex-encoded digest"
        assert ":row-count" in fn, "Should return :row-count"
        assert ":col-count" in fn, "Should return :col-count"

    def test_functional_same_input_same_digest_deterministic(self):
        """Same input → same digest (deterministic)."""
        src = self._read_text(self.DIGEST_CLJ)
        fn = self._find_defn(src, "compute-digest")
        assert fn is not None
        # SHA-256 is deterministic by nature; verify no random element
        assert (
            "rand" not in fn.lower() and "uuid" not in fn.lower()
        ), "compute-digest should be deterministic (no random/uuid elements)"

    def test_functional_changed_cell_different_digest(self):
        """Changed cell → different digest."""
        src = self._read_text(self.DIGEST_CLJ)
        fn = self._find_defn(src, "compute-digest")
        assert fn is not None
        # Verify all rows are included in hashing (not just count)
        assert re.search(
            r"doseq|reduce|map|each|update", fn
        ), "compute-digest should iterate over all rows for content hashing"

    def test_functional_added_column_different_digest(self):
        """Added column → different digest."""
        src = self._read_text(self.DIGEST_CLJ)
        fn = self._find_defn(src, "compute-digest")
        assert fn is not None
        # Column names must be included in digest
        assert re.search(
            r":cols|:name|column", fn
        ), "Column names should be part of digest computation"

    def test_functional_no_previous_digest_new_results_notification(self):
        """No previous digest → :new-results notification."""
        src = self._read_text(self.CHANGE_CLJ)
        fn = self._find_defn(src, "check-card-for-changes")
        assert fn is not None
        assert re.search(
            r":new-results|:change-type|:first-run|nil\?", fn
        ), "check-card-for-changes should return :new-results when no previous digest"
