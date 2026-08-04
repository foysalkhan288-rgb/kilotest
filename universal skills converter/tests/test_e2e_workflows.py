"""End-to-end integration tests covering full user workflows."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from usc.cli import cli
from usc.converter import CONVERSION_HEADER, convert, convert_file
from usc.frontmatter import parse_frontmatter, normalize_frontmatter, dump_frontmatter
from usc.installer import install_skill
from usc.validator import validate_skill


class TestFullCLIWorkflow:
    """Simulate complete user workflows through the CLI."""

    def test_convert_check_install_workflow(self, tmp_path):
        """Full workflow: create skill, convert, validate, install."""
        skill_content = """---
name: Test Workflow Skill
description: Tests the full workflow
allowed-tools: [Read, Edit]
---

# Test Workflow Skill

Use Claude Code for this.
claude --dangerously-skip-permissions
Model: Opus.
Path: ~/.claude/skills/test-workflow.md
"""
        source = tmp_path / "workflow.md"
        source.write_text(skill_content)

        runner = CliRunner()

        # Step 1: convert to file
        result = runner.invoke(cli, ["convert", str(source), "--target", "opencode", "--output", str(tmp_path / "converted.md")])
        assert result.exit_code == 0, result.output
        converted = (tmp_path / "converted.md").read_text()
        assert "Claude Code" not in converted
        assert "claude --dangerously-skip-permissions" not in converted
        assert "Opus" not in converted
        assert "~/.claude/skills/" not in converted
        assert "allowed-capabilities" in converted

        # Step 2: validate the converted skill
        check_result = runner.invoke(cli, ["check", str(tmp_path / "converted.md"), "--target", "opencode"])
        assert check_result.exit_code == 0, check_result.output
        assert "PASS" in check_result.output

        # Step 3: install
        install_result = runner.invoke(cli, ["convert", str(source), "--target", "opencode", "--install", "--name", "workflow-skill", "--force"])
        assert install_result.exit_code == 0, install_result.output
        assert "Skill installed to:" in install_result.output

    def test_batch_then_check_workflow(self, tmp_path):
        """Batch convert a directory, then validate all outputs."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        out_dir = tmp_path / "converted"
        out_dir.mkdir()

        skill1 = skills_dir / "alpha.md"
        skill1.write_text("# Alpha\nUse Claude Code.\n")
        skill2 = skills_dir / "beta.md"
        skill2.write_text("# Beta\nRun claude --flag\nModel: Sonnet\n")

        runner = CliRunner()
        result = runner.invoke(cli, ["batch", str(skills_dir), "--target", "cursor", "--output-dir", str(out_dir)])
        assert result.exit_code == 0, result.output
        assert "Found 2 skill file(s)." in result.output

        for name in ["alpha.md", "beta.md"]:
            out_file = out_dir / name
            assert out_file.exists(), f"{name} missing"
            content = out_file.read_text()
            assert "Claude Code" not in content
            assert "claude --flag" not in content
            assert "Sonnet" not in content

            check = runner.invoke(cli, ["check", str(out_file), "--target", "cursor"])
            assert check.exit_code == 0, f"Validation failed for {name}: {check.output}"

    def test_init_convert_validate_workflow(self, tmp_path):
        """Create a skill with init, convert it (no-op), and validate it clean."""
        runner = CliRunner()
        out_file = tmp_path / "new-skill.md"

        result = runner.invoke(cli, ["init", "Brand New Skill", "--target", "opencode", "--output", str(out_file)])
        assert result.exit_code == 0, result.output
        assert out_file.exists()

        content = out_file.read_text()
        assert "name: Brand New Skill" in content
        assert "allowed-capabilities" in content

        check = runner.invoke(cli, ["check", str(out_file), "--target", "opencode"])
        assert check.exit_code == 0, check.output
        assert "PASS" in check.output


