# Task: Fix GitLab CI Security Pipeline Templates

## Background

The existing GitLab CI security scanning templates under `lib/gitlab/ci/templates/Security/` have missing or incomplete `extends` and `rules` fields, causing them to fail validation. These templates need to be updated to conform to GitLab CI template standards.

## Files to Modify

- `lib/gitlab/ci/templates/Security/SAST.gitlab-ci.yml` - Fix missing extends/rules
- `lib/gitlab/ci/templates/Security/Dependency-Scanning.gitlab-ci.yml` - Fix missing extends/rules
- `lib/gitlab/ci/templates/Security/Secret-Detection.gitlab-ci.yml` - Fix missing extends/rules

## Requirements

### For each Security template:
- Ensure every job definition includes `extends` referencing the correct base job (if applicable)
- Add proper `rules` section with:
  - CI pipeline trigger conditions
  - Branch/merge request filtering
  - `allow_failure` settings where appropriate
- Ensure `stage` is set correctly (typically `test` or a security-specific stage)
- `artifacts:reports` paths must be correctly configured for SARIF or JSON output
- Template variables (`$SAST_EXCLUDED_PATHS`, `$DS_EXCLUDED_PATHS`, etc.) should have sensible defaults

### Validation
- All YAML files must be syntactically valid Ruby-parseable YAML
- Template structure must follow GitLab CI syntax conventions

## Acceptance Criteria

- `lib/gitlab/ci/templates/Security/*.yml` files are valid YAML
- Each security template contains proper `rules` and `extends` fields
- Templates conform to GitLab CI pipeline syntax
