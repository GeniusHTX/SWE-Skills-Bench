# Task: Build an Evaluation Framework for LLM Output Quality in HELM

## Background

HELM (https://github.com/stanford-crfm/helm) is a holistic evaluation framework for language models. The project needs a modular evaluation toolkit that can score LLM outputs across multiple quality dimensions — accuracy, coherence, relevance, and safety — using both automated metrics (BLEU, ROUGE, BERTScore) and LLM-as-judge scoring. The framework must support pointwise and pairwise evaluation, aggregate results across test sets, and detect performance regressions between model versions.

## Files to Create/Modify

- `src/helm/benchmark/metrics/quality_evaluator.py` (create) — `QualityEvaluator` class computing automated text quality metrics: exact match, BLEU, ROUGE-L, and a configurable custom metric interface
- `src/helm/benchmark/metrics/llm_judge.py` (create) — `LLMJudge` class implementing pointwise scoring (1-5 scale on configurable dimensions) and pairwise comparison (preference between two outputs), with structured prompt templates
- `src/helm/benchmark/metrics/regression_detector.py` (create) — `RegressionDetector` class comparing evaluation results across two runs and flagging statistically significant regressions using paired t-tests
- `src/helm/benchmark/metrics/evaluation_suite.py` (create) — `EvaluationSuite` class orchestrating multiple evaluators over a test dataset and producing aggregated reports with per-metric breakdowns
- `tests/test_llm_evaluation.py` (create) — Tests for metric calculations, LLM judge prompt construction, regression detection, and suite orchestration

## Requirements

### QualityEvaluator

- Constructor: `QualityEvaluator(metrics: list[str])` where each metric is one of `"exact_match"`, `"bleu"`, `"rouge_l"`, `"f1"`, or a custom metric name
- `evaluate(prediction: str, reference: str) -> dict[str, float]` — Return a dict mapping each metric name to its score (0.0-1.0)
- Metric implementations:
  - `exact_match`: 1.0 if `prediction.strip().lower() == reference.strip().lower()`, else 0.0
  - `bleu`: Compute BLEU-4 score using unigram through 4-gram precision with brevity penalty; tokenize by whitespace splitting and lowercasing
  - `rouge_l`: Longest common subsequence between prediction and reference tokens divided by reference length (recall-oriented)
  - `f1`: Token-level F1 score — compute precision (shared tokens / prediction tokens) and recall (shared tokens / reference tokens), return harmonic mean; tokens are whitespace-split and lowercased
- `evaluate_batch(predictions: list[str], references: list[str]) -> dict[str, float]` — Return per-metric averages across all pairs
- `register_metric(name: str, fn: Callable[[str, str], float])` — Register a custom metric function
- If `predictions` and `references` have different lengths, raise `ValueError`
- Empty strings score 0.0 for all metrics except `exact_match` (two empty strings = 1.0)

### LLMJudge

- Constructor: `LLMJudge(judge_fn: Callable[[str], str], dimensions: list[str] = None)`
- Default dimensions: `["accuracy", "coherence", "relevance", "helpfulness"]`
- `score_pointwise(question: str, answer: str) -> dict[str, int]` — Build a prompt asking the judge to rate each dimension 1-5, parse the response, return dimension-to-score mapping
  - Prompt template: `"Rate the following answer on a scale of 1-5 for each dimension.\n\nQuestion: {question}\nAnswer: {answer}\n\nDimensions: {dimensions}\n\nRespond in JSON format: {\"dimension\": score}"`
  - Parse the judge response as JSON; if parsing fails, return all dimensions scored as 0 with an `"_parse_error": True` flag
- `compare_pairwise(question: str, answer_a: str, answer_b: str) -> dict` — Ask judge which answer is better, return `{"winner": "A" | "B" | "tie", "reasoning": str}`
  - Prompt template: `"Compare these two answers.\n\nQuestion: {question}\nAnswer A: {answer_a}\nAnswer B: {answer_b}\n\nWhich is better? Respond with JSON: {\"winner\": \"A\"/\"B\"/\"tie\", \"reasoning\": \"...\"}"`
- `evaluate_batch(test_cases: list[dict]) -> dict` — Each test case has `question` and `answer`; return per-dimension averages and score distributions

### RegressionDetector

- Constructor: `RegressionDetector(significance_level: float = 0.05)`
- `compare(baseline_scores: list[float], candidate_scores: list[float]) -> dict`:
  - Perform a paired t-test; return `{"baseline_mean": float, "candidate_mean": float, "delta": float, "p_value": float, "is_regression": bool, "is_improvement": bool}`
  - `is_regression` = True if candidate_mean < baseline_mean AND p_value < significance_level
  - `is_improvement` = True if candidate_mean > baseline_mean AND p_value < significance_level
- `compare_reports(baseline: dict, candidate: dict) -> dict` — Accept two evaluation reports (from `EvaluationSuite`) and run regression detection per metric; return `{"regressions": list[str], "improvements": list[str], "unchanged": list[str], "details": dict}`
- If score lists have different lengths, raise `ValueError`
- If score lists have fewer than 2 elements, skip the t-test and report `"insufficient_data"`

### EvaluationSuite

- Constructor: `EvaluationSuite(evaluator: QualityEvaluator, judge: LLMJudge = None)`
- `run(test_cases: list[dict]) -> dict` — Each test case has `{"question": str, "prediction": str, "reference": str}`; run `evaluate_batch` on predictions vs references, optionally run judge scoring, return:
  - `metric_scores`: per-metric averages from `QualityEvaluator`
  - `judge_scores`: per-dimension averages from `LLMJudge` (or null if no judge)
  - `per_case_results`: list of per-test-case result dicts
  - `total_cases`: int
  - `timestamp`: ISO 8601 string
- `run_comparison(test_cases: list[dict], model_a_fn: Callable, model_b_fn: Callable) -> dict` — Generate predictions from both models, evaluate both, run pairwise comparison, return win/loss/tie counts and per-metric comparison

### Edge Cases

- BLEU with prediction shorter than 4 tokens: apply brevity penalty, resulting in low but non-zero score (unless prediction is empty, then 0.0)
- ROUGE-L with no common subsequence: return 0.0
- LLM judge returning malformed JSON: set all scores to 0 and flag `_parse_error`
- Regression detection with identical score lists: p_value = 1.0, all metrics `"unchanged"`

## Expected Functionality

- Given prediction "The cat sat on a mat" and reference "The cat sat on the mat": `exact_match` = 0.0, `bleu` ≈ 0.57, `rouge_l` ≈ 0.86, `f1` ≈ 0.86
- `LLMJudge` constructs the correct prompt and parses `{"accuracy": 4, "coherence": 5, "relevance": 3, "helpfulness": 4}` from judge response
- `RegressionDetector.compare([0.8, 0.85, 0.78], [0.6, 0.65, 0.58])` detects a regression with p_value < 0.05
- `EvaluationSuite.run()` over 100 test cases returns aggregated scores and per-case details

## Acceptance Criteria

- `QualityEvaluator` correctly computes exact match, BLEU-4, ROUGE-L, and token F1 scores matching standard definitions
- Custom metrics can be registered and are included in evaluation results
- `LLMJudge` constructs valid pointwise and pairwise prompts and handles JSON parse failures gracefully
- `RegressionDetector` correctly identifies statistically significant regressions and improvements using paired t-tests
- `EvaluationSuite` orchestrates metric computation, judge scoring, and model comparison into structured reports
- All edge cases (empty strings, short predictions, malformed judge output, identical scores) are handled
- All tests pass with `pytest`
