"""Tests for the frontmatter module."""

from usc.frontmatter import (
    dump_frontmatter,
    normalize_frontmatter,
    parse_frontmatter,
    strip_frontmatter,
)


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_parse_frontmatter_simple(self):
        """Basic YAML frontmatter is parsed correctly."""
        text = "---\ntitle: My Skill\ndescription: A test skill\n---\nHello world"
        metadata, body = parse_frontmatter(text)
        assert metadata == {"title": "My Skill", "description": "A test skill"}
        assert body == "Hello world"

    def test_parse_frontmatter_none(self):
        """Text without frontmatter returns None and original text."""
        text = "Hello world"
        metadata, body = parse_frontmatter(text)
        assert metadata is None
        assert body == "Hello world"

    def test_parse_frontmatter_nested(self):
        """Nested YAML structures are handled."""
        text = "---\nmetadata:\n  author: Test\n  version: 1.0\n---\nBody"
        metadata, body = parse_frontmatter(text)
        assert metadata == {"metadata": {"author": "Test", "version": 1.0}}
        assert body == "Body"

    def test_parse_frontmatter_malformed(self):
        """Malformed frontmatter returns None gracefully."""
        text = "---\n{invalid yaml\n---\nBody"
        metadata, body = parse_frontmatter(text)
        assert metadata is None
        assert body == "Body"

    def test_parse_frontmatter_only_closing(self):
        """Missing opening delimiter returns None."""
        text = "Body\n---\n---\n"
        metadata, body = parse_frontmatter(text)
        assert metadata is None


class TestStripFrontmatter:
    """Tests for strip_frontmatter function."""

    def test_strip_frontmatter(self):
        """Frontmatter is removed, body remains."""
        text = "---\ntitle: My Skill\n---\nHello world"
        result = strip_frontmatter(text)
        assert result == "Hello world"

    def test_strip_frontmatter_none(self):
        """No frontmatter returns original text."""
        text = "Hello world"
        result = strip_frontmatter(text)
        assert result == "Hello world"


class TestNormalizeFrontmatter:
    """Tests for normalize_frontmatter function."""

    def test_normalize_frontmatter_removes_model(self):
        """model field is removed."""
        metadata = {"name": "test", "model": "claude-3-opus"}
        result = normalize_frontmatter(metadata)
        assert "model" not in result
        assert result == {"name": "test"}

    def test_normalize_frontmatter_removes_tool_fields(self):
        """Tool-specific keys containing source_tool name are removed."""
        metadata = {
            "name": "test",
            "claude-model": "opus",
            "allowed-tools": "Edit, Read",
            "description": "A test",
        }
        result = normalize_frontmatter(metadata, source_tool="Claude Code")
        assert "claude-model" not in result
        assert "allowed-tools" not in result
        assert result == {"name": "test", "description": "A test", "allowed-capabilities": "Edit, Read"}

    def test_normalize_frontmatter_renames_allowed_tools(self):
        """allowed-tools is renamed to allowed-capabilities."""
        metadata = {"allowed-tools": "Edit, Read"}
        result = normalize_frontmatter(metadata)
        assert "allowed-tools" not in result
        assert result == {"allowed-capabilities": "Edit, Read"}

    def test_normalize_frontmatter_none_input(self):
        """None input returns None."""
        result = normalize_frontmatter(None)
        assert result is None

    def test_normalize_frontmatter_empty_input(self):
        """Empty dict returns None."""
        result = normalize_frontmatter({})
        assert result is None

    def test_normalize_frontmatter_no_source_tool(self):
        """Without source_tool, only exact matches are removed."""
        metadata = {"name": "test", "allowed-tools": "Read"}
        result = normalize_frontmatter(metadata)
        assert "allowed-tools" not in result
        assert result == {"name": "test", "allowed-capabilities": "Read"}


class TestRoundtrip:
    """Tests for roundtrip: parse -> normalize -> dump."""

    def test_roundtrip(self):
        """Parse, normalize, dump preserves non-tool-specific structure."""
        text = "---\ntitle: My Skill\nversion: 1.0\n---\nHello world"
        metadata, body = parse_frontmatter(text)
        normalized = normalize_frontmatter(metadata)
        dumped = dump_frontmatter(normalized)
        assert dumped == "---\ntitle: My Skill\nversion: 1.0\n---\n"
        assert body == "Hello world"

    def test_roundtrip_full_text(self):
        """Full text roundtrip reconstructs correctly."""
        text = "---\nname: skill\n---\nSome content"
        metadata, body = parse_frontmatter(text)
        normalized = normalize_frontmatter(metadata)
        result = dump_frontmatter(normalized) + body
        assert result == "---\nname: skill\n---\nSome content"

    def test_dump_frontmatter_none(self):
        """dump_frontmatter returns empty string for None."""
        assert dump_frontmatter(None) == ""

    def test_dump_frontmatter_empty(self):
        """dump_frontmatter returns empty string for empty dict."""
        assert dump_frontmatter({}) == ""

    def test_dump_frontmatter_with_values(self):
        """dump_frontmatter serializes dict to YAML."""
        metadata = {"title": "Test", "version": 2}
        result = dump_frontmatter(metadata)
        assert result == "---\ntitle: Test\nversion: 2\n---\n"
