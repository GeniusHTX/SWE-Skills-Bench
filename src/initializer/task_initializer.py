"""
Task Initializer - Task initializer
Prepares the benchmark workspace before a run.
"""

from typing import Dict, Any, Optional
from enum import Enum

from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger

logger = get_logger(__name__)


class InitMode(Enum):
    """Initialization mode."""

    DEGRADATION = "degradation"  # Code degradation mode (fix-type tasks)
    FRESH = "fresh"  # Clean checkout mode (development-type tasks)


class TaskInitializer:
    """
    Task initializer.

    Prepares the benchmark workspace.

    Mode 1: Code Degradation
        - For fix-type tasks (e.g. add-uint-support)
        - Backs up target files and removes or disables configured code paths
        - Simulates a "feature missing" state

    Mode 2: Fresh Setup
        - For development-type tasks
        - Switches to the specified commit to ensure a clean environment
    """

    def __init__(
        self,
        docker_manager: DockerManager,
        config: Dict[str, Any],
        skill_config: Dict[str, Any],
    ):
        """
        Initialize.

        Args:
            docker_manager: Docker manager instance
            config: Global configuration
            skill_config: Skill configuration
        """
        self.docker_manager = docker_manager
        self.config = config
        self.skill_config = skill_config
        self.global_config = config.get("global", {})

        # Determine initialization mode
        pre_process = skill_config.get("pre_process")
        if pre_process and pre_process.get("mode") == "degradation":
            self.mode = InitMode.DEGRADATION
        else:
            self.mode = InitMode.FRESH

    async def initialize(self) -> bool:
        """
        Execute initialization.

        Returns:
            bool: Whether initialization succeeded
        """
        logger.info(f"Initializing task with mode: {self.mode.value}")

        try:
            # 1. Check and install skill-specific dependencies
            await self._install_dependencies()

            # 2. Execute initialization based on mode
            if self.mode == InitMode.DEGRADATION:
                from .degradation import DegradationHandler

                handler = DegradationHandler(self.docker_manager, self.config)
                pre_process = self.skill_config.get("pre_process", {})
                await handler.run(pre_process)
            else:
                from .fresh_setup import FreshSetupHandler

                handler = FreshSetupHandler(self.docker_manager, self.config)
                await handler.run(self.skill_config)

            logger.info("Task initialization completed")
            return True

        except Exception as e:
            logger.error(f"Task initialization failed: {e}")
            return False

    async def _install_dependencies(self):
        """Install skill-specific dependencies."""
        env_config = self.skill_config.get("environment", {})
        dependencies = env_config.get("dependencies", [])

        if not dependencies:
            logger.debug("No additional dependencies to install")
            return

        logger.info(f"Installing dependencies: {dependencies}")

        # Build install command
        if any("pip" in dep for dep in dependencies):
            pip_deps = [d for d in dependencies if "pip" not in d]
            if pip_deps:
                install_cmd = f"pip install {' '.join(pip_deps)}"
                result = self.docker_manager.execute_command(install_cmd)
                if result.exit_code != 0:
                    logger.warning(f"Dependency installation warning: {result.stderr}")

    async def backup_original_files(self, target_files: list) -> bool:
        """
        Back up original files (for subsequent similarity comparison).

        Args:
            target_files: List of files to back up

        Returns:
            bool: Whether backup succeeded
        """
        golden_dir = self.global_config.get(
            "golden_reference_dir", "/tmp/golden_reference"
        )
        workspace_dir = self.global_config.get("workspace_dir", "/workspace")

        logger.info(f"Backing up original files to {golden_dir}")

        # Create backup directory
        result = self.docker_manager.execute_command(f"mkdir -p {golden_dir}")
        if result.exit_code != 0:
            logger.error(f"Failed to create backup directory: {result.stderr}")
            return False

        # Back up each target file
        for target_file in target_files:
            src_path = f"{workspace_dir}/{target_file}"
            dst_path = f"{golden_dir}/{target_file}"

            # Create destination directory
            dst_dir = f"{golden_dir}/{'/'.join(target_file.split('/')[:-1])}"
            self.docker_manager.execute_command(f"mkdir -p {dst_dir}")

            # Copy file
            result = self.docker_manager.execute_command(f"cp {src_path} {dst_path}")
            if result.exit_code != 0:
                logger.warning(f"Failed to backup {target_file}: {result.stderr}")
            else:
                logger.debug(f"Backed up: {target_file}")

        logger.info("File backup completed")
        return True

    def get_mode(self) -> InitMode:
        """Get the current initialization mode."""
        return self.mode
