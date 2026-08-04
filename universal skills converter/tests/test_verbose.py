"""Tests for verbose transformation logging."""

import pytest
import usc.converter as converter_module

from usc.converter import convert, set_verbose, transform_text


class TestVerboseLogging:
    """Tests for verbose transformation logging."""

    def setup_method(self):
        self._original_verbose = converter_module.VERBOSE

    def teardown_method(self):
        set_verbose(self._original_verbose)

    def test_verbose_off_no_output(self, capsys):
        """No output when VERBOSE is False."""
        set_verbose(False)
        transform_text("Claude Code")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_verbose_on_logs_transformations(self, capsys):
        """Capture stdout and verify log lines appear."""
        set_verbose(True)
        transform_text("Claude Code")
        captured = capsys.readouterr()
        assert "[CONVERT]" in captured.out
        assert "Pattern" in captured.out
        assert "matched" in captured.out

    def test_set_verbose_toggle(self):
        """Verify flag toggles correctly."""
        set_verbose(True)
        assert converter_module.VERBOSE is True
        set_verbose(False)
        assert converter_module.VERBOSE is False
