import os
import re
from typing import Any


DEFAULT_CONFIG_PATHS = [
    os.path.expanduser("~/.config/usc/config.yaml"),
    os.path.expanduser("~/.usc.yaml"),
    os.path.expanduser("./.usc.yaml"),
]


def _load_yaml():
    try:
        import yaml

        return yaml
    except ImportError:
        return None


def load_config() -> dict[str, Any]:
    yaml = _load_yaml()
    if yaml is None:
        return {}

    for path in DEFAULT_CONFIG_PATHS:
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError):
            continue

    return {}


def get_custom_patterns(config: dict[str, Any]) -> list[tuple[re.Pattern[str], str]]:
    patterns = []
    raw_patterns = config.get("patterns", [])
    if not isinstance(raw_patterns, list):
        return patterns

    for entry in raw_patterns:
        if not isinstance(entry, dict):
            continue
        regex_str = entry.get("regex")
        replacement = entry.get("replacement", "")
        if not isinstance(regex_str, str) or not regex_str.strip():
            continue
        try:
            compiled = re.compile(regex_str)
            patterns.append((compiled, str(replacement)))
        except re.error:
            continue

    return patterns


def get_enabled_tools(config: dict[str, Any]) -> list[str]:
    from usc.tools_registry import list_tools, get_tool

    raw = config.get("enabled_tools", [])
    if not isinstance(raw, list):
        return list_tools()

    all_tools = set(list_tools())
    enabled = [key for key in raw if isinstance(key, str) and key in all_tools]
    return enabled if enabled else list_tools()


def merge_patterns(
    base_patterns: list[tuple[re.Pattern[str], str]],
    custom_patterns: list[tuple[re.Pattern[str], str]],
) -> list[tuple[re.Pattern[str], str]]:
    return list(base_patterns) + list(custom_patterns)
