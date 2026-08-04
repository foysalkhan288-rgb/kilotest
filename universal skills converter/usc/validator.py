"""Validation module for checking tool-specific references in skills."""

import re
from typing import Optional

from usc.patterns.base import PATTERN_CATEGORIES

# Map category names to the pattern types used in findings
CATEGORY_TO_TYPE = {
    'TOOL_NAMES': 'tool_name',
    'COMMANDS': 'command',
    'PATHS': 'path',
    'MODELS': 'model',
    'BUILTIN_TOOLS': 'builtin_tool',
    'BUILTIN_TOOLS_BARE': 'builtin_tool',
    'UI_HINTS': 'ui_hint',
}

# Patterns to skip (lines that start with # or are inside code blocks)
_CODE_BLOCK_MARKER = re.compile(r'^```')


def _split_outside_code_blocks(text: str) -> list[tuple[str, bool]]:
    """Split text into chunks that are either code blocks or normal text."""
    lines = text.split('\n')
    chunks: list[tuple[str, bool]] = []
    in_code_block = False
    current_chunk: list[str] = []

    for line in lines:
        if _CODE_BLOCK_MARKER.match(line.strip()):
            if current_chunk:
                chunks.append(('\n'.join(current_chunk), not in_code_block))
                current_chunk = []
            in_code_block = not in_code_block
            current_chunk.append(line)
        else:
            current_chunk.append(line)

    if current_chunk:
        chunks.append(('\n'.join(current_chunk), not in_code_block))

    return chunks


def find_tool_specific_references(
    text: str,
    tools: Optional[list[str]] = None,
) -> list[dict]:
    """Scan text for tool-specific patterns.

    Returns list of findings: {pattern_type, matched_text, line_number, context}.
    """
    findings: list[dict] = []

    chunks = _split_outside_code_blocks(text)
    document_line_offset = 0

    for chunk, is_normal in chunks:
        if not is_normal:
            document_line_offset += chunk.count('\n')
            continue

        lines = chunk.split('\n')
        for line_number_relative, line in enumerate(lines, start=1):
            absolute_line_number = document_line_offset + line_number_relative
            matched_in_tool_names = False

            for category_name, pattern, _ in PATTERN_CATEGORIES:
                if tools is not None and category_name == 'TOOL_NAMES':
                    tool_set = set(t.lower() for t in tools)
                    for match in pattern.finditer(line):
                        matched_text = match.group(0)
                        if matched_text.lower() in tool_set:
                            findings.append({
                                'pattern_type': CATEGORY_TO_TYPE[category_name],
                                'matched_text': matched_text,
                                'line_number': absolute_line_number,
                                'context': line.strip(),
                            })
                            matched_in_tool_names = True
                            break
                    if matched_in_tool_names:
                        break
                    continue

                for match in pattern.finditer(line):
                    findings.append({
                        'pattern_type': CATEGORY_TO_TYPE[category_name],
                        'matched_text': match.group(0),
                        'line_number': absolute_line_number,
                        'context': line.strip(),
                    })

        document_line_offset += chunk.count('\n')

    return findings


def validate_skill(content: str, strict: bool = False, tools: list[str] | None = None) -> dict:
    """Run validation on skill content and return a report dict.

    Report schema:
        {
            'score': int,            # 0-100
            'total_references': int, # number of findings
            'findings': list[dict],
            'is_clean': bool,        # score >= 80 (or strict mode: no findings)
            'recommendation': str,
        }
    """
    findings = find_tool_specific_references(content, tools=tools)
    total = len(findings)
    score = max(0, 100 - (total * 10))

    if strict:
        is_clean = total == 0
    else:
        is_clean = score >= 80

    if is_clean:
        recommendation = "Skill is clean — no tool-specific references detected."
    else:
        recommendation = (
            f"Skill contains {total} tool-specific reference(s). "
            "Review and replace with universal language before distributing."
        )

    return {
        'score': score,
        'total_references': total,
        'findings': findings,
        'is_clean': is_clean,
        'recommendation': recommendation,
    }


def format_validation_report(report: dict) -> str:
    """Format a validation report as a human-readable string."""
    lines: list[str] = []
    lines.append("=" * 50)
    lines.append("  Universal Skills Converter — Validation Report")
    lines.append("=" * 50)
    lines.append("")

    status = "PASS" if report['is_clean'] else "FAIL"
    lines.append(f"  Status:       {status}")
    lines.append(f"  Score:        {report['score']}/100")
    lines.append(f"  References:   {report['total_references']}")
    lines.append("")

    if report['findings']:
        lines.append("  Findings:")
        lines.append("  " + "-" * 46)
        for finding in report['findings']:
            lines.append(
                f"    [{finding['pattern_type']}] "
                f"Line {finding['line_number']}: "
                f"{finding['matched_text']!r}"
            )
            lines.append(f"      Context: {finding['context']}")
        lines.append("  " + "-" * 46)
    else:
        lines.append("  No tool-specific references found.")

    lines.append("")
    lines.append(f"  Recommendation: {report['recommendation']}")
    lines.append("=" * 50)

    return '\n'.join(lines)
