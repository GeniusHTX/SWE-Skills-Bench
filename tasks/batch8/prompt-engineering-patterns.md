# Task: Implement a Prompt Optimization Toolkit for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for building LLM-powered applications. The project needs a prompt optimization toolkit that enables users to build structured prompt templates with few-shot example selection, chain-of-thought formatting, and A/B testing of prompt variants. The toolkit should integrate with LangChain's existing `PromptTemplate` and `ChatPromptTemplate` abstractions and be usable within LangChain chains and agents.

## Files to Create/Modify

- `libs/langchain/langchain/prompts/optimizer.py` (create) — `PromptOptimizer` class that manages prompt variants, selects few-shot examples by semantic similarity, and formats chain-of-thought reasoning steps
- `libs/langchain/langchain/prompts/few_shot_selector.py` (create) — `SemanticFewShotSelector` class that selects the most relevant examples from a pool using embedding similarity, with configurable max examples and diversity sampling
- `libs/langchain/langchain/prompts/cot_formatter.py` (create) — `ChainOfThoughtFormatter` class that wraps prompts with step-by-step reasoning instructions and can inject reasoning traces from few-shot examples
- `libs/langchain/langchain/prompts/ab_test.py` (create) — `PromptABTest` class that runs multiple prompt variants against a test set and reports accuracy, consistency, and average token usage per variant
- `tests/test_prompt_engineering_patterns.py` (create) — Test suite covering few-shot selection, CoT formatting, A/B testing logic, and end-to-end prompt optimization

## Requirements

### SemanticFewShotSelector

- Constructor: `SemanticFewShotSelector(examples: list[dict], embedding_fn: Callable[[str], list[float]], max_examples: int = 3)`
- Each example is a dict with keys `input` (str) and `output` (str), and optionally `reasoning` (str)
- `select(query: str) -> list[dict]` — Embed the query and all example inputs, return the top `max_examples` by cosine similarity
- `select_diverse(query: str, lambda_param: float = 0.5) -> list[dict]` — Use Maximal Marginal Relevance: iteratively pick examples that balance relevance to query (cosine similarity) and diversity from already-selected examples; `lambda_param` controls the trade-off (1.0 = pure relevance, 0.0 = pure diversity)
- If `examples` is empty, both methods return an empty list
- If `max_examples` exceeds the number of available examples, return all examples sorted by relevance

### ChainOfThoughtFormatter

- Constructor: `ChainOfThoughtFormatter(style: str = "step_by_step")` where `style` is one of `"step_by_step"`, `"zero_shot"`, `"structured"`
- `format_instruction(instruction: str) -> str`:
  - `"step_by_step"`: Append `"\n\nLet's solve this step by step:\nStep 1:"` to the instruction
  - `"zero_shot"`: Append `"\n\nLet's think step by step."` to the instruction
  - `"structured"`: Append `"\n\nAnalysis:\n1. Identify the key elements\n2. Apply relevant rules\n3. Derive the answer\n\nAnswer:"` to the instruction
- `format_example(example: dict) -> str` — If example has `reasoning` key, format as `"Input: {input}\nReasoning: {reasoning}\nOutput: {output}"`; otherwise `"Input: {input}\nOutput: {output}"`
- Raise `ValueError` if `style` is not one of the three valid values

### PromptOptimizer

- Constructor: `PromptOptimizer(template: str, selector: SemanticFewShotSelector, formatter: ChainOfThoughtFormatter)`
- `template` is a string with `{instruction}`, `{examples}`, and `{query}` placeholders
- `build_prompt(query: str) -> str`:
  1. Select few-shot examples using the selector with the query
  2. Format each example using the formatter
  3. Format the instruction using the formatter
  4. Substitute all placeholders in the template and return the final prompt string
- `build_prompt_diverse(query: str, lambda_param: float = 0.5) -> str` — Same as `build_prompt` but uses `select_diverse` for example selection
- The optimizer must not modify the original template string

### PromptABTest

- Constructor: `PromptABTest(variants: dict[str, PromptOptimizer])` where keys are variant names (e.g., `"baseline"`, `"cot"`, `"few_shot_3"`)
- `run(test_cases: list[dict], eval_fn: Callable[[str, str], float]) -> dict`:
  - Each test case has `query` (str) and `expected` (str)
  - For each variant, build the prompt for each query, call `eval_fn(built_prompt, expected)` to get a score (0.0-1.0)
  - Return a dict mapping variant names to result dicts: `{"mean_score": float, "scores": list[float], "avg_prompt_length": float}`
- `best_variant() -> str` — Return the variant name with the highest mean score from the most recent `run()` call; raise `RuntimeError` if `run()` has not been called yet
- If `variants` is empty, `run()` raises `ValueError`

### Edge Cases

- Embedding function that returns zero vectors must not cause division by zero in cosine similarity — return similarity of 0.0
- Template with missing placeholders must raise `KeyError` identifying which placeholder is missing
- A/B test with all variants scoring 0.0 must still return a valid result (pick first variant alphabetically as best)

## Expected Functionality

- Given 10 labelled examples and a query, `SemanticFewShotSelector` returns the 3 most similar examples by embedding cosine distance
- `select_diverse` with `lambda_param=0.5` returns examples that are both relevant and different from each other
- `ChainOfThoughtFormatter("step_by_step")` appends structured reasoning instructions to any prompt
- `PromptOptimizer.build_prompt("What is 2+2?")` returns a fully assembled prompt with selected examples, CoT formatting, and the query substituted
- `PromptABTest` compares a baseline variant against a CoT variant and reports that CoT scores higher on reasoning tasks

## Acceptance Criteria

- `SemanticFewShotSelector.select()` returns examples ranked by cosine similarity to the query embedding
- `select_diverse()` produces results where selected examples have lower pairwise similarity than `select()` results when `lambda_param < 1.0`
- `ChainOfThoughtFormatter` produces the exact suffix strings specified for each style
- `PromptOptimizer.build_prompt()` assembles a complete prompt with examples, CoT formatting, and query substitution
- `PromptABTest.run()` evaluates all variants against all test cases and correctly identifies the best-performing variant
- Zero-vector embeddings, empty example pools, and missing template placeholders are handled without crashes
- All tests pass with `pytest`
