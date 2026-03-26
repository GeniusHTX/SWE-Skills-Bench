"""
Remove Docker containers for the specified skill.

Container names are derived from ANTHROPIC_DEFAULT_SONNET_MODEL (env) and
the active batch set in config global.active_batch.

Usage:
    python scripts/clean_container.py -s <skill-id>
    python scripts/clean_container.py -s <skill-id> --no-use-skill
    python scripts/clean_container.py -s <skill-id> --no-use-agent
    python scripts/clean_container.py -s <skill-id> -c path/to/config.yaml
    python scripts/clean_container.py --all                     # clean containers for ALL batches
    python scripts/clean_container.py --all -c path/to/config.yaml
"""

import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.orchestrator import DockerManager
from src.utils import (
    generate_container_name,
    load_yaml_config,
    get_model_name,
    get_active_batch,
)

load_dotenv()


@click.command()
@click.option(
    "--skill",
    "-s",
    default=None,
    help="Skill ID to clean (used to derive container name)",
)
@click.option(
    "--use-skill/--no-use-skill",
    default=True,
    help="Match the runtime flag to derive the container name (default: --use-skill)",
)
@click.option(
    "--use-agent/--no-use-agent",
    default=True,
    help="Match the runtime flag to derive the container name (default: --use-agent)",
)
@click.option(
    "--all",
    "clean_all",
    is_flag=True,
    default=False,
    help="Clean all containers for every skill defined in the config file",
)
@click.option(
    "--config", "-c", default="config/benchmark_config.yaml", help="Config file path"
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Log level",
)
def clean(
    skill: str,
    use_skill: bool,
    use_agent: bool,
    clean_all: bool,
    config: str,
    log_level: str,
):
    """Remove Docker containers for the specified skill (terminal output only)"""

    # Simple terminal output function with timestamp
    def log(msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"[{ts}] {level}: {msg}")

    # Always load config for model name and batch info
    try:
        config_data = load_yaml_config(config)
    except Exception as e:
        log(f"Failed to load config file: {e}", level="ERROR")
        sys.exit(1)

    _model_name = get_model_name()
    all_batches = [str(b) for b in config_data.get("global", {}).get("batches", [])]
    active_batch = get_active_batch(config_data)

    targets: list[str] = []

    if clean_all:
        batches_to_clean = all_batches if all_batches else [active_batch]
        skills = config_data.get("skills", [])
        for batch_name in batches_to_clean:
            for s in skills:
                sid = s.get("id")
                if sid:
                    # Generate all four combinations (use-skill/use-agent)
                    for usk in (True, False):
                        for uag in (True, False):
                            targets.append(
                                generate_container_name(
                                    sid,
                                    usk,
                                    uag,
                                    model_name=_model_name,
                                    batch=batch_name,
                                )
                            )
    elif skill:
        targets.append(
            generate_container_name(
                skill, use_skill, use_agent, model_name=_model_name, batch=active_batch
            )
        )
    else:
        log("Please specify --skill or --all", level="ERROR")
        sys.exit(1)

    # Deduplicate
    targets = list(dict.fromkeys(targets))

    log(f"Preparing to clean {len(targets)} container(s)")

    removed = 0
    skipped = 0

    for name in targets:
        docker_manager = DockerManager()
        if docker_manager.attach_to_container(name):
            log(f"Found container: {name}, removing...")
            try:
                docker_manager.cleanup()
                click.echo(f"✓ Removed: {name}")
                removed += 1
            except Exception as e:
                log(f"Failed to remove [{name}]: {e}", level="ERROR")
                skipped += 1
        else:
            log(f"Container not found, skipping: {name}", level="DEBUG")
            skipped += 1

    click.echo(f"\nDone: {removed} removed, {skipped} skipped")
    sys.exit(0 if skipped == 0 or removed > 0 else 1)


if __name__ == "__main__":
    clean()
