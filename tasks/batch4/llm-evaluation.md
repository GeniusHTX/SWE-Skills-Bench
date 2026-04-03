# Task: Build an LLM Evaluation Framework with Automated Metrics and LLM-as-Judge for HELM

## Background

The HELM repository (https://github.com/stanford-crfm/helm) is a holistic evaluation framework for language models. A new evaluation module is needed that provides an extensible evaluation suite with automated metrics (BLEU, ROUGE, BERTScore, exact match), LLM-as-Judge scoring (pointwise and pairwise), dataset management for test cases, and a reporting engine that compares model performance across metrics with statistical significance testing.

## Files to Create/Modify

- `src/helm/benchmark/evaluation/eval_suite.py` (create) — `EvaluationSuite` class orchestrating metric computation across test cases
- `src/helm/benchmark/evaluation/metrics.py` (create) — Metric implementations: exact match, BLEU, ROUGE-L, F1, and custom metric support
- `src/helm/benchmark/evaluation/llm_judge.py` (create) — `LLMJudge` class for pointwise scoring and pairwise comparison using an LLM
- `src/helm/benchmark/evaluation/reporter.py` (create) — `EvaluationReporter` producing summary statistics, comparisons, and significance tests
- `src/helm/benchmark/evaluation/test_evaluation.py` (create) — Tests for all metrics, judge, and reporter

## Requirements

### EvaluationSuite Class

- Constructor accepts: `metrics` (list of metric names or Metric objects), `test_cases` (list of dicts with `"input"`, `"expected"`, optional `"context"`)
- `evaluate(predict_fn: callable) -> EvaluationResult` — runs `predict_fn(input)` for each test case, computes all metrics, returns an `EvaluationResult`
- `EvaluationResult` contains: `per_case` (list of dicts with input, expected, predicted, and per-metric scores), `aggregated` (dict of metric_name → mean score), `metadata` (dict with total cases, evaluation time, failed cases count)
- If `predict_fn` raises an exception for a test case, that case is marked as failed with score 0 for all metrics; the evaluation continues to the remaining cases

### Built-in Metrics

- `exact_match(predicted, expected) -> float` — returns 1.0 if strings match (after stripping whitespace), 0.0 otherwise
- `f1_score(predicted, expected) -> float` — token-level F1: precision × recall × 2 / (precision + recall); tokenize by whitespace splitting and lowering
- `bleu_score(predicted, expected) -> float` — sentence-level BLEU using up to 4-grams with smoothing
- `rouge_l(predicted, expected) -> float` — ROUGE-L F-measure based on longest common subsequence
- `contains_match(predicted, expected) -> float` — returns 1.0 if `expected` appears as a substring in `predicted` (case-insensitive), 0.0 otherwise
- Each metric must be callable with `(predicted: str, expected: str) -> float` signature
- Custom metrics registered via `register_metric(name: str, fn: callable)` must follow the same signature

### LLMJudge Class

- Constructor accepts: `judge_fn` (callable: str → str, simulating an LLM call), `scoring_rubric` (str describing the 1-5 scoring criteria)
- `score_pointwise(question: str, response: str, reference: str = None) -> dict` — returns `{"score": int (1-5), "reasoning": str}`; the prompt sent to `judge_fn` must include the rubric, the question, the response, and optionally the reference
- `compare_pairwise(question: str, response_a: str, response_b: str) -> dict` — returns `{"winner": "A" or "B" or "tie", "reasoning": str}`; the prompt must present both responses without revealing which is A/B in the judgment (position debiasing by evaluating both orderings and checking consistency)
- `score` must be an integer 1–5; if the judge returns an unparseable score, default to 3 with a warning in the reasoning

### EvaluationReporter

- Constructor accepts: `results` (list of `EvaluationResult`, one per model/configuration)
- `summary_table() -> list[dict]` — one row per model with mean and std for each metric
- `compare(model_a: str, model_b: str, metric: str) -> dict` — returns `{"model_a_mean": float, "model_b_mean": float, "difference": float, "p_value": float, "significant": bool}` using a paired t-test with significance threshold 0.05
- `best_model(metric: str) -> str` — returns the model name with the highest mean score for the given metric
- If a metric name is not found in the results, raise `ValueError`

### Expected Functionality

- Evaluating a model that always returns "Paris" against test cases with expected "Paris" yields `exact_match=1.0`
- `f1_score("the quick brown fox", "quick fox jumps")` returns the correct token F1 (~0.57)
- `bleu_score("the cat sat on the mat", "the cat is on the mat")` returns a positive BLEU score < 1.0
- LLM judge scoring "What is 2+2?" with response "4" and rubric for math accuracy returns score 5
- Pairwise comparison of a correct vs. incorrect response returns the correct one as winner
- Reporter comparing two models on exact_match produces a p-value and significance flag

## Acceptance Criteria

- EvaluationSuite runs all test cases, handles prediction failures gracefully, and aggregates scores
- All built-in metrics produce correct scores for known input/output pairs
- Custom metrics can be registered and used alongside built-in metrics
- LLMJudge produces pointwise scores (1–5) and pairwise comparisons with reasoning
- Pairwise comparison uses position debiasing (evaluates both orderings)
- Reporter generates summary tables, pairwise comparisons with p-values, and identifies the best model
- Tests cover all metrics with known-answer cases, judge scoring, and reporter statistics
