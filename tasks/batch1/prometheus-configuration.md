# Task: Create Multi-Job Scrape Configuration Example for Prometheus

## Background
   Add a comprehensive scrape configuration example demonstrating multi-job
   setup with relabeling rules, and add unit tests to verify configuration parsing.

## Files to Create/Modify
   - documentation/examples/multi-job-prometheus.yml - Configuration example
   - config/config_test.go - Add parsing unit tests

## Requirements
   
   Configuration Example (multi-job-prometheus.yml):
   
   Multiple Scrape Jobs:
   1) prometheus (self-monitoring)
   2) node-exporter (static_configs)
   3) kubernetes-pods (with relabel_configs)
   
   Required Sections:
   ```yaml
   scrape_configs:
     - job_name: 'prometheus'
       static_configs:
         - targets: ['localhost:9090']
     
     - job_name: 'node-exporter'
       static_configs:
         - targets: ['node1:9100', 'node2:9100']
       relabel_configs:
         - source_labels: [__address__]
           target_label: instance
           regex: '([^:]+):\d+'
           replacement: '${1}'
     
     - job_name: 'kubernetes-pods'
       metric_relabel_configs:
         - source_labels: [__name__]
           regex: 'go_.*'
           action: drop
   ```
   
   Relabeling Features to Demonstrate:
   - source_labels and target_label
   - regex matching and replacement
   - metric_relabel_configs for metric filtering
   - action: keep/drop/replace

4. Test Cases (in config_test.go):
   - Configuration parses without errors
   - Job count matches expected (3 jobs)
   - Relabeling rules applied in correct sequence
   - Target labels transformed correctly
   - metric_relabel_configs filtering works

## Acceptance Criteria
   - `go test ./config/...` passes all tests including new ones (exit 0)
   - Configuration example is valid YAML
   - Relabeling transformation results match expected values
