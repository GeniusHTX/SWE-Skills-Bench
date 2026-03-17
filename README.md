# SWE-Skills-Bench

<p align="center">The official repo for our paper, "SWE-Skills-Bench: Do Agent Skills Actually Help in Real-World Software Engineering".</p>

<p align="center">
  <strong><a href="README_CN.md">中文</a></strong>
</p>

<p align="center">
  <a href="https://www.python.org/">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.8%2B-3776AB">
  </a>
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Required-2496ED">
  <img alt="CLI" src="https://img.shields.io/badge/CLI-Click-5C4EE5">
  <a href="LICENSE">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-blue">
  </a>
</p>

## Overview

This repository is built for controlled skill ablation experiments. It keeps the task, repository, tests, and container environment as stable as possible, and only changes whether a skill is injected and whether the agent is enabled.

The workflow has two separate stages:

1. `main.py run`: create the container, prepare the repository, and run Claude interaction.
2. `eval.py`: attach to the existing container and run evaluation.

The output of `eval.py` is raw experiment data, not the final paper-level metric. Paper results such as pass rate comparison, failure analysis, token cost, and duration should be computed later with scripts under `scripts/`.

## Layout

```text
config/benchmark_config.yaml   Global config and skill definitions
skills/<skill-id>/SKILL.md     Skill content
tasks/<skill-id>.md            Task prompt
tests/test_<skill-id>.py       Evaluation tests
main.py                        Run entrypoint
eval.py                        Evaluation entrypoint
run_all_skills.py              Batch run
run_all_skills_eval.py         Batch evaluation
scripts/                       Metric post-processing scripts
reports/                       Run and eval reports
claude_process/                Claude output and thinking logs
```

## Prerequisites

- Python 3.8+
- Docker running locally
- The container image must provide the `claude` command
- Claude or Anthropic credentials configured

Note: Docker images used by this repository are published on Docker Hub under the `zhangyiiiiii` namespace (for example: `zhangyiiiiii/swe-skills-bench-python[:tag]`). The `config/benchmark_config.yaml` refers to these images; omitting a tag will pull `:latest` if available, but for reproducible experiments prefer an explicit tag.

Install dependencies:

```bash
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

On Windows, you can also copy `.env.example` to `.env` manually. At minimum, set:

```text
ANTHROPIC_AUTH_TOKEN=your-anthropic-api-key
ANTHROPIC_BASE_URL=
```

## Claude Model Configuration

You can configure the Claude Code model used inside the container through `.claude/settings.json` in the workspace. During `main.py run`, the framework reads that file and copies it into the container as `/home/dev/.claude/settings.json`.

In practice, the recommended way to switch models is to update `.claude/settings.json` and rerun the experiment.

## Quick Start

```bash
python main.py validate --config config/benchmark_config.yaml
python main.py list-skills --config config/benchmark_config.yaml
python main.py run -s add-uint-support -c config/benchmark_config.yaml
python eval.py -s add-uint-support --use-skill --use-agent
```

Run reports are written to `reports/interactive` by default, and evaluation reports are written to `reports/eval`.

## Common Experiment Modes

| Flags | Meaning |
| --- | --- |
| `--use-skill --use-agent` | Inject the skill and run the agent |
| `--no-use-skill --use-agent` | Disable the skill and compare the base agent |
| `--use-skill --no-use-agent` | Inject the skill but skip agent interaction |
| `--no-use-skill --no-use-agent` | Pure control condition |

Use the same flag combination for both `run` and `eval` when comparing results.

## Post-processing and Paper Metrics

Recommended flow:

1. Run `main.py run`
2. Run `eval.py`
3. Run post-processing scripts

Common scripts:

- `python scripts/compare_pass_rate.py -s <skill_id>`: compare L2 test pass rate
- `python scripts/extract_failed_tests.py`: extract and compare failed tests
- `python scripts/analyze_tokens.py`: summarize token usage and duration

Typical output directories:

- `reports/compare`
- `reports/failed_test`
- `reports/token_and_duration`

## Batch Execution

```bash
python run_all_skills.py
python run_all_skills_eval.py
```

Common optional flags include `--dry-run`, `--resume`, `--only`, `--skip`, `--no-use-skill`, and `--no-use-agent`.

## Adding a Skill

The minimum runnable unit usually includes:

1. `skills/<skill-id>/SKILL.md`
2. `tasks/<skill-id>.md`
3. `tests/test_<skill-id>.py`
4. A matching entry in `config/benchmark_config.yaml`

Recommended validation sequence:

```bash
python main.py validate --config config/benchmark_config.yaml
python main.py run -s <skill-id>
python eval.py -s <skill-id> --use-skill --use-agent
```

## FAQ

### `claude` command not found

Make sure the target image already has Claude Code CLI installed and that `claude` is available in the container PATH.

### `eval.py` cannot find the container

This usually means `skill_id`, `use-skill`, or `use-agent` does not match the run stage, or the container was cleaned up after the run.

### Docker disk usage keeps growing

Containers are preserved by default for later evaluation and debugging. Use the cleanup script when needed:

```bash
python scripts/clean_container.py --all
```

## License

MIT. See `LICENSE` for details.
