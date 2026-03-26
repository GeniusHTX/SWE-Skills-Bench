# Task: Create CI Failure Analysis Script for Sentry

## Background
   Add a CI failure analysis script that parses pytest output logs,
   extracts failure information, and generates structured diagnostic reports.

## Files to Create/Modify
   - `scripts/analyze_ci_failures.py` (新建)
   - `sample_pytest_output.log` (新建，测试用的 pytest 输出样本)

## Requirements
   
   Script Functionality:
   - Parse pytest format test output logs
   - Extract failed test names
   - Identify error types (AssertionError, Exception, etc.)
   - Generate stack trace summaries
   
   Output JSON Structure:
   ```json
   {
     "failed_tests": ["test_name_1", "test_name_2"],
     "error_type": "AssertionError",
     "stack_summary": "Brief stack trace excerpt"
   }
   ```

   Sample Log File (sample_pytest_output.log):
   - 创建一个合法的 pytest 输出样本文件，包含至少 1 个失败的测试用例
   - 包含 pytest 典型输出格式：FAILED 标记、traceback、AssertionError 等

   CLI Interface:
   - `--input`: Path to pytest output log
   - `--output`: Path for JSON report

## Acceptance Criteria
   - `python scripts/analyze_ci_failures.py --input sample_pytest_output.log --output report.json` succeeds
   - Output JSON contains failed_tests, error_type, stack_summary fields
   - Script exits with code 0
