# Task: Fix Security CI Templates in the GitLab Repository

## Background

The GitLab repository (https://github.com/gitlabhq/gitlabhq) ships CI/CD pipeline templates under `lib/gitlab/ci/templates/Security/`. The SAST, DAST, and Dependency-Scanning templates have incomplete or missing job configuration fields that need to be fixed to ensure they function correctly when included in user pipelines.

## Files to Modify

- `lib/gitlab/ci/templates/Security/SAST.gitlab-ci.yml` — SAST scanner job template
- `lib/gitlab/ci/templates/Security/DAST.gitlab-ci.yml` — DAST scanner job template
- `lib/gitlab/ci/templates/Security/Dependency-Scanning.gitlab-ci.yml` — Dependency scanning job template

## Requirements

### Template Structure

- Each security template must be valid YAML
- Each template must define at least one CI job with complete configuration
- Jobs must include execution control fields (rules, only/when, or allow_failure) to define when they run
- Jobs must include script, include, or extends sections to define what they do

### SAST Template

- Must reference a scanner image and configure artifact report output
- Must define variables for configurable parameters

### DAST Template

- Must define jobs with an explicit stage assignment
- Must include variables for runtime configuration

### Dependency Scanning Template

- Must configure artifacts collection for scan results
- Must define variables for scanner options

### Ruby Syntax

- All YAML files must pass Ruby YAML syntax validation

## Expected Functionality

- Each template can be included in a parent `.gitlab-ci.yml` via `include`
- Jobs defined in the templates execute at the correct stage with proper rules
- Security scan results are collected as pipeline artifacts

## Acceptance Criteria

- The SAST, DAST, and dependency-scanning templates each define complete jobs with execution rules, stages, and runnable behavior.
- Each template can be included from a parent pipeline without requiring undocumented manual fixes.
- Security scanning jobs declare the expected variables, artifacts, and scanner-specific configuration.
- Generated pipeline behavior clearly separates the three security scanning concerns rather than conflating them in one generic job.
- Invalid or incomplete template fields that would break normal GitLab CI usage are eliminated.
