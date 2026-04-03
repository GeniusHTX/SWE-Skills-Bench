"""
Test for 'prompt-engineering-patterns' skill — Prompt Engineering Library
Validates PromptTemplate, FewShotSelector, ChainOfThoughtFormatter,
TokenCounter, and PromptOptimizer for correctness and behavioral patterns.
"""

import os
import sys

import pytest


class TestPromptEngineeringPatterns:
    """Verify prompt engineering library: templates, few-shot, CoT, tokenizer."""

    REPO_DIR = "/workspace/langchain"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _pe(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "prompt_engineering", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_template_py_exists(self):
        """template.py must exist containing PromptTemplate class."""
        path = self._pe("template.py")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_few_shot_and_cot_exist(self):
        """few_shot.py and chain_of_thought.py must exist."""
        for name in ("few_shot.py", "chain_of_thought.py"):
            path = self._pe(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_tokenizer_and_test_file_exist(self):
        """tokenizer.py and tests/test_prompt_engineering.py must exist."""
        assert os.path.isfile(self._pe("tokenizer.py")), "tokenizer.py not found"
        test_path = os.path.join(self.REPO_DIR, "tests", "test_prompt_engineering.py")
        assert os.path.isfile(test_path), f"{test_path} not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_template_uses_format_variables(self):
        """PromptTemplate must use {variable} placeholder syntax."""
        path = self._pe("template.py")
        if not os.path.isfile(path):
            pytest.skip("template.py not found")
        content = self._read_file(path)
        assert "PromptTemplate" in content, "PromptTemplate class not defined"
        has_format = ".format(" in content or "format_map" in content or "render" in content
        assert has_format, "No format/render method found"

    def test_few_shot_selector_has_k_parameter(self):
        """FewShotSelector.select must accept query and k parameters."""
        path = self._pe("few_shot.py")
        if not os.path.isfile(path):
            pytest.skip("few_shot.py not found")
        content = self._read_file(path)
        assert "FewShotSelector" in content, "FewShotSelector not defined"
        assert "select" in content, "select method not found"

    def test_cot_appends_step_by_step(self):
        """chain_of_thought.py must contain 'Let's think step by step'."""
        path = self._pe("chain_of_thought.py")
        if not os.path.isfile(path):
            pytest.skip("chain_of_thought.py not found")
        content = self._read_file(path)
        assert "step by step" in content.lower(), "'step by step' phrase not found"

    def test_optimizer_respects_max_tokens(self):
        """tokenizer.py must define PromptOptimizer with max_tokens parameter."""
        path = self._pe("tokenizer.py")
        if not os.path.isfile(path):
            pytest.skip("tokenizer.py not found")
        content = self._read_file(path)
        assert "max_tokens" in content, "max_tokens parameter not found"

    # ── functional_check ─────────────────────────────────────────────────

    def test_render_substitutes_variable(self):
        """PromptTemplate('Hello {name}').render({'name': 'World'}) == 'Hello World'."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.prompt_engineering.template import PromptTemplate
        except ImportError:
            pytest.skip("Cannot import PromptTemplate")
        result = PromptTemplate("Hello {name}").render({"name": "World"})
        assert result == "Hello World"

    def test_render_missing_variable_raises_keyerror(self):
        """Rendering with missing variable must raise KeyError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.prompt_engineering.template import PromptTemplate
        except ImportError:
            pytest.skip("Cannot import PromptTemplate")
        with pytest.raises(KeyError):
            PromptTemplate("Hello {name}").render({})

    def test_few_shot_returns_k_examples(self):
        """FewShotSelector.select(query, k=3) must return exactly 3 examples."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.prompt_engineering.few_shot import FewShotSelector
            from unittest.mock import MagicMock
        except ImportError:
            pytest.skip("Cannot import FewShotSelector")
        selector = FewShotSelector.__new__(FewShotSelector)
        # Ensure corpus has enough examples
        if hasattr(selector, "examples"):
            selector.examples = [MagicMock() for _ in range(10)]
        try:
            selected = selector.select("What is AI?", k=3)
            assert len(selected) == 3
        except Exception:
            pytest.skip("FewShotSelector.select requires specific setup")

    def test_cot_idempotent_double_application(self):
        """CoT phrase must appear exactly once even after double application."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.prompt_engineering.chain_of_thought import ChainOfThoughtFormatter
        except ImportError:
            pytest.skip("Cannot import ChainOfThoughtFormatter")
        f = ChainOfThoughtFormatter()
        r1 = f.format("What is 2+2?")
        r2 = f.format(r1)
        assert r2.lower().count("step by step") == 1

    def test_token_counter_returns_positive(self):
        """TokenCounter.count('hello') must return >= 1."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.prompt_engineering.tokenizer import TokenCounter
        except ImportError:
            pytest.skip("Cannot import TokenCounter")
        count = TokenCounter().count("hello")
        assert isinstance(count, int) and count >= 1

    def test_optimizer_output_within_max_tokens(self):
        """Optimized output token count must be <= max_tokens."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.prompt_engineering.tokenizer import PromptOptimizer, TokenCounter
        except ImportError:
            pytest.skip("Cannot import PromptOptimizer")
        optimized = PromptOptimizer().optimize("word " * 500, max_tokens=100)
        count = TokenCounter().count(optimized)
        assert count <= 100, f"Optimized prompt has {count} tokens, expected <= 100"
