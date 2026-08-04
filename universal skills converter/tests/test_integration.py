"""Integration tests for the universal skills converter."""

from unittest.mock import patch

import pytest

from usc.converter import CONVERSION_HEADER, convert, convert_file
from usc.installer import install_skill


class TestEndToEndConvertLocalFile:
    """End-to-end conversion of a local skill file."""

    def test_end_to_end_convert_local_file(self, tmp_path):
        """Create a temp skill file with tool references, convert it, verify no tool names remain."""
        skill_content = """# My Skill
Use Claude Code.
claude --flag
~/.claude/skills/
"""
        input_file = tmp_path / "skill.md"
        input_file.write_text(skill_content)
        output_file = tmp_path / "converted.md"

        result = convert_file(str(input_file), str(output_file))
        converted = output_file.read_text()

        assert result == str(output_file)
        assert "Claude Code" not in converted
        assert "claude --flag" not in converted
        assert "~/.claude/skills/" not in converted
        assert converted.startswith(CONVERSION_HEADER)


class TestEndToEndInstall:
    """End-to-end conversion and installation."""

    def test_end_to_end_install(self, tmp_path):
        """Convert and install to a temp skills directory."""
        skill_content = "# Test Skill\nUse Claude Code"
        source_file = tmp_path / "source.md"
        source_file.write_text(skill_content)

        converted = convert_file(str(source_file))

        skills_dir = tmp_path / "skills"

        with patch("usc.installer.get_tool", return_value={"skills_dir": str(skills_dir)}):
            dest = install_skill(converted, "Test Skill", "claude-code", force=True)

        assert dest == str(skills_dir / "test-skill.md")
        assert (skills_dir / "test-skill.md").read_text() == converted


class TestCodeBlockPreservedInConversion:
    """Verify code blocks are preserved during conversion."""

    def test_code_block_preserved_in_conversion(self):
        """Verify code blocks with tool commands are preserved."""
        content = """# Guide
Use Claude Code.
```
claude --flag
```
"""
        result = convert(content)
        assert "Claude Code" not in result
        assert "claude --flag" in result
