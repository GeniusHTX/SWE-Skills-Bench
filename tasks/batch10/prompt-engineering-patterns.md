# Task: Implement Few-Shot and Chain-of-Thought Prompt Template System for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) provides composable building blocks for LLM applications. The project needs a new prompt template module that supports dynamic few-shot example selection, chain-of-thought reasoning elicitation, and structured output formatting. This module will live in `libs/langchain/` and integrate with LangChain's existing `PromptTemplate` and `ChatPromptTemplate` infrastructure, providing production-ready prompt patterns that handle variable interpolation, example management, and multi-turn conversation templates.

## Files to Create/Modify

- `libs/langchain/langchain/prompts/advanced_templates.py` (new) — Prompt template classes for few-shot learning with dynamic example selection, chain-of-thought prompting, and system prompt composition
- `libs/langchain/langchain/prompts/example_selector.py` (new) — Example selector implementations supporting semantic similarity–based and diversity-based selection strategies
- `libs/core/tests/unit_tests/prompts/test_advanced_templates.py` (new) — Unit tests covering template rendering, example selection, CoT formatting, and edge cases

## Requirements

### Few-Shot Prompt Template (`advanced_templates.py`)

- Implement a `FewShotPromptTemplate` class with constructor parameters:
  - `system_message: str` — system-level instruction
  - `instruction: str` — task instruction with `{input}` placeholder
  - `example_template: str` — format string for each example with `{input}` and `{output}` placeholders
  - `examples: list[dict]` — static list of example dicts each containing `"input"` and `"output"` keys
  - `example_separator: str` — separator between examples (default `"\n\n"`)
  - `max_examples: int` — maximum number of examples to include (default `3`)
  - `suffix: str | None` — optional text appended after the input
- Method `format(input: str, **kwargs) -> str` must render the full prompt: system message, then selected examples formatted via `example_template`, then the instruction with `{input}` replaced, then the suffix if provided
- If `len(examples) > max_examples`, only the first `max_examples` examples are included
- All `{placeholder}` variables in `instruction` and `suffix` beyond `{input}` must be filled from `**kwargs`; missing kwargs must raise `KeyError` with the placeholder name

### Dynamic Example Selector (`example_selector.py`)

- Implement a `SemanticSimilaritySelector` class that accepts:
  - `examples: list[dict]` — pool of examples
  - `embedding_fn: Callable[[str], list[float]]` — function that returns an embedding vector for a string
  - `k: int` — number of examples to select (default `3`)
- Method `select(query: str) -> list[dict]` must compute cosine similarity between `embedding_fn(query)` and `embedding_fn(example["input"])` for each example, then return the top `k` examples sorted by descending similarity
- Implement a `DiversitySelector` class that accepts the same parameters but selects examples using maximal marginal relevance: the first example is the most similar to the query, each subsequent example maximizes `lambda * similarity_to_query - (1 - lambda) * max_similarity_to_selected`, with `lambda_param: float = 0.5`
- Both selectors must be usable as the `example_selector` parameter on `FewShotPromptTemplate` (when provided, `example_selector.select(input)` is called instead of using the static `examples` list)

### Chain-of-Thought Template (`advanced_templates.py`)

- Implement a `ChainOfThoughtTemplate` class with constructor parameters:
  - `system_message: str`
  - `instruction: str` with `{input}` placeholder
  - `reasoning_prefix: str` — text prepended before the reasoning section (default `"Let's think step by step:\n"`)
  - `answer_prefix: str` — text that marks the final answer section (default `"\nTherefore, the answer is: "`)
  - `examples: list[dict] | None` — optional few-shot examples, each having `"input"`, `"reasoning"`, and `"output"` keys
- Method `format(input: str) -> str` must render: system message, optional examples (each showing input → reasoning → output), then the instruction with input, then `reasoning_prefix`
- When `examples` is provided (few-shot CoT), each example must show the full reasoning trace; when `examples` is `None` (zero-shot CoT), only the reasoning prefix is appended

### System Prompt Composer (`advanced_templates.py`)

- Implement a `SystemPromptComposer` class that builds system prompts from modular components:
  - `role: str` — the role/persona (e.g., `"You are an expert SQL developer."`)
  - `constraints: list[str]` — behavioral constraints (e.g., `["Never generate DROP statements"]`)
  - `output_format: str | None` — expected output format description
  - `context: str | None` — background context/information
- Method `compose() -> str` must concatenate: role, then constraints as a numbered list under a `"Constraints:"` header, then context under `"Context:"` if provided, then output format under `"Output Format:"` if provided
- Each section must be separated by a blank line

### Expected Functionality

- `FewShotPromptTemplate` with 5 examples and `max_examples=3` → rendered prompt contains exactly 3 examples
- `FewShotPromptTemplate` with 0 examples → rendered prompt contains system message and instruction but no examples section
- `FewShotPromptTemplate.format(input="test")` where instruction is `"Translate {input} to {language}"` and `language` not in kwargs → raises `KeyError("language")`
- `SemanticSimilaritySelector` with 10 examples, `k=3`, and a query → returns 3 examples; the first is the most semantically similar to the query
- `DiversitySelector` with 10 examples, `k=3` → first example is most similar to query; second and third are diverse (not the 2nd and 3rd most similar)
- `ChainOfThoughtTemplate` with `examples=None` → output ends with `"Let's think step by step:\n"` (zero-shot CoT)
- `ChainOfThoughtTemplate` with 2 examples → output includes both reasoning traces before the new input
- `SystemPromptComposer(role="Expert", constraints=["Be concise", "Cite sources"], output_format="JSON", context="User is a developer").compose()` → output has `"Expert"`, numbered constraints, context section, and format section separated by blank lines
- `SystemPromptComposer(role="Expert", constraints=[], output_format=None, context=None).compose()` → output contains only the role with no empty section headers

## Acceptance Criteria

- `FewShotPromptTemplate` correctly renders system message, examples (up to `max_examples`), and instruction with interpolated variables
- Missing template variables raise `KeyError` with the variable name
- `SemanticSimilaritySelector` returns top-k examples by cosine similarity to the query
- `DiversitySelector` produces a more diverse set than pure similarity ranking (not identical to top-k similarity)
- `ChainOfThoughtTemplate` supports both zero-shot (no examples) and few-shot (with reasoning traces) modes
- `SystemPromptComposer` omits sections that are `None` or empty without leaving blank headers
- All tests in `libs/core/tests/unit_tests/prompts/test_advanced_templates.py` pass via `python -m pytest libs/core/tests/unit_tests/prompts/test_advanced_templates.py -v`
