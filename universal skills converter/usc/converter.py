from __future__ import annotations

import re
from typing import List, Optional

from usc.frontmatter import dump_frontmatter, normalize_frontmatter, parse_frontmatter
from usc.patterns.base import get_all_patterns


CONVERSION_HEADER = "<!-- Converted by Universal Skills Converter -->\n"
VERBOSE = False


def set_verbose(enabled: bool) -> None:
    global VERBOSE
    VERBOSE = enabled


def split_code_blocks(text: str) -> List[tuple[str, bool]]:
    parts: List[tuple[str, bool]] = []
    lines = text.split("\n")
    in_code_block = False
    current_block_lines: List[str] = []

    for line in lines:
        if line.strip().startswith("```"):
            if not in_code_block:
                if current_block_lines:
                    parts.append(("\n".join(current_block_lines), False))
                    current_block_lines = []
                in_code_block = True
                current_block_lines.append(line)
            else:
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
    for pattern, replacement in get_all_patterns():
        if VERBOSE:
            for m in re.finditer(pattern, text):
                print(f"[CONVERT] Pattern '{pattern.pattern}' matched: '{m.group()}' -> '{replacement}'")
        text = re.sub(pattern, replacement, text)
    return text


def convert(content: str) -> str:
    metadata, body = parse_frontmatter(content)

    normalized_metadata = normalize_frontmatter(metadata)
    frontmatter_str = dump_frontmatter(normalized_metadata)

    if frontmatter_str:
        full_text = frontmatter_str + body
    else:
        full_text = body

    parts = split_code_blocks(full_text)
    if VERBOSE:
        print(f"[CONVERT] Input: {len(content)} chars, {len(parts)} parts")
    result_parts: List[str] = []

    for part, is_code_block in parts:
        if is_code_block:
            result_parts.append(part)
        else:
            result_parts.append(transform_text(part))

    converted = "\n".join(result_parts)
    result = CONVERSION_HEADER + converted
    if VERBOSE:
        print(f"[CONVERT] Output: {len(result)} chars")
    return result


def convert_file(input_path: str, output_path: Optional[str] = None) -> str:
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    converted = convert(content)

    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(converted)
        return output_path

    return converted
