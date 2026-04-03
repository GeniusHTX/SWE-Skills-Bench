# Task: Add BERTScore and Semantic Similarity Metrics to the HELM Evaluation Framework

## Background

HELM (https://github.com/stanford-crfm/helm) is a holistic evaluation framework for language models. The `metrics` module provides evaluation metrics like BLEU, ROUGE, and exact match. The task is to add BERTScore (precision, recall, F1 using contextual embeddings), semantic similarity (cosine similarity of sentence embeddings), and answer relevance (LLM-as-judge scoring) as new metric classes integrated into HELM's metric infrastructure.

## Files to Create/Modify

- `src/helm/benchmark/metrics/bertscore_metric.py` (create) — `BERTScoreMetric` class computing BERTScore precision, recall, and F1 between generated and reference texts
- `src/helm/benchmark/metrics/semantic_similarity_metric.py` (create) — `SemanticSimilarityMetric` class computing cosine similarity between sentence embeddings
- `src/helm/benchmark/metrics/answer_relevance_metric.py` (create) — `AnswerRelevanceMetric` class that scores answer relevance on a 1-5 scale using an LLM judge
- `src/helm/benchmark/metrics/__init__.py` (modify) — Export new metric classes
- `src/helm/benchmark/metrics/metric_name.py` (modify) — Register new metric names: `bertscore_precision`, `bertscore_recall`, `bertscore_f1`, `semantic_similarity`, `answer_relevance`
- `tests/benchmark/metrics/test_bertscore_metric.py` (create) — Unit tests for BERTScore
- `tests/benchmark/metrics/test_semantic_similarity_metric.py` (create) — Unit tests for semantic similarity
- `tests/benchmark/metrics/test_answer_relevance_metric.py` (create) — Unit tests for answer relevance

## Requirements

### `BERTScoreMetric` (`bertscore_metric.py`)

Inherits from HELM's `Metric` base class.

#### Constructor
```python
BERTScoreMetric(model_name: str = "microsoft/deberta-xlarge-mnli", batch_size: int = 64, device: str = "cpu")
```

#### `evaluate(request_state: RequestState) -> list[Stat]`
1. Extract the generated text from `request_state.result.completions[0].text`
2. Extract reference texts from `request_state.instance.references` (use only references with `CORRECT` tag)
3. Compute BERTScore between the generated text and each reference:
   a. Tokenize both texts using the model's tokenizer
   b. Compute contextual embeddings for all tokens
   c. Compute pairwise cosine similarity matrix between generated and reference token embeddings
   d. **Precision**: For each generated token, take the max similarity across reference tokens; average over all generated tokens
   e. **Recall**: For each reference token, take the max similarity across generated tokens; average over all reference tokens
   f. **F1**: Harmonic mean of precision and recall
4. If multiple references exist, take the maximum F1 across references (best-match)
5. Return three `Stat` objects: `bertscore_precision`, `bertscore_recall`, `bertscore_f1`

#### IDF Weighting (optional enhancement)
- If `use_idf=True` (constructor parameter, default `False`), weight token similarities by inverse document frequency computed over the reference corpus before averaging

### `SemanticSimilarityMetric` (`semantic_similarity_metric.py`)

#### Constructor
```python
SemanticSimilarityMetric(model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu")
```

#### `evaluate(request_state: RequestState) -> list[Stat]`
1. Extract generated text and reference texts (same as BERTScore)
2. Encode both texts into sentence embeddings using the sentence-transformers model
3. Compute cosine similarity between the generated embedding and each reference embedding
4. Return the maximum similarity as a `Stat(name="semantic_similarity", value=<float>)`
5. Similarity values range from -1.0 to 1.0

### `AnswerRelevanceMetric` (`answer_relevance_metric.py`)

#### Constructor
```python
AnswerRelevanceMetric(judge_model: str = "openai/gpt-4", max_tokens: int = 256)
```

#### `evaluate(request_state: RequestState) -> list[Stat]`
1. Extract the question/prompt from `request_state.instance.input.text`
2. Extract the generated answer from `request_state.result.completions[0].text`
3. Extract reference answer(s) from `request_state.instance.references`
4. Construct a judge prompt:
   ```
   Rate the following answer on a scale of 1-5 for relevance to the question.
   
   Question: {question}
   Reference Answer: {reference}
   Generated Answer: {generated}
   
   Rating criteria:
   5: Fully answers the question with correct, complete information
   4: Mostly correct with minor omissions
   3: Partially correct but missing key information
   2: Tangentially related but does not answer the question
   1: Completely irrelevant or incorrect
   
   Respond with only the numeric rating (1-5).
   ```
5. Call the judge model via HELM's model serving infrastructure
6. Parse the numeric rating from the response (extract the first digit 1-5)
7. Return `Stat(name="answer_relevance", value=<int>)`
8. If parsing fails (no valid rating in response), return `Stat(name="answer_relevance", value=0)` with a warning

### Metric Registration (`metric_name.py`)

Add the following to the MetricName enum or registry:
- `BERTSCORE_PRECISION = "bertscore_precision"`
- `BERTSCORE_RECALL = "bertscore_recall"`
- `BERTSCORE_F1 = "bertscore_f1"`
- `SEMANTIC_SIMILARITY = "semantic_similarity"`
- `ANSWER_RELEVANCE = "answer_relevance"`

### Performance Requirements

- `BERTScoreMetric` must batch token embeddings (process `batch_size` pairs at once)
- `SemanticSimilarityMetric` must cache the model after first load (singleton pattern)
- All metrics must handle empty generated text gracefully (return 0.0 scores)
- All metrics must handle missing references gracefully (return 0.0 scores with a warning)

## Expected Functionality

- Given generated text "The capital of France is Paris" and reference "Paris is the capital of France":
  - BERTScore F1 should be high (>0.9) due to semantic equivalence
  - Semantic similarity should be high (>0.85)
- Given generated text "Bananas are yellow" and reference "Paris is the capital of France":
  - BERTScore F1 should be low (<0.5)
  - Semantic similarity should be low (<0.3)
- Given a question "What is the capital of France?", generated "Paris", reference "Paris": answer relevance should be 5

## Acceptance Criteria

- `BERTScoreMetric` correctly computes token-level precision, recall, and F1 using contextual embeddings
- BERTScore with identical texts returns values close to 1.0
- `SemanticSimilarityMetric` returns cosine similarity between sentence embeddings
- `AnswerRelevanceMetric` constructs the judge prompt correctly and parses the numeric rating
- All three metrics handle empty inputs and missing references by returning 0.0 scores
- New metric names are registered and accessible through HELM's metric infrastructure
- Metrics are importable from `helm.benchmark.metrics`
- All test suites pass with mock models and pre-computed embeddings
