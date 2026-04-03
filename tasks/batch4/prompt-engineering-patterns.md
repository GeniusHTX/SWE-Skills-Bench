# Task: Implement a Prompt Template Library with Few-Shot Selection for LangChain

## Background

The LangChain repository (https://github.com/langchain-ai/langchain) provides building blocks for LLM-powered applications. A new prompt engineering module is needed that provides structured prompt templates with variable interpolation, dynamic few-shot example selection based on semantic similarity, chain-of-thought formatting, and self-consistency verification — enabling users to build reliable, production-quality prompts with measurable performance.

## Files to Create/Modify

- `libs/langchain/langchain/prompts/structured_template.py` (create) — `StructuredPromptTemplate` class with system/instruction/example/output sections and variable interpolation
- `libs/langchain/langchain/prompts/few_shot_selector.py` (create) — `FewShotSelector` class for dynamic example selection using similarity scoring
- `libs/langchain/langchain/prompts/chain_of_thought.py` (create) — `ChainOfThoughtTemplate` class adding step-by-step reasoning scaffolding
- `libs/langchain/tests/unit_tests/prompts/test_structured_template.py` (create) — Tests for the structured template
- `libs/langchain/tests/unit_tests/prompts/test_few_shot_selector.py` (create) — Tests for few-shot selection

## Requirements

### StructuredPromptTemplate

- Constructor accepts: `system` (str, optional), `instruction` (str with `{variable}` placeholders), `output_format` (str, optional), `examples` (list of dicts, optional)
- `render(**kwargs)` method interpolates variables into the instruction, assembles the prompt in order: system → examples → instruction → output_format, and returns the complete prompt string
- Missing required variables (those in the instruction template) must raise `ValueError` listing all missing variable names
- Extra variables not present in the template must be silently ignored
- Variables containing `{` or `}` characters must be escaped to prevent injection into the template format
- `validate()` method checks that all placeholder variables have matching descriptions in an optional `variable_descriptions` dict

### FewShotSelector

- Constructor accepts: `examples` (list of dicts with `"input"` and `"output"` keys), `max_examples` (int, default 3), `selection_strategy` (one of `"random"`, `"similarity"`, `"diverse"`)
- `select(query: str) -> list[dict]` returns up to `max_examples` examples selected by the chosen strategy
- `"similarity"` strategy: compute cosine similarity between the query and each example's `"input"` using TF-IDF vectors; return the top-k most similar
- `"diverse"` strategy: select the most similar example first, then iteratively select the example most dissimilar to all already-selected examples (maximal marginal relevance)
- `"random"` strategy: return `max_examples` random examples (with deterministic seed support)
- When fewer examples exist than `max_examples`, return all available examples without error

### ChainOfThoughtTemplate

- Extends `StructuredPromptTemplate` by inserting a reasoning section between instruction and output
- `reasoning_steps` (list of strings) defines labeled steps the model should follow (e.g., `["Identify the key entities", "Determine relationships", "Form conclusion"]`)
- `render(**kwargs)` produces a prompt that includes numbered steps and a "Therefore, the answer is:" conclusion prefix
- `add_verification_step` (bool, default False): when True, appends a step asking the model to verify its reasoning before giving the final answer

### Integration

- `StructuredPromptTemplate` must accept a `FewShotSelector` via a `few_shot_selector` parameter; when present, `render(query=...)` automatically selects and formats examples
- Examples must be formatted as "Input: {input}\nOutput: {output}" blocks within the prompt

### Expected Functionality

- A template with instruction `"Translate {text} to {language}"` rendered with `text="Hello"` and `language="French"` produces a prompt containing `"Translate Hello to French"`
- Rendering with missing `language` raises `ValueError: Missing required variables: language`
- A `FewShotSelector` with strategy `"similarity"` and 10 examples returns the 3 most relevant when `max_examples=3`
- A `ChainOfThoughtTemplate` with 3 reasoning steps produces a prompt with numbered steps 1-3 followed by "Therefore, the answer is:"
- Adding verification step appends "Step 4: Verify the reasoning above is consistent and correct."
- A template with a `FewShotSelector` and `query="Convert USD to EUR"` automatically includes selected examples formatted as Input/Output pairs

## Acceptance Criteria

- `StructuredPromptTemplate.render()` correctly interpolates variables and assembles system/examples/instruction/output sections in order
- Missing variables raise `ValueError`; extra variables are ignored; injection-prone characters are escaped
- `FewShotSelector` correctly implements all three selection strategies with deterministic results (given fixed seed for random)
- `ChainOfThoughtTemplate` inserts numbered reasoning steps and optional verification step into the rendered prompt
- Integration between template and selector automatically selects and formats examples when `query` is provided
- All tests pass and cover: normal rendering, missing variables, each selection strategy, chain-of-thought formatting, and verification step
