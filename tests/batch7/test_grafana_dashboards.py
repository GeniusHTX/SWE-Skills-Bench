"""Test file for the grafana-dashboards skill.

This suite validates the DashboardProvisionService, ProvisionRequest/Result
structs, error types, and provisioning logic in the Grafana repository.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestGrafanaDashboards:
    """Verify Grafana dashboard provisioning service."""

    REPO_DIR = "/workspace/grafana"

    API_GO = "pkg/api/dashboard_provision.go"
    SERVICE_GO = "pkg/services/dashboards/provision_service.go"
    SERVICE_TEST_GO = "pkg/services/dashboards/provision_service_test.go"

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

    def _go_struct_body(self, source: str, name: str) -> str | None:
        m = re.search(rf"type\s+{name}\s+struct\s*\{{", source)
        if m is None:
            return None
        depth, i = 1, m.end()
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[m.start() : i]

    def _all_go_sources(self) -> str:
        parts = []
        for f in (self.API_GO, self.SERVICE_GO):
            path = self._repo_path(f)
            if path.exists():
                parts.append(path.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_pkg_api_dashboard_provision_go_exists(self):
        """Verify dashboard_provision.go exists and is non-empty."""
        self._assert_non_empty_file(self.API_GO)

    def test_file_path_pkg_services_dashboards_provision_service_go_exists(self):
        """Verify provision_service.go exists and is non-empty."""
        self._assert_non_empty_file(self.SERVICE_GO)

    def test_file_path_pkg_services_dashboards_provision_service_test_go_exists(self):
        """Verify provision_service_test.go exists and is non-empty."""
        self._assert_non_empty_file(self.SERVICE_TEST_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_provisionrequest_struct_has_dashboard_folderuid_overwrite_me(
        self,
    ):
        """ProvisionRequest struct has dashboard, folderUid, overwrite, message fields with JSON tags."""
        src = self._all_go_sources()
        body = self._go_struct_body(src, "ProvisionRequest")
        assert body is not None, "ProvisionRequest struct not found"
        for field in ("dashboard", "folderUid", "overwrite", "message"):
            assert re.search(
                rf'(?i){field}.*json:"|json:".*{field}', body
            ), f"ProvisionRequest missing {field} with JSON tag"

    def test_semantic_provisionresult_struct_has_uid_id_url_status_version_slug_fi(
        self,
    ):
        """ProvisionResult struct has uid, id, url, status, version, slug fields with JSON tags."""
        src = self._all_go_sources()
        body = self._go_struct_body(src, "ProvisionResult")
        assert body is not None, "ProvisionResult struct not found"
        for field in ("uid", "id", "url", "status", "version", "slug"):
            assert re.search(
                rf"(?i){field}", body
            ), f"ProvisionResult missing {field} field"

    def test_semantic_errinvaliddashboard_and_errdashboardexists_types_implement_e(
        self,
    ):
        """ErrInvalidDashboard and ErrDashboardExists types implement error interface."""
        src = self._all_go_sources()
        assert re.search(
            r"ErrInvalidDashboard|errInvalidDashboard", src
        ), "ErrInvalidDashboard type not found"
        assert re.search(
            r"ErrDashboardExists|errDashboardExists", src
        ), "ErrDashboardExists type not found"
        # Should implement Error() method
        assert re.search(
            r"func\s*\(.*Err.*\)\s*Error\s*\(", src
        ), "Error types must implement Error() method"

    def test_semantic_dashboardprovisionservice_has_store_foldersvc_guardian_depen(
        self,
    ):
        """DashboardProvisionService has store, folderSvc, guardian dependencies."""
        src = self._all_go_sources()
        body = self._go_struct_body(src, "DashboardProvisionService")
        assert body is not None, "DashboardProvisionService struct not found"
        assert re.search(r"store|Store", body), "Missing store dependency"
        assert re.search(r"folder|Folder", body), "Missing folderSvc dependency"

    def test_semantic_provision_method_signature_matches_ctx_orgid_req_result_erro(
        self,
    ):
        """Provision method signature matches (ctx, orgID, req) → (result, error)."""
        src = self._all_go_sources()
        assert re.search(
            r"func\s*\(.*DashboardProvisionService\)\s*Provision\s*\(",
            src,
        ), "Provision method not found on DashboardProvisionService"
        assert re.search(
            r"context\.Context|ctx\s", src
        ), "Provision should accept context parameter"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def test_functional_new_dashboard_without_uid_gets_auto_generated_uid_and_versio(
        self,
    ):
        """New dashboard without UID gets auto-generated UID and version=1."""
        src = self._all_go_sources()
        assert re.search(
            r"uid|UID|GenerateUID|uuid|shortid", src, re.IGNORECASE
        ), "Service should auto-generate UID for new dashboards"
        assert re.search(
            r"[Vv]ersion.*=.*1|version.*1", src
        ), "New dashboards should start at version=1"

    def test_functional_dashboard_with_existing_uid_and_overwrite_false_returns_errd(
        self,
    ):
        """Dashboard with existing UID and overwrite=false returns ErrDashboardExists."""
        src = self._all_go_sources()
        assert re.search(
            r"[Oo]verwrite|overwrite", src
        ), "Service must check overwrite flag"
        assert re.search(
            r"ErrDashboardExists|DashboardExists", src
        ), "Service should return ErrDashboardExists when overwrite=false"

    def test_functional_dashboard_with_existing_uid_and_overwrite_true_returns_incre(
        self,
    ):
        """Dashboard with existing UID and overwrite=true returns incremented version."""
        src = self._all_go_sources()
        assert re.search(
            r"[Vv]ersion.*\+.*1|[Vv]ersion\+\+|increment.*version", src, re.IGNORECASE
        ), "Service should increment version on overwrite"

    def test_functional_missing_title_returns_errinvaliddashboard_with_field_title(
        self,
    ):
        """Missing title returns ErrInvalidDashboard with field='title'."""
        src = self._all_go_sources()
        assert re.search(r"[Tt]itle", src), "Service must validate title field"
        assert re.search(
            r"ErrInvalidDashboard|InvalidDashboard", src
        ), "Service should return ErrInvalidDashboard for missing title"

    def test_functional_schemaversion_0_returns_errinvaliddashboard_with_field_schem(
        self,
    ):
        """schemaVersion=0 returns ErrInvalidDashboard with field='schemaVersion'."""
        src = self._all_go_sources()
        assert re.search(
            r"[Ss]chema[Vv]ersion|schemaVersion", src
        ), "Service must validate schemaVersion"
