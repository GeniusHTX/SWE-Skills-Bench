# Task: Create a Multi-Job Scrape Configuration Example for Prometheus

## Background

The Prometheus repository (https://github.com/prometheus/prometheus) is the standard toolkit for metrics monitoring. A complete scrape configuration example is needed that demonstrates multi-target scraping, relabeling rules, and job-specific configuration for a realistic monitoring setup.

## Files to Create/Modify

- `documentation/examples/multi_job_scrape.yml` (create) — Complete multi-job Prometheus scrape configuration example
- `config/testdata/multi_job.good.yml` (create) — Test fixture for configuration validation

## Requirements

### Scrape Configuration

- Define at least three distinct scrape jobs targeting different service types (e.g., a self-monitoring job, an application metrics job, and an infrastructure exporter job)
- Each job should have appropriate `scrape_interval` and `metrics_path` settings

### Relabeling Rules

- Include `relabel_configs` in at least one job to demonstrate label manipulation
- Show at minimum: label extraction from source labels, label replacement, and target filtering via `keep` or `drop` actions

### Service Discovery

- At least one job should use a dynamic service discovery mechanism (e.g., `file_sd_configs`, `dns_sd_configs`, or `kubernetes_sd_configs`)
- At least one job should use `static_configs` for comparison

### Global Settings

- Define global settings including default `scrape_interval`, `evaluation_interval`, and `external_labels`

## Expected Functionality

- The configuration is valid YAML parseable by Prometheus
- Each scrape job targets the correct endpoints and applies its relabeling rules
- Dynamic service discovery configuration allows adding targets without config reloads

## Acceptance Criteria

- The example configuration defines multiple scrape jobs with clearly different target types and scrape settings.
- At least one job uses static targets and at least one job uses a dynamic service-discovery mechanism.
- Relabeling rules demonstrate label extraction, replacement, and target filtering behavior in a realistic way.
- Global configuration includes default scrape settings and meaningful external labels.
- A reader can use the example to understand how multi-job Prometheus scraping and relabeling work together.
