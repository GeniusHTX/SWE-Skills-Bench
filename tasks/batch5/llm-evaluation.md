# Task: Build an LLM Evaluation Pipeline with Custom Metrics for HELM

## Background

HELM (https://github.com/stanford-crfm/helm) is a holistic evaluation framework for language models. This task requires implementing a custom evaluation scenario and metrics for evaluating question-answering systems on factual accuracy, relevance, and faithfulness to provided context. The evaluation module should integrate with HELM's scenario/metric architecture.

## Files to Create/Modify

- `src/helm/benchmark/scenarios/factual_qa_scenario.py` (create) — A `FactualQAScenario` that loads a dataset of question-context-answer triples and creates `Instance` objects for evaluation. The dataset is expected as a JSON file with entries containing `question`, `context`, `reference_answer`, and `difficulty` fields.
- `src/helm/benchmark/metrics/qa_quality_metrics.py` (create) — Custom metrics: `ExactMatchMetric` (case-insensitive exact match), `TokenOverlapMetric` (F1 token overlap between prediction and reference), `FaithfulnessMetric` (checks whether the answer's claims are supported by the context using token overlap heuristics), and `AnswerRelevanceMetric` (measures whether the answer addresses the question using keyword overlap).
- `src/helm/benchmark/run_specs/factual_qa_run_spec.py` (create) — Run specification that wires the scenario to the metrics and defines adapter parameters (prompt template, max tokens, temperature).
- `tests/test_factual_qa_evaluation.py` (create) — Tests for the scenario loading, each metric computation, and the run spec wiring.

## Requirements

### FactualQA Scenario

- `FactualQAScenario(dataset_path: str)` — loads the JSON dataset file.
- `get_instances()` → list of HELM `Instance` objects, each with:
  - `input`: formatted as `"Context: {context}\n\nQuestion: {question}\n\nAnswer:"`.
  - `references`: list containing the `reference_answer` as a `Reference` object.
  - `split`: assign first 80% of entries to `TRAIN_SPLIT` and rest to `TEST_SPLIT`.
- Validate that each entry has all required fields; skip entries with missing fields and log a warning.

### Metrics

- **ExactMatchMetric**: `evaluate(prediction, reference)` → returns 1.0 if `prediction.strip().lower() == reference.strip().lower()`, else 0.0.
- **TokenOverlapMetric**: tokenize both prediction and reference (split on whitespace, lowercase), compute precision = `|common| / |prediction_tokens|`, recall = `|common| / |reference_tokens|`, F1 = `2 * precision * recall / (precision + recall)`. Return F1 (0.0 if both are 0).
- **FaithfulnessMetric**: extract noun phrases or content words from the prediction (words ≥ 4 characters, excluding stop words). Check what fraction of these content words appear in the context. Score = `|content_words_in_context| / |content_words|`. Return 0.0 if no content words.
- **AnswerRelevanceMetric**: extract content words from the question and the answer. Score = `|question_words ∩ answer_words| / |question_words|`. Measures topical overlap.
- Each metric returns a `MetricResult` with the score (float 0.0–1.0) and the metric name.

### Run Specification

- Define `factual_qa_run_spec(dataset_path: str)` returning a `RunSpec` with:
  - Scenario: `FactualQAScenario(dataset_path)`.
  - Metrics: all four metrics.
  - Adapter: `method="generation"`, `max_tokens=100`, `temperature=0.0`.
  - `num_train_instances=3` (few-shot examples from train split).

### Expected Functionality

- Loading a dataset with 100 entries → `get_instances()` returns 100 instances (80 train, 20 test).
- `ExactMatchMetric.evaluate("Paris", "paris")` → 1.0.
- `TokenOverlapMetric.evaluate("The capital is Paris", "Paris is the capital of France")` → F1 ≈ 0.67.
- `FaithfulnessMetric.evaluate("Paris is in France", context="France's capital city is Paris, located in Europe.")` → 1.0 (all content words found in context).
- `FaithfulnessMetric.evaluate("Paris is in Germany", context="France's capital city is Paris.")` → < 1.0 ("Germany" not in context).

## Acceptance Criteria

- `FactualQAScenario` loads JSON datasets and produces correctly formatted HELM `Instance` objects with train/test splits.
- All four metrics compute correct scores for known input pairs within a tolerance of 0.01.
- `FaithfulnessMetric` correctly penalizes claims not supported by the provided context.
- The run specification correctly wires scenario, metrics, and adapter settings.
- Tests validate scenario loading (including entries with missing fields), each metric with multiple test cases, and run spec configuration.
