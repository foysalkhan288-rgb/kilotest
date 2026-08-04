"""Tests for the batch module."""

from pathlib import Path

import pytest

from usc.batch import batch_convert, find_skill_files, print_batch_results


class TestFindSkillFiles:
    """Tests for find_skill_files function."""

    def test_find_skill_files_single(self, tmp_path):
        """Single .md file is found."""
        skill = tmp_path / "skill.md"
        skill.write_text("Hello world")
        result = find_skill_files([str(skill)])
        assert result == [skill.resolve()]

    def test_find_skill_files_single_non_md(self, tmp_path):
        """Non-markdown file is ignored."""
        skill = tmp_path / "skill.txt"
        skill.write_text("Hello world")
        result = find_skill_files([str(skill)])
        assert result == []

    def test_find_skill_files_directory(self, tmp_path):
        """All .md files in a directory are found."""
        (tmp_path / "a.md").write_text("A")
        (tmp_path / "b.md").write_text("B")
        (tmp_path / "c.txt").write_text("C")
        result = find_skill_files([str(tmp_path)])
        assert len(result) == 2
        assert set(result) == {
            (tmp_path / "a.md").resolve(),
            (tmp_path / "b.md").resolve(),
        }

    def test_find_skill_files_directory_non_recursive(self, tmp_path):
        """Without recursive, only top-level .md files are found."""
        (tmp_path / "a.md").write_text("A")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("B")
        result = find_skill_files([str(tmp_path)], recursive=False)
        assert result == [(tmp_path / "a.md").resolve()]

    def test_find_skill_files_directory_recursive(self, tmp_path):
        """Recursive search finds .md files in subdirectories."""
        (tmp_path / "a.md").write_text("A")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("B")
        subsub = sub / "subsub"
        subsub.mkdir()
        (subsub / "c.md").write_text("C")
        result = find_skill_files([str(tmp_path)], recursive=True)
        assert len(result) == 3
        assert set(result) == {
            (tmp_path / "a.md").resolve(),
            (sub / "b.md").resolve(),
            (subsub / "c.md").resolve(),
        }

    def test_find_skill_files_glob(self, tmp_path):
        """Glob pattern matches .md files."""
        (tmp_path / "a.md").write_text("A")
        (tmp_path / "b.md").write_text("B")
        (tmp_path / "c.txt").write_text("C")
        result = find_skill_files([str(tmp_path / "*.md")])
        assert len(result) == 2
        assert set(result) == {
            (tmp_path / "a.md").resolve(),
            (tmp_path / "b.md").resolve(),
        }

    def test_find_skill_files_glob_recursive(self, tmp_path):
        """Recursive glob pattern matches all .md files."""
        (tmp_path / "a.md").write_text("A")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.md").write_text("B")
        result = find_skill_files([str(tmp_path / "**/*.md")], recursive=True)
        assert len(result) == 2
        assert set(result) == {
            (tmp_path / "a.md").resolve(),
            (sub / "b.md").resolve(),
        }

    def test_find_skill_files_mixed(self, tmp_path):
        """Mix of files, directories, and globs."""
        (tmp_path / "a.md").write_text("A")
        file_b = tmp_path / "b.md"
        file_b.write_text("B")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "c.md").write_text("C")
        result = find_skill_files([str(file_b), str(sub), str(tmp_path / "*.md")])
        assert len(result) == 3
        assert set(result) == {
            file_b.resolve(),
            (sub / "c.md").resolve(),
            (tmp_path / "a.md").resolve(),
        }

    def test_find_skill_files_unique_sorted(self, tmp_path):
        """Duplicate paths are deduplicated and results are sorted."""
        file_a = tmp_path / "a.md"
        file_a.write_text("A")
        result = find_skill_files([str(file_a), str(file_a)])
        assert result == [file_a.resolve()]


class TestBatchConvert:
    """Tests for batch_convert function."""

    def test_batch_convert_multiple(self, tmp_path):
        """Convert multiple markdown files."""
        (tmp_path / "a.md").write_text("Claude Code")
        (tmp_path / "b.md").write_text("claude --flag")
        results = batch_convert([str(tmp_path)], target="opencode")
        assert len(results) == 2
        for r in results:
            assert r["success"] is True
            assert r["error"] is None
            assert r["converted_size"] > 0
            assert r["output"] is not None
            assert Path(r["output"]).exists()
            assert "Claude Code" not in Path(r["output"]).read_text()

    def test_batch_convert_dry_run(self, tmp_path):
        """No files are written during dry run."""
        (tmp_path / "a.md").write_text("Claude Code")
        results = batch_convert([str(tmp_path)], target="opencode", dry_run=True)
        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["output"] is not None
        assert not Path(results[0]["output"]).exists()

    def test_batch_convert_output_dir(self, tmp_path):
        """Files are written to the specified output directory."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "a.md").write_text("Claude Code")
        out_dir = tmp_path / "out"
        results = batch_convert(
            [str(tmp_path / "src")], target="opencode", output_dir=str(out_dir)
        )
        assert len(results) == 1
        assert results[0]["success"] is True
        assert results[0]["output"] == str(out_dir / "a.md")
        assert (out_dir / "a.md").exists()

    def test_batch_convert_no_files(self, tmp_path):
        """Empty input returns empty results."""
        results = batch_convert([str(tmp_path)], target="opencode")
        assert results == []

    def test_batch_convert_force_overwrite(self, tmp_path):
        """Existing output file is overwritten when force=True."""
        (tmp_path / "a.md").write_text("Claude Code")
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        (out_dir / "a.md").write_text("OLD")
        results = batch_convert(
            [str(tmp_path / "a.md")],
            target="opencode",
            output_dir=str(out_dir),
            force=True,
        )
        assert results[0]["success"] is True
        content = (out_dir / "a.md").read_text()
        assert "OLD" not in content

    def test_batch_convert_error_result(self, tmp_path):
        """Errors are captured in result dicts."""
        skill = tmp_path / "skill.md"
        skill.write_text("Hello")
        results = batch_convert([str(skill)], target="opencode", output_dir="/nonexistent/dir")
        assert len(results) == 1
        assert results[0]["success"] is False
        assert results[0]["error"] is not None


class TestPrintBatchResults:
    """Tests for print_batch_results function."""

    def test_print_batch_results_empty(self, capsys):
        """Empty results produce no output."""
        print_batch_results([])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_print_batch_results_with_results(self, capsys):
        """Results are printed as a table."""
        results = [
            {
                "input": "/tmp/a.md",
                "output": "/tmp/out/a.md",
                "success": True,
                "error": None,
                "original_size": 100,
                "converted_size": 80,
            },
            {
                "input": "/tmp/b.md",
                "output": None,
                "success": False,
                "error": "No such file",
                "original_size": 50,
                "converted_size": 0,
            },
        ]
        print_batch_results(results)
        captured = capsys.readouterr()
        assert "/tmp/a.md" in captured.out
        assert "/tmp/out/a.md" in captured.out
        assert "/tmp/b.md" in captured.out
        assert "OK" in captured.out
        assert "ERROR" in captured.out
