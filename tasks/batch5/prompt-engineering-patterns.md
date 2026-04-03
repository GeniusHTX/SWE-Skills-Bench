# Task: Build a Reusable Prompt Template Library for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) provides composable building blocks for LLM applications. This task requires implementing a reusable prompt template library within the LangChain `libs/langchain/langchain/prompts/` directory that provides structured templates for common use cases: few-shot classification, chain-of-thought reasoning, and output-constrained generation. Each template must be composable, use `PromptTemplate` or `ChatPromptTemplate` as the base, and include built-in input validation.

## Files to Create/Modify

- `libs/langchain/langchain/prompts/library/classification.py` (create) — Few-shot classification prompt: accepts a list of labeled examples, an input query, and a label set. Dynamically formats examples into the prompt. Validates that example labels are within the allowed label set.
- `libs/langchain/langchain/prompts/library/chain_of_thought.py` (create) — Chain-of-thought prompt: wraps a user question with explicit "think step by step" instructions, includes optional hint text, and enforces a structured response format with separate `reasoning` and `answer` sections.
- `libs/langchain/langchain/prompts/library/constrained_output.py` (create) — Output-constrained prompt: accepts a JSON schema definition and instructs the LLM to produce output strictly matching the schema. Includes a validation function that checks LLM output against the provided schema.
- `libs/langchain/langchain/prompts/library/__init__.py` (create) — Package init exporting all three template classes.
- `tests/unit_tests/prompts/test_prompt_library.py` (create) — Tests for all three templates covering formatting, validation, and edge cases.

## Requirements

### Few-Shot Classification Template

- Class `FewShotClassificationPrompt` with parameters: `task_description` (str), `labels` (list of str), `examples` (list of dicts with keys `input` and `label`), `query` (str).
- The `format()` method produces a prompt string structured as:
  ```
  {task_description}
  Allowed labels: {comma-separated labels}
  
  Examples:
  Input: {example.input} → Label: {example.label}
  ...
  
  Input: {query} → Label:
  ```
- Validation: if any example's `label` is not in the `labels` list, raise `ValueError` with the invalid label name.
- Support adding examples incrementally via an `add_example(input, label)` method.

### Chain-of-Thought Template

- Class `ChainOfThoughtPrompt` with parameters: `question` (str), `hint` (optional str), `max_steps` (int, default 5).
- The `format()` method produces a prompt that instructs the model to reason step by step (up to `max_steps` steps), show its work, and then provide a final answer.
- Include a `parse_response(text)` static method that extracts the `reasoning` and `answer` sections from the LLM response using markers `[REASONING]...[/REASONING]` and `[ANSWER]...[/ANSWER]`.
- If the response does not contain the markers, `parse_response` returns `{"reasoning": None, "answer": text.strip()}`.

### Constrained Output Template

- Class `ConstrainedOutputPrompt` with parameters: `instruction` (str), `output_schema` (dict — a JSON Schema object), `strict` (bool, default True).
- The `format()` method embeds the JSON schema in the prompt and instructs the model to return only valid JSON matching the schema.
- Include a `validate_output(text)` method that parses the JSON from the LLM response and validates it against `output_schema` using `jsonschema.validate`. Returns `(parsed_dict, None)` on success or `(None, error_message)` on failure.
- If the response contains text before/after the JSON block, the method should extract the first `{...}` block.

### Expected Functionality

- `FewShotClassificationPrompt(task_description="Classify sentiment", labels=["positive", "negative"], examples=[{"input": "Great!", "label": "positive"}], query="Terrible.").format()` → well-formatted classification prompt.
- Adding an example with `label="neutral"` when labels are `["positive", "negative"]` → `ValueError`.
- `ChainOfThoughtPrompt(question="What is 15% of 240?").format()` → prompt with step-by-step instructions.
- `ConstrainedOutputPrompt(instruction="Extract person info", output_schema={"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}, "required": ["name"]}).validate_output('{"name": "Alice", "age": 30}')` → `({"name": "Alice", "age": 30}, None)`.

## Acceptance Criteria

- All three template classes are importable from `langchain.prompts.library`.
- `FewShotClassificationPrompt` formats examples correctly and validates labels.
- `ChainOfThoughtPrompt` produces step-by-step instructions and `parse_response` extracts reasoning/answer.
- `ConstrainedOutputPrompt` embeds JSON schema in the prompt and `validate_output` correctly validates or rejects LLM output.
- Tests cover happy paths, validation errors, edge cases (empty examples, missing markers, malformed JSON).
