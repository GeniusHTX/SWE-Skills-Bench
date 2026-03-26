# Task: Create an LLM Evaluation Demo Script for HELM

## Background

HELM (https://github.com/stanford-crfm/helm) is a holistic evaluation framework for language models. A new example script is needed that demonstrates how to set up and run a basic LLM evaluation suite with configurable metrics, test scenarios, and result reporting.

## Files to Create

- `examples/llm_eval_demo.py` — LLM evaluation demonstration script

## Requirements

### Evaluation Framework

- Define a set of evaluation scenarios (e.g., question answering, summarization, classification) with input prompts and expected outputs
- Support multiple evaluation metrics: exact match, F1 score, string similarity, and format compliance
- Run each scenario through a model interface (real or mock) and score the results

### Configuration

- Accept evaluation configuration specifying which scenarios to run, metric weights, and model parameters
- Support loading scenarios from a structured data source (JSON, YAML, or inline definitions)

### Result Reporting

- Produce a summary report with per-scenario scores and an aggregate score
- Display pass/fail status for each scenario based on configurable thresholds
- The script must have a `__main__` entry point for standalone execution

## Expected Functionality

- Running the script executes all configured evaluation scenarios and produces scored results
- The summary report clearly shows which scenarios passed and which failed
- Different model configurations produce different scores

## Acceptance Criteria

- The evaluation script can define and run multiple scenario types such as question answering, summarization, or classification.
- Each scenario is scored with the configured metrics and contributes to an aggregate evaluation summary.
- Scenario-level pass/fail outcomes are visible and tied to explicit thresholds.
- The configuration can control which scenarios run, which metrics apply, and how the final score is weighted.
- The output clearly communicates both per-scenario results and overall evaluation performance.
