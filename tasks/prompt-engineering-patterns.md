# Task: Implement Prompt Engineering Templates with Automated Evaluation

## Background
   Create a reproducible prompt engineering template system with automated
   evaluation capabilities in the LangChain repository.

## Files to Create/Modify
   - examples/prompt_templates/ (new directory)
   - scripts/run_prompt_eval.py
   - tests/test_prompt_eval.py

## Requirements
   
   Prompt Templates (multiple use cases):
   - Instruction-type prompts
   - Conversational prompts
   - Extraction prompts
   - Translation prompts
   - Code generation prompts
   - Evaluation prompts
   
   JSON Schema (input/output):
   - input_id: unique identifier
   - prompt: the prompt text
   - expected_output: expected response
   - metadata: additional context
   
   Evaluation Script:
   - Pluggable scorers (string assertion, similarity, custom)
   - Generate JSON/CSV report
   - Support batch evaluation

4. Output Requirements:
   - JSON schema compliant output
   - Evaluation report generated
   - All required fields present and typed correctly

## Acceptance Criteria
   - `python scripts/run_prompt_eval.py` exits with code 0
   - Output follows JSON schema
   - Report file generated (JSON or CSV)
