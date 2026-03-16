"""
Test for 'clojure-write' skill — Clojure Currency Formatter
Validates that the Agent created a Clojure currency formatting namespace
with proper locale handling and tests.
"""

import os
import subprocess
import pytest


class TestClojureWrite:
    """Verify Clojure currency formatter in Metabase."""

    REPO_DIR = "/workspace/metabase"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_formatter_file_exists(self):
        """A currency_formatter.clj file must exist somewhere in src/."""
        found = []
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if "currency" in f.lower() and f.endswith(".clj"):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No currency formatter .clj file found"

    def test_test_file_exists(self):
        """Test file for currency formatter must exist."""
        found = []
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "test")):
            for f in files:
                if "currency" in f.lower() and f.endswith(".clj"):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No currency formatter test file found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_formatter(self):
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if "currency" in f.lower() and f.endswith(".clj"):
                    return os.path.join(root, f)
        return None

    def test_has_namespace_declaration(self):
        """Formatter must have proper (ns ...) declaration."""
        fpath = self._find_formatter()
        assert fpath, "Formatter file not found"
        with open(fpath, "r") as f:
            content = f.read()
        assert "(ns " in content, "Missing (ns ...) declaration"

    def test_format_currency_function(self):
        """Must define a format-currency function."""
        fpath = self._find_formatter()
        assert fpath, "Formatter file not found"
        with open(fpath, "r") as f:
            content = f.read()
        fn_patterns = [
            "format-currency",
            "format_currency",
            "defn format",
            "defn- format",
        ]
        found = any(p in content for p in fn_patterns)
        assert found, "No format-currency function found"

    def test_supports_multiple_currencies(self):
        """Formatter must support multiple currencies (USD, EUR, etc.)."""
        fpath = self._find_formatter()
        assert fpath, "Formatter file not found"
        with open(fpath, "r") as f:
            content = f.read()
        currencies = ["USD", "EUR", "GBP", "JPY", "CNY"]
        found = sum(1 for c in currencies if c in content)
        assert found >= 2, f"Only {found} currency codes found, need >= 2"

    def test_locale_handling(self):
        """Formatter must handle locale-specific formatting."""
        fpath = self._find_formatter()
        assert fpath, "Formatter file not found"
        with open(fpath, "r") as f:
            content = f.read()
        locale_patterns = [
            "locale",
            "Locale",
            "java.util.Locale",
            "NumberFormat",
            "java.text",
        ]
        found = any(p in content for p in locale_patterns)
        assert found, "No locale handling found"

    def test_currency_symbol_handling(self):
        """Formatter must handle currency symbols ($, €, etc.)."""
        fpath = self._find_formatter()
        assert fpath, "Formatter file not found"
        with open(fpath, "r") as f:
            content = f.read()
        symbol_patterns = [
            "$",
            "€",
            "£",
            "symbol",
            "currency-symbol",
            "getCurrencyInstance",
            "Currency",
        ]
        found = any(p in content for p in symbol_patterns)
        assert found, "No currency symbol handling found"

    def test_decimal_precision(self):
        """Formatter must handle decimal precision."""
        fpath = self._find_formatter()
        assert fpath, "Formatter file not found"
        with open(fpath, "r") as f:
            content = f.read()
        precision_patterns = [
            "decimal",
            "precision",
            "scale",
            "fraction",
            "setMinimumFractionDigits",
            "BigDecimal",
            ".2f",
            "round",
        ]
        found = any(p in content for p in precision_patterns)
        assert found, "No decimal precision handling found"

    def test_bracket_balance(self):
        """Clojure source must have balanced brackets."""
        fpath = self._find_formatter()
        assert fpath, "Formatter file not found"
        with open(fpath, "r") as f:
            content = f.read()
        opens = content.count("(") + content.count("[") + content.count("{")
        closes = content.count(")") + content.count("]") + content.count("}")
        diff = abs(opens - closes)
        assert diff <= 3, f"Bracket imbalance: {diff}"

    def test_test_file_has_assertions(self):
        """Test file must contain (is ...) or deftest assertions."""
        found = []
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "test")):
            for f in files:
                if "currency" in f.lower() and f.endswith(".clj"):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "Test file not found"
        with open(found[0], "r") as f:
            content = f.read()
        assert "deftest" in content, "Test file missing deftest"
        assert (
            "(is " in content or "(are " in content
        ), "Test file missing (is ...) assertions"

    def test_edge_cases_in_tests(self):
        """Test file should cover edge cases (zero, negative, large)."""
        found = []
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "test")):
            for f in files:
                if "currency" in f.lower() and f.endswith(".clj"):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1
        with open(found[0], "r") as f:
            content = f.read()
        edge_patterns = [
            "0",
            "negative",
            "-1",
            "1000000",
            "nil",
            "zero",
            "large",
            "small",
        ]
        found_edges = sum(1 for p in edge_patterns if p in content.lower())
        assert found_edges >= 2, "Test file needs more edge case coverage"
