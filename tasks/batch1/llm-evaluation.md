# Task: Add LLM Evaluation Example and Test Cases for HELM

## Background
   Add a small LLM evaluation use case with configuration, sample inputs,
   and execution script to the HELM repository.

## Files to Create/Modify
   - examples/llm_eval_demo.py (new)
   - examples/eval_config.yaml (configuration)
   - benchmarks/simple_eval/ (optional directory)

## Requirements
   
   Evaluation Configuration:
   - Small, locally runnable evaluation
   - Clear dependency documentation
   - Sample input data included
   
   Evaluation Script:
   - Load configuration
   - Run evaluation on sample inputs
   - Generate structured output
   
   Output Format:
   - score: numeric evaluation score
   - labels: classification labels if applicable
   - metrics: detailed metric breakdown

4. Dependencies:
   - All dependencies documented
   - Can run locally without external APIs
   - Mock model if needed for testing

## Acceptance Criteria
   - `python examples/llm_eval_demo.py` exits with code 0
   - Output contains score and labels fields
   - Evaluation report generated (JSON/CSV)
