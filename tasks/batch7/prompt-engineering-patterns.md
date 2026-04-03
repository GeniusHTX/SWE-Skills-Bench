# Task: Implement a Dynamic Few-Shot Prompt Template with Semantic Example Selection in LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) provides prompt template infrastructure for LLM applications. The task is to implement a `SemanticFewShotPromptTemplate` that dynamically selects the most relevant examples from a pool based on semantic similarity to the user's input, formats them into a few-shot prompt, and supports chain-of-thought reasoning traces in the examples.

## Files to Create/Modify

- `libs/langchain/langchain/prompts/semantic_few_shot.py` (create) — `SemanticFewShotPromptTemplate` class with dynamic example selection, formatting, and CoT support
- `libs/langchain/langchain/prompts/example_store.py` (create) — `ExampleStore` class for managing few-shot examples with embedding-based retrieval
- `libs/langchain/langchain/prompts/__init__.py` (modify) — Export new classes
- `libs/langchain/tests/unit_tests/prompts/test_semantic_few_shot.py` (create) — Unit tests

## Requirements

### `ExampleStore` Class (`example_store.py`)

```python
class ExampleStore:
    def __init__(self, examples: list[dict], embedding_function: Callable[[str], list[float]], input_key: str = "input"):
```

- `examples` — List of dicts, each containing at minimum an `input_key` field and an `output` field, optionally a `reasoning` field for chain-of-thought
- `embedding_function` — Callable that takes a string and returns an embedding vector
- On initialization, compute and cache embeddings for all examples' input fields

#### Methods

- `select(query: str, k: int = 3) -> list[dict]` — Returns the top-k most similar examples to the query, ranked by cosine similarity between the query embedding and cached example embeddings
- `select_diverse(query: str, k: int = 3, lambda_mult: float = 0.5) -> list[dict]` — Returns k examples using Maximal Marginal Relevance (MMR): balance relevance to the query with diversity among selected examples. `lambda_mult` controls the relevance-diversity tradeoff (1.0 = pure relevance, 0.0 = pure diversity)
- `add_example(example: dict) -> None` — Adds a new example to the store, computes and caches its embedding
- `remove_example(index: int) -> None` — Removes the example at the given index

### `SemanticFewShotPromptTemplate` Class (`semantic_few_shot.py`)

```python
class SemanticFewShotPromptTemplate(BasePromptTemplate):
    def __init__(self, system_template: str, instruction_template: str, example_store: ExampleStore,
                 k: int = 3, selection_strategy: str = "similarity", include_reasoning: bool = False,
                 example_separator: str = "\n---\n", output_format: str | None = None):
```

- Inherits from `langchain_core.prompts.BasePromptTemplate`
- `system_template` — System prompt template with optional `{variables}`
- `instruction_template` — User instruction template; must contain `{input}` placeholder
- `example_store` — `ExampleStore` instance for example retrieval
- `k` — Number of examples to include
- `selection_strategy` — `"similarity"` or `"mmr"`
- `include_reasoning` — If `True`, include the `reasoning` field from examples (chain-of-thought)
- `example_separator` — String separating examples in the formatted prompt
- `output_format` — Optional output format instruction appended after examples

#### Methods

- `format(**kwargs) -> str`:
  1. Select k examples from the store using the configured strategy, based on `kwargs["input"]`
  2. Format each example as: `Input: {example['input']}\nOutput: {example['output']}` — if `include_reasoning` is True and the example has a `reasoning` field, insert `Reasoning: {example['reasoning']}` between Input and Output
  3. Join examples with `example_separator`
  4. Interpolate `system_template` and `instruction_template` with `kwargs`
  5. Compose the full prompt: system prompt + formatted examples + instruction + output format (if set)
  6. Return the complete prompt string

- `format_messages(**kwargs) -> list[BaseMessage]`:
  - Returns a list of `[SystemMessage(system_prompt), HumanMessage(examples + instruction)]`

#### Properties

- `input_variables` — Returns the set of variables required by both templates plus `"input"`

### Cosine Similarity

- Implement a `cosine_similarity(a: list[float], b: list[float]) -> float` utility function in `example_store.py`
- Use only standard library and numpy (no external vector DB dependencies)

### MMR Implementation

The MMR selection algorithm:
1. Compute similarity of all examples to the query
2. Select the most similar example first
3. For each subsequent selection, choose the example that maximizes: `lambda_mult * sim(example, query) - (1 - lambda_mult) * max(sim(example, already_selected))`

## Expected Functionality

- Given 100 SQL examples and the query `"find users registered this month"`, `select(query, k=3)` returns the 3 most semantically similar SQL examples
- `select_diverse(query, k=3, lambda_mult=0.5)` returns 3 examples that are both relevant and diverse (not all about the same SQL pattern)
- `format(input="find active users")` produces a complete prompt with system message, 3 selected examples, and the instruction
- With `include_reasoning=True`, examples include chain-of-thought reasoning traces between input and output
- `format_messages(input="query")` returns properly structured `SystemMessage` and `HumanMessage` objects

## Acceptance Criteria

- `ExampleStore.select` returns examples ranked by cosine similarity to the query
- `ExampleStore.select_diverse` implements MMR and produces more diverse selections than pure similarity
- `SemanticFewShotPromptTemplate.format` produces a complete prompt string with system template, formatted examples, and instruction
- With `include_reasoning=True`, chain-of-thought reasoning appears in the formatted examples
- `format_messages` returns a list of `SystemMessage` and `HumanMessage` objects
- `input_variables` correctly reports all required template variables
- `add_example` and `remove_example` correctly update the store and cached embeddings
- All classes are importable from `langchain.prompts`
