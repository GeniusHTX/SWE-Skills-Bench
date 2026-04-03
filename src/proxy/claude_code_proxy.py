"""
Claude Code CLI proxy
Invokes the Claude Code CLI directly inside a Docker container to execute tasks.
"""

import os
import time
import threading
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..orchestrator.docker_manager import DockerManager
from ..orchestrator.logger import get_logger
from ..utils import generate_report_filename, get_timestamp, get_model_name

logger = get_logger(__name__)


@dataclass
class ClaudeCodeResult:
    """Claude Code execution result."""

    success: bool
    output: str
    stderr: str
    exit_code: int
    duration_sec: float


class ClaudeCodeProxy:
    """
    Claude Code CLI interaction proxy.

    Usage:
    1. Write task file content into the container
    2. Invoke the claude CLI to let it operate autonomously inside the container
    3. Wait for completion and collect results
    """

    def __init__(self, docker_manager: DockerManager, config: Dict[str, Any]):
        """
        Initialize the Claude Code proxy.

        Args:
            docker_manager: Docker manager instance
            config: Configuration dictionary
        """
        self.docker_manager = docker_manager
        self.config = config

        # Get timeout configuration
        limits = config.get("limits", {})
        self.timeout_per_command = limits.get("timeout_per_command", 300)
        self.total_timeout_sec = limits.get("total_timeout_sec", 1800)

        # Working directory inside the container (usually the repository directory)
        self.workspace_dir = config.get("global", {}).get("workspace_dir", "/workspace")

        # Runtime artifacts are always placed in /workspace to avoid polluting the project directory
        self.runtime_root_dir = "/workspace"

        # Host-side log directory structure
        # claude_process/{model_name}/{batch}/
        #   ├── claude_output/     # Redirected CLI output
        #   └── claude_thinking/   # Thinking JSON files from ~/.claude/projects/-workspace
        _model_name = get_model_name()
        _batch = config.get("batch", "")
        if _batch:
            self.process_base_dir = os.path.join(
                os.getcwd(), "claude_process", _model_name, _batch
            )
        else:
            self.process_base_dir = os.path.join(
                os.getcwd(), "claude_process", _model_name
            )
        self.output_log_dir = os.path.join(self.process_base_dir, "claude_output")
        self.thinking_json_dir = os.path.join(self.process_base_dir, "claude_thinking")
        os.makedirs(self.output_log_dir, exist_ok=True)
        os.makedirs(self.thinking_json_dir, exist_ok=True)

        # Output directory inside the container, fixed under /workspace
        self.container_output_dir = f"{self.runtime_root_dir}/claude_output"

        # Claude thinking-file base directory inside the container (for recursive searching)
        self.container_thinking_base_dir = "/home/dev/.claude/projects"

        # Status monitor flags
        self._monitor_stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

        logger.info("Claude Code Proxy initialized")
        logger.info(f"  Output logs -> {self.output_log_dir}")
        logger.info(f"  Thinking JSONs -> {self.thinking_json_dir}")

    async def execute_task(self, task_content: str) -> ClaudeCodeResult:
        """
        Execute a task: write the task content into the container and invoke the claude CLI.

        Args:
            task_content: Task description content

        Returns:
            ClaudeCodeResult: Execution result
        """
        start_time = time.time()

        # Pre-check: confirm that the `claude` executable exists in the container
        try:
            check = self.docker_manager.execute_command("which claude", timeout=10)
            if check.exit_code != 0:
                err = (
                    "claude CLI not found in container PATH. "
                    "Install the claude binary in the container image or provide it via volumes."
                )
                logger.error(err)
                duration = time.time() - start_time
                return ClaudeCodeResult(
                    success=False,
                    output="",
                    stderr=err,
                    exit_code=127,
                    duration_sec=duration,
                )
        except Exception:
            # If the check itself fails, log and continue; let the subsequent execution report a more specific error
            logger.debug(
                "Failed to run 'which claude' check; continuing to run claude command"
            )

        # Before writing the task to the container, inject mandatory execution instructions
        # to require Claude to directly modify repository files,
        # avoiding plans-only or clarifying-question responses.
        # Do not re-inject if the task already contains these instructions.
        instruction_prefix = (
            "INTERNAL_INSTRUCTION: DO_NOT_ASK_OR_PLAN\n"
            "You MUST directly modify files in the repository under the workspace to implement the task.\n"
            "Do NOT output a design plan or ask clarifying questions.\n"
            "Write/update the necessary files (provide full file paths and contents).\n"
            "Only output a concise summary of files changed and the final status.\n"
            "EndInstruction\n\n"
        )

        if not task_content.startswith("INTERNAL_INSTRUCTION: DO_NOT_ASK_OR_PLAN"):
            task_content = instruction_prefix + task_content

        # Step 1: Write the task file into the container
        task_file_path = f"{self.runtime_root_dir}/task.md"
        self._write_task_to_container(task_file_path, task_content)

        # Step 2: Build the claude CLI command (pass task text directly to claude and add skip-permissions flag)
        claude_cmd = self._build_claude_command(task_content)

        # Step 3: Execute the command
        print("\n" + "=" * 60)
        print("🤖 Claude Code starting task execution...")
        print("=" * 60)
        logger.info(f"Executing Claude Code in container...")

        # Ensure the task file is owned by dev:dev (it may be written as root)
        try:
            chown_task = self.docker_manager.execute_command(
                f"chown -R dev:dev {task_file_path} || true", timeout=30, user="root"
            )
            logger.debug(f"chown task exit: {chown_task.exit_code}")
        except Exception:
            logger.debug("chown task failed or skipped")

        # Create the output directory inside the container
        self.docker_manager.execute_command(
            f"mkdir -p {self.container_output_dir}", timeout=30, user="root"
        )
        self.docker_manager.execute_command(
            f"chown -R dev:dev {self.container_output_dir} || true",
            timeout=30,
            user="root",
        )

        # Start status monitor thread
        self._start_status_monitor()

        # Execute claude as the dev user
        result = self.docker_manager.execute_command(
            claude_cmd,
            timeout=self.total_timeout_sec,
            user="dev",
        )

        # Stop status monitor
        self._stop_status_monitor()

        duration = time.time() - start_time

        # Print completion status
        status_icon = "✅" if result.exit_code == 0 else "❌"
        print(
            f"\n{status_icon} Claude Code execution finished (elapsed: {duration:.1f}s, exit code: {result.exit_code})"
        )
        print("=" * 60 + "\n")

        # Step 4: Copy output log from the container to the host
        self._copy_output_log_to_host()

        # Step 5: Copy thinking JSON files
        self._copy_thinking_json_to_host()

        # Step 6: Return the result
        return ClaudeCodeResult(
            success=result.exit_code == 0,
            output=result.stdout or "",
            stderr=result.stderr or "",
            exit_code=result.exit_code,
            duration_sec=duration,
        )

    def _write_task_to_container(self, task_file_path: str, task_content: str):
        """Write task content to a file inside the container."""
        logger.debug(f"Writing task content to: {task_file_path}")

        # Write file using shell-quoted echo; embedded newlines are preserved by the shell
        escaped_content = task_content.replace("'", "'\\''")
        cmd = f"echo '{escaped_content}' > {task_file_path}"

        result = self.docker_manager.execute_command(cmd, timeout=30)

        if result.exit_code != 0:
            logger.error(f"Failed to write task file: {result.stderr}")
            raise RuntimeError(f"Failed to write task file: {result.stderr}")

        logger.info(f"Task file written to: {task_file_path}")

    def _build_claude_command(self, task_content: str) -> str:
        """
        Build the claude CLI command.

        Uses CI=true to disable interactive UI and --verbose for detailed thinking output.
        Output is redirected to a log file for later extraction.
        """
        # Wrap task text in single quotes, escaping any internal single quotes
        escaped = task_content.replace("'", "'\\''")
        # Generate a consistently named log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        skill_id = None
        use_skill_flag = None
        use_agent_flag = None
        try:
            skill_id = self.config.get("skill_id") or self.config.get(
                "metadata", {}
            ).get("skill_id")
            use_skill_flag = self.config.get("use_skill")
            use_agent_flag = self.config.get("use_agent")
        except Exception:
            pass

        log_filename = generate_report_filename(
            prefix="claude_log",
            skill=skill_id,
            use_agent=use_agent_flag,
            use_skill=use_skill_flag,
            timestamp=timestamp,
            ext=".log",
        )
        log_file = f"{self.container_output_dir}/{log_filename}"
        # Save current log path for later copying
        self._current_log_file = log_file
        self._current_timestamp = timestamp
        # CI=true disables interactive UI; --verbose outputs detailed thinking
        cmd = (
            f"cd {self.workspace_dir} && "
            f"CI=true claude '{escaped}' --dangerously-skip-permissions --verbose "
            f"> {log_file} 2>&1"
        )
        return cmd

    def _copy_output_log_to_host(self):
        """
        Copy the output log file from the container to the host's claude_process/claude_output directory.
        """
        if not hasattr(self, "_current_log_file") or not self._current_log_file:
            logger.debug("No log file to copy")
            return

        try:
            # Read the log file from the container
            cat_result = self.docker_manager.execute_command(
                f"cat {self._current_log_file}", timeout=60, user="dev"
            )
            if cat_result.exit_code == 0 and cat_result.stdout:
                # Write to host
                log_filename = os.path.basename(self._current_log_file)
                host_log_path = os.path.join(self.output_log_dir, log_filename)
                with open(host_log_path, "w", encoding="utf-8") as f:
                    f.write(cat_result.stdout)
                logger.info(f"Output log saved to: {host_log_path}")
            else:
                logger.warning(
                    f"Failed to read log file from container: {cat_result.stderr}"
                )
        except Exception as e:
            logger.error(f"Failed to copy output log: {e}")

    def _copy_thinking_json_to_host(self):
        """
        Copy JSONL files from ~/.claude/projects inside the container
        to the host's claude_process/claude_thinking directory.
        Uses find to recursively search for all JSONL files.
        """
        try:
            # Use find to recursively search for all JSONL files
            list_result = self.docker_manager.execute_command(
                f"find {self.container_thinking_base_dir} -name '*.jsonl' -type f 2>/dev/null || true",
                timeout=30,
                user="dev",
            )

            if list_result.exit_code != 0 or not list_result.stdout.strip():
                logger.debug(
                    f"No JSONL files found in {self.container_thinking_base_dir}"
                )
                return

            jsonl_files = [
                f.strip() for f in list_result.stdout.strip().split("\n") if f.strip()
            ]

            if not jsonl_files:
                logger.debug("No thinking JSONL files to copy")
                return

            logger.info(f"Found {len(jsonl_files)} thinking JSONL file(s) to copy")

            for jsonl_file in jsonl_files:
                try:
                    # Read the JSONL file content
                    cat_result = self.docker_manager.execute_command(
                        f"cat '{jsonl_file}'", timeout=60, user="dev"
                    )

                    if cat_result.exit_code == 0 and cat_result.stdout:
                        # Generate a consistently named file: prefix_skill_use-agent_x_use-skill_y_timestamp.jsonl
                        timestamp = (
                            getattr(self, "_current_timestamp", None) or get_timestamp()
                        )

                        skill_id = None
                        use_skill_flag = None
                        use_agent_flag = None

                        try:
                            skill_id = self.config.get("skill_id") or self.config.get(
                                "metadata", {}
                            ).get("skill_id")
                            use_skill_flag = self.config.get("use_skill")
                            use_agent_flag = self.config.get("use_agent")
                        except Exception:
                            pass

                        host_filename = generate_report_filename(
                            prefix="claude",
                            skill=skill_id,
                            use_agent=use_agent_flag,
                            use_skill=use_skill_flag,
                            timestamp=timestamp,
                            ext=".jsonl",
                        )
                        host_path = os.path.join(self.thinking_json_dir, host_filename)

                        with open(host_path, "w", encoding="utf-8") as f:
                            f.write(cat_result.stdout)
                        logger.info(f"Thinking JSONL saved to: {host_path}")
                    else:
                        logger.warning(f"Failed to read JSONL file: {jsonl_file}")
                except Exception as e:
                    logger.error(f"Failed to copy JSONL file {jsonl_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to copy thinking JSONL files: {e}")

    def _start_status_monitor(self):
        """Start the status monitor thread to periodically check Claude Code's working state."""
        self._monitor_stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._status_monitor_loop, daemon=True
        )
        self._monitor_thread.start()

    def _stop_status_monitor(self):
        """Stop the status monitor thread."""
        self._monitor_stop_event.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

    def _status_monitor_loop(self):
        """Status monitor loop: periodically checks and prints Claude Code working state, reading from JSONL."""
        check_interval = 5  # Check every 5 seconds
        last_line_count = 0
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        spinner_idx = 0
        start_time = time.time()
        last_action = ""

        while not self._monitor_stop_event.wait(check_interval):
            try:
                elapsed = time.time() - start_time
                elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

                # Check whether the claude process is running
                proc_result = self.docker_manager.execute_command(
                    "pgrep -f 'claude' | head -1", timeout=5, user="dev"
                )
                is_running = proc_result.exit_code == 0 and proc_result.stdout.strip()

                # Read the latest thinking state from JSONL files
                current_action = self._get_latest_thinking_action()
                if current_action and current_action != last_action:
                    last_action = current_action

                # Build status line
                spinner = spinner_chars[spinner_idx % len(spinner_chars)]
                spinner_idx += 1

                if is_running:
                    # Show current action
                    display_action = last_action if last_action else "Processing..."
                    # Truncate overly long action descriptions
                    if len(display_action) > 60:
                        display_action = display_action[:57] + "..."
                    status_line = f"\r{spinner} [{elapsed_str}] {display_action}"
                else:
                    status_line = (
                        f"\r⏳ Waiting for Claude Code response [{elapsed_str}]"
                    )

                # Print status (use \r to overwrite the same line)
                print(status_line.ljust(100), end="", flush=True)

            except Exception as e:
                logger.debug(f"Status monitor error: {e}")

    def _get_latest_thinking_action(self) -> str:
        """
        Read the latest action/state from the JSONL thinking file inside the container.
        Parses the JSONL format and extracts meaningful status information.
        """
        try:
            # Find the latest JSONL file first, then read its last few lines;
            # use find recursively sorted by modification time to get the newest file
            tail_result = self.docker_manager.execute_command(
                f"find {self.container_thinking_base_dir} -name '*.jsonl' -type f -printf '%T+ %p\\n' 2>/dev/null | sort -r | head -1 | cut -d' ' -f2- | xargs -r tail -n 5 2>/dev/null | tail -n 3",
                timeout=5,
                user="dev",
            )

            if tail_result.exit_code != 0 or not tail_result.stdout.strip():
                return ""

            lines = tail_result.stdout.strip().split("\n")

            # Parse from the back, looking for meaningful status
            for line in reversed(lines):
                line = line.strip()
                if not line or line.startswith("==>"):
                    continue

                try:
                    entry = json.loads(line)

                    # Extract state based on message type
                    msg_type = entry.get("type", "")

                    if msg_type == "assistant":
                        # Assistant message, may contain tool calls
                        message = entry.get("message", {})
                        content = message.get("content", [])
                        for item in (
                            reversed(content) if isinstance(content, list) else []
                        ):
                            if isinstance(item, dict):
                                item_type = item.get("type", "")
                                if item_type == "tool_use":
                                    tool_name = item.get("name", "unknown")
                                    tool_input = item.get("input", {})
                                    return self._format_tool_action(
                                        tool_name, tool_input
                                    )
                                elif item_type == "text":
                                    text = item.get("text", "")
                                    if text:
                                        # Use the first line as a summary
                                        first_line = text.split("\n")[0].strip()
                                        if first_line:
                                            return f"💭 {first_line}"

                    elif msg_type == "user":
                        # User message (usually a tool result)
                        message = entry.get("message", {})
                        content = message.get("content", [])
                        for item in content if isinstance(content, list) else []:
                            if (
                                isinstance(item, dict)
                                and item.get("type") == "tool_result"
                            ):
                                return "📥 Processing tool result..."

                    elif msg_type == "summary":
                        # Summary message
                        summary = entry.get("summary", "")
                        if summary:
                            return f"📋 {summary[:50]}"

                except json.JSONDecodeError:
                    continue

            return ""

        except Exception as e:
            logger.debug(f"Error reading thinking status: {e}")
            return ""

    def _format_tool_action(self, tool_name: str, tool_input: dict) -> str:
        """
        Format a tool call as a human-readable status description.
        """
        tool_icons = {
            "Read": "📖",
            "Write": "✏️",
            "Edit": "✏️",
            "Bash": "💻",
            "Search": "🔍",
            "Grep": "🔍",
            "List": "📁",
            "Glob": "📁",
            "TodoRead": "📋",
            "TodoWrite": "📋",
        }

        # Get icon
        icon = "🔧"
        for key, emoji in tool_icons.items():
            if key.lower() in tool_name.lower():
                icon = emoji
                break

        # Format per-tool input
        if "file_path" in tool_input:
            path = tool_input["file_path"]
            # Show only the filename
            filename = os.path.basename(path) if path else "unknown"
            return f"{icon} {tool_name}: {filename}"
        elif "command" in tool_input:
            cmd = tool_input["command"]
            # Truncate long commands
            if len(cmd) > 40:
                cmd = cmd[:37] + "..."
            return f"{icon} {tool_name}: {cmd}"
        elif "pattern" in tool_input:
            pattern = tool_input["pattern"]
            return f"{icon} {tool_name}: {pattern}"
        elif "query" in tool_input:
            query = tool_input["query"]
            if len(query) > 30:
                query = query[:27] + "..."
            return f"{icon} {tool_name}: {query}"
        elif "content" in tool_input:
            return f"{icon} {tool_name}: writing content..."
        else:
            return f"{icon} {tool_name}"

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics."""
        return {
            "proxy_type": "claude_code_cli",
            "workspace_dir": self.workspace_dir,
            "timeout_per_command": self.timeout_per_command,
            "total_timeout_sec": self.total_timeout_sec,
            "output_log_dir": self.output_log_dir,
            "thinking_json_dir": self.thinking_json_dir,
        }
