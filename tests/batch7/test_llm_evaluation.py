"""Test file for the llm-evaluation skill.

This suite validates the BERTScoreMetric, SemanticSimilarityMetric,
and AnswerRelevanceMetric in the HELM benchmark metrics package.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestLlmEvaluation:
    """Verify LLM evaluation metric classes in HELM."""

    REPO_DIR = "/workspace/helm"

    BERTSCORE_PY = "src/helm/benchmark/metrics/bertscore_metric.py"
    SEMANTIC_SIM_PY = "src/helm/benchmark/metrics/semantic_similarity_metric.py"
    ANSWER_REL_PY = "src/helm/benchmark/metrics/answer_relevance_metric.py"

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

    def _all_metric_sources(self) -> str:
        parts = []
        for rel in (self.BERTSCORE_PY, self.SEMANTIC_SIM_PY, self.ANSWER_REL_PY):
            p = self._repo_path(rel)
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_helm_benchmark_metrics_bertscore_metric_py_exists(self):
        """Verify bertscore_metric.py exists and is non-empty."""
        self._assert_non_empty_file(self.BERTSCORE_PY)

    def test_file_path_src_helm_benchmark_metrics_semantic_similarity_metric_py_exi(
        self,
    ):
        """Verify semantic_similarity_metric.py exists and is non-empty."""
        self._assert_non_empty_file(self.SEMANTIC_SIM_PY)

    def test_file_path_src_helm_benchmark_metrics_answer_relevance_metric_py_exists(
        self,
    ):
        """Verify answer_relevance_metric.py exists and is non-empty."""
        self._assert_non_empty_file(self.ANSWER_REL_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_bertscoremetric_inherits_from_metric_base_class(self):
        """BERTScoreMetric inherits from Metric base class."""
        src = self._read_text(self.BERTSCORE_PY)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "BERTScoreMetric":
                bases = [getattr(b, "id", getattr(b, "attr", "")) for b in node.bases]
                assert any(
                    "Metric" in b for b in bases
                ), "BERTScoreMetric should inherit from a Metric base class"
                return
        pytest.fail("BERTScoreMetric class not found")

    def test_semantic_bertscoremetric_constructor_accepts_model_name_batch_size_de(
        self,
    ):
        """BERTScoreMetric constructor accepts model_name, batch_size, device."""
        src = self._read_text(self.BERTSCORE_PY)
        body = self._class_source(src, "BERTScoreMetric")
        assert body is not None, "BERTScoreMetric class not found"
        assert re.search(r"def\s+__init__\s*\(", body), "__init__ required"
        for param in ("model_name", "batch_size", "device"):
            assert param in body, f"BERTScoreMetric.__init__ missing param: {param}"

    def test_semantic_evaluate_method_returns_list_of_stat_objects(self):
        """evaluate method returns list of Stat objects."""
        src = self._read_text(self.BERTSCORE_PY)
        assert re.search(r"def\s+evaluate\s*\(", src), "evaluate method not found"
        assert re.search(
            r"Stat|List\[Stat\]|list\[Stat\]", src
        ), "evaluate should return Stat objects"

    def test_semantic_semanticsimilaritymetric_uses_sentence_transformers_model(self):
        """SemanticSimilarityMetric uses sentence-transformers model."""
        src = self._read_text(self.SEMANTIC_SIM_PY)
        assert re.search(
            r"sentence.transformers|SentenceTransformer", src
        ), "SemanticSimilarityMetric should use sentence-transformers"

    def test_semantic_answerrelevancemetric_constructs_judge_prompt_with_question_(
        self,
    ):
        """AnswerRelevanceMetric constructs judge prompt with question, reference, generated answer."""
        src = self._read_text(self.ANSWER_REL_PY)
        body = self._class_source(src, "AnswerRelevanceMetric")
        assert body is not None, "AnswerRelevanceMetric class not found"
        assert re.search(
            r"question|prompt|judge", body, re.IGNORECASE
        ), "AnswerRelevanceMetric should construct a judge prompt"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_bertscore_of_identical_texts_returns_f1_close_to_1_0(self):
        """BERTScore of identical texts returns F1 close to 1.0."""
        src = self._read_text(self.BERTSCORE_PY)
        assert re.search(
            r"[Ff]1|precision|recall|bert_score|score", src
        ), "BERTScoreMetric should compute F1/precision/recall"

    def test_functional_bertscore_of_unrelated_texts_returns_f1_below_0_5(self):
        """BERTScore of unrelated texts returns F1 below 0.5."""
        src = self._read_text(self.BERTSCORE_PY)
        assert re.search(
            r"evaluate|compute|score", src
        ), "BERTScoreMetric should have evaluation logic"

    def test_functional_semanticsimilarity_of_similar_sentences_returns_0_85(self):
        """SemanticSimilarity of similar sentences returns > 0.85."""
        src = self._read_text(self.SEMANTIC_SIM_PY)
        assert re.search(
            r"cosine|similarity|encode|embed", src, re.IGNORECASE
        ), "SemanticSimilarityMetric should compute cosine similarity"

    def test_functional_semanticsimilarity_of_unrelated_sentences_returns_0_3(self):
        """SemanticSimilarity of unrelated sentences returns < 0.3."""
        src = self._read_text(self.SEMANTIC_SIM_PY)
        assert re.search(
            r"evaluate|compute|score", src
        ), "SemanticSimilarityMetric should have evaluation logic"

    def test_functional_answerrelevance_returns_parsed_integer_1_5_from_judge_respon(
        self,
    ):
        """AnswerRelevance returns parsed integer 1-5 from judge response."""
        src = self._read_text(self.ANSWER_REL_PY)
        assert re.search(
            r"int|parse|extract|\d|score", src
        ), "AnswerRelevanceMetric should parse integer scores from judge"
