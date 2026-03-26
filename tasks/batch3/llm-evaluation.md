# Task: Build an LLM Evaluation Framework with Multi-Metric Scoring for HELM

## Background

HELM (https://github.com/stanford-crfm/helm) is Stanford CRFM's holistic evaluation framework for language models. The project needs a modular evaluation module that defines metrics for accuracy, faithfulness, toxicity detection, and coherence; supports LLM-as-judge scoring; and produces structured evaluation reports. This should integrate with HELM's existing scenario and metric infrastructure under the `src/helm` directory.

## Files to Create/Modify

- `src/helm/benchmark/metrics/multi_metric_scorer.py` (create) — Multi-metric evaluation engine supporting automated metrics and LLM-as-judge
- `src/helm/benchmark/metrics/faithfulness_metric.py` (create) — Faithfulness metric comparing generated text against reference sources
- `src/helm/benchmark/metrics/evaluation_report.py` (create) — Structured evaluation report generator with per-sample and aggregate results
- `src/helm/benchmark/metrics/test_multi_metric_scorer.py` (create) — Tests for the evaluation framework

## Requirements

### Multi-Metric Scorer

- Implement a `MultiMetricScorer` class that evaluates an LLM output against multiple metrics in a single pass
- Accept a list of `Metric` objects, each with a `name` and a `score(prediction: str, reference: str, context: dict) -> MetricResult` method
- `MetricResult` contains: `score` (float 0.0–1.0), `explanation` (str), `metadata` (dict)
- Return a `SampleResult` for each input containing all metric scores and an aggregate score (configurable: mean, weighted mean, or minimum)
- Support weighting: each metric can have a `weight` (default: 1.0); weighted mean = Σ(weight_i × score_i) / Σ(weight_i)

### Built-in Metrics

- **ExactMatchMetric**: 1.0 if prediction matches reference exactly (after whitespace normalization), 0.0 otherwise
- **ContainsMetric**: 1.0 if reference string is contained in prediction, 0.0 otherwise; case-insensitive by default with a `case_sensitive` parameter
- **RougeMetric**: Compute ROUGE-L F1 score between prediction and reference (use longest common subsequence)
- **LengthPenaltyMetric**: 1.0 if prediction length is within [min_length, max_length]; linearly penalize down to 0.0 outside this range; configurable min/max

### Faithfulness Metric

- Given a prediction and a list of source passages, compute a faithfulness score
- For each claim-bearing sentence in the prediction, check if it is supported by at least one source passage
- The score is the fraction of supported sentences: `num_supported / num_total_sentences`
- Sentence splitting: split on `.`, `!`, `?` followed by whitespace or end-of-string
- A sentence is "supported" if it has a word overlap ratio ≥ 0.5 with at least one source passage (ratio = |intersection| / |sentence_words|)
- Return per-sentence support details in the metadata

### LLM-as-Judge Support

- Implement an `LLMJudgeMetric` class that uses a configurable `judge_function: (prompt: str, prediction: str, reference: str) -> float`
- The `judge_function` is injected (not hardcoded to any specific LLM provider)
- The metric constructs an evaluation prompt with the prediction and reference, calls the judge function, and interprets the returned float as the score
- If the judge function raises an exception, the metric returns score 0.0 with the exception message in `explanation`

### Evaluation Report

- Implement an `EvaluationReport` class that aggregates results across multiple samples
- Provide methods: `add_sample(sample_id, sample_result)`, `summary() -> ReportSummary`
- `ReportSummary` includes: per-metric mean/median/std across all samples, overall aggregate score, number of samples, per-metric score distribution (min, max, p25, p50, p75)
- Provide `to_json() -> str` and `to_csv(path)` export methods
- The JSON output must be deterministic (sorted keys, 4-space indent)

### Expected Functionality

- Scoring `"The capital of France is Paris"` against reference `"Paris"` with `ContainsMetric` returns 1.0
- Scoring the same with `ExactMatchMetric` returns 0.0 (not an exact match)
- Faithfulness of `"Paris is in France. Mars is a planet."` against source `"Paris is the capital of France"` returns 0.5 (1 of 2 sentences supported)
- A `MultiMetricScorer` with ExactMatch (weight=1) and Contains (weight=2) returns weighted mean = (0×1 + 1×2) / 3 = 0.667
- An evaluation report with 100 samples produces a summary with correct mean and percentile statistics
- `to_json()` produces valid JSON with sorted keys

## Acceptance Criteria

- `MultiMetricScorer` evaluates all metrics and computes aggregate scores correctly (mean, weighted mean, minimum)
- `ExactMatchMetric`, `ContainsMetric`, `RougeMetric`, and `LengthPenaltyMetric` produce correct scores
- `FaithfulnessMetric` computes sentence-level support correctly with word overlap ratio ≥ 0.5
- `LLMJudgeMetric` calls the injected judge function and handles exceptions gracefully
- `EvaluationReport` correctly aggregates per-metric statistics (mean, median, std, percentiles)
- `to_json()` output is deterministic and valid JSON; `to_csv()` produces correct CSV output
- Tests cover all metrics with known inputs, weighted aggregation, faithfulness edge cases, and report generation
