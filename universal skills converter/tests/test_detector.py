"""Tests for the detector module."""

import os
from unittest.mock import patch, MagicMock

import pytest

from usc.detector import detect_from_config, detect_running_tool, detect_tool


class TestDetectRunningTool:
    """Tests for detect_running_tool function."""

    def test_detect_running_tool_found(self):
        """Mock psutil to return a matching process."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "claude"}
        with patch("usc.detector.psutil.process_iter", return_value=[mock_proc]):
            result = detect_running_tool()
        assert result == "claude-code"

    def test_detect_running_tool_not_found(self):
        """Mock psutil to return no matches."""
        mock_proc = MagicMock()
        mock_proc.info = {"name": "unknown"}
        with patch("usc.detector.psutil.process_iter", return_value=[mock_proc]):
            result = detect_running_tool()
        assert result is None


class TestDetectFromConfig:
    """Tests for detect_from_config function."""

    def test_detect_from_config_found(self, tmp_path):
        """Create a temp config file, verify detection."""
        config_file = tmp_path / "settings.json"
        config_file.write_text("{}")

        with patch.dict("usc.detector.TOOLS", {
            "test-tool": {
                "config_file": str(config_file),
                "binary": "test"
            }
        }), patch("os.path.isfile", side_effect=lambda p: p == str(config_file)):
            result = detect_from_config()
        assert result == "test-tool"

    def test_detect_from_config_not_found(self):
        """No config files exist."""
        with patch.dict("usc.detector.TOOLS", {
            "test-tool": {
                "config_file": "/nonexistent/path",
                "binary": "test"
            }
        }), patch("os.path.isfile", return_value=False):
            result = detect_from_config()
        assert result is None


class TestDetectTool:
    """Tests for detect_tool function."""

    def test_detect_tool_explicit_target(self):
        """Returns explicit target."""
        with patch.dict("usc.detector.TOOLS", {"claude-code": {}}):
            result = detect_tool("claude-code")
        assert result == "claude-code"

    def test_detect_tool_invalid_target(self):
        """Raises ValueError for unknown tool."""
        with patch.dict("usc.detector.TOOLS", {"claude-code": {}}):
            with pytest.raises(ValueError, match="Unknown tool"):
                detect_tool("invalid-tool")

    def test_detect_tool_auto_fallback(self):
        """Falls back through process then config."""
        with patch.dict("usc.detector.TOOLS", {
            "claude-code": {"binary": "claude", "config_file": "/tmp/c.json"}
        }), patch("usc.detector.detect_running_tool", return_value=None), \
             patch("usc.detector.detect_from_config", return_value="claude-code"):
            result = detect_tool()
        assert result == "claude-code"
