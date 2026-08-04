"""Tests for the installer module."""

import os
from unittest.mock import patch

import pytest

from usc.installer import get_skills_dir, install_skill, sanitize_name


class TestGetSkillsDir:
    """Tests for get_skills_dir function."""

    def test_get_skills_dir(self, tmp_path):
        """Returns expanded path."""
        with patch("usc.installer.get_tool", return_value={"skills_dir": str(tmp_path)}):
            result = get_skills_dir("claude-code")
        assert result == str(tmp_path)


class TestSanitizeName:
    """Tests for sanitize_name function."""

    def test_sanitize_name(self):
        """Lowercase, spaces to hyphens, special chars removed."""
        assert sanitize_name("My Skill Name") == "my-skill-name"
        assert sanitize_name("Test_Skill 123!") == "test-skill-123"
        assert sanitize_name("  spaces  ") == "spaces"
        assert sanitize_name("UPPERCASE") == "uppercase"
        assert sanitize_name("special!@#chars") == "specialchars"


class TestInstallSkill:
    """Tests for install_skill function."""

    def test_install_skill_creates_file(self, tmp_path):
        """Writes file to temp dir."""
        with patch("usc.installer.get_tool", return_value={"skills_dir": str(tmp_path)}):
            dest = install_skill("# Content", "My Skill", "claude-code")
        assert dest == os.path.join(str(tmp_path), "my-skill.md")
        assert os.path.exists(dest)
        with open(dest, "r", encoding="utf-8") as f:
            assert f.read() == "# Content"

    def test_install_skill_force_overwrites(self, tmp_path):
        """Overwrites existing file when force=True."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        existing = skills_dir / "my-skill.md"
        existing.write_text("old content")

        with patch("usc.installer.get_tool", return_value={"skills_dir": str(skills_dir)}):
            dest = install_skill("new content", "My Skill", "claude-code", force=True)
        assert dest == os.path.join(str(skills_dir), "my-skill.md")
        with open(dest, "r", encoding="utf-8") as f:
            assert f.read() == "new content"

    def test_install_skill_no_force_raises(self, tmp_path):
        """Raises FileExistsError when force=False and file exists."""
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        existing = skills_dir / "my-skill.md"
        existing.write_text("old content")

        with patch("usc.installer.get_tool", return_value={"skills_dir": str(skills_dir)}):
            with pytest.raises(FileExistsError):
                install_skill("new content", "My Skill", "claude-code")
