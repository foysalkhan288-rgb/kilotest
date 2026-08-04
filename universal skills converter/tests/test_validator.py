"""Tests for the validator module."""

import pytest

from usc.validator import (
    find_tool_specific_references,
    format_validation_report,
    validate_skill,
)


class TestFindToolSpecificReferences:
    """Tests for find_tool_specific_references."""

    def test_find_tool_specific_references_finds_names(self):
        """Detects 'Claude Code' as a tool-specific reference."""
        text = "Use Claude Code to edit files."
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        types = [f['pattern_type'] for f in findings]
        assert 'tool_name' in types
        matched_texts = [f['matched_text'] for f in findings if f['pattern_type'] == 'tool_name']
        assert any('Claude Code' in t for t in matched_texts)

    def test_find_tool_specific_references_finds_paths(self):
        """Detects '~/.claude/' as a tool-specific path reference."""
        text = "Skills are stored in ~/.claude/skills/."
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        types = [f['pattern_type'] for f in findings]
        assert 'path' in types
        matched_texts = [f['matched_text'] for f in findings if f['pattern_type'] == 'path']
        assert any('.claude' in t for t in matched_texts)

    def test_find_tool_specific_references_ignores_code_blocks(self):
        """Does not flag references inside triple-backtick code blocks."""
        text = "Use Claude Code\n```\nclaude --flag\n~/.claude/\n```\nAnd more text."
        findings = find_tool_specific_references(text)
        for finding in findings:
            assert finding['matched_text'] != 'claude --flag'
            assert '.claude' not in finding['matched_text']

    def test_find_tool_specific_references_finds_models(self):
        """Detects model names like 'Opus'."""
        text = "Use the Opus model for best results."
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        types = [f['pattern_type'] for f in findings]
        assert 'model' in types

    def test_find_tool_specific_references_finds_builtin_tools(self):
        """Detects 'the Edit tool' references."""
        text = "Use the Edit tool to change files."
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        types = [f['pattern_type'] for f in findings]
        assert 'builtin_tool' in types

    def test_find_tool_specific_references_finds_ui_hints(self):
        """Detects UI hints like 'Press Cmd+K'."""
        text = "Press Cmd+K to open the palette."
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        types = [f['pattern_type'] for f in findings]
        assert 'ui_hint' in types

    def test_find_tool_specific_references_finds_commands(self):
        """Detects command-line invocations like 'claude --flag' at line start."""
        text = "Run the following:\nclaude --print --max-turns 10"
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        types = [f['pattern_type'] for f in findings]
        assert 'command' in types

    def test_find_tool_specific_references_line_number(self):
        """Records the correct line number for each finding."""
        text = "Hello\nUse Claude Code\nGoodbye"
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        assert findings[0]['line_number'] == 2

    def test_find_tool_specific_references_context(self):
        """Records surrounding context for each finding."""
        text = "Please use Claude Code now."
        findings = find_tool_specific_references(text)
        assert len(findings) >= 1
        assert findings[0]['context'] == text

    def test_find_tool_specific_references_tools_filter(self):
        """tools parameter restricts which tool names are flagged."""
        text = "Use Claude Code or Cursor."
        findings = find_tool_specific_references(text, tools=["Claude Code"])
        matched_texts = [f['matched_text'] for f in findings if f['pattern_type'] == 'tool_name']
        assert any('Claude Code' in t for t in matched_texts)
        assert not any('Cursor' in t for t in matched_texts)

    def test_find_tool_specific_references_clean_skill(self):
        """Returns empty list for a clean skill."""
        text = "This skill helps you write clean Python code.\n\nUse functions and classes."
        findings = find_tool_specific_references(text)
        assert findings == []

    def test_find_tool_specific_references_multiline(self):
        """Tracks line numbers correctly across multiple lines."""
        text = "First line\nClaude Code here\nThird line\n~/.claude/skills/ here"
        findings = find_tool_specific_references(text)
        line_numbers = [f['line_number'] for f in findings]
        assert 2 in line_numbers
        assert 4 in line_numbers


