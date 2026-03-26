"""
Container Utils - Container-related utility functions
Provides helper functionality for container naming and status queries.
"""

import re
from typing import Optional, Tuple


def generate_container_name(
    skill_id: str,
    use_skill: bool,
    use_agent: bool,
    model_name: Optional[str] = None,
    batch: Optional[str] = None,
) -> str:
    """
    Generate a standardized container name.

    Container naming format:
        benchmark[_{batch}]_{skill_id}_use-skill-{true|false}_use-agent-{true|false}[_{model_name}]

    Args:
        skill_id: Skill ID
        use_skill: Whether to use the skill file
        use_agent: Whether to use the agent
        model_name: Optional model name suffix for multi-model evaluation
        batch: Optional batch prefix (e.g. "batch1") placed at the front

    Returns:
        str: Container name
    """
    # Strip illegal characters (keep only letters, digits, dots, underscores, hyphens)
    safe_skill = re.sub(r"[^A-Za-z0-9._-]+", "-", skill_id)
    if not safe_skill:
        safe_skill = "skill"

    use_skill_flag = "true" if use_skill else "false"
    use_agent_flag = "true" if use_agent else "false"

    safe_batch = re.sub(r"[^A-Za-z0-9._-]+", "-", batch) if batch else None

    if safe_batch:
        name = f"benchmark_{safe_batch}_{safe_skill}_use-skill-{use_skill_flag}_use-agent-{use_agent_flag}"
    else:
        name = f"benchmark_{safe_skill}_use-skill-{use_skill_flag}_use-agent-{use_agent_flag}"

    if model_name:
        safe_model = re.sub(r"[^A-Za-z0-9._-]+", "-", model_name)
        if safe_model:
            name = f"{name}_{safe_model}"

    return name


def parse_container_name(container_name: str) -> Tuple[str, bool, bool]:
    """
    Parse parameters from a container name.

    Args:
        container_name: Container name

    Returns:
        Tuple[str, bool, bool]: (skill_id, use_skill, use_agent)

    Raises:
        ValueError: If the container name format is invalid
    """
    # batch prefix (batchN_) and model_name suffix are both optional
    pattern = r"^benchmark_(?:batch\d+_)?(.+)_use-skill-(true|false)_use-agent-(true|false)(?:_.+)?$"
    match = re.match(pattern, container_name)

    if not match:
        raise ValueError(f"Invalid container name format: {container_name}")

    skill_id = match.group(1)
    use_skill = match.group(2) == "true"
    use_agent = match.group(3) == "true"

    return skill_id, use_skill, use_agent
