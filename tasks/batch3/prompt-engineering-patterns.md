# Task: Build a Prompt Template Library with Testing Framework for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for building applications powered by language models. The project needs a structured prompt template library that supports few-shot prompting, chain-of-thought formatting, and systematic prompt testing with deterministic evaluation. This should integrate with LangChain's existing prompt template system in the `libs/core` package.

## Files to Create/Modify

- `libs/core/langchain_core/prompts/template_library.py` (create) — Reusable prompt template library with categorized templates, few-shot formatting, and chain-of-thought patterns
- `libs/core/langchain_core/prompts/prompt_tester.py` (create) — Testing framework for evaluating prompt templates against expected outputs
- `libs/core/tests/unit_tests/prompts/test_template_library.py` (create) — Tests for the template library
- `libs/core/tests/unit_tests/prompts/test_prompt_tester.py` (create) — Tests for the prompt testing framework

## Requirements

### Template Library

- Implement a `TemplateLibrary` class that stores and retrieves prompt templates by category and name
- Each template is registered with: `name` (unique string), `category` (e.g., `"classification"`, `"extraction"`, `"summarization"`, `"reasoning"`), `template` (a `PromptTemplate` or `ChatPromptTemplate`), `metadata` (dict with optional tags, version, description)
- Support listing templates by category: `library.get_by_category("classification")` returns all classification templates
- Support versioned templates: `library.register(name, category, template, version="1.0")` and `library.get(name, version="1.0")`; if version is omitted, return the latest version
- Raise `DuplicateTemplateError` if the same name+version combination is registered twice

### Few-Shot Template Builder

- Implement a `FewShotBuilder` class that assembles few-shot prompts from:
  - A system instruction (string)
  - A list of examples, each with `input` and `expected_output` fields
  - An input placeholder for the actual query
- Support configurable example formatting: each example is rendered as `"Input: {input}\nOutput: {expected_output}"`; the format string is customizable
- Support dynamic example selection: accept a `selector` function `(query, examples) -> selected_examples` that picks the most relevant examples (e.g., by keyword overlap)
- Limit the number of examples included to a configurable `max_examples` (default: 5)

### Chain-of-Thought Formatter

- Implement a `ChainOfThoughtFormatter` that wraps any prompt template with chain-of-thought instructions
- Given a base prompt, produce a new prompt that appends: `"\n\nLet's think step by step:\n1. "` (customizable prefix)
- Support structured CoT output parsing: the formatter should include instructions for the model to output its final answer in a tagged block: `<answer>...</answer>`
- Provide a `parse_answer(text)` method that extracts content from the `<answer>` tag; raises `ParseError` if the tag is not found

### Prompt Testing Framework

- Implement a `PromptTester` class that evaluates prompt templates without calling an LLM
- Test cases are defined as: `{"input_variables": {"var1": "value1"}, "expected_rendered": "expected full text"}`
- `tester.run(template, test_cases)` renders each test case and compares the output to `expected_rendered`
- Return a `TestReport` with: number of passed/failed cases, detailed diffs for failed cases, and overall pass rate
- Support regex matching mode: `expected_rendered` can be a regex pattern if the test case has `"match_mode": "regex"`

### Expected Functionality

- Registering 3 classification templates and calling `library.get_by_category("classification")` returns all 3
- Registering `"summarizer"` v1.0 and v2.0, then calling `library.get("summarizer")` returns v2.0
- Registering `"summarizer"` v1.0 twice raises `DuplicateTemplateError`
- `FewShotBuilder` with 10 examples and `max_examples=3` includes only 3 examples in the rendered prompt
- `ChainOfThoughtFormatter.parse_answer("Reasoning...\n<answer>42</answer>")` returns `"42"`
- `ChainOfThoughtFormatter.parse_answer("No answer tag here")` raises `ParseError`
- `PromptTester` with 5 test cases where 4 match returns `TestReport(passed=4, failed=1, pass_rate=0.8)`

## Acceptance Criteria

- `TemplateLibrary` registers, retrieves, and lists templates by category and version correctly
- Latest version is returned when no version is specified in `get()`
- `DuplicateTemplateError` is raised for duplicate name+version registrations
- `FewShotBuilder` renders examples in the correct format and respects `max_examples` limit
- Dynamic example selection via the `selector` function works correctly
- `ChainOfThoughtFormatter` appends CoT instructions and parses `<answer>` tags
- `ParseError` is raised when the answer tag is missing
- `PromptTester` correctly compares rendered output in both exact and regex modes
- `TestReport` accurately reflects pass/fail counts and diffs
- All tests pass and cover normal usage, edge cases, and error conditions
