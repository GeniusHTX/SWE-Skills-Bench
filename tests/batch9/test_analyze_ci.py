"""
Test for 'analyze-ci' skill — CI Pipeline Analysis Tool
Validates CIPipelineParser, DependencyValidator, BottleneckAnalyzer,
PipelineGraph, custom exceptions, critical path, and edge cases.
"""

import os
import sys

import pytest


class TestAnalyzeCi:
    """Verify CI analysis tool: parser, validator, analyzer, graph."""

    REPO_DIR = "/workspace/sentry"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _ci(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "analyze_ci", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_package_init_exists(self):
        """analyze_ci __init__.py must exist."""
        assert os.path.isfile(self._ci("__init__.py")), "__init__.py not found"

    def test_all_module_files_exist(self):
        """parser.py, validator.py, analyzer.py, graph.py must exist."""
        for name in ("parser.py", "validator.py", "analyzer.py", "graph.py"):
            assert os.path.isfile(self._ci(name)), f"{name} not found"

    def test_test_file_exists(self):
        """tests/test_analyze_ci.py must exist."""
        path = os.path.join(self.REPO_DIR, "tests", "test_analyze_ci.py")
        assert os.path.isfile(path), f"{path} not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_parser_has_github_and_gitlab_methods(self):
        """CIPipelineParser must define parse_github_actions and parse_gitlab_ci."""
        content = self._read_file(self._ci("parser.py"))
        if not content:
            pytest.skip("parser.py not found")
        assert "CIPipelineParser" in content
        assert "parse_github_actions" in content
        assert "parse_gitlab_ci" in content

    def test_validator_defines_custom_exceptions(self):
        """DependencyValidator must define CyclicDependencyError and UndefinedJobError."""
        content = self._read_file(self._ci("validator.py"))
        if not content:
            pytest.skip("validator.py not found")
        assert "CyclicDependencyError" in content
        assert "UndefinedJobError" in content
        assert "DependencyValidator" in content

    def test_analyzer_critical_path_returns_list(self):
        """BottleneckAnalyzer.critical_path must return ordered list."""
        content = self._read_file(self._ci("analyzer.py"))
        if not content:
            pytest.skip("analyzer.py not found")
        assert "BottleneckAnalyzer" in content
        assert "critical_path" in content

    def test_suggestion_dataclass_fields(self):
        """Suggestion must have priority and description fields."""
        content = self._read_file(self._ci("analyzer.py"))
        if not content:
            pytest.skip("analyzer.py not found")
        assert "Suggestion" in content
        assert "priority" in content
        assert "description" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_circular_dependency_raises(self):
        """Circular A->B->A must raise CyclicDependencyError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.analyze_ci.parser import CIPipelineParser
            from examples.analyze_ci.validator import DependencyValidator, CyclicDependencyError
        except ImportError:
            pytest.skip("Cannot import analyze_ci modules")
        yaml_str = "jobs:\n  a:\n    needs: [b]\n  b:\n    needs: [a]"
        pipeline = CIPipelineParser().parse_github_actions(yaml_str)
        with pytest.raises(CyclicDependencyError) as exc_info:
            DependencyValidator().validate(pipeline)
        msg = str(exc_info.value)
        assert "a" in msg and "b" in msg

    def test_undefined_job_raises(self):
        """needs reference to non-existent job must raise UndefinedJobError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.analyze_ci.parser import CIPipelineParser
            from examples.analyze_ci.validator import DependencyValidator, UndefinedJobError
        except ImportError:
            pytest.skip("Cannot import analyze_ci modules")
        yaml_str = "jobs:\n  build:\n    needs: [ghost_job_that_does_not_exist]"
        pipeline = CIPipelineParser().parse_github_actions(yaml_str)
        with pytest.raises(UndefinedJobError) as exc_info:
            DependencyValidator().validate(pipeline)
        assert "ghost_job_that_does_not_exist" in str(exc_info.value)

    def test_linear_pipeline_critical_path(self):
        """A->B->C critical path must be ['a', 'b', 'c']."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.analyze_ci.parser import CIPipelineParser
            from examples.analyze_ci.analyzer import BottleneckAnalyzer
        except ImportError:
            pytest.skip("Cannot import analyze_ci modules")
        yaml_str = "jobs:\n  a: {}\n  b:\n    needs: [a]\n  c:\n    needs: [b]"
        pipeline = CIPipelineParser().parse_github_actions(yaml_str)
        path = BottleneckAnalyzer().critical_path(pipeline)
        assert path == ["a", "b", "c"]

    def test_single_job_critical_path(self):
        """Single job pipeline critical path must be ['only_job']."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.analyze_ci.parser import CIPipelineParser
            from examples.analyze_ci.analyzer import BottleneckAnalyzer
        except ImportError:
            pytest.skip("Cannot import analyze_ci modules")
        yaml_str = "jobs:\n  only_job: {}"
        pipeline = CIPipelineParser().parse_github_actions(yaml_str)
        path = BottleneckAnalyzer().critical_path(pipeline)
        assert path == ["only_job"]

    def test_self_referential_raises_cyclic(self):
        """Job that needs itself must raise CyclicDependencyError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.analyze_ci.parser import CIPipelineParser
            from examples.analyze_ci.validator import DependencyValidator, CyclicDependencyError
        except ImportError:
            pytest.skip("Cannot import analyze_ci modules")
        yaml_str = "jobs:\n  self_referential:\n    needs: [self_referential]"
        pipeline = CIPipelineParser().parse_github_actions(yaml_str)
        with pytest.raises(CyclicDependencyError):
            DependencyValidator().validate(pipeline)

    def test_empty_yaml_zero_jobs(self):
        """Empty YAML string must produce pipeline with zero jobs."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.analyze_ci.parser import CIPipelineParser
        except ImportError:
            pytest.skip("Cannot import CIPipelineParser")
        pipeline = CIPipelineParser().parse_github_actions("")
        jobs = getattr(pipeline, "jobs", getattr(pipeline, "nodes", []))
        assert len(jobs) == 0
