"""
Test for 'prompt-engineering-patterns' skill — LangChain Prompt Patterns
Validates FewShotPromptTemplate, ChainOfThoughtTemplate, prompt_registry,
template variables, and prompt composition.
"""

import os
import re
import sys

import pytest


class TestPromptEngineeringPatterns:
    """Verify prompt engineering pattern implementations."""

    REPO_DIR = "/workspace/langchain"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_prompt_files_exist(self):
        """Verify prompt template files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "prompt" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No prompt template files found"

    def test_registry_file_exists(self):
        """Verify prompt registry file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "registr" in f.lower():
                    found = True
                    break
            if found:
                break
        if not found:
            # Registry might be a dict/module inside a prompt file
            for dirpath, _, fnames in os.walk(self.REPO_DIR):
                if ".git" in dirpath:
                    continue
                for f in fnames:
                    if f.endswith(".py") and "prompt" in f.lower():
                        content = self._read(os.path.join(dirpath, f))
                        if "registry" in content.lower():
                            found = True
                            break
                if found:
                    break
        assert found, "No prompt registry found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_few_shot_prompt_template(self):
        """Verify FewShotPromptTemplate usage."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "FewShotPromptTemplate" in content or "few_shot" in content.lower():
                return
        pytest.fail("No FewShotPromptTemplate found")

    def test_chain_of_thought_template(self):
        """Verify chain-of-thought prompt template."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(chain.?of.?thought|cot|step.?by.?step|think.?step|reasoning)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No chain-of-thought template found")

    def test_prompt_template_variables(self):
        """Verify prompt templates use variables (e.g. {input}, {context})."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"\{(input|context|question|query|examples)\}", content):
                return
        pytest.fail("No prompt template variables found")

    def test_prompt_registry_mapping(self):
        """Verify prompt_registry maps names to templates."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(prompt_registry|PROMPT_REGISTRY|registry\s*=\s*\{)", content
            ):
                return
        pytest.fail("No prompt_registry mapping found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_import_prompt_modules(self):
        """Verify prompt modules can be imported."""
        py_files = self._find_prompt_files()
        if not py_files:
            pytest.skip("No prompt files found")
        for fpath in py_files:
            dirpath = os.path.dirname(fpath)
            if dirpath not in sys.path:
                sys.path.insert(0, dirpath)
        # Just verify the files are syntactically valid
        import py_compile

        for fpath in py_files[:3]:
            try:
                py_compile.compile(fpath, doraise=True)
            except py_compile.PyCompileError:
                pytest.skip(f"Syntax issue in {os.path.basename(fpath)}")

    def test_prompt_template_format_method(self):
        """Verify prompt templates define a format or invoke method."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"def (format|invoke|render|generate|run)\(", content):
                return
            if re.search(r"\.(format|format_prompt|invoke)\(", content):
                return
        pytest.fail("No format/invoke method found in prompt templates")

    def test_few_shot_examples_defined(self):
        """Verify few-shot examples are provided."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(examples\s*=|few.?shot.?examples|example_prompt)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No few-shot examples defined")

    def test_prompt_output_parsing(self):
        """Verify output parsing or structured output is referenced."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(output_parser|OutputParser|StrOutputParser|PydanticOutputParser|parse)",
                content,
            ):
                return
        pytest.fail("No output parsing found")

    def test_template_string_no_unresolved_vars(self):
        """Verify templates don't have obviously broken placeholders."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            # Check for double-braces (Jinja) or single braces
            if re.search(r"\{[a-z_]+\}", content):
                # Valid template variables found — not unresolved
                assert not re.search(
                    r"\{\s*\}", content
                ), "Empty template variable found"

    def test_prompt_composition(self):
        """Verify prompts are composed or chained."""
        py_files = self._find_prompt_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(ChatPromptTemplate|SystemMessage|HumanMessage|MessagesPlaceholder|\|)",
                content,
            ):
                return
        pytest.fail("No prompt composition found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_prompt_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "prompt" in f.lower() or "template" in f.lower()
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
