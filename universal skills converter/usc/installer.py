from __future__ import annotations

import os
import re

from usc.tools_registry import get_tool


def get_skills_dir(tool_key: str) -> str:
    """
    Get the skills directory path for a given tool.

    Retrieves the tool metadata from the tools registry and expands the
    skills_dir path (resolving ~ to the user's home directory).

    Args:
        tool_key: The key identifying the tool in the tools registry.

    Returns:
        The absolute, expanded path to the tool's skills directory.
    """
    metadata = get_tool(tool_key)
    skills_dir = metadata['skills_dir']
    return os.path.expanduser(skills_dir)


def sanitize_name(name: str) -> str:
    """
    Sanitize a skill name for use as a filename.

    Converts the name to lowercase, replaces spaces and underscores with
    hyphens, removes any characters that are not alphanumeric or hyphens,
    and strips leading/trailing hyphens.

    Args:
        name: The raw skill name to sanitize.

    Returns:
        The sanitized skill name.
    """
    name = name.lower()
    name = name.replace(' ', '-').replace('_', '-')
    name = re.sub(r'[^a-z0-9-]', '', name)
    name = name.strip('-')
    return name


def install_skill(content: str, skill_name: str, tool_key: str, force: bool = False) -> str:
    """
    Install a skill content as a markdown file in the tool's skills directory.

    Args:
        content: The markdown content of the skill.
        skill_name: The name of the skill (will be sanitized for the filename).
        tool_key: The key identifying the target tool.
        force: If True, overwrite an existing skill file. If False, raise
               FileExistsError if the destination already exists.

    Returns:
        The absolute path to the installed skill file.

    Raises:
        FileExistsError: If the destination file exists and force is False.
    """
    skills_dir = get_skills_dir(tool_key)
    os.makedirs(skills_dir, exist_ok=True)

    file_name = sanitize_name(skill_name)
    dest_path = os.path.join(skills_dir, f"{file_name}.md")

    if os.path.exists(dest_path) and not force:
        raise FileExistsError(
            f"Skill '{skill_name}' already exists at '{dest_path}'. "
            "Use --force to overwrite."
        )

    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return dest_path