class TestValidateSkill:
    """Tests for validate_skill."""

    def test_validate_skill_clean_skill(self):
        """High score for a clean skill with no tool-specific references."""
        content = (
            "This skill helps you write clean Python code.\n\n"
            "Use functions and classes.\n"
            "Follow best practices.\n"
        )
        report = validate_skill(content)
        assert report['score'] == 100
        assert report['total_references'] == 0
        assert report['is_clean'] is True
        assert report['findings'] == []

    def test_validate_skill_dirty_skill(self):
        """Low score for a skill with multiple tool-specific references."""
        content = (
            "Use Claude Code to edit files.\n"
            "Run: claude --print --max-turns 10\n"
            "Skills live at ~/.claude/skills/.\n"
            "Use Opus for best results.\n"
        )
        report = validate_skill(content)
        assert report['total_references'] >= 3
        assert report['score'] < 80
        assert report['is_clean'] is False

    def test_validate_skill_strict_mode(self):
        """strict=True marks as not clean even with a single finding."""
        content = "Use Claude Code."
        report = validate_skill(content, strict=True)
        assert report['total_references'] >= 1
        assert report['is_clean'] is False

    def test_validate_skill_strict_mode_clean(self):
        """strict=True marks clean when no findings."""
        content = "This is a clean skill."
        report = validate_skill(content, strict=True)
        assert report['is_clean'] is True
        assert report['score'] == 100

    def test_validate_skill_score_calculation(self):
        """Score is 100 minus 10 per finding, minimum 0."""
        content = (
            "Claude Code\n"
            "claude --print\n"
            "~/.claude/\n"
            "Opus\n"
            "the Edit tool\n"
            "Press Cmd+K\n"
            "Cursor\n"
            "Gemini CLI\n"
            "Sonnet\n"
            "GPT-4o\n"
            "Sonnet again\n"
        )
        report = validate_skill(content)
        assert report['score'] == max(0, 100 - (report['total_references'] * 10))

    def test_validate_skill_score_minimum_zero(self):
        """Score never drops below 0."""
        content = "Claude Code\n" * 20
        report = validate_skill(content)
        assert report['score'] == 0

    def test_validate_skill_report_keys(self):
        """Report dict contains all required keys."""
        content = "Hello world"
        report = validate_skill(content)
        assert 'score' in report
        assert 'total_references' in report
        assert 'findings' in report
        assert 'is_clean' in report
        assert 'recommendation' in report


class TestFormatValidationReport:
    """Tests for format_validation_report."""

    def test_format_validation_report(self):
        """Formats report as a readable string with key sections."""
        report = {
            'score': 60,
            'total_references': 4,
            'findings': [
                {
                    'pattern_type': 'tool_name',
                    'matched_text': 'Claude Code',
                    'line_number': 1,
                    'context': 'Use Claude Code.',
                },
            ],
            'is_clean': False,
            'recommendation': "Review and replace references.",
        }
        output = format_validation_report(report)

        assert "Universal Skills Converter" in output
        assert "Validation Report" in output
        assert "60" in output
        assert "FAIL" in output
        assert "Claude Code" in output
        assert "Line 1" in output
        assert "Review and replace references" in output

    def test_format_validation_report_clean(self):
        """Shows PASS when skill is clean."""
        report = {
            'score': 100,
            'total_references': 0,
            'findings': [],
            'is_clean': True,
            'recommendation': "Skill is clean.",
        }
        output = format_validation_report(report)
        assert "PASS" in output
        assert "No tool-specific references found." in output

    def test_format_validation_report_multiple_findings(self):
        """Lists all findings in the output."""
        report = {
            'score': 70,
            'total_references': 3,
            'findings': [
                {
                    'pattern_type': 'tool_name',
                    'matched_text': 'Claude Code',
                    'line_number': 1,
                    'context': 'Use Claude Code.',
                },
                {
                    'pattern_type': 'path',
                    'matched_text': '~/.claude/',
                    'line_number': 3,
                    'context': 'Found at ~/.claude/.',
                },
            ],
            'is_clean': False,
            'recommendation': "Fix references.",
        }
        output = format_validation_report(report)
        assert output.count('[tool_name]') == 1
        assert output.count('[path]') == 1
        assert "Line 3" in output
