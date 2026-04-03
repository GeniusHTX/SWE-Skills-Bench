"""
Test for 'django-patterns' skill — Django Product Manager for Saleor
Validates that the Agent implemented custom QuerySet managers, model methods,
signals, and GraphQL structure for the Saleor product module.
"""

import ast
import glob
import os
import re

import pytest


class TestDjangoPatterns:
    """Verify Django design patterns in the Saleor product module."""

    REPO_DIR = "/workspace/saleor"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _managers_text(self):
        return self._read(os.path.join(self.REPO_DIR, "saleor/product/managers.py"))

    def _models_text(self):
        return self._read(os.path.join(self.REPO_DIR, "saleor/product/models.py"))

    def _method_names(self):
        tree = ast.parse(self._managers_text())
        return [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]

    # ---- file_path_check ----

    def test_managers_py_exists(self):
        """Verifies saleor/product/managers.py exists."""
        path = os.path.join(self.REPO_DIR, "saleor/product/managers.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_models_py_exists(self):
        """Verifies saleor/product/models.py exists."""
        path = os.path.join(self.REPO_DIR, "saleor/product/models.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_views_py_exists(self):
        """Verifies saleor/product/views.py exists."""
        path = os.path.join(self.REPO_DIR, "saleor/product/views.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_graphql_product_dir_exists(self):
        """Verifies saleor/graphql/product/ directory exists."""
        path = os.path.join(self.REPO_DIR, "saleor/graphql/product/")
        assert os.path.exists(path), f"Directory not found: {path}"

    # ---- semantic_check ----

    def test_sem_active_method_text(self):
        """Verifies 'def active' or 'active()' in managers."""
        text = self._managers_text()
        assert (
            "def active" in text or "active()" in text
        ), "'active' method not found in managers.py"

    def test_sem_active_in_method_names(self):
        """Verifies 'active' method via AST."""
        names = self._method_names()
        assert "active" in names, "'active' not in parsed method names"

    def test_sem_available_in_channel(self):
        """Verifies 'available_in_channel' method via AST."""
        names = self._method_names()
        assert (
            "available_in_channel" in names
        ), "'available_in_channel' not in method names"

    def test_sem_ast_parseable(self):
        """Verifies managers.py is valid Python (AST-parseable)."""
        tree = ast.parse(self._managers_text())
        assert tree is not None

    # ---- functional_check ----

    def test_func_is_published_filter(self):
        """Verifies 'is_published' and 'filter' in managers."""
        text = self._managers_text()
        assert (
            "is_published" in text and "filter" in text
        ), "'is_published' filter not found in managers"

    def test_func_get_absolute_url(self):
        """Verifies get_absolute_url in models.py."""
        text = self._models_text()
        assert "get_absolute_url" in text, "'get_absolute_url' not found in models.py"

    def test_func_slug_and_products_url(self):
        """Verifies 'slug' and '/products/' in models."""
        text = self._models_text()
        assert (
            "slug" in text and "/products/" in text
        ), "'slug' or '/products/' missing in models.py"

    def test_func_signals_files_exist(self):
        """Verifies at least one signals.py exists."""
        signals_files = glob.glob(
            os.path.join(self.REPO_DIR, "saleor/**/signals.py"),
            recursive=True,
        )
        assert len(signals_files) >= 1, "No signals.py files found"

    def test_func_post_save_signal(self):
        """Verifies post_save signal in some signals.py."""
        signals_files = glob.glob(
            os.path.join(self.REPO_DIR, "saleor/**/signals.py"),
            recursive=True,
        )
        assert any(
            "post_save" in self._read(f) for f in signals_files
        ), "'post_save' not found in any signals.py"

    def test_func_created_signal(self):
        """Verifies 'created' keyword in some signals.py."""
        signals_files = glob.glob(
            os.path.join(self.REPO_DIR, "saleor/**/signals.py"),
            recursive=True,
        )
        assert any(
            "created" in self._read(f) for f in signals_files
        ), "'created' not found in any signals.py"

    def test_func_select_related(self):
        """Verifies select_related usage in managers or product code."""
        managers_text = self._managers_text()
        all_py = glob.glob(
            os.path.join(self.REPO_DIR, "saleor/product/**/*.py"),
            recursive=True,
        )
        select_related_used = "select_related" in managers_text or any(
            "select_related" in self._read(f) for f in all_py
        )
        assert select_related_used, "'select_related' not used anywhere"

    def test_func_active_missing_is_published(self):
        """Failure case: active() must include is_published filter."""
        text = self._managers_text()
        assert "is_published" in text, "active() is missing is_published filter"

    def test_func_graphql_schema_file(self):
        """Verifies graphql product has a schema/types file."""
        gql_dir = os.path.join(self.REPO_DIR, "saleor/graphql/product/")
        files = os.listdir(gql_dir) if os.path.isdir(gql_dir) else []
        assert len(files) > 0, "GraphQL product directory is empty"
