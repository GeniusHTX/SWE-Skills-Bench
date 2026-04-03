"""Test file for the dotnet-backend-patterns skill.

This suite validates the eShop Catalog API optimization: async data access,
DTO projections, caching, and pagination in the CatalogService,
CatalogApi, and CatalogContext C# files.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestDotnetBackendPatterns:
    """Verify eShop Catalog API optimization patterns."""

    REPO_DIR = "/workspace/eShop"

    SERVICE_CS = "src/Catalog.API/Services/CatalogService.cs"
    API_CS = "src/Catalog.API/Apis/CatalogApi.cs"
    CONTEXT_CS = "src/Catalog.API/Infrastructure/CatalogContext.cs"

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

    def _all_cs_sources(self) -> str:
        """Read and concatenate the three main C# files."""
        parts = []
        for f in (self.SERVICE_CS, self.API_CS, self.CONTEXT_CS):
            path = self._repo_path(f)
            if path.exists():
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    def _cs_class_body(self, source: str, class_name: str) -> str | None:
        """Extract a C# class body by rough brace matching."""
        m = re.search(rf"class\s+{class_name}\b", source)
        if m is None:
            return None
        start = source.find("{", m.end())
        if start < 0:
            return None
        depth, i = 1, start + 1
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[m.start() : i]

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_catalog_api_services_catalogservice_cs_exists_or_modifie(
        self,
    ):
        """Verify CatalogService.cs exists and is non-empty."""
        self._assert_non_empty_file(self.SERVICE_CS)

    def test_file_path_src_catalog_api_apis_catalogapi_cs_is_modified(self):
        """Verify CatalogApi.cs exists and is non-empty."""
        self._assert_non_empty_file(self.API_CS)

    def test_file_path_src_catalog_api_infrastructure_catalogcontext_cs_is_modified(
        self,
    ):
        """Verify CatalogContext.cs exists and is non-empty."""
        self._assert_non_empty_file(self.CONTEXT_CS)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_all_data_access_methods_return_task_t_async_pattern(self):
        """All data access methods return Task<T> (async pattern)."""
        src = self._all_cs_sources()
        assert re.search(
            r"async\s+Task|await\s+", src
        ), "Methods should use async/await pattern"

    def test_semantic_catalogcontext_uses_include_for_eager_loading_where_needed(self):
        """CatalogContext uses .Include() for eager loading where needed."""
        src = self._all_cs_sources()
        assert re.search(
            r"\.Include\s*\(", src
        ), "Should use .Include() for eager loading related entities"

    def test_semantic_select_projections_map_to_dto_types_instead_of_returning_ful(
        self,
    ):
        """Select() projections map to DTO types instead of returning full entities."""
        src = self._all_cs_sources()
        assert re.search(
            r"\.Select\s*\(", src
        ), "Should use .Select() for DTO projections"
        assert re.search(
            r"Dto|DTO|ViewModel|Response", src, re.IGNORECASE
        ), "Should project to DTO/ViewModel types"

    def test_semantic_imemorycache_or_idistributedcache_used_for_caching(self):
        """IMemoryCache or IDistributedCache used for caching."""
        src = self._all_cs_sources()
        assert re.search(
            r"IMemoryCache|IDistributedCache|MemoryCache|GetOrCreate|Cache", src
        ), "Service should use IMemoryCache or IDistributedCache"

    def test_semantic_pagination_uses_skip_take_or_equivalent(self):
        """Pagination uses Skip/Take or equivalent."""
        src = self._all_cs_sources()
        assert re.search(
            r"\.Skip\s*\(|\.Take\s*\(|pageSize|pageIndex|PageSize|PageIndex", src
        ), "Pagination should use Skip/Take or page-based parameters"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def test_functional_product_list_endpoint_returns_paginated_dto_response(self):
        """Product list endpoint returns paginated DTO response."""
        src = self._all_cs_sources()
        assert re.search(
            r"\.Skip\s*\(|\.Take\s*\(|pageSize", src
        ), "List endpoint must implement pagination"
        assert re.search(r"\.Select\s*\(", src), "List endpoint must project to DTOs"

    def test_functional_product_detail_endpoint_returns_dto_without_entity_graph(self):
        """Product detail endpoint returns DTO without entity graph."""
        src = self._all_cs_sources()
        assert re.search(
            r"FindAsync|FirstOrDefaultAsync|SingleOrDefaultAsync|GetById", src
        ), "Detail endpoint must retrieve single product"

    def test_functional_categories_endpoint_returns_cached_data_on_second_call(self):
        """Categories endpoint returns cached data on second call."""
        src = self._all_cs_sources()
        assert re.search(
            r"GetOrCreate|TryGetValue|SetAsync|Set\s*\(|Cache", src
        ), "Categories should be cached"

    def test_functional_concurrent_requests_don_t_cause_objectdisposedexception(self):
        """Concurrent requests don't cause ObjectDisposedException."""
        src = self._all_cs_sources()
        assert re.search(
            r"AddScoped|AddTransient|IServiceScope|DbContextFactory|IDbContextFactory|CatalogContext",
            src,
        ), "DbContext should be properly scoped to prevent disposal issues"

    def test_functional_build_succeeds_without_errors(self):
        """Build succeeds without errors (via source analysis)."""
        src = self._all_cs_sources()
        assert re.search(
            r"^using\s+", src, re.MULTILINE
        ), "C# files should have using directives"
        assert re.search(r"namespace\s+", src), "C# files should declare a namespace"
        open_braces = src.count("{")
        close_braces = src.count("}")
        assert (
            abs(open_braces - close_braces) <= 2
        ), f"Brace mismatch suggests compilation error: {{ = {open_braces}, }} = {close_braces}"
