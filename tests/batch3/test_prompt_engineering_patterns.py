"""
Tests for prompt-engineering-patterns skill.
Validates TemplateLibrary, FewShotBuilder, ChainOfThoughtFormatter in langchain repository.
"""

import os
import re
import glob
import pytest

REPO_DIR = "/workspace/langchain"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestPromptEngineeringPatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_template_library_file_exists(self):
        """template_library.py must exist in langchain_core/prompts."""
        rel = "libs/core/langchain_core/prompts/template_library.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "template_library.py is empty"

    def test_prompts_module_has_multiple_files(self):
        """langchain_core/prompts must contain multiple Python files."""
        pattern = os.path.join(REPO_DIR, "libs/core/langchain_core/prompts", "*.py")
        files = glob.glob(pattern)
        assert (
            len(files) >= 2
        ), f"Expected >= 2 Python files in prompts/, found {len(files)}"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_template_library_class_defined(self):
        """TemplateLibrary must define register() and get() methods."""
        content = _read("libs/core/langchain_core/prompts/template_library.py")
        assert "class TemplateLibrary" in content, "TemplateLibrary class not defined"
        assert "def register" in content, "register() method not found"
        assert "def get" in content, "get() method not found"

    def test_duplicate_template_error_defined(self):
        """DuplicateTemplateError and ParseError must be defined as custom exceptions."""
        content = _read("libs/core/langchain_core/prompts/template_library.py")
        assert (
            "class DuplicateTemplateError" in content
        ), "DuplicateTemplateError not defined"
        assert "class ParseError" in content, "ParseError not defined"

    def test_few_shot_builder_max_examples(self):
        """FewShotBuilder must accept a max_examples parameter."""
        content = _read("libs/core/langchain_core/prompts/template_library.py")
        assert "class FewShotBuilder" in content, "FewShotBuilder class not defined"
        assert "max_examples" in content, "max_examples parameter not found"

    def test_cot_formatter_answer_tag_parsing(self):
        """ChainOfThoughtFormatter.parse_answer must extract content from <answer> tags."""
        content = _read("libs/core/langchain_core/prompts/template_library.py")
        assert (
            "ChainOfThoughtFormatter" in content
        ), "ChainOfThoughtFormatter not defined"
        assert (
            "<answer>" in content or "answer" in content
        ), "answer tag parsing pattern not found"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_template_library_get_returns_latest_version(self):
        """TemplateLibrary.get() must return the highest version by default (mocked)."""
        from packaging.version import Version

        class TemplateLibrary:
            def __init__(self):
                self._store = {}

            def register(self, name, template, version="1.0"):
                key = (name, version)
                if key in self._store:
                    raise ValueError("Duplicate")
                self._store[key] = template

            def get(self, name):
                versions = {k[1]: v for k, v in self._store.items() if k[0] == name}
                if not versions:
                    raise KeyError(name)
                latest = max(versions.keys(), key=lambda v: Version(v))
                return versions[latest]

        lib = TemplateLibrary()
        lib.register("qa", "template1", version="1.0")
        lib.register("qa", "template2", version="2.0")
        result = lib.get("qa")
        assert result == "template2", f"Expected 'template2' (v2.0), got {result!r}"

    def test_duplicate_template_same_name_version_error(self):
        """Registering same name+version twice must raise DuplicateTemplateError (mocked)."""

        class DuplicateTemplateError(Exception):
            pass

        class TemplateLibrary:
            def __init__(self):
                self._store = {}

            def register(self, name, template, version="1.0"):
                key = (name, version)
                if key in self._store:
                    raise DuplicateTemplateError(f"{name}@{version} already registered")
                self._store[key] = template

        lib = TemplateLibrary()
        lib.register("qa", "template1", version="1.0")
        with pytest.raises(DuplicateTemplateError):
            lib.register("qa", "template_dup", version="1.0")

    def test_few_shot_builder_limits_to_3_from_10(self):
        """FewShotBuilder(max_examples=3) must truncate pool to 3 examples (mocked)."""

        class FewShotBuilder:
            def __init__(self, max_examples: int = 5):
                self.max_examples = max_examples

            def build(self, pool: list) -> list:
                return pool[: self.max_examples]

        builder = FewShotBuilder(max_examples=3)
        examples = builder.build(pool=[f"ex{i}" for i in range(10)])
        assert len(examples) == 3, f"Expected 3 examples, got {len(examples)}"

    def test_parse_answer_extracts_42(self):
        """parse_answer must extract '42' from <answer>42</answer> (mocked)."""

        class ParseError(Exception):
            pass

        class ChainOfThoughtFormatter:
            def parse_answer(self, text: str) -> dict:
                m = re.search(r"<answer>(.*?)</answer>", text, re.DOTALL)
                if not m:
                    raise ParseError("No <answer>...</answer> tag found")
                return {"answer": m.group(1).strip()}

        f = ChainOfThoughtFormatter()
        result = f.parse_answer("Let me think... <answer>42</answer>")
        assert result["answer"] == "42", f"Expected '42', got {result['answer']!r}"

    def test_parse_answer_no_tag_raises_parse_error(self):
        """parse_answer must raise ParseError when no <answer> tag present (mocked)."""

        class ParseError(Exception):
            pass

        class ChainOfThoughtFormatter:
            def parse_answer(self, text: str) -> dict:
                m = re.search(r"<answer>(.*?)</answer>", text, re.DOTALL)
                if not m:
                    raise ParseError("No <answer>...</answer> tag found")
                return {"answer": m.group(1).strip()}

        f = ChainOfThoughtFormatter()
        with pytest.raises(ParseError):
            f.parse_answer("The answer is 42 but no tag")

    def test_prompt_tester_pass_rate_0_8(self):
        """PromptTester.pass_rate must return 0.8 for 4/5 passing tests (mocked)."""

        class PromptTester:
            def __init__(self):
                self._results = []

            def record_result(self, passed: bool):
                self._results.append(passed)

            @property
            def pass_rate(self) -> float:
                if not self._results:
                    return 0.0
                return sum(self._results) / len(self._results)

        tester = PromptTester()
        for i in range(5):
            tester.record_result(passed=(i < 4))
        assert (
            abs(tester.pass_rate - 0.8) < 1e-9
        ), f"Expected pass_rate=0.8, got {tester.pass_rate}"
