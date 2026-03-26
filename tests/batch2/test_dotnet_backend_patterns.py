"""
Test for 'dotnet-backend-patterns' skill — Catalog Service Optimization
Validates that the Agent optimized the eShop Catalog API with async patterns,
DTO projections, caching, and concurrent data access improvements.
"""

import os
import re

import pytest


class TestDotnetBackendPatterns:
    """Verify eShop Catalog API optimization."""

    REPO_DIR = "/workspace/eshop"
    CATALOG_DIR = "src/Catalog.API"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_cs_file(self, name):
        """Find a .cs file by name under the Catalog.API directory."""
        catalog = os.path.join(self.REPO_DIR, self.CATALOG_DIR)
        for root, _dirs, files in os.walk(catalog):
            if name in files:
                return os.path.join(root, name)
        return None

    # ------------------------------------------------------------------
    # L1: Key files exist
    # ------------------------------------------------------------------

    def test_catalog_service_exists(self):
        """CatalogService.cs must exist."""
        path = self._find_cs_file("CatalogService.cs")
        assert path is not None, "CatalogService.cs not found"

    def test_catalog_api_exists(self):
        """CatalogApi.cs must exist."""
        path = self._find_cs_file("CatalogApi.cs")
        assert path is not None, "CatalogApi.cs not found"

    def test_catalog_context_exists(self):
        """CatalogContext.cs must exist."""
        path = self._find_cs_file("CatalogContext.cs")
        assert path is not None, "CatalogContext.cs not found"

    # ------------------------------------------------------------------
    # L2: Async patterns
    # ------------------------------------------------------------------

    def test_service_uses_async(self):
        """CatalogService.cs must use async/await patterns."""
        path = self._find_cs_file("CatalogService.cs")
        assert path is not None
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"async\s+Task", content
        ), "CatalogService does not use async Task methods"
        assert re.search(r"await\s+", content), "CatalogService does not use await"

    def test_api_uses_async(self):
        """CatalogApi.cs must use async endpoints."""
        path = self._find_cs_file("CatalogApi.cs")
        assert path is not None
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"async", r"Task<", r"await"]
        found = sum(1 for p in patterns if re.search(p, content))
        assert found >= 2, "CatalogApi does not use async patterns"

    # ------------------------------------------------------------------
    # L2: DTO projections
    # ------------------------------------------------------------------

    def test_has_dto_definitions(self):
        """Catalog API must define response DTOs."""
        catalog = os.path.join(self.REPO_DIR, self.CATALOG_DIR)
        found = False
        for root, _dirs, files in os.walk(catalog):
            for f in files:
                if f.endswith(".cs"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"class\s+\w+(Dto|DTO|Response|ViewModel)", text):
                        found = True
                        break
        assert found, "No DTO or response class found"

    def test_uses_select_projections(self):
        """Queries should use Select projections instead of full entities."""
        catalog = os.path.join(self.REPO_DIR, self.CATALOG_DIR)
        found = False
        for root, _dirs, files in os.walk(catalog):
            for f in files:
                if f.endswith(".cs"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"\.Select\(", text):
                        found = True
                        break
        assert found, "No Select() projection found in queries"

    # ------------------------------------------------------------------
    # L2: Caching
    # ------------------------------------------------------------------

    def test_implements_caching(self):
        """Service should implement caching for read-only data."""
        path = self._find_cs_file("CatalogService.cs")
        assert path is not None
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"IMemoryCache",
            r"IDistributedCache",
            r"cache",
            r"Cache",
            r"GetOrCreate",
            r"CacheEntry",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "CatalogService does not implement caching"

    # ------------------------------------------------------------------
    # L2: Optimized queries
    # ------------------------------------------------------------------

    def test_eager_loading_or_includes(self):
        """Queries should use eager loading or Include()."""
        catalog = os.path.join(self.REPO_DIR, self.CATALOG_DIR)
        found = False
        for root, _dirs, files in os.walk(catalog):
            for f in files:
                if f.endswith(".cs"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"\.Include\(|\.ThenInclude\(", text):
                        found = True
                        break
        assert found, "No eager loading (Include) found"

    def test_efficient_pagination(self):
        """Pagination should use Skip/Take or equivalent."""
        catalog = os.path.join(self.REPO_DIR, self.CATALOG_DIR)
        found = False
        for root, _dirs, files in os.walk(catalog):
            for f in files:
                if f.endswith(".cs"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"\.Skip\(|\.Take\(|pageSize|PageSize", text):
                        found = True
                        break
        assert found, "No efficient pagination (Skip/Take) found"

    # ------------------------------------------------------------------
    # L2: Concurrency safety
    # ------------------------------------------------------------------

    def test_proper_scope_for_dbcontext(self):
        """DbContext should be properly scoped or injected."""
        path = self._find_cs_file("CatalogService.cs")
        assert path is not None
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"CatalogContext", r"DbContext", r"IServiceScope", r"constructor"]
        assert any(
            re.search(p, content) for p in patterns
        ), "CatalogService does not properly manage DbContext"
