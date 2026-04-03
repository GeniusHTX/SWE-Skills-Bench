"""
Benchmark Lifecycle - Run workflow control
Manages the lifecycle of the main benchmark run.
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from .docker_manager import DockerManager, ContainerConfig, ExecutionResult
from .logger import get_logger, log_section
from ..utils import (
    generate_container_name,
    generate_report_filename,
    get_model_name,
    get_active_batch,
    get_resolved_tasks_dir,
)

logger = get_logger(__name__)


class LifecycleStage(Enum):
    """Lifecycle stages."""

    INIT = "initialization"
    ENV_SETUP = "environment_setup"
    PRE_PROCESS = "pre_process"
    SANITY_CHECK = "sanity_check"
    INTERACTION = "interaction"
    EVALUATION = "evaluation"
    CLEANUP = "cleanup"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BenchmarkResult:
    """Benchmark run result."""

    skill_id: str
    success: bool
    stage: str
    start_time: str
    end_time: str
    duration_sec: float
    iterations: int
    evaluation_scores: Dict[str, Any]
    logs: List[str]
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class BenchmarkLifecycle:
    """
    Benchmark lifecycle manager.

    Responsibilities:
    1. Load Config: load YAML and determine the skill to run
    2. Environment Setup: start Docker, mount source code, run pre_process
    3. Sanity Check: run environment alignment and build check
    4. Interaction Loop: agent interaction loop
    5. Cleanup: stop or remove the container and finalize run state
    """

    def __init__(
        self,
        config: Dict[str, Any],
        skill_id: str,
        use_skill: bool = True,
        use_agent: bool = True,
        clean_container: bool = False,
    ):
        """
        Initialize the lifecycle manager.

        Args:
            config: Full configuration dictionary
            skill_id: ID of the skill to run
            use_skill: Whether to copy local skills/ into the container
            use_agent: Whether to run the agent interaction stage
            clean_container: Whether to remove the container after completion
        """
        self.config = config
        self.skill_id = skill_id
        self.skill_config = self._find_skill_config(skill_id)

        if not self.skill_config:
            raise ValueError(f"Skill not found: {skill_id}")

        self.docker_manager = DockerManager()
        self.stage = LifecycleStage.INIT
        self.logs: List[str] = []
        self.start_time: Optional[datetime] = None
        self.iterations = 0
        self.evaluation_scores: Dict[str, Any] = {}
        # Controls whether to copy local skills/ to the container (set via CLI --use-skill)
        self.use_skill = bool(use_skill)
        # Controls whether to run the agent interaction stage (set via CLI --use-agent)
        self.use_agent = bool(use_agent)
        # Controls whether to remove the container after completion (set via CLI --clean-container)
        self.clean_container = bool(clean_container)
        # Active batch derived from config (global.active_batch or first in global.batches)
        self.batch = get_active_batch(config)
        # Actual repository path inside the container (e.g. /workspace/upgradle)
        self.repo_dir: Optional[str] = None

        # Deferred imports to avoid circular dependencies
        self._initializer = None
        self._proxy = None
        self._evaluator = None

    def _find_skill_config(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Find the configuration for a given skill ID."""
        skills = self.config.get("skills", [])
        for skill in skills:
            if skill.get("id") == skill_id:
                return skill
        return None

    def _log(self, message: str):
        """Record a log entry."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(message)

    def _transition_to(self, stage: LifecycleStage):
        """Transition to a new lifecycle stage."""
        self._log(f"Stage transition: {self.stage.value} -> {stage.value}")
        self.stage = stage

    async def _validate_task_file(self):
        """
        Validate the task file before starting any environment.

        If the task file is missing the program exits immediately without
        spinning up a Docker container, saving time and resources.
        """
        import sys

        log_section("Task File Validation")
        self._log(f"Validating task file for skill: {self.skill_id}")

        # Get task file path
        tasks_dir = get_resolved_tasks_dir(self.config)
        task_file_path = os.path.join(tasks_dir, f"{self.skill_id}.md")

        try:
            # Check if task file exists
            if not os.path.exists(task_file_path):
                raise FileNotFoundError(f"Task file not found: {task_file_path}")

            # Read task file content
            with open(task_file_path, "r", encoding="utf-8") as f:
                task_content = f.read()

            self._log(f"[OK] Task file validated: {task_file_path}")
            self._log(f"Task content loaded ({len(task_content)} chars)")

            # Save task content for later stages
            self._task_content = task_content

        except FileNotFoundError as e:
            # Task file is missing — exit immediately
            error_banner = f"""
{'='*70}
CRITICAL ERROR: Task file missing! Benchmark cannot proceed.
{'='*70}

