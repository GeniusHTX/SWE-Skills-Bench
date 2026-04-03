"""Test file for the analyze-ci skill.

This suite validates the ci_analysis package layout, analyzer semantics, and
runtime classification behavior expected in the sentry repository.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib.util
import inspect
import json
import pathlib
import py_compile
import re
import subprocess
import sys
import textwrap
import types

import pytest


class TestAnalyzeCi:
    """Verify the Sentry CI failure analyzer implementation."""

    REPO_DIR = "/workspace/sentry"
    _setup_attempted = False
    _setup_ok = False
    _setup_reason = ""

    def _repo_path(self, relative_path: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative_path.split("/"))

    def _read_text(self, relative_path: str) -> str:
        path = self._repo_path(relative_path)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _compile_python(self, relative_path: str) -> pathlib.Path:
        path = self._repo_path(relative_path)
        assert path.is_file(), f"Expected Python file to exist: {path}"
        py_compile.compile(str(path), doraise=True)
        return path

    def _parse_ast(self, relative_path: str) -> ast.Module:
        return ast.parse(self._read_text(relative_path))

    @classmethod
    def _ensure_optional_setup(cls) -> None:
        if cls._setup_attempted:
            if not cls._setup_ok:
                pytest.skip(cls._setup_reason)
            return
        cls._setup_attempted = True
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "django", "djangorestframework"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            cls._setup_reason = (
                "Skipping setup-dependent Sentry test because pip install failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
            pytest.skip(cls._setup_reason)
        cls._setup_ok = True

    def _ensure_package_stub(
        self, package_name: str, package_path: pathlib.Path
    ) -> None:
        if package_name in sys.modules:
            module = sys.modules[package_name]
            if getattr(module, "__path__", None) is None:
                module.__path__ = [str(package_path)]
            return
        module = types.ModuleType(package_name)
        module.__path__ = [str(package_path)]
        sys.modules[package_name] = module

    def _load_module_from_path(self, module_name: str, file_path: pathlib.Path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        assert spec and spec.loader, f"Could not create module spec for {file_path}"
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _load_analyzer_module(self):
        src_dir = self._repo_path("src")
        ci_dir = self._repo_path("src/sentry/ci_analysis")
        self._ensure_package_stub("sentry", src_dir / "sentry")
        self._ensure_package_stub("sentry.ci_analysis", ci_dir)

        models_stub = types.ModuleType("sentry.ci_analysis.models")

        class CIBuildFailure:  # pragma: no cover - simple import stub
            pass

        models_stub.CIBuildFailure = CIBuildFailure
        sys.modules["sentry.ci_analysis.models"] = models_stub

        analyzer_path = ci_dir / "analyzer.py"
        try:
            return self._load_module_from_path(
                "sentry.ci_analysis.analyzer", analyzer_path
            )
        except ModuleNotFoundError as error:
            missing = str(error)
            if "django" in missing or "rest_framework" in missing:
                self._ensure_optional_setup()
                return self._load_module_from_path(
                    "sentry.ci_analysis.analyzer", analyzer_path
                )
            raise

    def _normalize(self, value):
        if dataclasses.is_dataclass(value):
            return {
                key: self._normalize(item)
                for key, item in dataclasses.asdict(value).items()
            }
        if isinstance(value, dict):
            return {key: self._normalize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._normalize(item) for item in value]
        if hasattr(value, "__dict__") and not isinstance(value, type):
            return {
                key: self._normalize(item)
                for key, item in vars(value).items()
                if not key.startswith("_")
            }
        return value

    def _invoke_analyze(self, raw_log: str) -> dict:
        analyzer_module = self._load_analyzer_module()
        analyzer_cls = getattr(analyzer_module, "CIFailureAnalyzer", None)
        assert analyzer_cls is not None, "Expected CIFailureAnalyzer to be defined"

        instance = None
        try:
            instance = analyzer_cls()
        except TypeError:
            instance = analyzer_cls.__new__(analyzer_cls)

        candidates = []
        if hasattr(instance, "analyze"):
            candidates.append(getattr(instance, "analyze"))
        if hasattr(analyzer_cls, "analyze"):
            candidates.append(getattr(analyzer_cls, "analyze"))

        for candidate in candidates:
            attempts = [
                lambda: candidate(raw_log),
                lambda: candidate(raw_log=raw_log),
                lambda: candidate(log=raw_log),
                lambda: candidate(raw_log.splitlines()),
                lambda: candidate(lines=raw_log.splitlines()),
            ]
            for attempt in attempts:
                try:
                    return self._normalize(attempt())
                except TypeError:
                    continue

        pytest.fail(
            "Could not invoke CIFailureAnalyzer.analyze with any supported calling convention"
        )

    def test_file_path_src_sentry_ci_analysis___init___py_exists(self) -> None:
        """Verify that the ci_analysis package initializer exists and compiles as valid Python."""
        self._compile_python("src/sentry/ci_analysis/__init__.py")

    def test_file_path_src_sentry_ci_analysis_models_py_exists_with_cibuildfailure_(
        self,
    ) -> None:
        """Verify that models.py exists, compiles, and defines the CIBuildFailure model class."""
        self._compile_python("src/sentry/ci_analysis/models.py")
        tree = self._parse_ast("src/sentry/ci_analysis/models.py")
        class_names = {
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        }
        assert (
            "CIBuildFailure" in class_names
        ), f"Expected CIBuildFailure model class, got: {sorted(class_names)}"

    def test_file_path_src_sentry_ci_analysis_analyzer_py_exists_with_cifailureanal(
        self,
    ) -> None:
        """Verify that analyzer.py exists, compiles, and defines the CIFailureAnalyzer class."""
        self._compile_python("src/sentry/ci_analysis/analyzer.py")
        tree = self._parse_ast("src/sentry/ci_analysis/analyzer.py")
        class_names = {
            node.name for node in tree.body if isinstance(node, ast.ClassDef)
        }
        assert (
            "CIFailureAnalyzer" in class_names
        ), f"Expected CIFailureAnalyzer class, got: {sorted(class_names)}"

    def test_semantic_cibuildfailure_model_has_all_required_fields_organization_re(
        self,
    ) -> None:
        """Verify that the CIBuildFailure model declares the expected persistence fields for CI failures."""
        tree = self._parse_ast("src/sentry/ci_analysis/models.py")
        required_fields = {
            "organization",
            "repository",
            "workflow_name",
            "job_name",
            "run_id",
            "job_id",
            "failure_type",
            "status",
            "raw_log",
            "analysis_result",
            "created_at",
            "analyzed_at",
        }
        class_node = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "CIBuildFailure"
        )
        field_names = set()
        for statement in class_node.body:
            if isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        field_names.add(target.id)
            if isinstance(statement, ast.AnnAssign) and isinstance(
                statement.target, ast.Name
            ):
                field_names.add(statement.target.id)
        missing = sorted(required_fields - field_names)
        assert not missing, f"Expected CIBuildFailure fields to include {missing}"

    def test_semantic_cibuildfailure_has_indexes_on_organization_repository_reposi(
        self,
    ) -> None:
        """Verify that models.py defines index metadata covering repository and failure lookup patterns."""
        content = self._read_text("src/sentry/ci_analysis/models.py")
        assert re.search(
            r"indexes|index_together", content
        ), "Expected model index metadata in models.py"
        assert re.search(r"organization", content) and re.search(
            r"repository", content
        ), "Expected repository index fields to include organization and repository"
        assert re.search(
            r"created_at", content
        ), "Expected repository time index to include created_at"
        assert re.search(
            r"failure_type", content
        ), "Expected an index or lookup path for failure_type"

    def test_semantic_cifailureanalyzer_analyze_returns_analysisresult_dataclass(
        self,
    ) -> None:
        """Verify that analyzer.py defines an AnalysisResult dataclass and that analyze constructs or returns it."""
        tree = self._parse_ast("src/sentry/ci_analysis/analyzer.py")
        analysis_result = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "AnalysisResult"
        )
        decorator_names = {
            decorator.id
            for decorator in analysis_result.decorator_list
            if isinstance(decorator, ast.Name)
        }
        assert (
            "dataclass" in decorator_names
        ), "Expected AnalysisResult to be a dataclass"

        analyzer_class = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "CIFailureAnalyzer"
        )
        analyze_method = next(
            node
            for node in analyzer_class.body
            if isinstance(node, ast.FunctionDef) and node.name == "analyze"
        )
        method_source = (
            ast.get_source_segment(
                self._read_text("src/sentry/ci_analysis/analyzer.py"), analyze_method
            )
            or ""
        )
        assert (
            "AnalysisResult" in method_source
        ), "Expected analyze to construct or return AnalysisResult"

    def test_semantic_classification_uses_regex_patterns_for_each_failure_type(
        self,
    ) -> None:
        """Verify that analyzer.py classifies failures through regex-driven patterns for multiple failure categories."""
        content = self._read_text("src/sentry/ci_analysis/analyzer.py")
        categories = {
            "test_failure",
            "build_error",
            "timeout",
            "infrastructure",
            "dependency",
        }
        present = {name for name in categories if name in content}
        assert (
            present == categories
        ), f"Expected all classifier categories, got: {sorted(present)}"
        regex_uses = len(re.findall(r"re\.(?:compile|search|findall|match)", content))
        assert (
            regex_uses >= 3
        ), "Expected regex-based failure classification logic in analyzer.py"

    def test_semantic_traceback_extraction_captures_from_traceback_most_recent_cal(
        self,
    ) -> None:
        """Verify that analyzer.py contains traceback extraction logic spanning from the Traceback header to the final exception."""
        content = self._read_text("src/sentry/ci_analysis/analyzer.py")
        assert (
            "Traceback (most recent call last):" in content
        ), "Expected traceback extraction to anchor on the standard Python traceback header"
        assert re.search(
            r"exception|traceback|stack", content, re.IGNORECASE
        ), "Expected analyzer.py to retain traceback or exception context"

    def test_functional_log_with_failed_tests_test_auth_py_testlogin_test_invalid_pa(
        self,
    ) -> None:
        """Verify that pytest FAILED output is classified as a test failure and preserves failed test identity."""
        result = self._invoke_analyze(
            """
            ============================= test session starts =============================
            FAILED tests/test_auth.py::TestLogin::test_invalid_password - AssertionError: expected 403
            Traceback (most recent call last):
              File \"tests/test_auth.py\", line 44, in test_invalid_password
                assert response.status_code == 403
            AssertionError: expected 403
            """.strip()
        )
        serialized = json.dumps(result)
        assert "test_failure" in serialized, result
        assert (
            "tests/test_auth.py::TestLogin::test_invalid_password" in serialized
        ), result

    def test_functional_log_with_error_cannot_find_crate_for_serde_classified_as_bui(
        self,
    ) -> None:
        """Verify via a subprocess invocation that a build-tool error is classified as a build_error result."""
        analyzer_path = self._repo_path("src/sentry/ci_analysis/analyzer.py")
        command = textwrap.dedent(
            f"""
            import dataclasses
            import importlib.util
            import json
            import pathlib
            import sys
            import types

            analyzer_path = pathlib.Path({str(analyzer_path)!r})
            src_dir = analyzer_path.parent.parent.parent
            ci_dir = analyzer_path.parent

            sentry_pkg = types.ModuleType("sentry")
            sentry_pkg.__path__ = [str(src_dir / "sentry")]
            sys.modules["sentry"] = sentry_pkg

            ci_pkg = types.ModuleType("sentry.ci_analysis")
            ci_pkg.__path__ = [str(ci_dir)]
            sys.modules["sentry.ci_analysis"] = ci_pkg

            models_stub = types.ModuleType("sentry.ci_analysis.models")
            class CIBuildFailure:
                pass
            models_stub.CIBuildFailure = CIBuildFailure
            sys.modules["sentry.ci_analysis.models"] = models_stub

            spec = importlib.util.spec_from_file_location("sentry.ci_analysis.analyzer", analyzer_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["sentry.ci_analysis.analyzer"] = module
            spec.loader.exec_module(module)

            analyzer_cls = module.CIFailureAnalyzer
            try:
                instance = analyzer_cls()
            except TypeError:
                instance = analyzer_cls.__new__(analyzer_cls)

            method = getattr(instance, "analyze", getattr(analyzer_cls, "analyze"))
            log_text = "error: cannot find crate for serde"
            for candidate in (
                lambda: method(log_text),
                lambda: method(raw_log=log_text),
                lambda: method(log=log_text),
                lambda: method(log_text.splitlines()),
                lambda: method(lines=log_text.splitlines()),
            ):
                try:
                    value = candidate()
                    break
                except TypeError:
                    continue
            else:
                raise RuntimeError("Could not invoke analyzer")

            if dataclasses.is_dataclass(value):
                value = dataclasses.asdict(value)
            elif hasattr(value, "__dict__"):
                value = {{key: val for key, val in vars(value).items() if not key.startswith("_")}}

            print(json.dumps(value, default=str))
            """
        )
        result = subprocess.run(
            [sys.executable, "-c", command],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            "Expected analyzer subprocess to succeed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        payload = json.loads(result.stdout.strip())
        assert "build_error" in json.dumps(payload), payload

    def test_functional_log_with_exceeded_the_maximum_time_limit_classified_as_timeo(
        self,
    ) -> None:
        """Verify that timeout-oriented log text is classified as a timeout result."""
        result = self._invoke_analyze(
            "Job exceeded the maximum time limit after 3600 seconds"
        )
        assert "timeout" in json.dumps(result), result

    def test_functional_log_with_no_space_left_on_device_classified_as_infrastructur(
        self,
    ) -> None:
        """Verify that infrastructure failures such as disk exhaustion are classified as infrastructure issues."""
        result = self._invoke_analyze(
            """
            collecting ...
            OSError: [Errno 28] No space left on device
            Traceback (most recent call last):
              File \"build.py\", line 12, in <module>
                raise OSError("No space left on device")
            """.strip()
        )
        serialized = json.dumps(result)
        assert "infrastructure" in serialized, result
        assert "No space left on device" in serialized, result

    def test_functional_log_with_could_not_resolve_dependencies_classified_as_depend(
        self,
    ) -> None:
        """Verify that dependency-resolution failures are classified as dependency issues."""
        result = self._invoke_analyze(
            "Could not resolve dependencies for project lockfile"
        )
        assert "dependency" in json.dumps(result), result
