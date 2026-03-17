"""
Agent Skills Benchmark - Evaluation entry for inject/no-inject skill experiments
Standalone evaluation entry: runs L1/L2/L3 evaluation on containers with/without skill injection and generates reports
"""

import asyncio
import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

import click
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.orchestrator import DockerManager, setup_logger, get_logger, log_section
from src.evaluator import ModularEvaluator
from src.utils import (
    load_yaml_config,
    save_json_report,
    get_timestamp,
    generate_report_filename,
    generate_container_name,
)

# Load environment variables
load_dotenv()


@click.command()
@click.option("--skill", "-s", required=True, help="Skill ID to evaluate")
@click.option(
    "--config", "-c", default="config/benchmark_config.yaml", help="Config file path"
)
@click.option("--output", "-o", default="reports/eval", help="Report output directory")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    help="Log level",
)
@click.option(
    "--use-skill/--no-use-skill",
    default=True,
    help="Match --use-skill flag used in the main.py run",
)
@click.option(
    "--use-agent/--no-use-agent",
    default=True,
    help="Match --use-agent flag used in the main.py run",
)
@click.option(
    "--clean-container/--no-clean-container",
    default=False,
    help="Clean up container after evaluation",
)
def evaluate(
    skill: str,
    config: str,
    output: str,
    log_level: str,
    use_skill: bool,
    use_agent: bool,
    clean_container: bool,
):
    """Run L1/L2/L3 evaluation on an existing container with or without skill injection, and generate a report."""

    # Generate timestamp and filename identifier
    timestamp = get_timestamp()
    safe_skill = re.sub(r"[^A-Za-z0-9._-]+", "-", skill)
    if not safe_skill:
        safe_skill = "skill"

    usk_flag = "true" if use_skill else "false"
    uag_flag = "true" if use_agent else "false"

    # Initialize logger
    setup_logger(
        level=log_level,
        log_dir=output,
        log_file=f"eval_{safe_skill}_use-skill-{usk_flag}_use-agent-{uag_flag}_{timestamp}.log",
    )
    logger = get_logger(__name__)

    logger.info(f"Starting evaluation for skill: {skill}")

    # Load configuration
    try:
        config_data = load_yaml_config(config)
        logger.info(f"Loaded configuration from: {config}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Verify skill exists
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

    # Build container name
    container_name = generate_container_name(skill, use_skill, use_agent)
    logger.info(f"Looking for container: {container_name}")

    # Run evaluation
    try:
        result = asyncio.run(
            _run_evaluation(
                config_data=config_data,
                skill_config=skill_config,
                skill_id=skill,
                container_name=container_name,
                clean_container=clean_container,
                logger=logger,
            )
        )

        # Save report
        report_filename = generate_report_filename(
            prefix="eval_report",
            skill=skill,
            use_agent=use_agent,
            use_skill=use_skill,
            timestamp=timestamp,
            ext=".json",
        )
        report_path = os.path.join(output, report_filename)
        save_json_report(result, report_path)

        logger.info(f"Evaluation report saved to: {report_path}")

        # Output summary
        click.echo("\n" + "=" * 60)
        click.echo("EVALUATION RESULT SUMMARY")
        click.echo("=" * 60)
        click.echo(f"Skill: {skill}")
        click.echo(f"Container: {container_name}")
        click.echo(f"Success: {'✓' if result.get('success') else '✗'}")

        if result.get("evaluation_scores"):
            click.echo(f"\nEvaluation Scores:")
            overall = result["evaluation_scores"].get("overall_score", 0)
            click.echo(f"  Overall Score: {overall:.2%}")

            for detail in result["evaluation_scores"].get("details", []):
                status_icon = "✓" if detail["status"] == "passed" else "✗"
                click.echo(
                    f"  {status_icon} {detail['level']} {detail['method']}: {detail['score']:.2%}"
                )

        click.echo("=" * 60)

        sys.exit(0 if result.get("success") else 1)

    except Exception as e:
        logger.error(f"Evaluation failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


async def _run_evaluation(
    config_data: dict,
    skill_config: dict,
    skill_id: str,
    container_name: str,
    clean_container: bool,
    logger,
) -> dict:
    """Run evaluation asynchronously."""

    docker_manager = DockerManager()
    logs = []
    start_time = datetime.now()

    def _log(message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        logs.append(log_entry)
        logger.info(message)

    try:
        # Check and connect to container
        log_section("Container Connection")
        _log(f"Connecting to container: {container_name}")

        if not docker_manager.attach_to_container(container_name):
            raise RuntimeError(f"Container not found: {container_name}")

        # Check container status
        status = docker_manager.get_container_status()
        _log(f"Container status: {status}")

        # Restart the container if it has stopped
        if status != "running":
            _log("Container is not running, restarting...")
            if not docker_manager.restart_container():
                raise RuntimeError("Failed to restart container")
            _log("Container restarted successfully")

        # Get repository directory
        repo_config = skill_config.get("repo", {})
        repo_url = repo_config.get("url", "")
        global_config = config_data.get("global", {})
        workspace_dir = global_config.get("workspace_dir", "/workspace")
        tests_dir = global_config.get("tests_dir", "tests")

        # Extract repository name from URL
        if repo_url:
            repo_name = repo_url.rstrip("/").split("/")[-1]
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            repo_dir = f"{workspace_dir}/{repo_name}"
        else:
            repo_dir = workspace_dir

        _log(f"Using repo directory: {repo_dir}")

        # Copy local test files
        await _copy_local_test_files(
            docker_manager=docker_manager,
            skill_config=skill_config,
            tests_dir=tests_dir,
            log_func=_log,
        )

        # Ensure pytest is installed
        await _ensure_pytest_installed(
            docker_manager=docker_manager,
            log_func=_log,
        )

        # Execute evaluation
        log_section("Evaluation")
        _log("Starting evaluation...")

        # Dynamically inject working_dir into all evaluation configs
        evaluation_configs = skill_config.get("evaluation", [])
        if not evaluation_configs:
            evaluation_configs = skill_config.get("environment", {}).get(
                "evaluation", []
            )

        for eval_config in evaluation_configs:
            params = eval_config.get("params", {})
            if "working_dir" not in params:
                params["working_dir"] = repo_dir
                eval_config["params"] = params

        _log(f"Evaluating with working_dir: {repo_dir}")

        evaluator = ModularEvaluator(
            docker_manager=docker_manager,
            skill_config=skill_config,
            global_config=global_config,
        )

        evaluation_scores = await evaluator.evaluate_all()

        _log(f"Evaluation completed: {json.dumps(evaluation_scores, indent=2)}")

        success = True
        error = None

    except Exception as e:
        success = False
        error = str(e)
        evaluation_scores = {}
        logger.error(f"Evaluation failed: {e}")

    finally:
        # Cleanup phase
        log_section("Cleanup")
        try:
            if clean_container:
                docker_manager.cleanup()
                _log("Cleanup completed (container removed)")
            else:
                docker_manager.stop_container()
                _log(f"Container stopped but preserved: {container_name}")
        except Exception as e:
            _log(f"Cleanup error (non-fatal): {e}")

    # Generate result
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    return {
        "skill_id": skill_id,
        "container_name": container_name,
        "success": success,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_sec": duration,
        "evaluation_scores": evaluation_scores,
        "logs": logs,
        "error": error,
    }


async def _copy_local_test_files(
    docker_manager: DockerManager, skill_config: dict, tests_dir: str, log_func
):
    """Copy local test files to an isolated directory in the container."""
    repo_root = Path(__file__).parent.resolve()
    normalized_tests_dir = Path(tests_dir.replace("/", os.sep))

    def resolve_local_test_path(test_file_path: str) -> str:
        workspace_tests_prefix = "/workspace/tests/"
        workspace_prefix = "/workspace/"

        if test_file_path.startswith(workspace_tests_prefix):
            relative_test_path = test_file_path[len(workspace_tests_prefix) :].replace(
                "/", os.sep
            )
            return str(repo_root / normalized_tests_dir / relative_test_path)

        if test_file_path.startswith(workspace_prefix):
            relative_path = test_file_path[len(workspace_prefix) :].replace("/", os.sep)
            return str(repo_root / relative_path)

        return str(repo_root / test_file_path.replace("/", os.sep))

    evaluation_configs = skill_config.get("evaluation", [])
    if not evaluation_configs:
        evaluation_configs = skill_config.get("environment", {}).get("evaluation", [])

    log_func(
        f"_copy_local_test_files: Found {len(evaluation_configs)} evaluation configs"
    )
    log_func(f"Using local tests directory: {normalized_tests_dir}")

    for eval_config in evaluation_configs:
        if eval_config.get("method") == "unit_test":
            params = eval_config.get("params", {})
            test_command = params.get("test_command", "")

            # Extract test file path from test_command (supports hyphens and underscores)
            match = re.search(r"([\w/]+/tests/[\w_-]+\.py)", test_command)
            log_func(
                f"Regex match for test file in '{test_command}': {match.group(1) if match else 'None'}"
            )

            if match:
                test_file_path = match.group(1)
                # Convert to local path
                local_test_path = resolve_local_test_path(test_file_path)

                log_func(
                    f"Checking local test file: {local_test_path} (exists: {os.path.exists(local_test_path)})"
                )

                if os.path.exists(local_test_path):
                    # Copy to the container's isolated directory (avoids import conflicts)
                    container_test_dir = "/tmp/benchmark_tests"
                    test_file_name = os.path.basename(local_test_path)
                    container_path = f"{container_test_dir}/{test_file_name}"

                    log_func(
                        f"Copying test file to container: {local_test_path} -> {container_path}"
                    )

                    # Create directory
                    mkdir_result = docker_manager.execute_command(
                        f"mkdir -p {container_test_dir}"
                    )
                    log_func(f"mkdir result: exit_code={mkdir_result.exit_code}")

                    # Copy file
                    docker_manager.copy_to_container(local_test_path, container_path)

                    # Verify copy result
                    verify_result = docker_manager.execute_command(
                        f"ls -la {container_path}"
                    )
                    log_func(
                        f"Verify copy: {verify_result.stdout or verify_result.stderr}"
                    )

                    log_func(f"Test file copied successfully: {test_file_name}")

                    # Copy dependency utils (shared modules required by other test files)
                    dep_utils_local = str(
                        repo_root / normalized_tests_dir / "_dependency_utils.py"
                    )
                    if os.path.exists(dep_utils_local):
                        dep_utils_container = (
                            f"{container_test_dir}/_dependency_utils.py"
                        )
                        docker_manager.copy_to_container(
                            dep_utils_local, dep_utils_container
                        )
                        log_func(
                            f"Dependency utils copied: {dep_utils_local} -> {dep_utils_container}"
                        )
                    else:
                        log_func(
                            f"INFO: Dependency utils not found at {dep_utils_local}, skipping"
                        )

                    # Update test_command in params
                    updated_command = test_command.replace(
                        test_file_path, container_path
                    )
                    params["test_command"] = updated_command
                    log_func(f"Updated test command: {updated_command}")
                else:
                    log_func(f"WARNING: Test file not found at {local_test_path}")
            else:
                log_func(
                    f"WARNING: Could not extract test file path from command: {test_command}"
                )


async def _ensure_pytest_installed(docker_manager: DockerManager, log_func):
    """Ensure pytest is installed."""
    log_func("Checking/installing pytest...")

    # Check if pytest is already installed
    check_result = docker_manager.execute_command("python -m pytest --version")

    if check_result.exit_code == 0:
        version = check_result.stdout.strip() if check_result.stdout else "unknown"
        log_func(f"pytest already installed: {version}")
        return

    # Install pytest
    log_func("Installing pytest (this may take 30-60 seconds)...")
    install_result = docker_manager.execute_command(
        "python -m pip install pytest -q --break-system-packages", timeout=120
    )

    if install_result.exit_code != 0:
        error_msg = install_result.stderr or install_result.stdout or "Unknown error"
        log_func(f"pytest installation failed: {error_msg[:500]}")
        raise RuntimeError(f"Failed to install pytest: {error_msg[:500]}")

    # Verify installation
    verify_result = docker_manager.execute_command("python -m pytest --version")
    if verify_result.exit_code == 0:
        version = verify_result.stdout.strip() if verify_result.stdout else "unknown"
        log_func(f"pytest installed successfully: {version}")
    else:
        raise RuntimeError("pytest installation verification failed")


if __name__ == "__main__":
    evaluate()
