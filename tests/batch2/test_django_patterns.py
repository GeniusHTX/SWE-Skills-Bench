"""
Test for 'django-patterns' skill — Django Low-Stock Alerts
Validates that the Agent created a low-stock alert feature for saleor
with Django models, REST views, serializers, URL routes, and alerting logic.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestDjangoPatterns.REPO_DIR)


class TestDjangoPatterns:
    """Verify Django low-stock alert feature for saleor."""

    REPO_DIR = "/workspace/saleor"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_alert_files(self):
        """Find the stock alert module files."""
        results = {}
        for root, _dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                path = os.path.join(root, f)
                if f == "models.py" and "stock_alert" in root.replace("\\", "/"):
                    results["models"] = path
                elif f == "views.py" and "stock_alert" in root.replace("\\", "/"):
                    results["views"] = path
                elif f == "serializers.py" and "stock_alert" in root.replace("\\", "/"):
                    results["serializers"] = path
                elif f == "urls.py" and "stock_alert" in root.replace("\\", "/"):
                    results["urls"] = path
        # Fallback: look for stock_alert in warehouse or other module
        if not results:
            for root, _dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if f.endswith(".py"):
                        path = os.path.join(root, f)
                        try:
                            with open(path, "r", errors="ignore") as fh:
                                text = fh.read()
                            if "StockAlert" in text:
                                if f == "models.py":
                                    results.setdefault("models", path)
                                elif f == "views.py":
                                    results.setdefault("views", path)
                                elif f == "serializers.py":
                                    results.setdefault("serializers", path)
                                elif f == "urls.py":
                                    results.setdefault("urls", path)
                        except Exception:
                            pass
        return results

    # ------------------------------------------------------------------
    # L1: Model file existence and structure
    # ------------------------------------------------------------------

    def test_stock_alert_model_exists(self):
        """A models.py containing StockAlert must exist."""
        files = self._find_alert_files()
        assert "models" in files, "No models.py with StockAlert found"

    def test_model_compiles(self):
        """The models.py file must be syntactically valid."""
        files = self._find_alert_files()
        assert "models" in files
        result = subprocess.run(
            ["python", "-m", "py_compile", files["models"]],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_stock_alert_model_fields(self):
        """StockAlert model must have required fields."""
        files = self._find_alert_files()
        assert "models" in files
        with open(files["models"], "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"class\s+StockAlert", content), "StockAlert class not defined"
        required_fields = ["product", "warehouse", "threshold"]
        found = [
            f for f in required_fields if re.search(rf"{f}", content, re.IGNORECASE)
        ]
        assert len(found) >= 2, f"StockAlert only has {len(found)} of {required_fields}"

    def test_stock_alert_config_model(self):
        """StockAlertConfig model should exist for alert configuration."""
        files = self._find_alert_files()
        assert "models" in files
        with open(files["models"], "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"class\s+StockAlertConfig",
            r"class\s+AlertConfig",
            r"threshold",
            r"enabled",
        ]
        found = sum(1 for p in patterns if re.search(p, content))
        assert (
            found >= 2
        ), "StockAlertConfig or threshold configuration not defined in models"

    # ------------------------------------------------------------------
    # L1: Views and serializers
    # ------------------------------------------------------------------

    def test_views_file_exists(self):
        """A views.py for stock alerts must exist."""
        files = self._find_alert_files()
        assert "views" in files, "No views.py with StockAlert found"

    def test_views_compile(self):
        """views.py must be syntactically valid."""
        files = self._find_alert_files()
        assert "views" in files
        result = subprocess.run(
            ["python", "-m", "py_compile", files["views"]],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_serializers_exist(self):
        """A serializers.py for stock alerts must exist."""
        files = self._find_alert_files()
        assert "serializers" in files, "No serializers.py with StockAlert found"

    def test_urls_exist(self):
        """A urls.py for stock alert endpoints must exist."""
        files = self._find_alert_files()
        assert "urls" in files, "No urls.py with StockAlert routes found"

    # ------------------------------------------------------------------
    # L2: REST endpoint patterns
    # ------------------------------------------------------------------

    def test_views_define_crud_endpoints(self):
        """Views must define list/create/detail endpoints."""
        files = self._find_alert_files()
        assert "views" in files
        with open(files["views"], "r", errors="ignore") as fh:
            content = fh.read()
        crud_patterns = [
            r"list|List",
            r"create|Create",
            r"retrieve|detail|Detail",
            r"update|Update",
            r"delete|Delete|destroy",
        ]
        found = sum(1 for p in crud_patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, f"Only {found} CRUD operation(s) in views — need at least 2"

    def test_serializer_fields(self):
        """Serializers must declare model fields."""
        files = self._find_alert_files()
        assert "serializers" in files
        with open(files["serializers"], "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"class\s+\w*StockAlert\w*Serializer", content
        ), "No StockAlert serializer class found"
        assert re.search(r"fields", content), "Serializer does not declare fields"

    def test_urls_register_routes(self):
        """URL configuration must register stock alert routes."""
        files = self._find_alert_files()
        assert "urls" in files
        with open(files["urls"], "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"urlpatterns", r"path\(", r"router", r"register", r"url\("]
        assert any(
            re.search(p, content) for p in patterns
        ), "urls.py does not register any routes"

    # ------------------------------------------------------------------
    # L2: Alert threshold logic
    # ------------------------------------------------------------------

    def test_threshold_trigger_logic(self):
        """Alert logic must check stock against threshold."""
        files = self._find_alert_files()
        found_logic = False
        for key in ("models", "views"):
            if key not in files:
                continue
            with open(files[key], "r", errors="ignore") as fh:
                content = fh.read()
            patterns = [
                r"quantity.*threshold",
                r"stock.*<=",
                r"below.*threshold",
                r"alert.*trigger",
                r"check.*stock",
                r"low.*stock",
            ]
            if any(re.search(p, content, re.IGNORECASE) for p in patterns):
                found_logic = True
                break
        assert found_logic, "No threshold trigger logic found in models or views"

    def test_duplicate_alert_prevention(self):
        """System must prevent duplicate alerts."""
        files = self._find_alert_files()
        found = False
        for key in ("models", "views"):
            if key not in files:
                continue
            with open(files[key], "r", errors="ignore") as fh:
                content = fh.read()
            patterns = [
                r"get_or_create",
                r"unique_together",
                r"exists\(\)",
                r"filter.*exists",
                r"UniqueConstraint",
                r"duplicate",
                r"already.*exist",
            ]
            if any(re.search(p, content, re.IGNORECASE) for p in patterns):
                found = True
                break
        assert found, "No duplicate alert prevention mechanism found"