{e}

To fix this issue:
1. Create the missing task file: {task_file_path}
2. The task file should contain the specific mission description for the agent

{'='*70}
"""
            print(error_banner, file=sys.stderr)
            logger.critical(str(e))
            self._log(f"CRITICAL: {e}")
            sys.exit(1)

    async def run(self) -> BenchmarkResult:
        """
        Run the complete benchmark workflow.

        Returns:
            BenchmarkResult: Benchmark run result
        """
        self.start_time = datetime.now()
        error = None
        completed_successfully = False

        try:
            # Stage 0: Strict task validation (verify task file before starting any environment)
            await self._validate_task_file()

            # Stage 1: Environment setup
            await self._stage_environment_setup()

            # Stage 2: Pre-processing (code degradation etc.)
            await self._stage_pre_process()

            # Stage 3: Sanity check
            await self._stage_sanity_check()

            # Stage 4: Agent interaction loop
            await self._stage_interaction_loop()

            # Note: evaluation stage has moved to eval.py and is not part of the main flow

            self._transition_to(LifecycleStage.COMPLETED)
            completed_successfully = True  # Record success state before cleanup

        except Exception as e:
            error = str(e)
            logger.error(f"Benchmark failed: {e}")
            self._transition_to(LifecycleStage.FAILED)

        finally:
            # Stage 6: Cleanup (based on clean_container, either fully remove or just stop)
            await self._stage_cleanup()

        # Generate result
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        return BenchmarkResult(
            skill_id=self.skill_id,
            success=completed_successfully,  # Use the pre-saved success state
            stage=self.stage.value,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_sec=duration,
            iterations=self.iterations,
            evaluation_scores=self.evaluation_scores,
            logs=self.logs,
            error=error,
        )

    async def _stage_environment_setup(self):
        """Environment setup stage."""
        log_section("Environment Setup")
        self._transition_to(LifecycleStage.ENV_SETUP)

        env_config = self.skill_config.get("environment", {})
        global_config = self.config.get("global", {})

        # Prepare container configuration
        limits = env_config.get("limits", {})

        # Claude Code config file paths (on host) - will be copied into the container later
        self._claude_config_files = {
            "settings": os.path.join(os.getcwd(), ".claude", "settings.json"),
            "settings_user": os.path.join(os.getcwd(), ".claude", "settings.user.json"),
            "claude_json": os.path.join(os.getcwd(), ".claude", ".claude.json"),
            "claudeignore": os.path.join(os.getcwd(), ".claude", ".claudeignore"),
        }

        volumes = {}

        container_config = ContainerConfig(
            image=env_config.get("base_image", "python:3.10"),
            name=generate_container_name(
                self.skill_id,
                self.use_skill,
                self.use_agent,
                model_name=get_model_name(),
                batch=self.batch,
            ),
            working_dir=global_config.get("workspace_dir", "/workspace"),
            network_mode=global_config.get("network_mode", "none"),
            cpus=float(limits.get("cpus", 4)),
            memory=limits.get("memory", "16g"),
            env_vars=env_config.get("env_vars", {}),
            volumes=volumes,
            timeout_per_command=limits.get("timeout_per_command", 300),
        )

        # Create and start container
        self._log(f"Creating container with image: {container_config.image}")
        if not self.docker_manager.create_container(container_config):
            raise RuntimeError("Failed to create container")

        if not self.docker_manager.start_container():
            raise RuntimeError("Failed to start container")

        self._log("Container started successfully")

        # Copy Claude config files to the container (not mounted, to avoid modifying the host)
        await self._copy_claude_config_to_container()

        # Clone repository
        repo_config = self.skill_config.get("repo", {})
        repo_url = repo_config.get("url")
        commit = repo_config.get("commit", "HEAD")

        if repo_url:
            await self._clone_repository(
                repo_url, commit, repo_config.get("sparse_checkout")
            )

    async def _copy_claude_config_to_container(self):
        """
        Copy Claude config files into the container (instead of mounting).
        This ensures container-side changes do not affect the host.
        Files are owned by the dev user so they can be modified.
        """
        self._log("Copying Claude config files to container...")

        # Create target directory inside the container
        self.docker_manager.execute_command(
            "mkdir -p /home/dev/.claude", timeout=30, user="root"
        )

        # Copy settings.json (template + local override + env var injection)
        try:
            content = self._build_claude_settings_content()
            if content is not None:
                success, msg = self.docker_manager.write_file_direct(
                    "/home/dev/.claude/settings.json", content
                )
                if success:
                    self._log(
                        f"Copied settings.json to container ({len(content)} bytes)"
                    )
                else:
                    self._log(f"Failed to copy settings.json: {msg}")
        except Exception as e:
            self._log(f"Error copying settings.json: {e}")

        # Copy .claude.json (onboarding configuration)
        claude_json_path = self._claude_config_files.get("claude_json")
        if claude_json_path and os.path.exists(claude_json_path):
            try:
                with open(claude_json_path, "rb") as f:
                    content = f.read()
                success, msg = self.docker_manager.write_file_direct(
                    "/home/dev/.claude.json", content
                )
                if success:
                    self._log(
                        f"Copied .claude.json to container ({len(content)} bytes)"
                    )
                else:
                    self._log(f"Failed to copy .claude.json: {msg}")
            except Exception as e:
                self._log(f"Error copying .claude.json: {e}")

        # Copy .claudeignore
        claudeignore_path = self._claude_config_files.get("claudeignore")
        if claudeignore_path and os.path.exists(claudeignore_path):
            try:
                with open(claudeignore_path, "rb") as f:
                    content = f.read()
                success, msg = self.docker_manager.write_file_direct(
                    "/workspace/.claudeignore", content
                )
                if success:
                    self._log(
                        f"Copied .claudeignore to container ({len(content)} bytes)"
                    )
                else:
                    self._log(f"Failed to copy .claudeignore: {msg}")
            except Exception as e:
                self._log(f"Error copying .claudeignore: {e}")

        # Ensure all files are owned by the dev user
        try:
            self._log("Adjusting ownership of Claude files to dev:dev")
            chown_cmds = [
                "chown -R dev:dev /home/dev/.claude || true",
                "chown dev:dev /home/dev/.claude.json || true",
                "chown dev:dev /workspace/.claudeignore || true",
            ]
            for cmd in chown_cmds:
                res = self.docker_manager.execute_command(cmd, timeout=30, user="root")
                self._log(f"Chown '{cmd}' exit_code={res.exit_code}")
        except Exception as e:
            self._log(f"Failed to chown claude files: {e}")

        # Copy local skills directory to ~/.claude/skills in the container (controlled by self.use_skill)
        try:
            if not getattr(self, "use_skill", False):
                self._log(
                    "Skipping copying local skills to container (use_skill flag is False)"
                )
            else:
                local_skills_dir = os.path.join(os.getcwd(), "skills")
                if os.path.exists(local_skills_dir) and os.path.isdir(local_skills_dir):
                    self._log(
                        f"Copying local skills from {local_skills_dir} to /home/dev/.claude/skills"
                    )

                    # assume /home/dev/.claude already exists in the container

                    # Count copied files
                    copied_count = 0
                    failed_count = 0

                    # Recursively copy each file (preserving directory structure)
                    for root, dirs, files in os.walk(local_skills_dir):
                        rel = os.path.relpath(root, local_skills_dir)
                        if rel == ".":
                            dest_dir = "/home/dev/.claude/skills"
                        else:
                            # Convert path separator to POSIX style (cross-platform)
                            rel_posix = rel.replace(os.sep, "/")
                            dest_dir = f"/home/dev/.claude/skills/{rel_posix}"

                        # Create directory (silent)
                        self.docker_manager.execute_command(
                            f"mkdir -p {dest_dir}", user="root"
                        )

                        for fname in files:
                            local_file = os.path.join(root, fname)
                            container_path = f"{dest_dir}/{fname}"
                            try:
                                self.docker_manager.copy_to_container(
                                    local_file, container_path
                                )
                                copied_count += 1
                            except Exception as e:
                                failed_count += 1
                                self._log(
                                    f"Failed to copy skill file {local_file}: {e}"
                                )

                    # Print copy summary
                    self._log(
                        f"Skills copy completed: {copied_count} files copied, {failed_count} failed"
                    )

                    # Set ownership to dev:dev
                    chown_skills = self.docker_manager.execute_command(
                        "chown -R dev:dev /home/dev/.claude/skills || true",
                        timeout=30,
                        user="root",
                    )
                    self._log(f"Chown skills exit_code={chown_skills.exit_code}")
                else:
                    self._log(
                        f"No local skills directory at {local_skills_dir}; skipping skills copy"
                    )
        except Exception as e:
            self._log(f"Error while copying skills to container: {e}")

    def _build_claude_settings_content(self) -> Optional[bytes]:
        """Build the Claude settings content to write into the container."""
        settings_path = self._claude_config_files.get("settings")
        settings_user_path = self._claude_config_files.get("settings_user")

        if not settings_path or not os.path.exists(settings_path):
            return None

        with open(settings_path, "r", encoding="utf-8") as f:
            settings_data = json.load(f)

        if settings_user_path and os.path.exists(settings_user_path):
            with open(settings_user_path, "r", encoding="utf-8") as f:
                user_settings = json.load(f)
            settings_data = self._deep_merge_dicts(settings_data, user_settings)

        env_config = settings_data.get("env", {})
        resolved_env = {}

        for key, value in env_config.items():
            resolved_value = self._resolve_claude_env_value(key, value)
            if resolved_value not in (None, ""):
                resolved_env[key] = resolved_value

        settings_data["env"] = resolved_env

        return json.dumps(settings_data, indent=2, ensure_ascii=False).encode("utf-8")

    def _resolve_claude_env_value(self, key: str, value: Any) -> Any:
        """Prefer host environment variables; fall back to resolving ${VAR} placeholders."""
        if key in os.environ and os.environ[key]:
            return os.environ[key]

        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_key = value[2:-1].strip()
            return os.environ.get(env_key, "")

        return value

    def _deep_merge_dicts(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge dictionaries; override file values take precedence."""
        merged = dict(base)
        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge_dicts(merged[key], value)
            else:
                merged[key] = value
        return merged

    async def _clone_repository(
        self, repo_url: str, commit: str, sparse_checkout: Optional[List[str]] = None
    ):
        """Clone a repository into the container."""
        self._log(f"Cloning repository: {repo_url}")

        # Check and install Git
        self._log("Checking/installing Git")
        exit_code, _ = self.docker_manager.container.exec_run("which git")
        self._log(f"which git exit code: {exit_code}")
        if exit_code != 0:
            self._log("Installing Git (may take 1-2 minutes)")
            # Update package list (quiet mode)
            self.docker_manager.container.exec_run("apt-get update -qq", user="root")
            # Install git (ignore return code; apt may produce warnings)
            self.docker_manager.container.exec_run(
                "apt-get install -y -qq git 2>/dev/null || apt-get install -y git",
                user="root",
            )
            # Wait for installation to complete
            import time

            time.sleep(2)

        # Final verification
        exit_code, output = self.docker_manager.container.exec_run("git --version")
        self._log(f"git --version exit code: {exit_code}")
        if exit_code == 0:
            git_version = output.decode().strip() if output else "unknown"
            self._log(f"Git is available: {git_version}")
        else:
            # Try again with --fix-missing to handle network issues
            self._log("Retrying Git installation with --fix-missing")
            self.docker_manager.container.exec_run("apt-get update", user="root")
            self.docker_manager.container.exec_run(
                "apt-get install -y --fix-missing git", user="root"
            )
            exit_code, output = self.docker_manager.container.exec_run("git --version")
            self._log(f"git --version (retry) exit code: {exit_code}")
            if exit_code == 0:
                git_version = output.decode().strip() if output else "unknown"
                self._log(f"Git is available: {git_version}")
            else:
                error_msg = output.decode() if output else "Unknown error"
                self._log(f"Git installation failed: {error_msg[:200]}")
                raise RuntimeError(f"Failed to install git: {error_msg}")

        # Extract repo name from URL
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        base_workspace = self.config.get("global", {}).get(
            "workspace_dir", "/workspace"
        )
        workspace_dir = f"{base_workspace}/{repo_name}"

        # Save actual repo path for use in later stages
        self.repo_dir = workspace_dir
        self._log(f"Repository will be cloned to: {workspace_dir}")

        # Initialize git repository
        init_commands = [
            f"git init {workspace_dir}",
            f"cd {workspace_dir} && git remote add origin {repo_url}",
        ]

        # Sparse checkout configuration
        if sparse_checkout:
            init_commands.extend(
                [
                    f"cd {workspace_dir} && git config core.sparseCheckout true",
                ]
            )
            # Write sparse checkout configuration
            sparse_paths = "\\n".join(sparse_checkout)
            init_commands.append(
                f"echo -e '{sparse_paths}' > {workspace_dir}/.git/info/sparse-checkout"
            )

        for cmd in init_commands:
            bash_cmd = f"bash -c '{cmd}'"
            result = self.docker_manager.execute_command(bash_cmd)
            if result.exit_code != 0:
                self._log(f"Command failed: {cmd}")
                self._log(f"Error: {result.stderr or result.stdout}")
                raise RuntimeError(
                    f"Failed to initialize repository: {result.stderr or result.stdout}"
                )

        # Pull code (use HEAD if commit is None)
        # Use --filter=blob:none for a blobless clone: fetch commits+tree only, blobs on demand
        # More suitable for large repos than --depth 1; avoids timeouts from pack computation
        ref = commit if commit else "HEAD"
        fetch_cmd = (
            f"cd {workspace_dir} && git fetch --depth 1 --filter=blob:none origin {ref}"
        )
        checkout_cmd = f"cd {workspace_dir} && git checkout FETCH_HEAD"

        # git fetch special handling for large repos: retries + extended timeout
        git_fetch_timeout = 1200  # 20 minutes, for large repositories
        max_retries = 3
        last_error = ""
        for attempt in range(1, max_retries + 1):
            self._log(
                f"git fetch attempt {attempt}/{max_retries} (timeout={git_fetch_timeout}s)"
            )
            result = self.docker_manager.execute_command(
                f"bash -c '{fetch_cmd}'",
                timeout=git_fetch_timeout,
            )
            if result.exit_code == 0:
                break
            last_error = result.stderr or result.stdout
            self._log(f"git fetch attempt {attempt} failed: {last_error[:300]}")
            if result.timed_out:
                self._log("Fetch timed out, retrying...")
            if attempt < max_retries:
                import time as _time

                _time.sleep(5 * attempt)  # Exponential backoff: 5s, 10s
        else:
            raise RuntimeError(
                f"git fetch failed after {max_retries} attempts: {last_error}"
            )

        # checkout
        result = self.docker_manager.execute_command(f"bash -c '{checkout_cmd}'")
        if result.exit_code != 0:
            self._log(f"git checkout failed: {result.stderr or result.stdout}")
            raise RuntimeError(
                f"Failed to checkout repository: {result.stderr or result.stdout}"
            )

        # Remove any residual .claude directories in the workspace repo
        cleanup_cmd = f"find {workspace_dir} -type d -name '.claude' -prune -exec rm -rf {{}} + || true"
        cleanup_bash = f"bash -c '{cleanup_cmd}'"
        cleanup_res = self.docker_manager.execute_command(cleanup_bash)
        stdout = getattr(cleanup_res, "stdout", None) or getattr(
            cleanup_res, "output", None
        )
        self._log(
            f"Removed repo .claude directories under {workspace_dir}: exit_code={cleanup_res.exit_code} stdout={stdout}"
        )

        self._log("Repository cloned successfully")

    async def _stage_pre_process(self):
        """Pre-processing stage (code degradation etc.)"""
        log_section("Pre-Process")
        self._transition_to(LifecycleStage.PRE_PROCESS)

        pre_process = self.skill_config.get("pre_process")

        if not pre_process:
            self._log("No pre-processing required")
            return

        mode = pre_process.get("mode", "degradation")

        if mode == "degradation":
            await self._run_degradation(pre_process)
        else:
            self._log(f"Pre-process mode: {mode} (no action needed)")

    async def _run_degradation(self, pre_process_config: Dict[str, Any]):
        """Run code degradation."""
        from ..initializer import DegradationHandler

        self._log("Running code degradation...")

        handler = DegradationHandler(self.docker_manager, self.config)
        await handler.run(pre_process_config)

        self._log("Code degradation completed")

    async def _stage_sanity_check(self):
        """Sanity check stage."""
        log_section("Sanity Check")
        self._transition_to(LifecycleStage.SANITY_CHECK)

        # Check whether code passes the base build (to rule out environment issues)
        evaluation = self.skill_config.get("evaluation", [])

        for eval_item in evaluation:
            if (
                eval_item.get("level") == "L1"
                and eval_item.get("method") == "build_check"
            ):
                # After degradation the build may fail — this is expected.
                # We only check that the environment is functional.
                self._log("Checking build environment...")
                params = eval_item.get("params", {})
                build_cmd = params.get("build_command", "python --version")
                # Use the actual repository directory
                repo_dir = self.repo_dir or "/workspace"

                result = self.docker_manager.execute_command(
                    f"cd {repo_dir} && {build_cmd}"
                )
                self._log(f"Build check result: exit_code={result.exit_code}")

                # Do not raise here because the degraded code may not compile
                break

        self._log("Sanity check completed")

    async def _stage_interaction_loop(self):
        """
        Agent interaction loop stage (Claude Code CLI mode).

        Workflow:
        1. Write task file into the container
        2. Invoke the claude CLI to operate autonomously inside the container
        3. Wait for completion
        """
        log_section("Interaction Loop (Claude Code CLI)")
        self._transition_to(LifecycleStage.INTERACTION)

        # Decide whether to skip the interaction stage based on config
        if not getattr(self, "use_agent", True):
            self._log("Skipping Interaction Loop because use_agent is False")
            self.iterations = 0
            return

        from ..proxy import ClaudeCodeProxy

        # Initialize Claude Code proxy with the corrected working directory
        proxy_config = self.config.copy()
        proxy_config["skill_id"] = self.skill_id
        proxy_config["use_skill"] = self.use_skill
        proxy_config["use_agent"] = self.use_agent
        proxy_config["batch"] = self.batch
        proxy_config.setdefault("metadata", {})["skill_id"] = self.skill_id
        if self.repo_dir:
            # Use the actual repository directory rather than /workspace
            if "global" not in proxy_config:
                proxy_config["global"] = {}
            proxy_config["global"]["workspace_dir"] = self.repo_dir
            self._log(f"Using repo directory for Claude Code: {self.repo_dir}")

        claude_proxy = ClaudeCodeProxy(
            docker_manager=self.docker_manager, config=proxy_config
        )

        self._log("Starting Claude Code interaction...")

        # Execute task
        result = await claude_proxy.execute_task(self._task_content)

        self.iterations = 1  # Claude Code CLI executes in a single pass

        if result.success:
            self._log(
                f"Claude Code completed successfully in {result.duration_sec:.2f}s"
            )
            self._log(f"Output length: {len(result.output)} chars")
        else:
            self._log(f"Claude Code failed with exit code: {result.exit_code}")
            if result.stderr:
                self._log(f"Stderr: {result.stderr[:500]}")
            # Raise exception when Claude fails to prevent marking as success
            raise RuntimeError(
                f"Claude Code execution failed with exit code {result.exit_code}"
            )

        # Output result summary
        self._log(
            f"Claude Code result: success={result.success}, duration={result.duration_sec:.2f}s"
        )

    async def _stage_cleanup(self):
        """Cleanup stage."""
        log_section("Cleanup")
        self._transition_to(LifecycleStage.CLEANUP)

        try:
            if self.clean_container:
                # Full cleanup: stop and remove container
                self.docker_manager.cleanup()
                self._log("Cleanup completed (container removed)")
            else:
                # Stop container only, preserve it for a later eval.py run
                container_name = generate_container_name(
                    self.skill_id, self.use_skill, self.use_agent
                )
                self.docker_manager.stop_container()
                self._log(f"Container stopped but preserved: {container_name}")
                self._log("Run eval.py with matching parameters to evaluate")
        except Exception as e:
            self._log(f"Cleanup error (non-fatal): {e}")

    def save_report(self, result: BenchmarkResult, output_dir: str = None):
        """
        Save the benchmark run report.

        Args:
            result: Benchmark run result
            output_dir: Output directory
        """
        if output_dir is None:
            output_dir = self.config.get("global", {}).get("reports_dir", "./reports")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Encode use_skill/use_agent state in the report filename (default true if not present)
        use_skill_flag = getattr(self, "use_skill", True)
        use_agent_flag = getattr(self, "use_agent", True)

        report_filename = generate_report_filename(
            prefix="report",
            skill=self.skill_id,
            use_agent=use_agent_flag,
            use_skill=use_skill_flag,
            timestamp=timestamp,
            ext=".json",
        )
        report_file = output_path / report_filename

        with open(report_file, "w", encoding="utf-8") as f:
            f.write(result.to_json())

        logger.info(f"Report saved to: {report_file}")
        return report_file
