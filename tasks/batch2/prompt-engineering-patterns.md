# Task: Create a Prompt Evaluation Runner for LangChain

## Background

LangChain (https://github.com/langchain-ai/langchain) is a framework for building LLM-powered applications. A new script is needed that automates the evaluation of prompt templates against configurable test cases, measuring output quality with automated scoring metrics.

## Files to Create

- `scripts/run_prompt_eval.py` — Prompt evaluation runner script

## Requirements

### Evaluation Framework

- Accept a prompt template (or set of templates) and a suite of test cases as input
- Each test case specifies input variables and expected output characteristics
- Run each prompt template against all test cases and collect results

### Scoring Metrics

- Implement at least two automated scoring metrics (e.g., string similarity, keyword presence, format compliance, or semantic relevance scoring)
- Each result should capture the prompt used, the input variables, the generated output, and the metric scores

### Configuration

- Support loading test cases from a JSON or YAML configuration file
- Support configurable model parameters (temperature, max tokens) passed as command-line arguments or config
- The script must have a `__main__` entry point for direct execution

### Output

- Print a summary report showing pass/fail rates and average scores per template
- Optionally export detailed results to a structured format (JSON or CSV)

## Expected Functionality

- Running the script with a prompt template and test cases produces a scored evaluation report
- Different templates can be compared by their aggregate scores
- The script runs without errors when provided valid configuration

## Acceptance Criteria

- The runner can evaluate one or more prompt templates against a defined suite of input cases.
- Each run records the prompt variant, the supplied inputs, the generated output, and the resulting metric scores.
- The tool supports at least two automated scoring dimensions and reports them per case and per template.
- Evaluation cases can be loaded from a structured configuration source rather than being hardcoded only in code.
- The summary output makes it easy to compare prompt templates by aggregate quality.
