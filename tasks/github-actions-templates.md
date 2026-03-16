# Task: Create Python CI Workflow Template for GitHub Actions

## Background
   Add a new CI workflow template for Python projects in the starter-workflows
   repository, covering multi-version testing with dependency caching.

## Files to Create/Modify
   - ci/python-pytest.yml - Workflow template
   - ci/properties/python-pytest.properties.json - Template metadata

## Requirements
   
   Workflow Template (python-pytest.yml):
   
   Triggers:
   - push to main/master
   - pull_request to main/master
   
   Matrix Strategy:
   - Python versions: 3.9, 3.10, 3.11, 3.12
   - OS: ubuntu-latest
   
   Steps:
   1. Checkout code
   2. Set up Python with version matrix
   3. Cache pip dependencies
   4. Install dependencies from requirements.txt
   5. Run pytest with coverage
   
   Caching:
   - Use actions/cache or setup-python's built-in cache
   - Cache key based on requirements.txt hash
   
   Properties File (python-pytest.properties.json):
   ```json
   {
     "name": "Python pytest",
     "description": "Run Python tests with pytest across multiple Python versions",
     "iconName": "python",
     "categories": ["Python", "CI"]
   }
   ```

4. Validation Requirements:
   - Workflow passes actionlint syntax check
   - Properties JSON is valid and contains required fields
   - Proper YAML formatting and indentation

## Acceptance Criteria
   - `actionlint ci/python-pytest.yml` exits with code 0 (no errors)
   - ci/properties/python-pytest.properties.json exists with required fields
   - Workflow syntax is valid GitHub Actions format
