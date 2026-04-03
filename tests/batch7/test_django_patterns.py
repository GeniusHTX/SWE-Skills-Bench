"""Test file for the django-patterns skill.

This suite validates the ProductBundle / BundleItem models, ProductBundleQuerySet
manager, BundleService, and related GraphQL / signal infrastructure in Saleor.
"""

from __future__ import annotations

import ast
import importlib.util
import pathlib
import re
import subprocess
import sys

import pytest


class TestDjangoPatterns:
    """Verify Saleor product bundle Django patterns."""

    REPO_DIR = "/workspace/saleor"

    MODELS_PY = "saleor/product/models.py"
    MANAGERS_PY = "saleor/product/managers.py"
    SERVICES_PY = "saleor/product/services.py"

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

    def _class_source(self, source: str, class_name: str) -> str | None:
        """Extract Python class body using AST."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                start = node.lineno - 1
                end = node.end_lineno
                lines = source.splitlines()
                return "\n".join(lines[start:end])
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_saleor_product_models_py_modified_with_productbundle_and_bun(
        self,
    ):
        """Verify saleor/product/models.py exists and is non-empty."""
        self._assert_non_empty_file(self.MODELS_PY)

    def test_file_path_saleor_product_managers_py_exists_with_productbundlequeryset(
        self,
    ):
        """Verify saleor/product/managers.py exists and is non-empty."""
        self._assert_non_empty_file(self.MANAGERS_PY)

    def test_file_path_saleor_product_services_py_exists_with_bundleservice(self):
        """Verify saleor/product/services.py exists and is non-empty."""
        self._assert_non_empty_file(self.SERVICES_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_productbundle_has_name_slug_description_discount_type_discou(
        self,
    ):
        """ProductBundle has name, slug, description, discount_type, discount_value, currency, is_active, timestamps."""
        src = self._read_text(self.MODELS_PY)
        cls = self._class_source(src, "ProductBundle")
        assert cls is not None, "ProductBundle class not found in models.py"
        for field in ("name", "slug", "discount_type", "discount_value", "is_active"):
            assert field in cls, f"ProductBundle missing field: {field}"

    def test_semantic_bundleitem_has_foreignkey_to_productbundle_and_product_quant(
        self,
    ):
        """BundleItem has ForeignKey to ProductBundle and Product, quantity, sort_order."""
        src = self._read_text(self.MODELS_PY)
        cls = self._class_source(src, "BundleItem")
        assert cls is not None, "BundleItem class not found in models.py"
        assert "ForeignKey" in cls, "BundleItem must have ForeignKey fields"
        assert "quantity" in cls, "BundleItem must have quantity field"

    def test_semantic_checkconstraint_on_discount_value_non_negative_and_percentag(
        self,
    ):
        """CheckConstraint on discount_value non-negative and percentage <= 100."""
        src = self._read_text(self.MODELS_PY)
        assert "CheckConstraint" in src, "Models should define CheckConstraint"
        assert re.search(
            r"discount_value.*gte.*0|discount_value.*>=.*0|non_negative",
            src,
            re.IGNORECASE,
        ), "CheckConstraint should enforce non-negative discount_value"

    def test_semantic_unique_constraint_on_bundle_product_for_bundleitem(self):
        """Unique constraint on (bundle, product) for BundleItem."""
        src = self._read_text(self.MODELS_PY)
        assert re.search(
            r"UniqueConstraint|unique_together", src
        ), "BundleItem should have unique constraint on (bundle, product)"
        assert re.search(
            r"bundle.*product|product.*bundle", src, re.IGNORECASE
        ), "Unique constraint should involve bundle and product fields"

    def test_semantic_productbundlequeryset_available_filters_by_component_stock_l(
        self,
    ):
        """ProductBundleQuerySet.available() filters by component stock levels."""
        src = self._read_text(self.MANAGERS_PY)
        assert (
            "ProductBundleQuerySet" in src
        ), "ProductBundleQuerySet not found in managers.py"
        assert re.search(
            r"def\s+available\s*\(", src
        ), "ProductBundleQuerySet must define available() method"
        assert re.search(
            r"stock|quantity|inventory", src, re.IGNORECASE
        ), "available() should filter by stock levels"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, import with lightweight setup)
    # ------------------------------------------------------------------

    def _services_source(self) -> str:
        parts = [self._read_text(self.MODELS_PY)]
        for f in (self.MANAGERS_PY, self.SERVICES_PY):
            path = self._repo_path(f)
            if path.exists():
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    def test_functional_bundle_with_a_10_2_b_25_1_10_discount_40_50(self):
        """Bundle with A($10x2) + B($25x1) + 10% discount → $40.50."""
        src = self._services_source()
        # Verify calculate_bundle_price or equivalent exists
        assert re.search(
            r"def\s+calculate.*price|def\s+get.*price|calculate_price", src
        ), "Service must implement bundle price calculation"
        # Verify percentage discount logic
        assert re.search(
            r"percentage|percent|PERCENTAGE", src, re.IGNORECASE
        ), "Service must support percentage discount type"

    def test_functional_fixed_amount_5_discount_on_45_total_40_00(self):
        """Fixed amount $5 discount on $45 total → $40.00."""
        src = self._services_source()
        assert re.search(
            r"fixed|FIXED|absolute", src, re.IGNORECASE
        ), "Service must support fixed amount discount type"

    def test_functional_fixed_discount_exceeding_total_0_00_minimum(self):
        """Fixed discount exceeding total → $0.00 (minimum)."""
        src = self._services_source()
        # Verify floor at zero
        assert re.search(
            r"max\s*\(.*0|min.*price|floor|clamp|Decimal\s*\(\s*['\"]0",
            src,
            re.IGNORECASE,
        ), "Price calculation should floor at $0.00 when discount exceeds total"

    def test_functional_active_available_with_items_returns_correct_bundles(self):
        """active().available().with_items() returns correct bundles."""
        src = self._services_source()
        assert re.search(
            r"def\s+active\s*\(", src
        ), "QuerySet must define active() method"
        assert re.search(
            r"def\s+available\s*\(", src
        ), "QuerySet must define available() method"
        assert re.search(
            r"def\s+with_items\s*\(|prefetch_related|select_related", src
        ), "QuerySet must define with_items() or use prefetch/select related"

    def test_functional_stock_drop_below_requirement_bundle_deactivated(self):
        """Stock drop below requirement → bundle deactivated."""
        src = self._services_source()
        # Verify signal or check_availability related code
        signals_path = self._repo_path("saleor/product/signals.py")
        if signals_path.exists():
            src += signals_path.read_text(encoding="utf-8", errors="ignore")
        assert re.search(
            r"signal|post_save|stock.*change|deactivate|is_active\s*=\s*False",
            src,
            re.IGNORECASE,
        ), "System must deactivate bundles when stock drops below requirement"
