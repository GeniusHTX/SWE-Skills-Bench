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
