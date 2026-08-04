"""YAML frontmatter handling for the universal skills converter."""

from __future__ import annotations

from typing import Any


def _simple_yaml_parse(text: str) -> dict[str, Any] | None:
    """Minimal fallback YAML parser handling simple key: value pairs."""
    result: dict[str, Any] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value in {"true", "True"}:
            value = True
        elif value in {"false", "False"}:
            value = False
        elif value in {"null", "None", "~"}:
            value = None
        else:
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]
        result[key] = value
    return result if result else None


try:
    import yaml  # type: ignore[import-untyped]

    def _parse_yaml(text: str) -> dict[str, Any] | None:
        try:
            data = yaml.safe_load(text)
            if data is None:
                return None
            if not isinstance(data, dict):
                return None
            return data
        except Exception:
            return None

except ImportError:
    yaml = None  # type: ignore[assignment]

    def _parse_yaml(text: str) -> dict[str, Any] | None:  # type: ignore[misc]
        return _simple_yaml_parse(text)


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Extract YAML frontmatter from markdown text.

    Args:
        text: The full markdown text possibly containing frontmatter.

    Returns:
        A tuple of (parsed_yaml_dict, remaining_markdown). If no frontmatter
        is present, returns (None, text).
    """
    if not (text.startswith("---\n") or text.startswith("---\r\n")):
        return None, text

    end = text.find("\n---", 4)
    if end == -1:
        end = text.find("\r\n---", 4)
    if end == -1:
        return None, text

    frontmatter_text = text[4:end]
    remaining = text[end + 4 :]

    if remaining.startswith("\n"):
        remaining = remaining[1:]
    elif remaining.startswith("\r\n"):
        remaining = remaining[2:]

    parsed = _parse_yaml(frontmatter_text)
    return parsed, remaining


def strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from markdown text.

    Args:
        text: The full markdown text possibly containing frontmatter.

    Returns:
        The markdown body with frontmatter removed.
    """
    _, remaining = parse_frontmatter(text)
    return remaining


def normalize_frontmatter(
    metadata: dict[str, Any] | None, source_tool: str | None = None
) -> dict[str, Any] | None:
    """Normalize tool-specific frontmatter fields.

    Removes or renames fields that are specific to particular AI tools.

    Args:
        metadata: The parsed frontmatter dictionary.
        source_tool: Optional source tool name used to identify tool-specific keys.

    Returns:
        A new dictionary with normalized fields, or None if metadata is None or empty.
    """
    if not metadata:
        return None

    result: dict[str, Any] = {}
    tool_keywords: set[str] = set()
    if source_tool:
        tool_keywords.add(source_tool.lower())
        for part in source_tool.lower().split():
            tool_keywords.add(part)

    for key, value in metadata.items():
        lower_key = key.lower()

        if lower_key == "allowed-tools":
            result["allowed-capabilities"] = value
            continue

        if lower_key == "model":
            continue

        if any(keyword in lower_key for keyword in tool_keywords):
            continue

        result[key] = value

    return result if result else None


def dump_frontmatter(metadata: dict[str, Any] | None) -> str:
    """Convert a dictionary back to a YAML frontmatter string.

    Args:
        metadata: The dictionary to serialize.

    Returns:
        A string like '---\\nkey: value\\n---\\n', or an empty string if
        metadata is None or empty.
    """
    if not metadata:
        return ""

    lines: list[str] = []
    for key, value in metadata.items():
        if value is None:
            lines.append(f"{key}:")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            str_value = str(value)
            if ":" in str_value or str_value == "" or str_value.lower() in {"true", "false", "null", "yes", "no"}:
                str_value = f'"{str_value}"'
            lines.append(f"{key}: {str_value}")

    yaml_block = "\n".join(lines)
    return f"---\n{yaml_block}\n---\n"
