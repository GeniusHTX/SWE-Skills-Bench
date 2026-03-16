"""
Docker Manager - Docker lifecycle management
Handles container creation, startup, command execution, and teardown.
"""

import docker
import tarfile
import io
import os
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class ContainerConfig:
    """Container configuration."""

    image: str
    name: str
    working_dir: str = "/workspace"
    network_mode: str = "none"
    cpus: float = 4.0
    memory: str = "16g"
    env_vars: Dict[str, str] = None
    volumes: Dict[str, Dict] = None
    timeout_per_command: int = 300
    user: Optional[str] = None

    def __post_init__(self):
        if self.env_vars is None:
            self.env_vars = {}
        if self.volumes is None:
            self.volumes = {}


@dataclass
class ExecutionResult:
    """Command execution result."""

    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False


class DockerManager:
    """
    Docker lifecycle manager.

    Responsibilities:
    - Image build and management
    - Container creation and destruction
    - Command execution and output capture
    - File transfer
    """

    def __init__(self):
        """Initialize the Docker client."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except docker.errors.DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise RuntimeError(
                "Docker is not available. Please ensure Docker is running."
            )

        self.container: Optional[docker.models.containers.Container] = None
        self.config: Optional[ContainerConfig] = None

    def build_image(
        self, dockerfile_path: str, tag: str, build_args: Dict[str, str] = None
    ) -> bool:
        """
        Build a Docker image.

        Args:
            dockerfile_path: Path to Dockerfile
            tag: Image tag
            build_args: Build arguments

        Returns:
            bool: Whether the build succeeded
        """
        logger.info(f"Building Docker image: {tag}")
        try:
            build_context = os.path.dirname(dockerfile_path)
            dockerfile_name = os.path.basename(dockerfile_path)

            image, build_logs = self.client.images.build(
                path=build_context,
                dockerfile=dockerfile_name,
                tag=tag,
                buildargs=build_args or {},
                rm=True,
                forcerm=True,
            )

            for log in build_logs:
                if "stream" in log:
                    logger.debug(log["stream"].strip())

            logger.info(f"Successfully built image: {tag}")
            return True

        except docker.errors.BuildError as e:
            logger.error(f"Failed to build image: {e}")
            return False
        except docker.errors.APIError as e:
            logger.error(f"Docker API error: {e}")
            return False

    def pull_image(self, image: str) -> bool:
        """
        Pull a Docker image.

        Args:
            image: Image name

        Returns:
            bool: Whether the pull succeeded
        """
        logger.info(f"Pulling Docker image: {image}")
        try:
            self.client.images.pull(image)
            logger.info(f"Successfully pulled image: {image}")
            return True
        except docker.errors.ImageNotFound:
            logger.error(f"Image not found: {image}")
            return False
        except docker.errors.APIError as e:
            logger.error(f"Failed to pull image: {e}")
            return False

    def image_exists(self, image: str) -> bool:
        """Check whether an image exists locally."""
        try:
            self.client.images.get(image)
            return True
        except docker.errors.ImageNotFound:
            return False

    def create_container(self, config: ContainerConfig) -> bool:
        """
        Create a container.

        Args:
            config: Container configuration

        Returns:
            bool: Whether creation succeeded
        """
        logger.info(f"Creating container: {config.name}")
        self.config = config

        try:
            # Ensure image exists
            if not self.image_exists(config.image):
                logger.info(f"Image {config.image} not found locally, pulling...")
                if not self.pull_image(config.image):
                    return False

            # Create container
            self.container = self.client.containers.create(
                image=config.image,
                name=config.name,
                working_dir=config.working_dir,
                network_mode=config.network_mode,
                environment=config.env_vars,
                volumes=config.volumes,
                user=config.user,
                cpu_count=int(config.cpus),
                mem_limit=config.memory,
                stdin_open=True,
                tty=True,
                detach=True,
            )

            logger.info(f"Container created: {self.container.id[:12]}")
            return True

        except docker.errors.APIError as e:
            logger.error(f"Failed to create container: {e}")
            return False

    def start_container(self) -> bool:
        """Start the container."""
        if not self.container:
            logger.error("No container to start")
            return False

        try:
            self.container.start()
            logger.info(f"Container started: {self.container.id[:12]}")
            return True
        except docker.errors.APIError as e:
            logger.error(f"Failed to start container: {e}")
            return False

    def stop_container(self, timeout: int = 10) -> bool:
        """Stop the container."""
        if not self.container:
            return True

        try:
            self.container.stop(timeout=timeout)
            logger.info(f"Container stopped: {self.container.id[:12]}")
            return True
        except docker.errors.APIError as e:
            logger.error(f"Failed to stop container: {e}")
            return False

    def remove_container(self, force: bool = True) -> bool:
        """Remove the container."""
        if not self.container:
            return True

        try:
            self.container.remove(force=force)
            logger.info(f"Container removed: {self.container.id[:12]}")
            self.container = None
            return True
        except docker.errors.APIError as e:
            logger.error(f"Failed to remove container: {e}")
            return False

    def execute_command(
        self,
        command: str,
        timeout: Optional[int] = None,
        workdir: Optional[str] = None,
        user: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute a command inside the container.

        Args:
            command: Command to execute
            timeout: Timeout in seconds; None uses the container default
            workdir: Working directory; None uses the container default

        Returns:
            ExecutionResult: Execution result
        """
        if not self.container:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="No container available",
                duration=0,
                timed_out=False,
            )

        timeout = timeout or (self.config.timeout_per_command if self.config else 300)

        logger.debug(f"Executing command: {command[:100]}...")
        start_time = time.time()

        try:
            # Wrap command in sh -c to support pipes, redirects, and other shell features
            shell_command = ["sh", "-c", command]

            # Create exec instance (supports specifying user)
            exec_kwargs: Dict[str, Any] = {
                "workdir": workdir,
                "tty": True,
                "stdin": True,
            }
            if user:
                exec_kwargs["user"] = user

            # Create exec instance
            exec_instance = self.client.api.exec_create(
                self.container.id, shell_command, **exec_kwargs
            )

            # Execute and collect output
            output = self.client.api.exec_start(exec_instance["Id"], stream=True)

            # Collect output (with timeout)
            stdout_data = []
            timed_out = False

            for chunk in output:
                if time.time() - start_time > timeout:
                    timed_out = True
                    break
                stdout_data.append(chunk.decode("utf-8", errors="replace"))

            # Get exit code
            exec_info = self.client.api.exec_inspect(exec_instance["Id"])
            exit_code = exec_info["ExitCode"] if not timed_out else -1

            duration = time.time() - start_time
            stdout = "".join(stdout_data)

            result = ExecutionResult(
                exit_code=exit_code,
                stdout=stdout,
                stderr="",  # In TTY mode stderr is merged into stdout
                duration=duration,
                timed_out=timed_out,
            )

            logger.debug(
                f"Command finished: exit_code={exit_code}, duration={duration:.2f}s"
            )
            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Command execution failed: {e}")
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration=duration,
                timed_out=False,
            )

    def write_file_direct(self, path: str, content: bytes) -> Tuple[bool, str]:
        """
        Write file content directly to the container via a tar stream (efficient and reliable).

        Args:
            path: File path inside the container
            content: File content (bytes)

        Returns:
            Tuple[bool, str]: (success, error message or success message)
        """
        if not self.container:
            return False, "No container available"

        try:
            # Ensure parent directory exists
            dir_path = os.path.dirname(path)
            if dir_path:
                mkdir_result = self.execute_command(f"mkdir -p '{dir_path}'")
                if mkdir_result.exit_code != 0:
                    return False, f"Failed to create directory: {mkdir_result.stderr}"

            # Create in-memory tar archive
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                # Create TarInfo object
                file_info = tarfile.TarInfo(name=os.path.basename(path))
                file_info.size = len(content)
                file_info.mtime = time.time()
                file_info.mode = 0o644

                # Add content to tar
                tar.addfile(file_info, io.BytesIO(content))

            tar_stream.seek(0)

            # Write using put_archive
            self.container.put_archive(dir_path or "/", tar_stream)

            logger.debug(f"Wrote {len(content)} bytes to container:{path}")
            return True, f"Successfully wrote {len(content)} bytes"

        except Exception as e:
            logger.error(f"Failed to write file to container: {e}")
            return False, str(e)

    def write_files_batch(self, files: Dict[str, bytes]) -> Tuple[bool, str]:
        """
        Write multiple files to the container in a single tar transfer (very efficient).

        Args:
            files: Dict mapping path to content (bytes)

        Returns:
            Tuple[bool, str]: (success, error or success message)
        """
        if not self.container:
            return False, "No container available"

        if not files:
            return True, "No files to write"

        try:
            # Collect all directories that need to be created
            dirs_to_create = set()
            for path in files.keys():
                dir_path = os.path.dirname(path)
                if dir_path and dir_path != "/":
                    dirs_to_create.add(dir_path)

            # Create directories in batch
            if dirs_to_create:
                mkdir_cmd = "mkdir -p " + " ".join(f"'{d}'" for d in dirs_to_create)
                mkdir_result = self.execute_command(mkdir_cmd)
                if mkdir_result.exit_code != 0:
                    return False, f"Failed to create directories: {mkdir_result.stderr}"

            # Group files by directory
            files_by_dir: Dict[str, Dict[str, bytes]] = {}
            for path, content in files.items():
                dir_path = os.path.dirname(path) or "/"
                if dir_path not in files_by_dir:
                    files_by_dir[dir_path] = {}
                files_by_dir[dir_path][os.path.basename(path)] = content

            # Create and upload a tar for each directory
            total_bytes = 0
            for dir_path, dir_files in files_by_dir.items():
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                    for filename, content in dir_files.items():
                        file_info = tarfile.TarInfo(name=filename)
                        file_info.size = len(content)
                        file_info.mtime = time.time()
                        file_info.mode = 0o644
                        tar.addfile(file_info, io.BytesIO(content))
                        total_bytes += len(content)

                tar_stream.seek(0)
                self.container.put_archive(dir_path, tar_stream)

            logger.debug(f"Batch wrote {len(files)} files ({total_bytes} bytes)")
            return True, f"Successfully wrote {len(files)} files ({total_bytes} bytes)"

        except Exception as e:
            logger.error(f"Failed to batch write files: {e}")
            return False, str(e)

    def copy_to_container(self, src_path: str, dst_path: str) -> bool:
        """
        Copy a file to the container.

        Args:
            src_path: Local source path
            dst_path: Destination path inside the container

        Returns:
            bool: Whether the copy succeeded
        """
        if not self.container:
            logger.error("No container available")
            return False

        try:
            # Create tar archive
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                tar.add(src_path, arcname=os.path.basename(src_path))
            tar_stream.seek(0)

            # Copy to container
            self.container.put_archive(os.path.dirname(dst_path), tar_stream)

            logger.debug(f"Copied {src_path} to container:{dst_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy file to container: {e}")
            return False

    def copy_from_container(self, src_path: str, dst_path: str) -> bool:
        """
        Copy a file from the container.

        Args:
            src_path: Source path inside the container
            dst_path: Local destination path

        Returns:
            bool: Whether the copy succeeded
        """
        if not self.container:
            logger.error("No container available")
            return False

        try:
            # Retrieve file from container
            bits, stat = self.container.get_archive(src_path)

            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            # Extract to destination
            tar_stream = io.BytesIO()
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)

            with tarfile.open(fileobj=tar_stream) as tar:
                tar.extractall(path=os.path.dirname(dst_path))

            logger.debug(f"Copied container:{src_path} to {dst_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to copy file from container: {e}")
            return False

    def get_container_status(self) -> Optional[str]:
        """Return the current container status."""
        if not self.container:
            return None
        try:
            self.container.reload()
            return self.container.status
        except:
            return None

    def get_container_by_name(self, name: str) -> Optional[Any]:
        """
        Get a container by name.

        Args:
            name: Container name

        Returns:
            Container object, or None if not found.
        """
        try:
            container = self.client.containers.get(name)
            logger.info(f"Found container: {name} (status: {container.status})")
            return container
        except docker.errors.NotFound:
            logger.info(f"Container not found: {name}")
            return None
        except docker.errors.APIError as e:
            logger.error(f"Error getting container {name}: {e}")
            return None

    def attach_to_container(self, name: str) -> bool:
        """
        Attach to an existing container.

        Args:
            name: Container name

        Returns:
            bool: Whether the attach succeeded
        """
        container = self.get_container_by_name(name)
        if container is None:
            return False

        self.container = container
        logger.info(f"Attached to container: {name}")
        return True

    def restart_container(self, timeout: int = 10) -> bool:
        """
        Restart the container.

        Args:
            timeout: Stop timeout in seconds

        Returns:
            bool: Whether the restart succeeded
        """
        if not self.container:
            logger.error("No container to restart")
            return False

        try:
            self.container.restart(timeout=timeout)
            logger.info(f"Container restarted: {self.container.id[:12]}")
            return True
        except docker.errors.APIError as e:
            logger.error(f"Failed to restart container: {e}")
            return False

    def container_exists(self, name: str) -> bool:
        """
        Check whether a container exists.

        Args:
            name: Container name

        Returns:
            bool: Whether the container exists
        """
        return self.get_container_by_name(name) is not None

    def cleanup(self):
        """Clean up all resources."""
        logger.info("Cleaning up Docker resources...")
        self.stop_container()
        self.remove_container(force=True)
        logger.info("Cleanup completed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False
