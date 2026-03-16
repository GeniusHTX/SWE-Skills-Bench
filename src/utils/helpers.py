"""
Helpers - Utility functions
Provides various helper utilities.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import yaml


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dict: Configuration dictionary
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_json_report(data: Dict[str, Any], output_path: str) -> str:
    """
    Save a JSON report.

    Args:
        data: Report data
        output_path: Output path

    Returns:
        str: Actual path the file was saved to
    """
    # Ensure the directory exists
    ensure_dir(os.path.dirname(output_path))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return output_path


def get_timestamp(format: str = "%Y%m%d_%H%M%S") -> str:
    """
    Get the current timestamp string.

    Args:
        format: Time format

    Returns:
        str: Timestamp string
    """
    return datetime.now().strftime(format)


def _flag_to_str(flag: Optional[Any]) -> str:
    """Convert bool/str/None to normalized flag string."""
    if isinstance(flag, bool):
        return "true" if flag else "false"
    if flag is None:
        return "unknown"
    return str(flag)


def generate_report_filename(
    prefix: str,
    skill: Optional[str],
    use_agent: Optional[Any],
    use_skill: Optional[Any],
    timestamp: Optional[str] = None,
    ext: str = ".json",
) -> str:
    """
    Generate a file name in the standard format:
    {prefix}_{skill}_use-agent-{...}_use-skill-{...}_{timestamp}{ext}

    Args:
        prefix: File name prefix, e.g. "report", "eval_report", "claude"
        skill: Skill name/ID; falls back to "unknown" when absent
        use_agent: Whether to use the agent (bool/str); falls back to "unknown" when None
        use_skill: Whether to use the skill (bool/str); falls back to "unknown" when None
        timestamp: Explicit timestamp; uses current timestamp when empty
        ext: Extension, default .json; can pass .jsonl/.log etc.

    Returns:
        str: Formatted file name (no path)
    """

    ts = timestamp or get_timestamp()
    skill_part = (skill or "unknown").replace(" ", "-")
    ua = _flag_to_str(use_agent)
    us = _flag_to_str(use_skill)
    if not ext.startswith("."):
        ext = f".{ext}"
    return f"{prefix}_{skill_part}_use-agent-{ua}_use-skill-{us}_{ts}{ext}"


def ensure_dir(dir_path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Directory path

    Returns:
        Path: Directory Path object
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def hash_file(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file.

    Args:
        file_path: Path to the file
        algorithm: Hash algorithm

    Returns:
        str: Hash value
    """
    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def truncate_string(s: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate a string.

    Args:
        s: Original string
        max_length: Maximum length
        suffix: Truncation suffix

    Returns:
        str: Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def parse_duration(duration_str: str) -> int:
    """
    Parse a duration string into seconds.

    Args:
        duration_str: e.g. "30m", "1h", "1800s"

    Returns:
        int: Number of seconds
    """
    if duration_str.endswith("s"):
        return int(duration_str[:-1])
    elif duration_str.endswith("m"):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith("h"):
        return int(duration_str[:-1]) * 3600
    else:
        return int(duration_str)


def format_duration(seconds: float) -> str:
    """
    Format a number of seconds as a human-readable string.

    Args:
        seconds: Number of seconds

    Returns:
        str: Formatted string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def merge_dicts(base: Dict, override: Dict) -> Dict:
    """
    Deep-merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Dict: Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


class Counter:
    """Simple counter."""

    def __init__(self, initial: int = 0):
        self.value = initial

    def increment(self, amount: int = 1) -> int:
        self.value += amount
        return self.value

    def decrement(self, amount: int = 1) -> int:
        self.value -= amount
        return self.value

    def reset(self):
        self.value = 0


class Timer:
    """Simple timer."""

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def start(self):
        self.start_time = datetime.now()
        self.end_time = None

    def stop(self):
        self.end_time = datetime.now()

    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0

        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()

    @property
    def elapsed_formatted(self) -> str:
        """Get the elapsed time as a formatted string."""
        return format_duration(self.elapsed)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
