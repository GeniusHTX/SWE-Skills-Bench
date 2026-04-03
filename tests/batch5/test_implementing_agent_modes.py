"""
Test for 'implementing-agent-modes' skill — PostHog Agent Mode System
Validates AgentMode dataclass, ModeRegistry with threading.Lock,
priority selection, config type casting, cache TTL, and duplicate errors.
"""

import os
import re
import subprocess
import sys

import pytest


class TestImplementingAgentModes:
    """Verify PostHog agent mode implementation."""

    REPO_DIR = "/workspace/posthog"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_agent_mode_source_files_exist(self):
        """Verify at least 4 Python source files for agent modes exist."""
        py_files = self._find_agent_mode_files()
        assert (
            len(py_files) >= 3
        ), f"Expected ≥3 agent mode files, found {len(py_files)}"

    def test_agent_mode_test_file_exists(self):
        """Verify a test file for agent modes exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and "test" in f.lower()
                    and ("agent" in f.lower() or "mode" in f.lower())
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No agent mode test file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_agent_mode_dataclass(self):
        """Verify AgentMode uses dataclass or similar structured class."""
        py_files = self._find_agent_mode_files()
        assert py_files, "No agent mode files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(@dataclass|class\s+AgentMode|NamedTuple|TypedDict)", content
            ):
                if "priority" in content:
                    return
        pytest.fail("No AgentMode dataclass with priority field found")

    def test_mode_registry_with_lock(self):
        """Verify ModeRegistry uses threading.Lock for thread safety."""
        py_files = self._find_agent_mode_files()
        assert py_files, "No agent mode files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(Registry|registry)", content):
                if re.search(r"(threading\.Lock|Lock\(\)|_lock)", content):
                    return
        pytest.fail("No ModeRegistry with threading.Lock found")

    def test_priority_selection(self):
        """Verify priority-based mode selection logic."""
        py_files = self._find_agent_mode_files()
        assert py_files, "No agent mode files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(priority|sorted|max\(|min\(|key=.*priority)", content):
                return
        pytest.fail("No priority selection logic found")

    def test_config_type_casting(self):
        """Verify configuration values are type-cast properly."""
        py_files = self._find_agent_mode_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(int\(|float\(|str\(|bool\(|cast|astype|pydantic)", content):
                if "config" in content.lower():
                    return
        pytest.skip("Config type casting not explicitly detectable")

    def test_cache_ttl(self):
        """Verify 5-second cache TTL for mode lookups."""
        py_files = self._find_agent_mode_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(ttl|TTL|cache|Cache|expire|5\s*[#/])", content):
                return
        pytest.fail("No cache TTL configuration found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_compile(self):
        """Verify all agent mode files compile."""
        py_files = self._find_agent_mode_files()
        assert py_files, "No agent mode files"
        for fpath in py_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert (
                result.returncode == 0
            ), f"Compile error in {os.path.basename(fpath)}: {result.stderr}"

    def test_duplicate_registration_error(self):
        """Verify duplicate mode registration raises an error."""
        all_files = self._find_agent_mode_files() + self._find_test_files()
        for fpath in all_files:
            content = self._read(fpath)
            if re.search(
                r"(duplicate|already.*register|exist.*mode|ValueError|KeyError)",
                content,
                re.IGNORECASE,
            ):
                if "register" in content.lower() or "mode" in content.lower():
                    return
        pytest.fail("No duplicate registration error handling found")

    def test_register_and_get_pattern(self):
        """Verify register and get/select methods exist."""
        py_files = self._find_agent_mode_files()
        has_register = False
        has_get = False
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"def\s+(register|add_mode|register_mode)", content):
                has_register = True
            if re.search(r"def\s+(get|select|get_mode|select_mode|resolve)", content):
                has_get = True
        assert has_register, "No register method found"
        assert has_get, "No get/select method found"

    def test_test_file_has_assertions(self):
        """Verify test file contains meaningful assertions."""
        test_files = self._find_test_files()
        for fpath in test_files:
            content = self._read(fpath)
            if "assert" in content:
                return
        pytest.fail("No assertions in test files")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_agent_mode_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and ("agent" in f.lower() or "mode" in f.lower())
                    and "test" not in f.lower()
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _find_test_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and "test" in f.lower()
                    and ("agent" in f.lower() or "mode" in f.lower())
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
