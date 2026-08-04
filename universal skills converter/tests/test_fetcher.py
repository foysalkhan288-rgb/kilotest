"""Tests for the fetcher module."""

from unittest.mock import patch, MagicMock, ANY, call

import pytest

from usc.fetcher import fetch, fetch_github, fetch_local, is_github_url, is_local_file, is_stdin


class TestIsGithubUrl:
    """Tests for is_github_url function."""

    def test_is_github_url(self):
        """True for github.com and raw.githubusercontent.com URLs."""
        assert is_github_url("https://github.com/user/repo") is True
        assert is_github_url("https://raw.githubusercontent.com/user/repo/main/file.md") is True
        assert is_github_url("https://gitlab.com/user/repo") is False
        assert is_github_url("/local/path") is False


class TestIsLocalFile:
    """Tests for is_local_file function."""

    def test_is_local_file(self, tmp_path):
        """True for existing file, false for non-existent."""
        existing = tmp_path / "file.md"
        existing.write_text("content")
        assert is_local_file(str(existing)) is True
        assert is_local_file("/nonexistent/path") is False


class TestIsStdin:
    """Tests for is_stdin function."""

    def test_is_stdin_piped(self):
        """Mock sys.stdin.isatty to return False."""
        with patch("sys.stdin.isatty", return_value=False):
            assert is_stdin() is True

    def test_is_stdin_tty(self):
        """Mock sys.stdin.isatty to return True."""
        with patch("sys.stdin.isatty", return_value=True):
            assert is_stdin() is False


class TestFetchLocal:
    """Tests for fetch_local function."""

    def test_fetch_local(self, tmp_path):
        """Reads file content."""
        file_path = tmp_path / "skill.md"
        file_path.write_text("skill content")
        assert fetch_local(str(file_path)) == "skill content"

    def test_fetch_local_not_found(self):
        """Raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            fetch_local("/nonexistent/path.md")


class TestFetchGithub:
    """Tests for fetch_github function."""

    def test_fetch_github_raw_url(self):
        """Mock requests.get for raw URL."""
        mock_response = MagicMock()
        mock_response.text = "raw content"
        with patch("usc.fetcher.requests.get", return_value=mock_response) as mock_get:
            result = fetch_github("https://raw.githubusercontent.com/user/repo/main/file.md")
        mock_get.assert_called_once()
        assert result == "raw content"

    def test_fetch_github_api_file(self):
        """Mock API returning file dict."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "type": "file",
            "download_url": "https://example.com/file.md",
        }
        mock_file_response = MagicMock()
        mock_file_response.text = "file content"

        with patch("usc.fetcher.requests.get", side_effect=[mock_response, mock_file_response]) as mock_get:
            result = fetch_github("https://github.com/user/repo")
        assert result == "file content"

    def test_fetch_github_api_directory(self):
        """Mock API returning list with skill files."""
        mock_list_response = MagicMock()
        mock_list_response.status_code = 200
        mock_list_response.json.return_value = [
            {"type": "file", "name": "SKILL.md", "path": "skills/SKILL.md"}
        ]
        mock_repo_response = MagicMock()
        mock_repo_response.status_code = 200
        mock_repo_response.json.return_value = {"default_branch": "main"}
        mock_file_response = MagicMock()
        mock_file_response.text = "directory skill content"

        with patch("usc.fetcher.requests.get", side_effect=[mock_list_response, mock_repo_response, mock_file_response]) as mock_get:
            result = fetch_github("https://github.com/user/repo")
        assert result == "directory skill content"

    def test_fetch_github_404_falls_back_to_clone(self):
        """Mock 404 then successful git clone."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_clone_result = MagicMock()
        mock_clone_result.returncode = 0
        mock_clone_result.stderr = ""

        mock_skill_path = MagicMock()
        mock_skill_path.read_text.return_value = "cloned content"

        with patch("usc.fetcher.requests.get", return_value=mock_response) as mock_get, \
             patch("usc.fetcher.subprocess.run", return_value=mock_clone_result) as mock_run, \
             patch("usc.fetcher._search_skill_files", return_value=[mock_skill_path]):
            result = fetch_github("https://github.com/user/repo")

        assert result == "cloned content"
        mock_run.assert_any_call(
            ["git", "clone", "--depth", "1", "https://github.com/user/repo.git", ANY],
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_fetch_github_rate_limit(self):
        """Mock 403 with rate limit header."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {"X-RateLimit-Remaining": "0"}
        mock_response.text = "rate limited"

        with patch("usc.fetcher.requests.get", return_value=mock_response):
            with pytest.raises(ValueError, match="rate limit"):
                fetch_github("https://github.com/user/repo")
