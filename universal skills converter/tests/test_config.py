"""Tests for the config module."""

import os
import re
import tempfile

import pytest

from usc.config import (
    DEFAULT_CONFIG_PATHS,
    get_custom_patterns,
    get_enabled_tools,
    load_config,
    merge_patterns,
)
from usc.patterns.base import PATTERN_CATEGORIES


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_default_paths_returns_empty_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = load_config()
                assert result == {}
            finally:
                os.chdir(original_cwd)

    def test_load_config_finds_project_local(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".usc.yaml")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("patterns: []\n")
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = load_config()
                assert "patterns" in result
            finally:
                os.chdir(original_cwd)

    def test_load_config_finds_global_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".usc.yaml")
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("patterns: []\n")
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = load_config()
                assert "patterns" in result
            finally:
                os.chdir(original_cwd)


class TestGetCustomPatterns:
    """Tests for get_custom_patterns function."""

    def test_get_custom_patterns_empty_config(self):
        result = get_custom_patterns({})
        assert result == []

    def test_get_custom_patterns_missing_key(self):
        result = get_custom_patterns({"other_key": "value"})
        assert result == []

    def test_get_custom_patterns_not_list(self):
        result = get_custom_patterns({"patterns": "not_a_list"})
        assert result == []

    def test_get_custom_patterns_valid_entry(self):
        config = {
            "patterns": [
                {"regex": r"Foo", "replacement": "Bar"},
            ]
        }
        result = get_custom_patterns(config)
        assert len(result) == 1
        assert result[0][1] == "Bar"

    def test_get_custom_patterns_invalid_regex_skipped(self):
        config = {
            "patterns": [
                {"regex": "[invalid", "replacement": "Bar"},
            ]
        }
        result = get_custom_patterns(config)
        assert result == []

    def test_get_custom_patterns_missing_replacement_defaults_empty(self):
        config = {
            "patterns": [
                {"regex": r"Foo"},
            ]
        }
        result = get_custom_patterns(config)
        assert len(result) == 1
        assert result[0][1] == ""

    def test_get_custom_patterns_entry_not_dict(self):
        config = {
            "patterns": ["not_a_dict"],
        }
        result = get_custom_patterns(config)
        assert result == []


class TestGetEnabledTools:
    """Tests for get_enabled_tools function."""

    def test_get_enabled_tools_missing_key(self):
        result = get_enabled_tools({})
        from usc.tools_registry import list_tools

        assert result == list_tools()

    def test_get_enabled_tools_empty_list(self):
        from usc.tools_registry import list_tools

        result = get_enabled_tools({"enabled_tools": []})
        assert result == list_tools()

    def test_get_enabled_tools_valid_filter(self):
        result = get_enabled_tools({"enabled_tools": ["claude-code"]})
        assert result == ["claude-code"]

    def test_get_enabled_tools_invalid_key_ignored(self):
        from usc.tools_registry import list_tools

        result = get_enabled_tools({"enabled_tools": ["nonexistent-tool"]})
        assert result == list_tools()


class TestMergePatterns:
    """Tests for merge_patterns function."""

    def test_merge_patterns_empty(self):
        result = merge_patterns([], [])
        assert result == []

    def test_merge_patterns_combines(self):
        base = [("a", "b")]
        custom = [("c", "d")]
        result = merge_patterns(base, custom)
        assert result == [("a", "b"), ("c", "d")]

    def test_merge_patterns_custom_after_base(self):
        base = [(re.compile("x"), "a")]
        custom = [(re.compile("y"), "b")]
        result = merge_patterns(base, custom)
        assert len(result) == 2
        assert result[0] == base[0]
        assert result[1] == custom[0]
