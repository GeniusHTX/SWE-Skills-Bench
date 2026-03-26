"""
Agent Skills Benchmark - CLI for running benchmark tasks
Run injection vs. non-injection skill experiments, start containers, and save benchmark reports
"""

import asyncio
import sys
import os
from pathlib import Path

import click
import re
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import BenchmarkLifecycle, setup_logger, get_logger
from src.utils import (
    load_yaml_config,
    save_json_report,
    get_timestamp,
    generate_report_filename,
    get_model_name,
)

# Load environment variables
load_dotenv()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Agent Skills Benchmark - CLI for running and inspecting benchmark tasks"""
    pass


@cli.command()
@click.option("--skill", "-s", required=True, help="Skill ID to benchmark")
@click.option(
    "--config", "-c", default="config/benchmark_config.yaml", help="Config file path"
)
@click.option("--output", "-o", default=None, help="Report output directory")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Log level",
)
@click.option(
    "--dry-run", is_flag=True, help="Validate configuration only, do not execute"
)
@click.option(
    "--use-skill/--no-use-skill",
    default=True,
    help="Copy local skills/ directory into the container (default: enabled)",
)
@click.option(
    "--use-agent/--no-use-agent",
    default=True,
    help="Use agent for the interaction stage (default: enabled)",
)
@click.option(
    "--clean-container/--no-clean-container",
    default=False,
    help="Remove container after execution (default: keep for evaluation)",
)
def run(
    skill: str,
    config: str,
    output: str,
    log_level: str,
    dry_run: bool,
    use_skill: bool,
    use_agent: bool,
    clean_container: bool,
):
    """Run a benchmark task"""

    # Determine output directory (model-aware when not explicitly specified)
    if output is None:
        output = os.path.join("reports", get_model_name(), "interactive")

    # Generate safe skill filename and timestamp for log file naming
    timestamp = get_timestamp()
    safe_skill = re.sub(r"[^A-Za-z0-9._-]+", "-", skill)
    if not safe_skill:
        safe_skill = "skill"

    # Encode use_skill/use_agent flags into the filename
    usk_flag = "true" if use_skill else "false"
    uag_flag = "true" if use_agent else "false"

    # Initialize logger (log file name includes skill + timestamp)
    setup_logger(
        level=log_level,
        log_dir=output,
        log_file=f"benchmark_{safe_skill}_use-skill-{usk_flag}_use-agent-{uag_flag}_{timestamp}.log",
    )
    logger = get_logger(__name__)

    logger.info(f"Starting benchmark for skill: {skill}")

    # Load configuration
    try:
        config_data = load_yaml_config(config)
        logger.info(f"Loaded configuration from: {config}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Validate skill exists
    skills = config_data.get("skills", [])
    skill_config = None
    for s in skills:
        if s.get("id") == skill:
            skill_config = s
            break

    if not skill_config:
        available_skills = [s.get("id") for s in skills]
        logger.error(f"Skill '{skill}' not found. Available: {available_skills}")
        sys.exit(1)

    logger.info(f"Skill configuration loaded: {skill_config.get('name', skill)}")

    if dry_run:
        logger.info("Dry run mode - configuration validated successfully")
        click.echo(f"✓ Configuration valid for skill: {skill}")
        click.echo(f"  Type: {skill_config.get('type')}")
        click.echo(f"  Repo: {skill_config.get('repo', {}).get('url')}")
        return

    # Run benchmark
    try:
        result = asyncio.run(
            _run_benchmark(config_data, skill, use_skill, use_agent, clean_container)
        )

        # Save report (using timestamp generated above)
        report_filename = generate_report_filename(
            prefix="report",
            skill=skill,
            use_agent=use_agent,
            use_skill=use_skill,
            timestamp=timestamp,
            ext=".json",
        )
        report_path = os.path.join(output, report_filename)
        save_json_report(result.to_dict(), report_path)

        logger.info(f"Report saved to: {report_path}")

        # Output summary
        click.echo("\n" + "=" * 60)
        click.echo("BENCHMARK RESULT SUMMARY")
        click.echo("=" * 60)
        click.echo(f"Skill: {skill}")
        click.echo(f"Status: {result.stage}")
        click.echo(f"Success: {'✓' if result.success else '✗'}")
        click.echo(f"Duration: {result.duration_sec:.1f}s")
        click.echo(f"Iterations: {result.iterations}")

        if result.evaluation_scores:
            click.echo(f"\nEvaluation Scores:")
            overall = result.evaluation_scores.get("overall_score", 0)
            click.echo(f"  Overall Score: {overall:.2%}")

            for detail in result.evaluation_scores.get("details", []):
                status_icon = "✓" if detail["status"] == "passed" else "✗"
                click.echo(
                    f"  {status_icon} {detail['level']} {detail['method']}: {detail['score']:.2%}"
                )

        click.echo("=" * 60)

        # Return appropriate exit code
        sys.exit(0 if result.success else 1)

    except Exception as e:
        logger.error(f"Benchmark failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def _run_benchmark(
    config: dict,
    skill_id: str,
    use_skill: bool = True,
    use_agent: bool = True,
    clean_container: bool = False,
):
    """Run benchmark asynchronously"""
    lifecycle = BenchmarkLifecycle(
        config,
        skill_id,
        use_skill=use_skill,
        use_agent=use_agent,
        clean_container=clean_container,
    )
    return await lifecycle.run()


@cli.command()
@click.option(
    "--config", "-c", default="config/benchmark_config.yaml", help="Config file path"
)
def list_skills(config: str):
    """List all available skills"""

    try:
        config_data = load_yaml_config(config)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    skills = config_data.get("skills", [])

    if not skills:
        click.echo("No skills defined in configuration")
        return

    click.echo("\nAvailable Skills:")
    click.echo("-" * 60)

    for skill in skills:
        skill_id = skill.get("id", "unknown")
        name = skill.get("name", skill_id)
        skill_type = skill.get("type", "unknown")
        repo = skill.get("repo", {}).get("url", "N/A")

        click.echo(f"\n  ID: {skill_id}")
        click.echo(f"  Name: {name}")
        click.echo(f"  Type: {skill_type}")
        click.echo(f"  Repo: {repo}")

    click.echo("\n" + "-" * 60)
    click.echo(f"Total: {len(skills)} skill(s)")


@cli.command()
@click.option(
    "--config", "-c", default="config/benchmark_config.yaml", help="Config file path"
)
def validate(config: str):
    """Validate configuration file"""

    click.echo(f"Validating configuration: {config}")

    try:
        config_data = load_yaml_config(config)
        click.echo("✓ YAML syntax valid")
    except Exception as e:
        click.echo(f"✗ YAML syntax error: {e}", err=True)
        sys.exit(1)

    # Validate required fields
    errors = []
    warnings = []

    # Check global configuration
    if "global" not in config_data:
        warnings.append("Missing 'global' section")

    # Check skills
    skills = config_data.get("skills", [])
    if not skills:
        errors.append("No skills defined")

    for i, skill in enumerate(skills):
        prefix = f"skills[{i}]"

        if "id" not in skill:
            errors.append(f"{prefix}: Missing 'id'")

        if "type" not in skill:
            warnings.append(f"{prefix}: Missing 'type'")

        if "repo" not in skill or "url" not in skill.get("repo", {}):
            errors.append(f"{prefix}: Missing 'repo.url'")

        if "evaluation" not in skill:
            warnings.append(f"{prefix}: No evaluation defined")

    # Output results
    if warnings:
        click.echo("\nWarnings:")
        for w in warnings:
            click.echo(f"  ⚠ {w}")

    if errors:
        click.echo("\nErrors:")
        for e in errors:
            click.echo(f"  ✗ {e}")
        sys.exit(1)

    click.echo("\n✓ Configuration is valid")


@cli.command()
@click.argument("report_path")
def show_report(report_path: str):
    """Display a benchmark report."""

    import json

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        click.echo(f"Error loading report: {e}", err=True)
        sys.exit(1)

    click.echo("\n" + "=" * 60)
    click.echo("BENCHMARK REPORT")
    click.echo("=" * 60)

    click.echo(f"\nSkill: {report.get('skill_id')}")
    click.echo(f"Success: {report.get('success')}")
    click.echo(f"Stage: {report.get('stage')}")
    click.echo(f"Start: {report.get('start_time')}")
    click.echo(f"End: {report.get('end_time')}")
    click.echo(f"Duration: {report.get('duration_sec', 0):.1f}s")
    click.echo(f"Iterations: {report.get('iterations')}")

    if report.get("error"):
        click.echo(f"\nError: {report.get('error')}")

    scores = report.get("evaluation_scores", {})
    if scores:
        click.echo(f"\n{'='*60}")
        click.echo("EVALUATION SCORES")
        click.echo(f"{'='*60}")
        click.echo(f"Overall Status: {scores.get('overall_status')}")
        click.echo(f"Overall Score: {scores.get('overall_score', 0):.2%}")
        click.echo(
            f"Passed: {scores.get('passed', 0)}/{scores.get('total_evaluations', 0)}"
        )

        click.echo("\nDetails:")
        for detail in scores.get("details", []):
            status_icon = "✓" if detail["status"] == "passed" else "✗"
            click.echo(f"  {status_icon} [{detail['level']}] {detail['method']}")
            click.echo(f"      Score: {detail['score']:.2%}")
            click.echo(f"      Message: {detail['message']}")

    click.echo("\n" + "=" * 60)


if __name__ == "__main__":
    cli()
