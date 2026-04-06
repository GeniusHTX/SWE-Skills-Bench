# SWE-Skills-Bench

<p align="left">A benchmark dataset for evaluating whether injected skill documents improve agent performance on real-world software engineering tasks.</p>


<p align="left">
  <a href="https://www.python.org/">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB">
  </a>
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Required-2496ED">
  <a href="LICENSE">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-blue">
  </a>
</p>

## What is this dataset?

SWE-Skills-Bench contains **49 real-world software engineering tasks** paired with curated skill documents. Each task tests whether providing an agent with domain-specific knowledge (a "skill") measurably improves its ability to complete the task.

The dataset is designed to answer: *Does giving an agent a skill document actually help?*

---

## Task List

<details>
<summary>All 49 tasks (click to expand)</summary>

| Skill ID | Name |
|----------|------|
| `add-uint-support` | Add UInt Support |
| `fix` | React Code Fix & Linter |
| `tdd-workflow` | TDD Workflow |
| `security-review` | Security Review |
| `springboot-tdd` | Spring Boot TDD |
| `add-admin-api-endpoint` | Ghost Admin API Endpoint Creator |
| `mcp-builder` | MCP Server Builder |
| `python-resilience` | Python Resilience Patterns |
| `xlsx` | Excel & Spreadsheet Automation |
| `turborepo` | Turborepo Monorepo Build System |
| `github-actions-templates` | GitHub Actions Templates |
| `analytics-events` | Metabase Frontend Analytics Events |
| `prometheus-configuration` | Prometheus Configuration |
| `python-anti-patterns` | Python Anti-Pattern Review |
| `implementing-jsc-classes-zig` | Bun Zig-JS Class Generator |
| `add-malli-schemas` | Metabase Malli Schema Architect |
| `clojure-write` | Clojure Development & REPL Workflow |
| `django-patterns` | Django Architecture Patterns |
| `python-background-jobs` | Python Background Jobs |
| `python-configuration` | Python Configuration Management |
| `creating-financial-models` | Financial Modeling Suite |
| `prompt-engineering-patterns` | Prompt Engineering Patterns |
| `risk-metrics-calculation` | Risk Metrics Calculation |
| `vector-index-tuning` | Vector Index Tuning |
| `rag-implementation` | RAG Implementation Framework |
| `spark-optimization` | Spark Optimization |
| `similarity-search-patterns` | Similarity Search Patterns |
| `llm-evaluation` | LLM Evaluation |
| `analyze-ci` | CI Failure Analyzer |
| `python-packaging` | Python Packaging & Distribution |
| `gitops-workflow` | GitOps Workflow for Kubernetes |
| `linkerd-patterns` | Linkerd Service Mesh Patterns |
| `changelog-automation` | Changelog Automation |
| `k8s-manifest-generator` | Kubernetes Manifest Generator |
| `nx-workspace-patterns` | Nx Workspace Patterns |
| `bazel-build-optimization` | Bazel Build Optimization |
| `istio-traffic-management` | Istio Traffic Management |
| `bash-defensive-patterns` | Bash Defensive Patterns |
| `gitlab-ci-patterns` | GitLab CI Patterns |
| `implementing-agent-modes` | PostHog Agent Mode Architect |
| `python-observability` | Python Observability Patterns |
| `distributed-tracing` | Distributed Tracing & Observability |
| `service-mesh-observability` | Service Mesh Observability |
| `slo-implementation` | SLO Implementation Framework |
| `python-performance-optimization` | Python Performance Optimizer |
| `grafana-dashboards` | Grafana Dashboards |
| `dbt-transformation-patterns` | dbt Transformation Patterns |
| `langsmith-fetch` | LangSmith Fetch |
| `v3-performance-optimization` | V3 Performance Optimization |

</details>

---

## How to Use This Dataset

There are two ways to use SWE-Skills-Bench depending on your goal.

---

### Option A: Load via HuggingFace (quick access)

Install the `datasets` library if you haven't already:

```bash
pip install datasets
```

```python
from datasets import load_dataset

ds = load_dataset("GeniusHTX/SWE-Skills-Bench", split="train")
print(ds)
# Dataset({features: ['skill_id', 'name', 'description', 'type',
#                     'task_prompt', 'skill_document', 'test_code',
#                     'repo_url', 'repo_commit', 'docker_image'],
#          num_rows: 49})
```

---

### Option B: Run the Full Evaluation Framework

The built-in evaluation framework automates the full pipeline: Docker container setup, agent execution inside the container, test evaluation, and report generation.

#### Prerequisites

- Python 3.8+
- Docker (running locally)
- Claude Code CLI (`claude` command available inside the container image — no local install required)
- An Anthropic API key

#### Step 1: Install and configure

```bash
# Create and activate a Python environment
conda create -n SWE-Skills-Bench python=3.10 -y
conda activate SWE-Skills-Bench
pip install -r requirements.txt

# Set credentials (copy the example file and fill in your values)
cp .env.example .env
```

Edit `.env` with your API credentials:

```text
# Official Anthropic API key — get one at https://console.anthropic.com/
ANTHROPIC_AUTH_TOKEN=your-anthropic-api-key

# If using a third-party proxy, set the proxy URL here; leave empty for direct API access
ANTHROPIC_BASE_URL=
```

#### Step 2: Configure the model

The framework runs the `claude` CLI inside each Docker container.

To change the model, edit `.env` before running — the framework copies it into the container automatically:

```bash
ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-4-6
```

#### Step 3: Validate the setup

```bash
# Confirm Docker is running
docker info

# Validate benchmark configuration and list available skills
python main.py validate --config config/benchmark_config.yaml
python main.py list-skills --config config/benchmark_config.yaml
```

#### Step 4: Evaluate all 49 skills

```bash
# Run the agent on all tasks
python run_all_skills.py --use-skill      # experiment group
python run_all_skills.py --no-use-skill   # control group

# Evaluate all tasks
python run_all_skills_eval.py --use-skill --use-agent
python run_all_skills_eval.py --no-use-skill --use-agent
```

Useful batch flags: `--dry-run` (preview commands without executing), `--resume` (skip already-completed tasks), `--only a,b` (run specific tasks), `--skip a,b` (exclude specific tasks).

#### Step 5: Generate summary metrics

Once evaluation reports exist in `reports/eval/`, run the post-processing scripts:

```bash
# Unit test pass rate: skill vs. no-skill, per task and average delta
python scripts/compare_pass_rate.py --all

# Which tests failed in each group
python scripts/extract_failed_tests.py

# Token usage and wall-clock duration per task
python scripts/analyze_tokens.py
```

Output is written to:

| Directory | Contents |
|-----------|----------|
| `reports/compare/` | Pass rate comparison table (skill vs. no-skill, delta) |
| `reports/failed_test/` | Per-task failed test lists and overlap analysis |
| `reports/token_and_duration/` | Token counts and duration by task and group |

---

## License

MIT. See `LICENSE` for details.
