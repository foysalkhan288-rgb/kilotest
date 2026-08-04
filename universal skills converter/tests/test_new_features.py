"""Tests for new CLI features: version, list-installed, diff, json output."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from usc.cli import cli


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_prints_version(self, capsys):
        """version command prints the package version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["version"])
        assert result.exit_code == 0
        assert "Universal Skills Converter v" in result.output
        assert "0.1.0" in result.output


class TestListInstalledCommand:
    """Tests for the list-installed command."""

    def test_list_installed_no_directory(self, tmp_path, capsys):
        """Lists no skills when directory doesn't exist."""
        runner = CliRunner()
        with patch("usc.cli.detect_tool", return_value="claude-code"):
            with patch("usc.cli.get_tool", return_value={"name": "Claude Code", "skills_dir": str(tmp_path / "nonexistent")}):
                result = runner.invoke(cli, ["list-installed"])
        assert result.exit_code == 0
        assert "No skills directory found" in result.output

    def test_list_installed_with_skills(self, tmp_path, capsys):
        """Lists installed skills."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "skill1.md").write_text("# Skill 1")
        (skills_dir / "skill2.md").write_text("# Skill 2")

        runner = CliRunner()
        with patch("usc.cli.detect_tool", return_value="claude-code"):
            with patch("usc.cli.get_tool", return_value={"name": "Claude Code", "skills_dir": str(skills_dir)}):
                result = runner.invoke(cli, ["list-installed"])
        assert result.exit_code == 0
        assert "skill1" in result.output
        assert "skill2" in result.output

    def test_list_installed_json_output(self, tmp_path, capsys):
        """JSON output contains skills array."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "skill1.md").write_text("# Skill 1")

        runner = CliRunner()
        with patch("usc.cli.detect_tool", return_value="claude-code"):
            with patch("usc.cli.get_tool", return_value={"name": "Claude Code", "skills_dir": str(skills_dir)}):
                result = runner.invoke(cli, ["list-installed", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["tool"] == "claude-code"
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "skill1"


class TestConvertDiffMode:
    """Tests for convert --diff flag."""

    def test_convert_diff_shows_changes(self):
        """diff mode shows unified diff."""
        runner = CliRunner()
        content = "Use Claude Code.\nRun claude --flag\n"
        with patch("usc.cli.detect_tool", return_value="opencode"):
            result = runner.invoke(cli, ["convert", "-", "--diff"], input=content)
        assert result.exit_code == 0
        assert "---" in result.output or "+++" in result.output

    def test_convert_diff_json_output(self):
        """diff mode with --json outputs JSON."""
        runner = CliRunner()
        content = "Use Claude Code.\n"
        with patch("usc.cli.detect_tool", return_value="opencode"):
            result = runner.invoke(cli, ["convert", "-", "--diff", "--json"], input=content)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "diff" in data
        assert "original_size" in data
        assert "converted_size" in data


class TestConvertJsonOutput:
    """Tests for convert --json flag."""

    def test_convert_json_output(self):
        """json mode outputs JSON with converted content."""
        runner = CliRunner()
        content = "Use Claude Code.\n"
        with patch("usc.cli.detect_tool", return_value="opencode"):
            result = runner.invoke(cli, ["convert", "-", "--json"], input=content)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "converted" in data
        assert "original_size" in data
        assert "converted_size" in data
        assert "target" in data
        assert data["target"] == "opencode"
        assert "Claude Code" not in data["converted"]
