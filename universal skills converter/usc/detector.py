from __future__ import annotations

import os
import psutil

from usc.tools_registry import TOOLS, get_tool


def detect_running_tool() -> str | None:
    """
    Detect a running tool by matching process names against the tools registry.

    Iterates over running processes and checks if any process name matches
    a known tool binary in TOOLS.

    Returns:
        The tool key if a matching process is found, otherwise None.
    """
    for proc in psutil.process_iter(['name']):
        try:
            process_name = proc.info['name']
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        for tool_key, metadata in TOOLS.items():
            if process_name == metadata['binary']:
                return tool_key
    return None


def detect_from_config() -> str | None:
    """
    Detect a tool by checking for the presence of its config file.

    Iterates over tools in TOOLS and returns the first tool whose config
    file exists on disk.

    Returns:
        The tool key if a config file is found, otherwise None.
    """
    for tool_key, metadata in TOOLS.items():
        config_path = os.path.expanduser(metadata['config_file'])
        if os.path.isfile(config_path):
            return tool_key
    return None


def detect_tool(target: str | None = None) -> str:
    """
    Detect the active tool using the specified priority order.

    Priority:
    1. Explicit --target flag (provided as the target parameter)
    2. Running process detection using psutil
    3. Config file presence detection

    Args:
        target: Optional tool key explicitly specified by the user.

    Returns:
        The detected tool key.

    Raises:
        ValueError: If target is provided but not a valid tool key, or if
                    no tool can be detected automatically.
    """
    if target is not None:
        if target not in TOOLS:
            raise ValueError(
                f"Unknown tool: '{target}'. Supported tools: {', '.join(sorted(TOOLS.keys()))}. "
                "Use the --target flag to specify one."
            )
        return target

    running_tool = detect_running_tool()
    if running_tool is not None:
        return running_tool

    config_tool = detect_from_config()
    if config_tool is not None:
        return config_tool

    raise ValueError(
        f"Could not auto-detect a tool. Supported tools: {', '.join(sorted(TOOLS.keys()))}. "
        "Use the --target flag to specify one."
    )
