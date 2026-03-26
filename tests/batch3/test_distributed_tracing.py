"""
Tests for distributed-tracing skill.
Validates OpenTelemetry trace analysis processor in opentelemetry-collector repository.
"""

import os
import subprocess
import pytest

REPO_DIR = "/workspace/opentelemetry-collector"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestDistributedTracing:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_processor_go_files_exist(self):
        """factory.go, config.go, and processor.go must exist in traceanalysisprocessor."""
        for rel in [
            "processor/traceanalysisprocessor/factory.go",
            "processor/traceanalysisprocessor/config.go",
            "processor/traceanalysisprocessor/processor.go",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    def test_processor_test_file_exists(self):
        """processor_test.go must exist."""
        rel = "processor/traceanalysisprocessor/processor_test.go"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_config_struct_defined(self):
        """config.go must define Config struct with SamplingRate field."""
        content = _read("processor/traceanalysisprocessor/config.go")
        assert "type Config struct" in content, "Config struct not found in config.go"
        assert (
            "SamplingRate" in content or "sampling_rate" in content
        ), "SamplingRate field not found in config.go"

    def test_factory_go_registers_processor(self):
        """factory.go must implement NewFactory and component type registration."""
        content = _read("processor/traceanalysisprocessor/factory.go")
        assert (
            "func NewFactory" in content
        ), "NewFactory function not found in factory.go"
        assert (
            "component.MustNewType" in content or "processorhelper" in content
        ), "Component type registration not found in factory.go"

    def test_processor_implements_traces_processor(self):
        """processor.go must implement ConsumeTraces or ProcessTraces method."""
        content = _read("processor/traceanalysisprocessor/processor.go")
        assert (
            "ConsumeTraces" in content or "ProcessTraces" in content
        ), "ConsumeTraces/ProcessTraces method not found in processor.go"

    def test_processor_adds_span_count_attribute(self):
        """processor.go must reference span_count and/or service_count attributes."""
        content = _read("processor/traceanalysisprocessor/processor.go")
        assert (
            "span_count" in content or "service_count" in content
        ), "span_count/service_count attribute keys not found in processor.go"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_go_tests_pass(self):
        """All Go unit tests in the processor package must pass."""
        result = _run("go test ./processor/traceanalysisprocessor/... -v")
        if result.returncode != 0 and "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"go test failed:\n{result.stdout}\n{result.stderr}"
        assert "PASS" in result.stdout

    def test_config_validates_negative_sampling_rate(self):
        """Config.Validate() must return error for sampling_rate=-0.1."""
        result = _run(
            "go test ./processor/traceanalysisprocessor/... -run TestConfigValidate -v"
        )
        if result.returncode != 0 and "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert result.returncode == 0, f"TestConfigValidate failed:\n{result.stdout}"
        assert "PASS" in result.stdout

    def test_same_trace_id_consistent_sampling(self):
        """Deterministic sampling: same trace ID must always yield the same decision."""
        result = _run(
            "go test ./processor/traceanalysisprocessor/... -run TestDeterministicSampling -v"
        )
        if result.returncode != 0 and "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"TestDeterministicSampling failed:\n{result.stdout}"

    def test_error_trace_sampled_at_low_rate(self):
        """Error traces must always be sampled regardless of configured rate."""
        result = _run(
            "go test ./processor/traceanalysisprocessor/... -run TestErrorTraceSampling -v"
        )
        if result.returncode != 0 and "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert (
            result.returncode == 0
        ), f"TestErrorTraceSampling failed:\n{result.stdout}"

    def test_orphan_span_logs_warning(self):
        """Processor must log a warning for orphan spans (no parent in trace)."""
        result = _run(
            "go test ./processor/traceanalysisprocessor/... -run TestOrphanSpanWarning -v"
        )
        if result.returncode != 0 and "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert result.returncode == 0, f"TestOrphanSpanWarning failed:\n{result.stdout}"

    def test_go_build_compiles_without_errors(self):
        """The processor package must compile without errors."""
        result = _run("go build ./processor/traceanalysisprocessor/...")
        if result.returncode != 0 and "no required module" in result.stderr:
            pytest.skip("Go module not available")
        assert result.returncode == 0, f"go build failed:\n{result.stderr}"
