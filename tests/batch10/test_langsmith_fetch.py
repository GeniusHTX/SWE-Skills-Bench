"""
Test for 'langsmith-fetch' skill — LangSmith fetch integration in langchain
Validates that the Agent implemented LangSmith data fetching patterns
within the langchain project.
"""

import os
import re

import pytest


class TestLangsmithFetch:
    """Verify LangSmith fetch integration in langchain."""

    REPO_DIR = "/workspace/langchain"

    def test_langsmith_client_usage(self):
        """Code must use LangSmith client or SDK."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"langsmith|LangSmith|lang_smith", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No LangSmith client usage found"

    def test_fetch_runs_or_traces(self):
        """Code must fetch runs, traces, or feedback from LangSmith."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"langsmith", content, re.IGNORECASE):
                        if re.search(r"list_runs|read_run|get_run|fetch|list_examples|list_feedback", content):
                            found = True
                            break
            if found:
                break
        assert found, "No fetch runs/traces functionality found"

    def test_api_key_configuration(self):
        """LangSmith API key must be configured via environment or parameter."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"LANGCHAIN_API_KEY|LANGSMITH_API_KEY|api_key", content):
                        if re.search(r"langsmith|LangSmith", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "No LangSmith API key configuration found"

    def test_project_name_parameter(self):
        """Code must accept a project name parameter."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"langsmith", content, re.IGNORECASE):
                        if re.search(r"project_name|project_id|LANGCHAIN_PROJECT", content):
                            found = True
                            break
            if found:
                break
        assert found, "No project name parameter found"

    def test_data_processing_or_filtering(self):
        """Fetched data must be processed or filtered."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"langsmith", content, re.IGNORECASE):
                        if re.search(r"filter|process|transform|parse|convert|format", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "No data processing found"

    def test_error_handling(self):
        """LangSmith fetch code must handle errors."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"langsmith", content, re.IGNORECASE):
                        if re.search(r"try:|except|raise|LangSmithError|APIError", content):
                            found = True
                            break
            if found:
                break
        assert found, "No error handling in LangSmith fetch code"

    def test_callback_or_tracing_handler(self):
        """Code should use callbacks or tracing handlers."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"LangChainTracer|CallbackHandler|tracing_enabled|callbacks", content):
                        found = True
                        break
            if found:
                break
        assert found, "No callback or tracing handler found"

    def test_output_format(self):
        """Results should be output or returned in a structured format."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"langsmith", content, re.IGNORECASE):
                        if re.search(r"return|json|dict|DataFrame|print|output", content):
                            found = True
                            break
            if found:
                break
        assert found, "No structured output format found"

    def test_pagination_or_limit(self):
        """Fetch operations should support pagination or limit."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"langsmith", content, re.IGNORECASE):
                        if re.search(r"limit|offset|page|max_results|batch_size", content):
                            found = True
                            break
            if found:
                break
        assert found, "No pagination or limit support found"

    def test_python_file_with_langsmith_import(self):
        """A Python file must import from langsmith."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"from\s+langsmith|import\s+langsmith", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Python file imports langsmith"
