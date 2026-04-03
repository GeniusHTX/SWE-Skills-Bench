# Task: Build a Prompt Template Library with Few-Shot Selection for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) needs a reusable prompt engineering library that implements advanced prompting patterns: few-shot learning with dynamic example selection, chain-of-thought templates, and self-consistency verification. The library must integrate with LangChain's prompt template system and be usable with any LLM provider.

## Files to Create/Modify

- `libs/langchain/langchain/prompts/few_shot_selector.py` (create) — `FewShotSelector` class that selects the most relevant examples from a pool based on semantic similarity, diversity, or random sampling
- `libs/langchain/langchain/prompts/chain_of_thought.py` (create) — `ChainOfThoughtTemplate` class that wraps any prompt with step-by-step reasoning instructions and optional verification steps
- `libs/langchain/langchain/prompts/self_consistency.py` (create) — `SelfConsistencyChecker` class that runs a prompt N times, collects responses, and selects the most common answer via majority voting
- `libs/langchain/langchain/prompts/template_library.py` (create) — Pre-built prompt templates for common tasks: `SQLGenerationTemplate`, `CodeReviewTemplate`, `SummarizationTemplate`, `ClassificationTemplate`
- `libs/tests/unit_tests/test_prompt_patterns.py` (create) — Unit tests for all prompt engineering classes

## Requirements

### Few-Shot Selector (`few_shot_selector.py`)

- Class `FewShotSelector` accepts: `examples` (list of dicts with `input` and `output` keys), `strategy` (one of `"semantic"`, `"diversity"`, `"random"`), `max_examples` (int, default 3), `embedding_function` (Optional callable, required for `"semantic"` strategy)
- Method `select(query: str) -> list[dict]` — Returns up to `max_examples` examples:
  - `"semantic"`: Compute cosine similarity between `query` embedding and each example's `input` embedding, return top-k
  - `"diversity"`: Select first by similarity, then iteratively select examples most dissimilar to already-selected ones (Maximal Marginal Relevance)
  - `"random"`: Return a random sample of `max_examples`
- Method `format_examples(examples: list[dict], template: str = "Input: {input}\nOutput: {output}") -> str` — Formats selected examples into a prompt string with the given template, separated by `"\n\n"`
- Cosine similarity must use `numpy.dot(a, b) / (numpy.linalg.norm(a) * numpy.linalg.norm(b))`
- MMR lambda parameter defaults to 0.5 (balance between relevance and diversity)

### Chain-of-Thought Template (`chain_of_thought.py`)

- Class `ChainOfThoughtTemplate` accepts: `task_description` (str), `reasoning_prefix` (str, default `"Let's think step by step:"`) , `verification_step` (bool, default False), `output_instruction` (str, default `"Therefore, the answer is:"`)
- Method `render(query: str, examples: Optional[list[dict]] = None) -> str` — Builds a prompt:
  1. Task description
  2. Few-shot examples (if provided), each including reasoning trace
  3. The query
  4. Reasoning prefix
  5. If `verification_step` is True, append `"\n\nLet me verify this reasoning:\n"` before the output instruction
  6. Output instruction
- Each example dict must include `input`, `reasoning`, and `output` keys
- The template must be compatible with LangChain's `PromptTemplate` interface (implements `format(**kwargs) -> str`)

### Self-Consistency Checker (`self_consistency.py`)

- Class `SelfConsistencyChecker` accepts: `num_samples` (int, default 5), `temperature` (float, default 0.7), `extract_answer_fn` (callable that extracts the final answer from a response string)
- Method `check(responses: list[str]) -> dict` — Takes a list of LLM response strings, applies `extract_answer_fn` to each, performs majority voting, returns `{"answer": most_common, "confidence": fraction_of_votes, "all_answers": list, "vote_counts": dict}`
- If there is a tie, return the answer that appeared first in the response list
- `confidence` is the fraction of responses that match the majority answer (e.g., 3/5 = 0.6)

### Template Library (`template_library.py`)

- `SQLGenerationTemplate` — System: expert SQL developer; includes schema context variable `{schema}`; instruction: convert `{query}` to SQL; output format: SQL code block
- `CodeReviewTemplate` — System: senior engineer; includes `{code}` and `{language}` variables; instruction: review for bugs, performance, security; output format: structured findings list
- `SummarizationTemplate` — System: professional writer; includes `{text}` and `{max_length}` variables; instruction: summarize in `{max_length}` words; output format: bullet points
- `ClassificationTemplate` — System: text classifier; includes `{text}` and `{categories}` variables; instruction: classify into one of the categories; output format: JSON `{"category": "...", "confidence": 0.X, "reasoning": "..."}`
- Each template must be a class with `render(**kwargs) -> str` method and expose its variables as a `required_variables: list[str]` property

### Expected Functionality

- `FewShotSelector` with semantic strategy and 10 examples returns the 3 most similar examples to a given query
- `ChainOfThoughtTemplate` with verification produces a prompt containing "Let's think step by step:" and "Let me verify this reasoning:"
- `SelfConsistencyChecker` with responses `["Paris", "Paris", "London", "Paris", "Berlin"]` returns `{"answer": "Paris", "confidence": 0.6}`
- `SQLGenerationTemplate().render(schema="users(id, name, email)", query="find all active users")` returns a complete prompt string with the schema and query interpolated

## Acceptance Criteria

- `FewShotSelector` correctly implements semantic, diversity (MMR), and random selection strategies
- Cosine similarity calculation matches expected results for known vector pairs
- `ChainOfThoughtTemplate` produces well-structured prompts with optional verification steps
- `SelfConsistencyChecker` performs majority voting with correct confidence calculation and tie-breaking
- All four template library classes render complete prompts with all variables interpolated
- `required_variables` property lists the correct variable names for each template
- `python -m pytest /workspace/tests/test_prompt_engineering_patterns.py -v --tb=short` passes
