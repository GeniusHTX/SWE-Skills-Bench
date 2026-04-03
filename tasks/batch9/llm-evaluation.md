# Task: Build an LLM Evaluation Framework with Automated Metrics and LLM-as-Judge

## Background

HELM (https://github.com/stanford-crfm/helm) is an LLM evaluation framework. A new evaluation module is needed that implements a composable evaluation pipeline supporting automated text metrics (BLEU, ROUGE, BERTScore), classification metrics (accuracy, F1, confusion matrix), retrieval metrics (MRR, NDCG), and LLM-as-judge evaluation with both pointwise and pairwise scoring. The framework must support running evaluation suites and producing structured reports.

## Files to Create/Modify

- `src/helm/benchmark/metrics/text_metrics.py` (create) — Text generation metrics: `BLEUMetric`, `ROUGEMetric`, `BERTScoreMetric` classes, each implementing a common `Metric` interface
- `src/helm/benchmark/metrics/classification_metrics.py` (create) — Classification metrics: `AccuracyMetric`, `F1Metric`, `ConfusionMatrixMetric`
- `src/helm/benchmark/metrics/retrieval_metrics.py` (create) — Retrieval metrics: `MRRMetric`, `NDCGMetric`, `PrecisionAtKMetric`, `RecallAtKMetric`
- `src/helm/benchmark/metrics/llm_judge.py` (create) — `LLMJudge` class with `pointwise_score` and `pairwise_compare` methods that use a configurable LLM function to evaluate responses
- `src/helm/benchmark/eval_suite.py` (create) — `EvalSuite` class that runs a collection of metrics on a dataset and produces a structured report
- `src/helm/benchmark/eval_report.py` (create) — Report generator: formats results as dict, DataFrame, Markdown, and JSON
- `tests/test_evaluation_framework.py` (create) — Tests with fixed inputs and expected metric values

## Requirements

### Metric Interface

- All metrics implement: `name: str` property, `compute(predictions: list[str], references: list[str], **kwargs) -> MetricResult`
- `MetricResult` is a dataclass: `{"metric_name": str, "score": float, "details": dict, "per_sample": Optional[list[float]]}`

### Text Metrics (`text_metrics.py`)

- `BLEUMetric` — Corpus-level BLEU-4 score using `nltk.translate.bleu_score.corpus_bleu` with `SmoothingFunction().method1`
  - `per_sample`: sentence-level BLEU for each prediction-reference pair
  - Handle empty predictions by returning score 0.0
- `ROUGEMetric(metric_type="rouge-l")` — ROUGE-L F1 score using `rouge_score` library
  - Accepts `metric_type` from `["rouge-1", "rouge-2", "rouge-l"]`
  - `per_sample`: per-sentence ROUGE scores
- `BERTScoreMetric(model_name="microsoft/deberta-xlarge-mnli")` — BERTScore F1 using the `bert_score` library
  - `per_sample`: per-sentence BERTScore F1 values
  - For testing without the actual model, accept an optional `mock_scorer` callable

### Classification Metrics (`classification_metrics.py`)

- `AccuracyMetric` — Fraction of correct predictions. `predictions` and `references` are label strings
- `F1Metric(average="macro")` — F1 score using `sklearn.metrics.f1_score`; `average` accepts `"micro"`, `"macro"`, `"weighted"`, `"binary"`
  - `details` includes per-class precision, recall, and F1
- `ConfusionMatrixMetric` — Returns `details` containing the confusion matrix as a nested list and the label list

### Retrieval Metrics (`retrieval_metrics.py`)

- Override interface: `compute(predictions: list[list[str]], references: list[list[str]], k: int = 10) -> MetricResult` where each prediction is a ranked list of document IDs and each reference is a list of relevant document IDs
- `MRRMetric` — Mean Reciprocal Rank: `1/Q * sum(1/rank_of_first_relevant)`; if no relevant document is in the prediction, reciprocal rank is 0
- `NDCGMetric(k=10)` — `1/Q * sum(DCG@k / IDCG@k)` where `DCG@k = sum(rel_i / log2(i+1))` for i in 1..k, with `rel_i = 1` if prediction at rank i is relevant
- `PrecisionAtKMetric(k=10)` — Fraction of top-k predictions that are relevant
- `RecallAtKMetric(k=10)` — Fraction of relevant documents found in top-k predictions

### LLM-as-Judge (`llm_judge.py`)

- Class `LLMJudge` accepts: `llm_fn` (callable taking prompt string, returns string), `rubric` (dict mapping score to description, e.g., `{1: "Poor", 2: "Fair", 3: "Good", 4: "Excellent"}`)
- Method `pointwise_score(question: str, response: str, reference: Optional[str] = None) -> dict`:
  - Builds a prompt asking the LLM to rate the response on the rubric scale
  - Parses the LLM output to extract a numeric score
  - Returns `{"score": int, "reasoning": str, "raw_output": str}`
  - If score parsing fails, returns `{"score": -1, "reasoning": "Parse error", "raw_output": str}`
- Method `pairwise_compare(question: str, response_a: str, response_b: str) -> dict`:
  - Builds a prompt asking the LLM which response is better (A or B) with justification
  - Returns `{"winner": "A"|"B"|"tie", "reasoning": str, "raw_output": str}`
  - Randomize presentation order to mitigate position bias; record which was actually A/B
- Method `evaluate_batch(questions, responses, references=None) -> list[dict]` — Runs `pointwise_score` on each sample, returns list of results with aggregate statistics

### Eval Suite (`eval_suite.py`)

- Class `EvalSuite` accepts: `metrics` (list of Metric instances), `name` (str)
- Method `run(predictions, references, **kwargs) -> EvalReport` — Runs all metrics, returns structured report
- `EvalReport` contains: `suite_name`, `timestamp`, `results` (list of MetricResult), `summary` (dict of metric_name → score)

### Expected Functionality

- `BLEUMetric().compute(["the cat sat on the mat"], ["the cat sat on a mat"])` returns a score between 0 and 1
- `AccuracyMetric().compute(["cat", "dog", "cat"], ["cat", "cat", "cat"])` returns score 0.667
- `MRRMetric().compute([["d1","d2","d3"]], [["d2"]])` returns score 0.5 (d2 is at rank 2)
- `LLMJudge` with a mock LLM returning "Score: 3\nReasoning: Good response" returns `{"score": 3, ...}`

## Acceptance Criteria

- All text metrics produce correct scores for known input-output pairs
- Classification metrics match sklearn results for the same inputs
- Retrieval metrics correctly handle queries with no relevant documents (MRR = 0)
- LLM Judge extracts numeric scores and winner labels from LLM responses
- Position bias mitigation randomizes response order in pairwise comparison
- EvalSuite runs all metrics and produces a structured report with per-metric scores
- `python -m pytest /workspace/tests/test_llm_evaluation.py -v --tb=short` passes
