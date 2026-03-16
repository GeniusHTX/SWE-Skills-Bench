"""
Fresh Setup Handler - Clean checkout handler
For development tasks: switches to the specified commit to ensure a clean environment.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SetupResult:
    """Setup result."""

    success: bool
    commit_hash: str
    branch: Optional[str] = None
    error: Optional[str] = None


class FreshSetupHandler:
    """
    Clean checkout handler.

    Responsibilities:
    - Switch to the specified commit
    - Ensure a clean workspace
    - Install project dependencies
    """

    def __init__(self, docker_manager: DockerManager, config: Dict[str, Any]):
        """
        Initialize.

        Args:
            docker_manager: Docker manager instance
            config: Global configuration
        """
        self.docker_manager = docker_manager
        self.config = config
        self.global_config = config.get("global", {})

    async def run(self, skill_config: Dict[str, Any]) -> SetupResult:
        """
        Run the fresh setup.

        Args:
            skill_config: Skill configuration

        Returns:
            SetupResult: Setup result
        """
        logger.info("Starting fresh setup")

        repo_config = skill_config.get("repo", {})
        commit = repo_config.get("commit", "HEAD")
        workspace_dir = self.global_config.get("workspace_dir", "/workspace")

        try:
            # 1. Ensure the workspace is clean
            await self._clean_workspace(workspace_dir)

            # 2. Check out the specified commit
            commit_hash = await self._checkout_commit(workspace_dir, commit)

            # 3. Install project dependencies from explicit setup commands or auto-detection
            await self._install_project_dependencies(workspace_dir, skill_config)

            logger.info(f"Fresh setup completed at commit: {commit_hash}")

            return SetupResult(success=True, commit_hash=commit_hash)

        except Exception as e:
            logger.error(f"Fresh setup failed: {e}")
            return SetupResult(success=False, commit_hash="", error=str(e))

    async def _clean_workspace(self, workspace_dir: str):
        """Clean the workspace."""
        logger.debug("Cleaning workspace")

        # Reset all changes
        result = self.docker_manager.execute_command(
            f"cd {workspace_dir} && git reset --hard HEAD"
        )

        if result.exit_code != 0:
            logger.warning(f"Git reset warning: {result.stderr}")

        # Clean untracked files
        result = self.docker_manager.execute_command(
            f"cd {workspace_dir} && git clean -fd"
        )

        if result.exit_code != 0:
            logger.warning(f"Git clean warning: {result.stderr}")

    async def _checkout_commit(self, workspace_dir: str, commit: str) -> str:
        """
        Check out a specific commit.

        Args:
            workspace_dir: Working directory
            commit: Commit hash or tag

        Returns:
            str: Actual commit hash
        """
        logger.debug(f"Checking out commit: {commit}")

        # If it is a tag or branch name, fetch it first
        result = self.docker_manager.execute_command(
            f"cd {workspace_dir} && git fetch origin {commit} --depth 1"
        )

        # Check out
        result = self.docker_manager.execute_command(
            f"cd {workspace_dir} && git checkout {commit}"
        )

        if result.exit_code != 0:
            raise RuntimeError(f"Failed to checkout {commit}: {result.stderr}")

        # Get the actual commit hash
        result = self.docker_manager.execute_command(
            f"cd {workspace_dir} && git rev-parse HEAD"
        )

        commit_hash = result.stdout.strip()
        logger.info(f"Checked out to: {commit_hash[:8]}")

        return commit_hash

    async def _install_project_dependencies(
        self, workspace_dir: str, skill_config: Dict[str, Any]
    ):
        """Install project dependencies."""
        logger.debug("Installing project dependencies")

        env_config = skill_config.get("environment", {})
        setup_commands = env_config.get("setup_commands", [])

        if not setup_commands:
            # Auto-detect common dependency installation methods
            setup_commands = await self._detect_setup_commands(workspace_dir)

        for cmd in setup_commands:
            logger.debug(f"Running setup command: {cmd}")
            result = self.docker_manager.execute_command(f"cd {workspace_dir} && {cmd}")

            if result.exit_code != 0:
                logger.warning(f"Setup command warning: {cmd}")
                logger.warning(f"Output: {result.stderr or result.stdout}")

    async def _detect_setup_commands(self, workspace_dir: str) -> list:
        """
        Auto-detect project dependency installation commands.

        Detection priority: lock files > package manager files

        Args:
            workspace_dir: Working directory

        Returns:
            list: Detected installation commands
        """
        commands = []

        # ========================================
        # Node.js / JavaScript ecosystem
        # ========================================
        # Check pnpm-lock.yaml (highest priority)
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/pnpm-lock.yaml && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("pnpm install --frozen-lockfile")
            return commands

        # Check yarn.lock
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/yarn.lock && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("yarn install --frozen-lockfile")
            return commands

        # Check bun.lockb
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/bun.lockb && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("bun install")
            return commands

        # Check package.json (use npm when no lock file present)
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/package.json && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("npm install")

        # ========================================
        # Python ecosystem
        # ========================================
        # Check pyproject.toml (Poetry project)
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/pyproject.toml && grep -q '\\[tool.poetry\\]' {workspace_dir}/pyproject.toml && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("pip install poetry && poetry install")
        else:
            # Check requirements.txt
            result = self.docker_manager.execute_command(
                f"test -f {workspace_dir}/requirements.txt && echo 'exists'"
            )
            if "exists" in result.stdout:
                commands.append("pip install -r requirements.txt")

            # Check setup.py
            result = self.docker_manager.execute_command(
                f"test -f {workspace_dir}/setup.py && echo 'exists'"
            )
            if "exists" in result.stdout:
                commands.append("pip install -e .")

        # ========================================
        # Go ecosystem
        # ========================================
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/go.mod && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("go mod download")

        # ========================================
        # Java / JVM ecosystem
        # ========================================
        # Check pom.xml (Maven)
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/pom.xml && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("mvn dependency:resolve -q -DskipTests")

        # Check build.gradle or build.gradle.kts (Gradle)
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/build.gradle && echo 'exists'"
        )
        if "exists" in result.stdout:
            if await self._check_gradlew_exists(workspace_dir):
                commands.append("./gradlew dependencies --quiet")
            else:
                commands.append("gradle dependencies --quiet")

        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/build.gradle.kts && echo 'exists'"
        )
        if "exists" in result.stdout:
            if await self._check_gradlew_exists(workspace_dir):
                commands.append("./gradlew dependencies --quiet")
            else:
                commands.append("gradle dependencies --quiet")

        # ========================================
        # Ruby ecosystem
        # ========================================
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/Gemfile && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("bundle install --jobs 4")

        # ========================================
        # Clojure ecosystem
        # ========================================
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/deps.edn && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("clojure -P")

        # ========================================
        # .NET ecosystem
        # ========================================
        result = self.docker_manager.execute_command(
            f"find {workspace_dir} -maxdepth 2 -name '*.csproj' -type f | head -1 | grep -q . && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("dotnet restore")

        # ========================================
        # Rust ecosystem
        # ========================================
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/Cargo.toml && echo 'exists'"
        )
        if "exists" in result.stdout:
            commands.append("cargo fetch")

        return commands

    async def _check_gradlew_exists(self, workspace_dir: str) -> bool:
        """Check whether gradlew exists."""
        result = self.docker_manager.execute_command(
            f"test -f {workspace_dir}/gradlew && echo 'exists'"
        )
        return "exists" in result.stdout