class TestWebUIFullFlow:
    """End-to-end tests for the web UI using Flask's test client."""

    @pytest.fixture()
    def client(self):
        from webui.app import app
        return app.test_client()

    def test_search_fetch_convert_download_flow(self, client):
        """Simulate the main web UI flow: search → fetch → convert → download."""
        mock_results = [
            {
                "name": "user/claude-skills",
                "url": "https://github.com/user/claude-skills",
                "description": "A collection of Claude Code skills",
                "stars": 42,
            }
        ]

        with patch("webui.app.search_github", return_value=mock_results):
            resp = client.get("/api/search?q=claude+code+prompting&max_results=5")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["results"][0]["name"] == "user/claude-skills"

        with patch("webui.app.fetch", return_value="# Skill\nUse Claude Code.\n"):
            resp = client.post(
                "/api/convert",
                json={"content": "", "target": "opencode", "source": "https://github.com/user/claude-skills"},
            )
        assert resp.status_code == 200
        converted = resp.get_json()["converted"]
        assert "Claude Code" not in converted

    def test_paste_convert_copy_flow(self, client):
        """Simulate paste → convert → copy flow."""
        resp = client.post(
            "/api/convert",
            json={"content": "# Skill\nUse Claude Code.\nRun claude --flag\n", "target": "cursor"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["original_size"] > 0
        assert data["converted_size"] > 0
        assert "Claude Code" not in data["converted"]
        assert "claude --flag" not in data["converted"]
        assert "<!-- Converted by Universal Skills Converter -->" in data["converted"]


class TestRealisticSkillConversion:
    """Test conversion with realistic, complex skill content."""

    def test_realistic_claude_code_skill(self):
        """Convert a skill that looks like a real Claude Code community skill."""
        skill = """---
name: advanced-prompting
description: Advanced prompting techniques
allowed-tools: [Read, Edit, Bash]
model: claude-3-opus
---

# Advanced Prompting Skill

This skill helps Claude Code write better prompts using Opus.

## Instructions

1. Use the Read tool to examine the current file
2. Use the Edit tool to make changes
3. Run tests with Bash: `claude --test`
4. Save results to ~/.claude/skills/advanced-prompting/

## Tips

- Always use Opus for best results
- Use subagents for complex tasks
- Check permissions before running

```bash
# Example
claude --dangerously-skip-permissions
```
"""
        result = convert(skill)

        assert "Claude Code" not in result
        assert "claude-3-opus" not in result
        assert "Opus" not in result
        assert "Read tool" not in result
        assert "Edit tool" not in result
        assert "your Bash capability" in result
        assert "claude --dangerously-skip-permissions" in result
        assert "claude --test" not in result
        assert "~/.claude/skills/" not in result
        assert "allowed-capabilities" in result
        assert "name: advanced-prompting" in result

    def test_realistic_cursor_skill(self):
        """Convert a skill that references Cursor-specific features."""
        skill = """---
name: cursor-refactor
description: Refactoring skill for Cursor
---

# Cursor Refactor Skill

Use Cursor's Composer feature to refactor code.
Press Cmd+K to activate.
Use the Tab tool for autocomplete.
"""
        result = convert(skill)

        assert "Cursor" not in result
        assert "your AI assistant's" in result
        assert "Cmd+K" not in result

    def test_multiple_frontmatter_fields_normalized(self):
        """Verify all frontmatter fields are correctly normalized."""
        raw = """---
name: test
description: A test skill
model: gpt-4o
allowed-tools: [Read, Write]
claude-specific-field: value
version: 1.0
---
Body"""
        metadata, body = parse_frontmatter(raw)
        normalized = normalize_frontmatter(metadata, source_tool="claude-code")
        assert "model" not in normalized
        assert "claude-specific-field" not in normalized
        assert normalized.get("allowed-capabilities") == ["Read", "Write"]
        assert normalized.get("version") == 1.0
        assert normalized.get("name") == "test"

        dumped = dump_frontmatter(normalized)
        assert "model:" not in dumped
        assert "claude-specific-field:" not in dumped
        assert "allowed-capabilities:" in dumped


class TestValidatorEndToEnd:
    """End-to-end validator tests with realistic content."""

    def test_validate_dirty_skill_reports_all_categories(self):
        """Validator finds references across all pattern categories."""
        skill = """
# Skill
Use Claude Code.
Run claude --flag
Path: ~/.claude/skills/
Model: Opus
Use the Edit tool.
Press Cmd+K
"""
        report = validate_skill(skill, strict=False)
        assert report["total_references"] >= 5
        assert report["score"] < 80
        assert report["is_clean"] is False

    def test_validate_clean_skill_after_conversion(self):
        """Skill is clean after conversion."""
        dirty = "Use Claude Code.\nRun claude --flag\n"
        clean = convert(dirty)
        report = validate_skill(clean, strict=False)
        assert report["is_clean"] is True
        assert report["score"] == 100

    def test_validate_with_tool_filter_finds_correct_references(self):
        """Validator with --target only finds references for that tool."""
        skill = """
# Skill
Use Claude Code.
Use Cursor.
Path: ~/.claude/skills/
Path: ~/.cursor/skills/
"""
        claude_report = validate_skill(skill, strict=False, tools=["claude-code"])
        assert claude_report["total_references"] >= 2

        cursor_report = validate_skill(skill, strict=False, tools=["cursor"])
        assert cursor_report["total_references"] >= 2

    def test_validate_strict_mode_fails_on_single_reference(self):
        """Strict mode fails even for a single reference."""
        skill = "Use Claude Code."
        report = validate_skill(skill, strict=True)
        assert report["is_clean"] is False
        assert report["total_references"] == 1

    def test_validate_json_output_has_required_fields(self):
        """JSON output contains all required report fields."""
        skill = "Use Claude Code."
        report = validate_skill(skill, strict=False)
        assert "score" in report
        assert "total_references" in report
        assert "findings" in report
        assert "is_clean" in report
        assert "recommendation" in report
        for finding in report["findings"]:
            assert "pattern_type" in finding
            assert "matched_text" in finding
            assert "line_number" in finding
            assert "context" in finding
            assert finding["line_number"] > 0


class TestConfigIntegration:
    """Integration tests for the config system."""

    def test_custom_patterns_are_applied(self, tmp_path):
        """Custom patterns from config are applied during conversion."""
        import tempfile
        import os

        config_content = """
patterns:
  - regex: '\\bSecretTool\\b'
    replacement: 'your AI assistant'
"""
        config_file = tmp_path / ".usc.yaml"
        config_file.write_text(config_content)

        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        try:
            from usc.config import load_config, get_custom_patterns, merge_patterns
            from usc.patterns.base import get_all_patterns

            config = load_config()
            custom = get_custom_patterns(config)
            all_patterns = merge_patterns(get_all_patterns(), custom)

            text = "Use SecretTool for this task."
            for pattern, replacement in all_patterns:
                text = pattern.sub(replacement, text)

            assert "SecretTool" not in text
            assert "your AI assistant" in text
        finally:
            os.chdir(original_cwd)


class TestEdgeCases:
    """Edge case tests for robustness."""

    def test_empty_input_conversion(self):
        """Empty string converts without error."""
        result = convert("")
        assert CONVERSION_HEADER in result

    def test_only_code_blocks(self):
        """Content with only code blocks is returned unchanged except header."""
        content = "```bash\nclaude --flag\n```"
        result = convert(content)
        assert "claude --flag" in result
        assert "Claude Code" not in result

    def test_nested_code_blocks(self):
        """Nested code blocks are handled correctly."""
        content = """
# Outer
```
inner code
```
More text.
```
another block
```
"""
        result = convert(content)
        assert "inner code" in result
        assert "another block" in result

    def test_frontmatter_only(self):
        """File with only frontmatter converts correctly."""
        content = """---
name: test
description: test
---
"""
        result = convert(content)
        assert "---" in result
        assert "name: test" in result

    def test_unicode_content(self):
        """Unicode content survives conversion."""
        content = "# Skill\nUse Claude Code.\n日本語\n🎉"
        result = convert(content)
        assert "日本語" in result
        assert "🎉" in result
        assert "Claude Code" not in result

    def test_very_long_lines(self):
        """Very long lines are handled correctly."""
        content = "# Skill\n" + "Use Claude Code. " * 1000
        result = convert(content)
        assert "Claude Code" not in result

    def test_multiple_tool_references_in_one_line(self):
        """Multiple tool references in one line are all converted."""
        content = "Use Claude Code with Opus model at ~/.claude/skills/."
        result = convert(content)
        assert "Claude Code" not in result
        assert "Opus" not in result
        assert "~/.claude/skills/" not in result

    def test_case_insensitive_tool_names(self):
        """Tool names are matched case-insensitively."""
        content = "use claude code\nUse CLAUDE CODE\nUse Claude code"
        result = convert(content)
        assert "claude code" not in result.lower()

    def test_conversion_preserves_markdown_structure(self):
        """Markdown headings, lists, links are preserved."""
        content = """# Title

## Subtitle

- List item 1
- List item 2

[Bold text](http://example.com)

> Blockquote

| Table | Header |
|-------|--------|
| Cell  | Value  |
"""
        result = convert(content)
        assert "# Title" in result
        assert "## Subtitle" in result
        assert "- List item 1" in result
        assert "[Bold text](http://example.com)" in result
        assert "> Blockquote" in result
        assert "| Table | Header |" in result
