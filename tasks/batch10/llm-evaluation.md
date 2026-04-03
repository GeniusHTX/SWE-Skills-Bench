# Task: Implement Automated Evaluation Suite with LLM-as-Judge for HELM

## Background

The HELM benchmark framework (`stanford-crfm/helm`) needs a new evaluation module under `src/helm/benchmark/` that provides automated text-generation metrics (BLEU, ROUGE, BERTScore), an LLM-as-judge evaluator with pointwise and pairwise modes, regression detection across evaluation runs, and a statistical A/B testing harness. This module will be used to systematically compare model outputs and detect quality regressions before deploying prompt or model changes.

## Files to Create/Modify

- `src/helm/benchmark/metrics/text_generation_metrics.py` (new) — BLEU, ROUGE-1/2/L, and BERTScore implementations with a unified `TextMetric` interface
- `src/helm/benchmark/metrics/llm_judge.py` (new) — LLM-as-judge evaluator supporting pointwise scoring (accuracy, helpfulness, clarity on 1–10 scale) and pairwise comparison (winner A/B/tie with confidence)
- `src/helm/benchmark/metrics/custom_metrics.py` (new) — Groundedness check via NLI, toxicity scorer, and factuality verifier against source documents
- `src/helm/benchmark/runner/evaluation_suite.py` (new) — `EvaluationSuite` class that accepts a list of metrics, runs them over test cases, aggregates scores, and produces a structured report
- `src/helm/benchmark/runner/regression_detector.py` (new) — Compares current evaluation results against a baseline, flags metrics that dropped below a configurable threshold, and outputs a regression report
- `src/helm/benchmark/runner/ab_test.py` (new) — A/B testing harness that collects per-variant scores, runs a two-sample t-test, computes Cohen's d effect size, and declares a winner at a given significance level
- `src/helm/benchmark/tests/test_text_generation_metrics.py` (new) — Unit tests for BLEU, ROUGE, BERTScore
- `src/helm/benchmark/tests/test_llm_judge.py` (new) — Unit tests for pointwise and pairwise LLM judge
- `src/helm/benchmark/tests/test_evaluation_suite.py` (new) — Unit tests for suite orchestration, regression detection, and A/B testing

## Requirements

### Text Generation Metrics (`text_generation_metrics.py`)

- Implement `calculate_bleu(reference: str, hypothesis: str) -> float` — tokenize on whitespace, compute sentence-level BLEU with smoothing; return value in `[0, 1]`
- Implement `calculate_rouge(reference: str, hypothesis: str) -> dict` — return `{"rouge1": float, "rouge2": float, "rougeL": float}` F-measure scores
- Implement `calculate_bertscore(references: list[str], hypotheses: list[str]) -> dict` — return `{"precision": float, "recall": float, "f1": float}` averaged across pairs
- Raise `ValueError` if inputs are empty strings
- Raise `ValueError` if `references` and `hypotheses` lists have different lengths for BERTScore

### LLM-as-Judge (`llm_judge.py`)

- Implement `LLMJudge` class with `__init__(self, model: str, api_key: str)`
- Method `pointwise_evaluate(question: str, response: str, context: str | None = None) -> dict` — returns `{"accuracy": int, "helpfulness": int, "clarity": int, "reasoning": str}` where scores are 1–10
- Method `pairwise_compare(question: str, response_a: str, response_b: str) -> dict` — returns `{"winner": "A"|"B"|"tie", "reasoning": str, "confidence": int}` where confidence is 1–10
- Method `reference_evaluate(question: str, response: str, reference: str) -> dict` — returns `{"semantic_similarity": float, "factual_accuracy": float, "completeness": float, "issues": list[str]}` with floats in `[0, 1]`
- All methods must structure the LLM prompt so the judge outputs valid JSON; parse and validate the response
- Raise `ValueError` if `question` or `response` is empty
- Raise `ConnectionError` if the LLM API call fails (wrap the underlying exception)

### Custom Metrics (`custom_metrics.py`)

- Implement `calculate_groundedness(response: str, context: str) -> float` — use NLI model to determine if context entails response; return confidence in `[0, 1]`
- Implement `calculate_toxicity(text: str) -> float` — return a toxicity score in `[0, 1]` where higher means more toxic
- Implement `calculate_factuality(claim: str, sources: list[str]) -> float` — check claim against each source via NLI; return the maximum entailment score across sources
- `calculate_factuality` with an empty `sources` list returns `0.0`

### EvaluationSuite (`evaluation_suite.py`)

