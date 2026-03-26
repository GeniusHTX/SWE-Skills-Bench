"""
Test for 'clojure-write' skill — Currency Conversion for Metabase Export
Validates that the Agent created currency conversion middleware for Metabase
query processor with configurable exchange rates and export pipeline integration.
"""

import os
import re

import pytest


class TestClojureWrite:
    """Verify currency conversion middleware for Metabase."""

    REPO_DIR = "/workspace/metabase"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_currency_conversion_exists(self):
        """currency_conversion.clj must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR,
                "src/metabase/query_processor/middleware/currency_conversion.clj",
            )
        )

    def test_format_rows_exists(self):
        """format_rows.clj must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, "src/metabase/query_processor/middleware/format_rows.clj"
            )
        )

    # ------------------------------------------------------------------
    # L1: Clojure namespace
    # ------------------------------------------------------------------

    def test_namespace_declaration(self):
        """currency_conversion.clj must have a proper namespace."""
        content = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        )
        assert re.search(
            r"\(ns\s+metabase\.query.processor\.middleware\.currency.conversion",
            content,
        ), "Incorrect or missing namespace declaration"

    # ------------------------------------------------------------------
    # L2: Conversion function
    # ------------------------------------------------------------------

    def test_has_conversion_function(self):
        """Module must define a currency conversion function."""
        content = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        )
        patterns = [
            r"\(defn\s+convert",
            r"\(defn-\s+convert",
            r"\(defn\s+currency-convert",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "No conversion function found"

    def test_accepts_source_and_target_currency(self):
        """Conversion must accept source and target currency codes."""
        content = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        )
        patterns = [
            r"source.*currency",
            r"target.*currency",
            r"from.*currency",
            r"to.*currency",
            r"src-curr",
            r"tgt-curr",
        ]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, "Conversion does not accept source and target currencies"

    def test_uses_exchange_rates(self):
        """Module must use configurable exchange rate data."""
        content = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        )
        patterns = [r"exchange.rate", r"rate", r"rates", r"exchange", r"config"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Module does not use exchange rate data"

    # ------------------------------------------------------------------
    # L2: Edge case handling
    # ------------------------------------------------------------------

    def test_handles_nil_values(self):
        """Module must handle nil values."""
        content = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        )
        patterns = [r"nil\?", r"when\s+", r"some\?", r"nil", r"if-not"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Module does not handle nil values"

    def test_handles_unknown_currency(self):
        """Module must handle unknown currency codes."""
        content = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        )
        patterns = [
            r"unknown",
            r"not.*found",
            r"missing",
            r"get.*rate.*nil",
            r"throw\s+\(ex-info",
            r"contains\?",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Module does not handle unknown currencies"

    def test_preserves_precision(self):
        """Conversion must preserve decimal precision."""
        content = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        )
        patterns = [
            r"BigDecimal",
            r"bigdec",
            r"with-precision",
            r"decimal",
            r"round",
            r"scale",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Module does not preserve decimal precision"

    # ------------------------------------------------------------------
    # L2: Export integration
    # ------------------------------------------------------------------

    def test_format_rows_imports_conversion(self):
        """format_rows.clj must reference currency_conversion."""
        content = self._read("src/metabase/query_processor/middleware/format_rows.clj")
        patterns = [
            r"currency.conversion",
            r"currency_conversion",
            r"convert.*currency",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "format_rows.clj does not reference currency conversion"

    def test_conversion_triggered_by_metadata(self):
        """Conversion should be triggered by column metadata."""
        combined = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        ) + self._read("src/metabase/query_processor/middleware/format_rows.clj")
        patterns = [
            r"metadata",
            r"column.*type",
            r":semantic_type",
            r":currency",
            r"annotation",
        ]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "Conversion is not triggered by column metadata"

    def test_non_currency_columns_unchanged(self):
        """Non-currency columns should pass through unchanged."""
        combined = self._read(
            "src/metabase/query_processor/middleware/currency_conversion.clj"
        ) + self._read("src/metabase/query_processor/middleware/format_rows.clj")
        patterns = [
            r"currency\?",
            r"is.*currency",
            r"semantic.type.*currency",
            r"when.*currency",
            r"if.*currency",
        ]
        assert any(
            re.search(p, combined, re.IGNORECASE) for p in patterns
        ), "No logic to skip non-currency columns"
