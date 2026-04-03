"""
Test for 'prompt-engineering-patterns' skill — Prompt Engineering Module
Validates that the Agent created a Python package for semantic few-shot
selection, chain-of-thought building, and prompt optimization.
"""

import os
import re
import sys

import pytest


class TestPromptEngineeringPatterns:
    """Verify prompt engineering module implementation."""

    REPO_DIR = "/workspace/langchain"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_prompt_engineering_package_exists(self):
        """Verify __init__.py and selector.py exist under src/prompt_engineering/."""
        for rel in ("src/prompt_engineering/__init__.py", "src/prompt_engineering/selector.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_optimizer_cot_models_exist(self):
        """Verify optimizer.py, cot_builder.py, and models.py exist."""
        for rel in ("src/prompt_engineering/optimizer.py",
                     "src/prompt_engineering/cot_builder.py",
                     "src/prompt_engineering/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_all_classes_importable(self):
        """SemanticFewShotSelector, PromptOptimizer, ChainOfThoughtBuilder importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from prompt_engineering.selector import SemanticFewShotSelector  # noqa: F401
            from prompt_engineering.optimizer import PromptOptimizer  # noqa: F401
            from prompt_engineering.cot_builder import ChainOfThoughtBuilder  # noqa: F401
        except ImportError:
            pytest.skip("prompt_engineering not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_selector_uses_cosine_or_tfidf(self):
        """Verify selector.py implements cosine similarity or TF-IDF scoring."""
        content = self._read(os.path.join(self.REPO_DIR, "src/prompt_engineering/selector.py"))
        assert content, "selector.py is empty or unreadable"
        found = any(kw in content for kw in (
            "cosine", "TfidfVectorizer", "TF-IDF", "dot(", "normalize"))
        assert found, "No similarity scoring mechanism found in selector.py"

    def test_cot_builder_format_defined(self):
        """Verify cot_builder.py outputs 'Think step by step' prefix."""
        content = self._read(os.path.join(self.REPO_DIR, "src/prompt_engineering/cot_builder.py"))
        assert content, "cot_builder.py is empty or unreadable"
        assert "Think step by step" in content

    def test_selector_handles_k_overflow(self):
        """Verify selector.py handles k > len(examples) gracefully."""
        content = self._read(os.path.join(self.REPO_DIR, "src/prompt_engineering/selector.py"))
        assert content, "selector.py is empty or unreadable"
        found = any(kw in content for kw in ("min(k", "min(len", "[:k]"))
        assert found, "No k-overflow handling found"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_select_returns_k_examples(self):
        """select() with k=2 returns exactly 2 examples from a pool of 3."""
        mod = self._import("prompt_engineering.selector")
        models = self._import("prompt_engineering.models")
        examples = [models.Example("apple pie"), models.Example("car engine"),
                    models.Example("apple cider")]
        result = mod.SemanticFewShotSelector().select("apple fruit", examples, k=2)
        assert len(result) == 2

    def test_apple_examples_ranked_higher_than_car(self):
        """For query 'apple fruit', apple-related examples rank higher than 'car engine'."""
        mod = self._import("prompt_engineering.selector")
        models = self._import("prompt_engineering.models")
        examples = [models.Example("apple pie"), models.Example("car engine"),
                    models.Example("apple cider")]
        results = mod.SemanticFewShotSelector().select("apple fruit", examples, k=2)
        texts = [r.text for r in results]
        assert "car engine" not in texts

    def test_select_empty_examples_returns_empty(self):
        """select() with empty examples list returns empty list."""
        mod = self._import("prompt_engineering.selector")
        result = mod.SemanticFewShotSelector().select("apple fruit", [], k=3)
        assert result == []

    def test_cot_builder_output_format(self):
        """ChainOfThoughtBuilder.build() starts with 'Think step by step:' and has numbered steps."""
        mod = self._import("prompt_engineering.cot_builder")
        output = mod.ChainOfThoughtBuilder().build(
            "What is 2+2?", ["Add the numbers", "The answer is 4"])
        assert output.startswith("Think step by step:")
        assert "1." in output
        assert "2." in output

    def test_optimizer_includes_task_description(self):
        """PromptOptimizer.optimize() output includes task_description in first 200 chars."""
        mod = self._import("prompt_engineering.optimizer")
        models = self._import("prompt_engineering.models")
        prompt = mod.PromptOptimizer().optimize(
            "{examples}\n{task}", [models.Example("sample text")], "Classify sentiment")
        assert "Classify sentiment" in prompt[:200]
