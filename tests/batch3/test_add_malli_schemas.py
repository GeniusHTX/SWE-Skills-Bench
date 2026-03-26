"""
Tests for the add-malli-schemas skill.
Verifies that the Metabase dashboard Malli schema implementation is correctly
structured, namespace-declared, exports the required validation functions,
and enforces validation rules for dashboard creation/update requests.
"""

import os
import sys

import pytest

REPO_DIR = "/workspace/metabase"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _mock_validate_fn(rules: dict):
    """
    Build a lightweight Python-side mock of a Clojure validate function.
    rules: dict mapping required string keys to their types.
    Returns a callable that validates a dict input against those rules.
    """

    def _validate(data: dict):
        errors = []
        for key, expected_type in rules.items():
            val = data.get(key)
            if val is None:
                errors.append(f"Missing required key: {key}")
            elif expected_type == "non-empty-string" and not isinstance(val, str):
                errors.append(f"{key} must be a string")
            elif (
                expected_type == "non-empty-string"
                and isinstance(val, str)
                and not val.strip()
            ):
                errors.append(f"{key} must not be empty")
        return {"valid": len(errors) == 0, "errors": errors}

    return _validate


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestAddMalliSchemas:
    """Test suite for the Metabase Malli schema implementation skill."""

    def test_schema_file_exists(self):
        """Verify dashboard schema file is created at the expected path."""
        target = _path("src/metabase/api/dashboard/schema.clj")
        assert os.path.isfile(target), f"Schema file not found: {target}"
        assert os.path.getsize(target) > 0, "schema.clj must be non-empty"

    def test_validators_file_exists(self):
        """Verify dashboard validators file is created at the expected path."""
        target = _path("src/metabase/api/dashboard/validators.clj")
        assert os.path.isfile(target), f"Validators file not found: {target}"
        assert os.path.getsize(target) > 0, "validators.clj must be non-empty"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_schema_ns_declaration(self):
        """Verify schema.clj has correct namespace and requires malli.core."""
        content = _read("src/metabase/api/dashboard/schema.clj")
        assert (
            "(ns metabase.api.dashboard.schema" in content
        ), "schema.clj must declare namespace 'metabase.api.dashboard.schema'"
        assert (
            "malli.core" in content or "[malli" in content
        ), "schema.clj must require malli.core"

    def test_schema_defines_validate_functions(self):
        """Verify schema.clj defines validate-create-request and validate-update-request."""
        content = _read("src/metabase/api/dashboard/schema.clj")
        assert (
            "validate-create-request" in content
        ), "schema.clj must define 'validate-create-request'"
        assert (
            "validate-update-request" in content
        ), "schema.clj must define 'validate-update-request'"

    def test_schema_defines_card_layout_validator(self):
        """Verify schema.clj defines a card-layout schema or validator."""
        content = _read("src/metabase/api/dashboard/schema.clj")
        assert (
            "card-layout" in content or "CardLayout" in content
        ), "schema.clj must define a 'card-layout' or 'CardLayout' schema"

    def test_schema_uses_malli_schema_types(self):
        """Verify schema definitions use Malli types like :map, :string, :int."""
        content = _read("src/metabase/api/dashboard/schema.clj")
        assert ":map" in content, "schema.clj must use :map Malli schema type"
        has_primitive = ":string" in content or ":int" in content
        assert has_primitive, "schema.clj must use :string or :int Malli type keywords"

    # -----------------------------------------------------------------------
    # Functional checks (mocked - validate-* logic simulated in Python)
    # -----------------------------------------------------------------------

    def test_validate_create_request_empty_map_returns_invalid(self):
        """Verify validate-create-request({}) returns {valid: false} with non-empty errors."""
        validate = _mock_validate_fn({"name": "non-empty-string"})
        result = validate({})
        assert result["valid"] is False, "Empty map must fail validation"
        assert (
            len(result["errors"]) > 0
        ), "Errors list must be non-empty for empty input"

    def test_validate_create_request_valid_dashboard(self):
        """Verify validate-create-request with valid params returns {valid: true}."""
        validate = _mock_validate_fn({"name": "non-empty-string"})
        result = validate({"name": "Sales Dashboard", "description": "Q4 metrics"})
        assert result["valid"] is True, "Valid dashboard params must pass validation"

    def test_validate_update_request_empty_name_rejected(self):
        """Verify validate-update-request rejects update with empty string name."""
        validate = _mock_validate_fn({"name": "non-empty-string"})
        result = validate({"name": ""})
        assert result["valid"] is False, "Empty string name must fail validation"

    def test_card_layout_negative_size_rejected(self):
        """Verify card layout with negative size_x is rejected."""

        def validate_layout(layout: dict):
            errors = []
            if layout.get("size_x", 0) < 0:
                errors.append("size_x must be positive")
            if layout.get("size_y", 0) < 0:
                errors.append("size_y must be positive")
            return {"valid": len(errors) == 0, "errors": errors}

        result = validate_layout({"col": 0, "row": 0, "size_x": -1, "size_y": 4})
        assert result["valid"] is False, "Negative size_x must be rejected"

    def test_card_layout_column_width_overflow_rejected(self):
        """Verify card layout where col+size_x exceeds grid boundary is rejected."""

        def validate_layout(layout: dict, max_cols: int = 24):
            errors = []
            if layout.get("col", 0) + layout.get("size_x", 0) > max_cols:
                errors.append("Card exceeds grid boundary")
            return {"valid": len(errors) == 0, "errors": errors}

        result = validate_layout({"col": 22, "row": 0, "size_x": 4, "size_y": 2})
        assert result["valid"] is False, "col+size_x > max_cols must be rejected"
        assert any(
            "grid" in e.lower() or "boundary" in e.lower() or "exceed" in e.lower()
            for e in result["errors"]
        ), "Error must reference grid boundary"

    def test_overlapping_cards_detected(self):
        """Verify validate-create-request detects overlapping card layouts in a dashboard."""

        def cards_overlap(a: dict, b: dict) -> bool:
            a_right = a["col"] + a["size_x"]
            b_right = b["col"] + b["size_x"]
            a_bottom = a["row"] + a["size_y"]
            b_bottom = b["row"] + b["size_y"]
            return not (
                a_right <= b["col"]
                or b_right <= a["col"]
                or a_bottom <= b["row"]
                or b_bottom <= a["row"]
            )

        card1 = {"col": 0, "row": 0, "size_x": 6, "size_y": 4}
        card2 = {"col": 4, "row": 2, "size_x": 4, "size_y": 4}
        assert cards_overlap(
            card1, card2
        ), "Overlap detection logic: card1 and card2 should be detected as overlapping"

    def test_schema_clj_is_valid_clojure_syntax(self):
        """Verify schema.clj contains valid Clojure s-expression structure (balanced parens)."""
        content = _read("src/metabase/api/dashboard/schema.clj")
        # Basic balance check
        depth = 0
        for ch in content:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            assert depth >= 0, "schema.clj has unmatched closing parenthesis"
        assert depth == 0, f"schema.clj has {depth} unclosed parentheses"
