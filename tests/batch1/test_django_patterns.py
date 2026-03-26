"""
Test for 'django-patterns' skill — Django Design Patterns in Saleor
Validates that the Agent implemented Django best practices including
custom model managers, signals, middleware, and proper migrations.
"""

import os
import subprocess
import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestDjangoPatterns.REPO_DIR)


class TestDjangoPatterns:
    """Verify Django design patterns in Saleor."""

    REPO_DIR = "/workspace/saleor"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_custom_manager_exists(self):
        """A custom model manager file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "manager" in f.lower():
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No custom manager .py file found"

    def test_middleware_exists(self):
        """A custom middleware file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "middleware" in f.lower():
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No middleware .py file found"

    def test_signals_file_exists(self):
        """A signals file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "signal" in f.lower():
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No signals .py file found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def test_custom_manager_uses_queryset(self):
        """Custom manager must use QuerySet methods."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "manager" in f.lower():
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    qs_patterns = [
                        "Manager",
                        "QuerySet",
                        "get_queryset",
                        "objects",
                        "models.Manager",
                    ]
                    if any(p in content for p in qs_patterns):
                        return
        pytest.fail("No manager using QuerySet found")

    def test_middleware_has_process_methods(self):
        """Middleware must implement __call__ or process_request."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "middleware" in f.lower():
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    method_patterns = [
                        "__call__",
                        "process_request",
                        "process_response",
                        "process_view",
                        "MiddlewareMixin",
                    ]
                    if any(p in content for p in method_patterns):
                        return
        pytest.fail("No middleware with proper methods found")

    def test_signals_use_receiver(self):
        """Signals must use @receiver decorator or signal.connect."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "signal" in f.lower():
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    signal_patterns = [
                        "@receiver",
                        ".connect(",
                        "post_save",
                        "pre_save",
                        "Signal()",
                        "django.dispatch",
                    ]
                    if any(p in content for p in signal_patterns):
                        return
        pytest.fail("No signal with @receiver or .connect found")

    def test_migration_exists(self):
        """New migration file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "migrations" in root:
                for f in files:
                    if f.endswith(".py") and f != "__init__.py":
                        found = True
                        break
            if found:
                break
        assert found, "No migration files found"

    def test_manage_py_check(self):
        """python manage.py check must pass."""
        result = subprocess.run(
            ["python", "manage.py", "check"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "DJANGO_SETTINGS_MODULE": "saleor.settings"},
        )
        assert result.returncode == 0, f"manage.py check failed:\n{result.stderr}"

    def test_files_compile(self):
        """All new Python files must compile."""
        targets = ["manager", "middleware", "signal"]
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and any(t in f.lower() for t in targets):
                    fpath = os.path.join(root, f)
                    result = subprocess.run(
                        ["python", "-m", "py_compile", fpath],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    assert (
                        result.returncode == 0
                    ), f"{fpath} failed to compile:\n{result.stderr}"

    def test_model_has_meta_class(self):
        """Models should define Meta class with ordering or indexes."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "model" in f.lower():
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    meta_patterns = [
                        "class Meta:",
                        "ordering",
                        "indexes",
                        "verbose_name",
                        "db_table",
                    ]
                    if any(p in content for p in meta_patterns):
                        found = True
                        break
            if found:
                break
        assert found, "No model with Meta class found"

    def test_type_hints_present(self):
        """New Python code should use type hints."""
        type_found = False
        targets = ["manager", "middleware", "signal"]
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and any(t in f.lower() for t in targets):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    type_patterns = [
                        "-> ",
                        ": str",
                        ": int",
                        ": bool",
                        ": list",
                        ": dict",
                        "Optional[",
                        "QuerySet[",
                        "Type[",
                    ]
                    if any(p in content for p in type_patterns):
                        type_found = True
                        break
            if type_found:
                break
        assert type_found, "No type hints in new code"