- `__init__(self, metrics: list[dict])` where each dict has `{"name": str, "fn": Callable}`
- Method `evaluate(model_fn: Callable, test_cases: list[dict]) -> dict` — for each test case call `model_fn(test_case["input"])` to get a prediction, run each metric with `prediction`, `reference` (from `test_case["expected"]`), and optional `context`; return `{"metrics": {name: mean_score}, "raw_scores": {name: [per_case_scores]}, "num_cases": int}`
- Method `generate_report(results: dict) -> str` — return a formatted text report with metric names, mean scores, min/max per metric, and number of test cases
- Handle cases where `test_case["expected"]` is missing by skipping reference-requiring metrics for that case

### Regression Detector (`regression_detector.py`)

- `__init__(self, baseline: dict[str, float], threshold: float = 0.05)`
- Method `check(current: dict[str, float]) -> dict` — for each metric in baseline, compute `relative_change = (current - baseline) / baseline`; flag as regression if `relative_change < -threshold`
- Return `{"has_regression": bool, "regressions": [{"metric": str, "baseline": float, "current": float, "change_pct": float}], "summary": str}`
- Metrics present in baseline but missing in current are flagged with `change_pct = -100.0`

### A/B Test Harness (`ab_test.py`)

- `__init__(self, variant_a_name: str = "A", variant_b_name: str = "B")`
- Method `add_result(variant: str, score: float)` — append to the variant's score list; raise `ValueError` if variant is not A or B
- Method `analyze(alpha: float = 0.05) -> dict` — compute means, run Welch's two-sample t-test, compute Cohen's d, return `{"variant_a_mean": float, "variant_b_mean": float, "p_value": float, "statistically_significant": bool, "cohens_d": float, "effect_size": str, "winner": str}`
- `effect_size` labels: `|d| < 0.2` → "negligible", `< 0.5` → "small", `< 0.8` → "medium", else "large"
- Raise `ValueError` if either variant has fewer than 2 scores (t-test requires at least 2 samples)

### Expected Functionality

- `calculate_bleu("the cat sat on the mat", "the cat sat on the mat")` → `1.0`
- `calculate_bleu("the cat sat on the mat", "the dog ran in the park")` → score significantly below `0.5`
- `calculate_bleu("", "some text")` → raises `ValueError`
- `calculate_rouge("the cat sat", "the cat sat on the mat")` → `rouge1` recall near `1.0`, precision below `1.0`
- `calculate_bertscore(["hello"], ["hello", "world"])` → raises `ValueError` (length mismatch)
- LLM judge pointwise evaluation on a factually wrong response → `accuracy` score below 5
- LLM judge pairwise comparison of a correct vs. incorrect answer → `winner` is the correct one
- `EvaluationSuite` with BLEU and ROUGE on 3 test cases → `num_cases = 3`, `raw_scores["bleu"]` has 3 elements
- Regression detector with baseline `{"bleu": 0.8}` and current `{"bleu": 0.7}` (threshold 0.05) → flags regression with `change_pct ≈ -12.5`
- Regression detector with baseline `{"bleu": 0.8}` and current `{"bleu": 0.78}` (threshold 0.05) → no regression (change is only -2.5%)
- Regression detector with baseline `{"bleu": 0.8, "rouge1": 0.7}` and current `{"bleu": 0.8}` → `rouge1` flagged with `change_pct = -100.0`
- A/B test with variant A scores `[0.8, 0.82, 0.79]` and variant B scores `[0.90, 0.91, 0.89]` → `statistically_significant = True`, `winner = "B"`
- A/B test `analyze()` with only 1 score per variant → raises `ValueError`

## Acceptance Criteria

- `python -m pytest src/helm/benchmark/tests/test_text_generation_metrics.py -v` passes
- `python -m pytest src/helm/benchmark/tests/test_llm_judge.py -v` passes
- `python -m pytest src/helm/benchmark/tests/test_evaluation_suite.py -v` passes
- BLEU returns `1.0` for identical strings and monotonically lower scores as hypothesis diverges from reference
- ROUGE returns separate rouge1, rouge2, rougeL scores as a dict
- BERTScore returns precision, recall, and f1 keys with values in `[0, 1]`
- LLM judge returns structured, parseable JSON for both pointwise and pairwise modes
- Evaluation suite aggregates metrics correctly and handles missing expected fields gracefully
- Regression detector flags only metrics that dropped by more than the threshold percentage
- A/B test computes correct t-test p-values and Cohen's d and refuses to run with fewer than 2 samples per variant
