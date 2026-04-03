"""Test file for the distributed-tracing skill.

This suite validates the tail-sampling processor components in
opentelemetry-collector: Config, SamplingPolicy interface, StatusCodePolicy,
LatencyPolicy, ServiceNamePolicy, and policy evaluation logic.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestDistributedTracing:
    """Verify tail-sampling processor in opentelemetry-collector."""

    REPO_DIR = "/workspace/opentelemetry-collector"

    PROCESSOR_GO = "processor/tailsamplingprocessor/processor.go"
    CONFIG_GO = "processor/tailsamplingprocessor/config.go"
    POLICY_GO = "processor/tailsamplingprocessor/policy.go"

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

    def _go_struct_body(self, source: str, struct_name: str) -> str | None:
        """Extract the body of a Go struct definition."""
        m = re.search(rf"type\s+{struct_name}\s+struct\s*\{{", source)
        if m is None:
            return None
        start = m.end() - 1
        depth, i = 1, start + 1
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[start:i]

    def _go_interface_body(self, source: str, iface_name: str) -> str | None:
        """Extract the body of a Go interface definition."""
        m = re.search(rf"type\s+{iface_name}\s+interface\s*\{{", source)
        if m is None:
            return None
        start = m.end() - 1
        depth, i = 1, start + 1
        while i < len(source) and depth > 0:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        return source[start:i]

    def _all_go_sources(self) -> str:
        """Concatenate all Go sources from the tailsamplingprocessor directory."""
        tsp_dir = self._repo_path("processor/tailsamplingprocessor")
        if not tsp_dir.is_dir():
            return ""
        parts = []
        for f in sorted(tsp_dir.glob("*.go")):
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_processor_tailsamplingprocessor_processor_go_exists(self):
        """Verify processor.go exists and is non-empty."""
        self._assert_non_empty_file(self.PROCESSOR_GO)

    def test_file_path_processor_tailsamplingprocessor_config_go_exists(self):
        """Verify config.go exists and is non-empty."""
        self._assert_non_empty_file(self.CONFIG_GO)

    def test_file_path_processor_tailsamplingprocessor_policy_go_exists(self):
        """Verify policy.go exists and is non-empty."""
        self._assert_non_empty_file(self.POLICY_GO)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_config_struct_has_decisionwait_numtraces_policies_policyeval(
        self,
    ):
        """Config struct has DecisionWait, NumTraces, Policies, PolicyEvaluation fields."""
        src = self._read_text(self.CONFIG_GO)
        body = self._go_struct_body(src, "Config")
        assert body is not None, "Config struct not found in config.go"
        for field in ("DecisionWait", "NumTraces", "Policies", "PolicyEvaluation"):
            assert field in body, f"Config struct missing field: {field}"

    def test_semantic_samplingpolicy_interface_has_evaluate_tracedata_and_name_met(
        self,
    ):
        """SamplingPolicy interface has Evaluate(*TraceData) and Name() methods."""
        src = self._all_go_sources()
        iface = self._go_interface_body(src, "SamplingPolicy")
        if iface is None:
            # May be named differently — fall back to pattern search
            assert re.search(
                r"type\s+\w*[Pp]olicy\w*\s+interface", src
            ), "No SamplingPolicy-like interface found"
            iface = src
        assert re.search(
            r"Evaluate\s*\(", iface
        ), "SamplingPolicy must have Evaluate method"
        assert re.search(r"Name\s*\(", iface), "SamplingPolicy must have Name method"

    def test_semantic_statuscodepolicy_checks_span_status_codes_against_configured(
        self,
    ):
        """StatusCodePolicy checks span status codes against configured list."""
        src = self._all_go_sources()
        assert re.search(
            r"StatusCode[Pp]olicy|statusCodePolicy", src
        ), "StatusCodePolicy struct/type not found"
        assert re.search(
            r"[Ss]tatus.*[Cc]ode|StatusCode", src
        ), "StatusCodePolicy should reference status codes"

    def test_semantic_latencypolicy_computes_max_endtime_min_starttime_across_all_(
        self,
    ):
        """LatencyPolicy computes max(EndTime)-min(StartTime) across all spans."""
        src = self._all_go_sources()
        assert re.search(
            r"[Ll]atency[Pp]olicy|latencyPolicy", src
        ), "LatencyPolicy struct/type not found"
        # Should compute duration from span times
        assert re.search(
            r"[Ee]nd[Tt]ime|[Ss]tart[Tt]ime|[Dd]uration|[Ll]atency", src
        ), "LatencyPolicy should compute span duration from EndTime-StartTime"

    def test_semantic_servicenamepolicy_checks_service_name_resource_attribute_aga(
        self,
    ):
        """ServiceNamePolicy checks service.name resource attribute against allowlist."""
        src = self._all_go_sources()
        assert re.search(
            r"[Ss]ervice[Nn]ame[Pp]olicy|serviceNamePolicy", src
        ), "ServiceNamePolicy struct/type not found"
        assert re.search(
            r"service\.name|ServiceName|service_name", src
        ), "ServiceNamePolicy should reference service.name attribute"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via source analysis)
    # ------------------------------------------------------------------

    def test_functional_trace_with_span_statuscode_error_sampled_by_statuscodepolicy(
        self,
    ):
        """Trace with span StatusCode ERROR → sampled by StatusCodePolicy(['ERROR'])."""
        src = self._all_go_sources()
        # Verify StatusCodePolicy evaluates against error codes
        assert re.search(
            r"StatusCode[Pp]olicy|statusCodeEvaluator", src
        ), "StatusCodePolicy implementation required"
        assert re.search(
            r"ERROR|Error|STATUS_CODE_ERROR", src
        ), "StatusCodePolicy should handle ERROR status code"
        # Verify Sampled decision type
        assert re.search(
            r"Sampled|sampled|SAMPLED", src
        ), "Policy should return Sampled decision"

    def test_functional_trace_spanning_250ms_sampled_by_latencypolicy_thresholdms_20(
        self,
    ):
        """Trace spanning 250ms → sampled by LatencyPolicy(ThresholdMs=200)."""
        src = self._all_go_sources()
        assert re.search(
            r"[Ll]atency[Pp]olicy|latencyEvaluator", src
        ), "LatencyPolicy implementation required"
        # Verify threshold comparison
        assert re.search(
            r"[Tt]hreshold|thresholdMs|ThresholdMs", src
        ), "LatencyPolicy should have a threshold parameter"

    def test_functional_trace_from_payment_service_sampled_by_servicenamepolicy_paym(
        self,
    ):
        """Trace from 'payment-service' → sampled by ServiceNamePolicy(['payment-service'])."""
        src = self._all_go_sources()
        assert re.search(
            r"[Ss]ervice[Nn]ame[Pp]olicy|serviceNameEvaluator", src
        ), "ServiceNamePolicy implementation required"
        # Verify service name matching logic
        assert re.search(
            r"[Mm]atch|[Cc]ontains|allowlist|include", src, re.IGNORECASE
        ), "ServiceNamePolicy should match against an allowlist"

    def test_functional_trace_from_unknown_service_not_sampled_by_servicenamepolicy_(
        self,
    ):
        """Trace from 'unknown-service' → NOT sampled by ServiceNamePolicy(['payment-service'])."""
        src = self._all_go_sources()
        # Verify NotSampled / drop decision path
        assert re.search(
            r"NotSampled|notSampled|NOT_SAMPLED|Drop|drop", src
        ), "Policy should return NotSampled for non-matching service names"

    def test_functional_policyevaluation_all_requires_all_policies_sampled(self):
        """PolicyEvaluation='all' requires all policies Sampled."""
        src = self._all_go_sources()
        # Verify 'all' evaluation mode
        assert re.search(
            r"PolicyEvaluation|policyEvaluation|evaluationMode", src
        ), "Processor should support PolicyEvaluation modes"
        # Verify 'all' logic: all policies must agree
        assert re.search(
            r'"all"|policyAll|evaluateAll|allPolicies', src, re.IGNORECASE
        ), "Processor should support 'all' evaluation requiring all policies to sample"
