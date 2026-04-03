"""
Test for 'prompt-engineering-patterns' skill — Structured Prompt Template
Validates that the Agent created StructuredPromptTemplate and ExampleSelector
with format, add_example, select_examples, and to_messages in langchain.
"""

import os
import sys

import pytest


class TestPromptEngineeringPatterns:
    """Verify StructuredPromptTemplate and ExampleSelector in langchain."""

    REPO_DIR = "/workspace/langchain"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _import_all(self):
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from langchain.prompts.structured_template import (
                StructuredPromptTemplate,
                ExampleSelector,
            )

            return StructuredPromptTemplate, ExampleSelector
        finally:
            sys.path[:] = old_path

    # ---- file_path_check ----

    def test_structured_template_exists(self):
        """Verifies langchain/prompts/structured_template.py exists."""
        path = os.path.join(self.REPO_DIR, "langchain/prompts/structured_template.py")
        assert os.path.exists(path), f"File not found: {path}"

    def test_init_py_exists(self):
        """Verifies langchain/prompts/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "langchain/prompts/__init__.py")
        assert os.path.exists(path), f"File not found: {path}"

    # ---- semantic_check ----

    def test_sem_imports(self):
        """Verifies StructuredPromptTemplate and ExampleSelector importable."""
        SPT, ES = self._import_all()
        assert SPT is not None
        assert ES is not None

    def test_sem_spt_methods(self):
        """Verifies StructuredPromptTemplate has required methods."""
        text = self._read(
            os.path.join(self.REPO_DIR, "langchain/prompts/structured_template.py")
        )
        for method in [
            "format",
            "add_example",
            "select_examples",
            "set_system_message",
            "get_token_estimate",
            "to_messages",
        ]:
            assert method in text, f"Missing method: {method}"

    def test_sem_es_select_method(self):
        """Verifies ExampleSelector has select method."""
        text = self._read(
            os.path.join(self.REPO_DIR, "langchain/prompts/structured_template.py")
        )
        assert "def select" in text, "ExampleSelector missing 'select' method"

    def test_sem_es_constructor_params(self):
        """Verifies ExampleSelector takes examples, embedding_fn, k."""
        text = self._read(
            os.path.join(self.REPO_DIR, "langchain/prompts/structured_template.py")
        )
        assert "examples" in text, "Missing 'examples' param"
        assert "embedding_fn" in text or "embed" in text, "Missing embedding param"
        assert "k" in text, "Missing 'k' param"

    # ---- functional_check ----

    def test_func_format_basic(self):
        """Verifies format() substitutes {question} correctly."""
        SPT, _ = self._import_all()
        tmpl = SPT("Answer: {question}", examples=[])
        result = tmpl.format(question="What is 2+2?")
        assert "What is 2+2?" in result

    def test_func_format_missing_raises(self):
        """Failure: format() without required var raises."""
        SPT, _ = self._import_all()
        tmpl = SPT("Answer: {question}", examples=[])
        with pytest.raises((KeyError, ValueError)):
            tmpl.format()

    def test_func_add_example(self):
        """Verifies add_example adds to examples list."""
        SPT, _ = self._import_all()
        tmpl = SPT("Answer: {question}", examples=[])
        tmpl.add_example({"input": "x", "output": "y"})
        assert len(tmpl.examples) == 1

    def test_func_example_selector_similarity(self):
        """Verifies ExampleSelector selects closest match."""
        import numpy as np

        _, ES = self._import_all()
        simple_embed = lambda t: np.array(
            [1.0 if "python" in t else 0.0, 1.0 if "java" in t else 0.0]
        )
        es = ES(
            [{"text": "python code"}, {"text": "java code"}],
            simple_embed,
            k=1,
        )
        selected = es.select("python class")
        assert selected[0]["text"] == "python code"

    def test_func_empty_selector(self):
        """Edge case: empty selector returns []."""
        import numpy as np

        _, ES = self._import_all()
        simple_embed = lambda t: np.array([0.0])
        es_empty = ES([], simple_embed, k=3)
        assert es_empty.select("query") == []

    def test_func_k_limit(self):
        """Verifies k=1 limits results to 1."""
        import numpy as np

        _, ES = self._import_all()
        simple_embed = lambda t: np.array([1.0])
        es = ES(
            [{"text": "a"}, {"text": "b"}, {"text": "c"}],
            simple_embed,
            k=1,
        )
        assert len(es.select("query")) <= 1

    def test_func_select_examples_respects_count(self):
        """Verifies select_examples returns at most len(examples) items."""
        SPT, _ = self._import_all()
        tmpl = SPT("Answer: {question}", examples=[])
        tmpl.add_example({"input": "x", "output": "y"})
        result = tmpl.select_examples("python", k=5)
        assert len(result) <= len(tmpl.examples)

    def test_func_to_messages(self):
        """Verifies to_messages returns list of dicts with role/content."""
        SPT, _ = self._import_all()
        tmpl = SPT("Answer: {question}", examples=[])
        msgs = tmpl.to_messages()
        assert isinstance(msgs, list)
        assert all("role" in m and "content" in m for m in msgs)
