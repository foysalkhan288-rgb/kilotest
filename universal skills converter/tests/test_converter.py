"""Tests for the converter module."""

import pytest
from usc.converter import convert, convert_file, split_code_blocks, transform_text, CONVERSION_HEADER


class TestSplitCodeBlocks:
    """Tests for split_code_blocks function."""

    def test_split_code_blocks_simple(self):
        """Text with no code blocks returns single tuple with is_code_block=False."""
        text = "Hello world"
        result = split_code_blocks(text)
        assert result == [("Hello world", False)]

    def test_split_code_blocks_single(self):
        """Text with one fenced code block splits correctly."""
        text = "Hello\n```python\ncode\n```\nWorld"
        result = split_code_blocks(text)
        assert len(result) == 3
        assert result[0] == ("Hello", False)
        assert result[1] == ("```python\ncode\n```", True)
        assert result[2] == ("World", False)

    def test_split_code_blocks_multiple(self):
        """Multiple code blocks split correctly."""
        text = "A\n```\ncode1\n```\nB\n```\ncode2\n```\nC"
        result = split_code_blocks(text)
        assert len(result) == 5
        assert result[0] == ("A", False)
        assert result[1] == ("```\ncode1\n```", True)
        assert result[2] == ("B", False)
        assert result[3] == ("```\ncode2\n```", True)
        assert result[4] == ("C", False)

    def test_split_code_blocks_no_language(self):
        """Code block without language specifier."""
        text = "Hello\n```\ncode\n```\nWorld"
        result = split_code_blocks(text)
        assert len(result) == 3
        assert result[1] == ("```\ncode\n```", True)


class TestTransformText:
    """Tests for transform_text function."""

    def test_transform_text_tool_names(self):
        """'Claude Code' becomes 'your AI assistant'."""
        assert transform_text("Claude Code") == "your AI assistant"

    def test_transform_text_commands(self):
        """'claude --flag' becomes ''."""
        assert transform_text("claude --flag") == ""

    def test_transform_text_paths(self):
        """'~/.claude/skills/' becomes ''."""
        assert transform_text("~/.claude/skills/") == ""

    def test_transform_text_models(self):
        """'Opus' becomes 'the best available model'."""
        assert transform_text("Opus") == "the best available model"

    def test_transform_text_builtin_tools(self):
        """'the Edit tool' becomes 'your Edit capability'."""
        assert transform_text("the Edit tool") == "your Edit capability"

    def test_transform_text_ui_hints(self):
        """'Press Cmd+K' becomes ''."""
        assert transform_text("Press Cmd+K") == ""


class TestConvert:
    """Tests for convert function."""

    def test_convert_preserves_code_blocks(self):
        """Content inside ``` is not transformed."""
        content = "Use Claude Code\n```\nclaude --flag\n```"
        result = convert(content)
        assert "Claude Code" not in result
        assert "claude --flag" in result

    def test_convert_adds_header(self):
        """Output starts with conversion header."""
        content = "Hello"
        result = convert(content)
        assert result.startswith(CONVERSION_HEADER)


class TestConvertFile:
    """Tests for convert_file function."""

    def test_convert_file(self, tmp_path):
        """Reads input, writes output, returns path."""
        input_file = tmp_path / "input.md"
        input_file.write_text("Hello world")
        output_file = tmp_path / "output.md"
        result = convert_file(str(input_file), str(output_file))
        assert result == str(output_file)
        assert output_file.exists()
        assert output_file.read_text().startswith(CONVERSION_HEADER)

    def test_convert_file_no_output(self, tmp_path):
        """Returns string when no output_path."""
        input_file = tmp_path / "input.md"
        input_file.write_text("Hello world")
        result = convert_file(str(input_file))
        assert isinstance(result, str)
        assert result.startswith(CONVERSION_HEADER)
