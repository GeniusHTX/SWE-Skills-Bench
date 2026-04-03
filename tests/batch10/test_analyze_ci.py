"""
Test for 'analyze-ci' skill — Sentry CI Failure Analyzer
Validates that the Agent created a CI failure analyzer CLI tool for Sentry,
including GitHub client, log parser, and analysis reporting.
"""

import os
import re

import pytest


class TestAnalyzeCi:
    """Verify Sentry CI failure analyzer implementation."""

    REPO_DIR = "/workspace/sentry"

    def test_ci_analyzer_cli_exists(self):
        """CI analyzer CLI entry point must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"argparse|click|typer", content) and re.search(r"ci.*analy|analyze.*ci|failure.*analy", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "CI analyzer CLI not found"

    def test_github_client_module_exists(self):
        """GitHub client module for fetching CI data must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and ("github" in f.lower() or "client" in f.lower()):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"github|GitHub|actions|workflow", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "GitHub client module not found"

    def test_log_parser_exists(self):
        """Log parser for CI failure logs must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"parse.*log|log.*pars|LogParser|parse_failure", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Log parser not found"

    def test_github_api_token_from_env(self):
        """GitHub API token must be read from environment variable."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and ("github" in f.lower() or "client" in f.lower() or "ci" in f.lower()):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"os\.environ|os\.getenv|GITHUB_TOKEN|GH_TOKEN", content):
                        found = True
                        break
            if found:
                break
        assert found, "GitHub token not read from environment"

    def test_analyzer_produces_report(self):
        """Analyzer must produce a structured report output."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"report|summary|output|json\.dump|print.*result", content, re.IGNORECASE) and re.search(r"ci|failure|analy", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Analyzer does not produce a report"

    def test_failure_categorization_logic(self):
        """Analyzer must categorize failures (flaky, infra, code, timeout, etc.)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"flaky|infrastructure|timeout|oom|categor", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No failure categorization logic found"

    def test_cli_accepts_repo_argument(self):
        """CLI must accept repository name/URL as argument."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"add_argument.*repo|--repo|repo.*arg|repository", content):
                        found = True
                        break
            if found:
                break
        assert found, "CLI does not accept repo argument"

    def test_error_handling_for_api_failures(self):
        """GitHub API failures must be handled gracefully."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and ("github" in f.lower() or "client" in f.lower()):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"except|try:|raise|HTTPError|RequestException", content):
                        found = True
                        break
            if found:
                break
        assert found, "No error handling for API failures"

    def test_rate_limiting_awareness(self):
        """GitHub client should handle rate limiting."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"rate.limit|retry|sleep|backoff|429", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No rate limiting handling found"

    def test_workflow_run_fetching(self):
        """Client must fetch workflow run data from GitHub Actions API."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"actions/runs|workflow_runs|workflow.*run", content):
                        found = True
                        break
            if found:
                break
        assert found, "No workflow run fetching logic found"

    def test_tests_exist_for_analyzer(self):
        """Test files for the CI analyzer must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ci.*analy|analyzer|log.*pars|failure", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No test files for CI analyzer"
