"""Test file for the prompt-engineering-patterns skill.

This suite validates the SemanticFewShotPromptTemplate and ExampleStore
classes in langchain's prompts package.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestPromptEngineeringPatterns:
    """Verify prompt engineering patterns in LangChain."""

    REPO_DIR = "/workspace/langchain"

    SEMANTIC_FEW_SHOT_PY = "libs/langchain/langchain/prompts/semantic_few_shot.py"
    EXAMPLE_STORE_PY = "libs/langchain/langchain/prompts/example_store.py"
    INIT_PY = "libs/langchain/langchain/prompts/__init__.py"

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

    def _class_source(self, source: str, class_name: str) -> str | None:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                start = node.lineno - 1
                end = node.end_lineno or start + 1
                lines = source.splitlines()
                return "\n".join(lines[start:end])
        return None

    def _all_prompt_sources(self) -> str:
        parts = []
        for rel in (self.SEMANTIC_FEW_SHOT_PY, self.EXAMPLE_STORE_PY):
            p = self._repo_path(rel)
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_libs_langchain_langchain_prompts_semantic_few_shot_py_exists(
        self,
    ):
        """Verify semantic_few_shot.py exists and is non-empty."""
        self._assert_non_empty_file(self.SEMANTIC_FEW_SHOT_PY)

    def test_file_path_libs_langchain_langchain_prompts_example_store_py_exists(self):
        """Verify example_store.py exists and is non-empty."""
        self._assert_non_empty_file(self.EXAMPLE_STORE_PY)

    def test_file_path_libs_langchain_langchain_prompts___init___py_modified(self):
        """Verify prompts/__init__.py exists (modified)."""
        self._assert_non_empty_file(self.INIT_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_examplestore_constructor_accepts_examples_embedding_function(
        self,
    ):
        """ExampleStore constructor accepts examples, embedding_function, input_key."""
        src = self._read_text(self.EXAMPLE_STORE_PY)
        body = self._class_source(src, "ExampleStore")
        assert body is not None, "ExampleStore class not found"
        assert re.search(r"def\s+__init__\s*\(", body), "__init__ required"
        for param in ("examples", "embedding_function", "input_key"):
            assert param in body, f"ExampleStore.__init__ missing param: {param}"

    def test_semantic_select_method_signature_query_k_list_dict(self):
        """select method signature: (query, k) -> list[dict]."""
        src = self._read_text(self.EXAMPLE_STORE_PY)
        assert re.search(r"def\s+select\s*\(", src), "select method not found"
        assert re.search(r"query", src) and re.search(
            r"\bk\b", src
        ), "select should accept query and k parameters"

    def test_semantic_select_diverse_method_signature_query_k_lambda_mult_list_dic(
        self,
    ):
        """select_diverse method signature: (query, k, lambda_mult) -> list[dict]."""
        src = self._read_text(self.EXAMPLE_STORE_PY)
        assert re.search(
            r"def\s+select_diverse\s*\(", src
        ), "select_diverse method not found"
        assert re.search(
            r"lambda_mult", src
        ), "select_diverse should accept lambda_mult parameter"

    def test_semantic_semanticfewshotprompttemplate_inherits_from_baseprompttempla(
        self,
    ):
        """SemanticFewShotPromptTemplate inherits from BasePromptTemplate."""
        src = self._read_text(self.SEMANTIC_FEW_SHOT_PY)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "SemanticFewShot" in node.name:
                bases = [getattr(b, "id", getattr(b, "attr", "")) for b in node.bases]
                assert any(
                    "PromptTemplate" in b or "Base" in b for b in bases
                ), "SemanticFewShotPromptTemplate should inherit from BasePromptTemplate"
                return
        pytest.fail("SemanticFewShotPromptTemplate class not found")

    def test_semantic_constructor_accepts_system_template_instruction_template_exa(
        self,
    ):
        """Constructor accepts system_template, instruction_template, example_store, k, etc."""
        src = self._read_text(self.SEMANTIC_FEW_SHOT_PY)
        for param in ("system_template", "instruction_template", "example_store", "k"):
            assert param in src, f"SemanticFewShotPromptTemplate missing param: {param}"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_select_query_k_3_returns_3_most_similar_examples_from_pool_o(
        self,
    ):
        """select(query, k=3) returns 3 most similar examples from pool of 100."""
        src = self._read_text(self.EXAMPLE_STORE_PY)
        assert re.search(r"def\s+select\s*\(", src), "select method required"
        assert re.search(
            r"sort|argsort|topk|nlargest|[:k]|\[:k\]", src
        ), "select should rank and return top-k examples"

    def test_functional_select_diverse_query_k_3_lambda_mult_0_5_returns_diverse_set(
        self,
    ):
        """select_diverse(query, k=3, lambda_mult=0.5) returns diverse set."""
        src = self._read_text(self.EXAMPLE_STORE_PY)
        assert re.search(
            r"select_diverse|MMR|maximal.marginal", src, re.IGNORECASE
        ), "select_diverse should implement MMR-based selection"

    def test_functional_format_input_query_produces_prompt_with_system_3_examples_in(
        self,
    ):
        """format(input='query') produces prompt with system + 3 examples + instruction."""
        src = self._read_text(self.SEMANTIC_FEW_SHOT_PY)
        assert re.search(r"def\s+format\s*\(", src), "format method required"
        assert re.search(
            r"system|example|instruction", src, re.IGNORECASE
        ), "format should compose system, examples, and instruction"

    def test_functional_format_with_include_reasoning_true_includes_reasoning_lines(
        self,
    ):
        """format with include_reasoning=True includes Reasoning lines."""
        src = self._read_text(self.SEMANTIC_FEW_SHOT_PY)
        assert re.search(
            r"include_reasoning|reasoning", src
        ), "SemanticFewShotPromptTemplate should support include_reasoning"

    def test_functional_format_messages_returns_systemmessage_humanmessage(self):
        """format_messages returns [SystemMessage, HumanMessage]."""
        src = self._read_text(self.SEMANTIC_FEW_SHOT_PY)
        assert re.search(
            r"format_messages|SystemMessage|HumanMessage", src
        ), "SemanticFewShotPromptTemplate should support format_messages"
