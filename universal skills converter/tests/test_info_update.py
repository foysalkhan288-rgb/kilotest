"""Tests for the CLI info and update commands."""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from usc.cli import cli
from usc.converter import convert as convert_skill


class TestInfoCommand:
    """Tests for the info command."""

    def test_info_shows_frontmatter(self, tmp_path, capsys):
        skill = tmp_path / "skill.md"
        skill.write_text("---\ntitle: Test Skill\ndescription: A test\n---\nBody content")
        with pytest.raises(SystemExit) as exc_info:
            cli(["info", str(skill)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "title: Test Skill" in captured.out
        assert "Body size:" in captured.out

    def test_info_shows_validation_score(self, tmp_path, capsys):
        skill = tmp_path / "skill.md"
        skill.write_text("# Clean Skill\nUse your AI assistant.")
        with pytest.raises(SystemExit) as exc_info:
            cli(["info", str(skill)])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Score:" in captured.out
        assert "CLEAN" in captured.out

    def test_info_with_target(self, tmp_path, capsys):
        skill = tmp_path / "skill.md"
        skill.write_text("# Skill\nUse Claude Code.")
        with pytest.raises(SystemExit) as exc_info:
            cli(["info", str(skill), "--target", "opencode"])
        assert exc_info.value.code == 0

    def test_info_missing_file_exits(self):
        with pytest.raises(SystemExit) as exc_info:
            cli(["info", "/nonexistent/path.md"])
        assert exc_info.value.code == 1


class TestUpdateCommand:
    """Tests for the update command."""

    def test_update_requires_source_or_force(self, tmp_path):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        skill = skill_dir / "my-skill.md"
        skill.write_text("# Skill")

        with patch("usc.cli.detect_tool", return_value="claude-code"):
            with patch("usc.cli.get_tool", return_value={"skills_dir": str(skill_dir)}):
                with pytest.raises(SystemExit) as exc_info:
                    cli(["update", "my-skill"])
        assert exc_info.value.code == 1

    def test_update_with_source_url(self, tmp_path):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()
        skill = skill_dir / "my-skill.md"
        skill.write_text("# Old Skill")

        new_content = "# New Skill\nUse your AI assistant."

        with patch("usc.cli.detect_tool", return_value="claude-code"):
            with patch("usc.cli.get_tool", return_value={"skills_dir": str(skill_dir)}):
                with patch("usc.cli.fetch", return_value=new_content):
                    with pytest.raises(SystemExit) as exc_info:
                        cli(["update", "my-skill", "--source", "https://github.com/user/repo"])
        assert exc_info.value.code == 0
        expected = convert_skill(new_content)
        assert skill.read_text() == expected

    def test_update_missing_skill_exits(self, tmp_path):
        skill_dir = tmp_path / "skills"
        skill_dir.mkdir()

        with patch("usc.cli.detect_tool", return_value="claude-code"):
            with patch("usc.cli.get_tool", return_value={"skills_dir": str(skill_dir)}):
                with pytest.raises(SystemExit) as exc_info:
                    cli(["update", "missing-skill"])
        assert exc_info.value.code == 1
