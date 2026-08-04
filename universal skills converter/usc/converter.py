from __future__ import annotations

import re
from typing import List, Optional

from usc.patterns.base import get_all_patterns


CONVERSION_HEADER = "<!-- Converted by Universal Skills Converter -->\n"


def split_code_blocks(text: str) -> List[tuple[str, bool]]:
    """
    Split markdown text into parts, identifying code blocks.

    A code block is any text between triple backticks (```).
    Both fenced code blocks with and without language specifiers are supported.

    Args:
        text: The markdown text to split.

    Returns:
        A list of tuples (content, is_code_block). Text parts have
        is_code_block=False, code block contents have is_code_block=True.
    """
    parts: List[tuple[str, bool]] = []
    lines = text.split("\n")
    in_code_block = False
    current_block_lines: List[str] = []

    for line in lines:
        if line.strip().startswith("```"):
            if not in_code_block:
                # Start of code block
                if current_block_lines:
                    parts.append(("\n".join(current_block_lines), False))
                    current_block_lines = []
                in_code_block = True
                current_block_lines.append(line)
            else:
                # End of code block
                current_block_lines.append(line)
                parts.append(("\n".join(current_block_lines), True))
                current_block_lines = []
                in_code_block = False
        else:
            current_block_lines.append(line)

    if current_block_lines:
        parts.append(("\n".join(current_block_lines), in_code_block))

    return parts


def transform_text(text: str) -> str:
    """
    Apply all regex patterns from get_all_patterns() to the text.

    Patterns are applied in order. For each match, replace with the
    replacement string using re.sub.

    Args:
        text: The text to transform.

    Returns:
        The transformed text.
    """
    for pattern, replacement in get_all_patterns():
        text = re.sub(pattern, replacement, text)
    return text


def convert(content: str) -> str:
    """
    Convert markdown content by applying patterns only to non-code parts.

    Args:
        content: The markdown content to convert.

    Returns:
        The converted content with a conversion header at the top.
    """
    parts = split_code_blocks(content)
    result_parts: List[str] = []

    for part, is_code_block in parts:
        if is_code_block:
            result_parts.append(part)
        else:
            result_parts.append(transform_text(part))

    return CONVERSION_HEADER + "\n".join(result_parts)


def convert_file(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Read an input file, convert its content, and optionally write to output.

    Args:
        input_path: Path to the input file.
        output_path: Optional path for the output file. If provided,
                     the converted content is written to this file.

    Returns:
        The converted content string, or output_path if output_path is provided.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    converted = convert(content)

    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(converted)
        return output_path

    return converted
