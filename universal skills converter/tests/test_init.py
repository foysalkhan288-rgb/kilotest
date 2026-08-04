"""Tests for the CLI init command."""

import sys
from io import StringIO
from unittest.mock import patch

import pytest

from usc.cli import cli


class TestInitCommand:
    """Tests for the init command."""

    def test_init_creates_skill_content(self, capsys):
        """init command outputs a skill template with frontmatter."""
        with pytest.raises(SystemExit) as exc_info:
            cli(["init", "My Test Skill"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "name: My Test Skill" in captured.out
        assert "# My Test Skill" in captured.out
        assert "description: Universal skill" in captured.out
        assert "allowed-capabilities: []" in captured.out

    def test_init_with_target_adds_tool_name(self, capsys):
        """init command includes tool name in description when --target is given."""
        with pytest.raises(SystemExit) as exc_info:
            cli(["init", "My Skill", "--target", "opencode"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "OpenCode" in captured.out

    def test_init_with_output_writes_file(self, tmp_path):
        """init command writes to file when --output is given."""
        output_file = tmp_path / "my-skill.md"
        with pytest.raises(SystemExit) as exc_info:
            cli(["init", "My Skill", "--output", str(output_file)])
        assert exc_info.value.code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "name: My Skill" in content
        assert "# My Skill" in content

    def test_init_sanitizes_name_for_filename(self, tmp_path):
        """init command sanitizes the skill name for use as filename."""
        output_file = tmp_path / "my-skill.md"
        with pytest.raises(SystemExit) as exc_info:
            cli(["init", "My Skill!", "--output", str(output_file)])
        assert exc_info.value.code == 0
        assert output_file.exists()

    def test_init_invalid_name_exits(self):
        """init command exits with error for invalid names."""
        with pytest.raises(SystemExit) as exc_info:
            cli(["init", ""])
        assert exc_info.value.code == 1
