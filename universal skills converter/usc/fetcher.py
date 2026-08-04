from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests


def is_github_url(text: str) -> bool:
    """Return True if text is a GitHub HTTPS URL."""
    return text.startswith("https://github.com/") or text.startswith("https://raw.githubusercontent.com/")


def is_local_file(text: str) -> bool:
    """Return True if text points to an existing file on disk."""
    return os.path.isfile(text)


def is_stdin() -> bool:
    """Return True if stdin has piped data (not a TTY)."""
    return not sys.stdin.isatty()


def _parse_github_url(url: str) -> tuple[str, str, str | None, str | None]:
    parsed = urlparse(url)

    if parsed.hostname == "raw.githubusercontent.com":
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 3:
            raise ValueError(f"Invalid raw.githubusercontent.com URL: {url}")
        owner, repo = parts[0], parts[1]
        ref = parts[2] if len(parts) > 2 else None
        path = "/".join(parts[3:]) if len(parts) > 3 else ""
        return owner, repo, ref, path

    if parsed.hostname == "github.com":
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        owner, repo = parts[0], parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        tree_match = re.search(r"(?:tree|blob)/([^/]+)(?:/(.*))?", url)
        if tree_match:
            ref = tree_match.group(1)
            path = tree_match.group(2) or ""
        else:
            ref = None
            path = "/".join(parts[2:]) if len(parts) > 2 else ""
        return owner, repo, ref, path

    raise ValueError(f"Not a GitHub URL: {url}")


def _search_skill_files(root: Path) -> list[Path]:
    candidates: list[Path] = []

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        name = p.name
        if name in ("SKILL.md", "skill.md"):
            candidates.append(p)
        elif name.endswith(".skill.md"):
            candidates.append(p)
        elif p.parts and p.parent.name == "skills" and name.endswith(".md"):
            candidates.append(p)

    return candidates


def fetch_github(url: str) -> str:
    """Fetch a skill file from a GitHub repository URL."""
    owner, repo, ref, path = _parse_github_url(url)

    if url.startswith("https://raw.githubusercontent.com/"):
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.text

    headers: dict[str, str] = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}" if path else f"https://api.github.com/repos/{owner}/{repo}/contents/"
    if ref:
        api_url += f"?ref={ref}"

    response = requests.get(api_url, headers=headers, timeout=30)

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            candidates = []
            for item in data:
                if item.get("type") != "file":
                    continue
                file_name = item.get("name", "")
                file_path = item.get("path", "")
                if file_name in ("SKILL.md", "skill.md") or file_name.endswith(".skill.md") or (
                    "skills" in file_path.split("/") and file_name.endswith(".md")
                ):
                    candidates.append(Path(file_path))
            if candidates:
                file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref or 'main'}/" + str(candidates[0])
                file_response = requests.get(file_url, timeout=30)
                file_response.raise_for_status()
                return file_response.text
            with tempfile.TemporaryDirectory() as tmpdir:
                clone_url = f"https://github.com/{owner}/{repo}.git"
                clone_result = subprocess.run(
                    ["git", "clone", "--depth", "1", clone_url, tmpdir],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if clone_result.returncode != 0:
                    raise ValueError(
                        f"Git clone failed for {owner}/{repo}: {clone_result.stderr}"
                    )
                root = Path(tmpdir)
                if ref:
                    subprocess.run(
                        ["git", "checkout", ref],
                        cwd=tmpdir,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                candidates = _search_skill_files(root)
                if not candidates:
                    raise ValueError(f"No skill file found in repository {owner}/{repo}")
                return candidates[0].read_text(encoding="utf-8")
        elif isinstance(data, dict) and data.get("type") == "file":
            download_url = data.get("download_url")
            if download_url:
                file_response = requests.get(download_url, timeout=30)
                file_response.raise_for_status()
                return file_response.text
            content = data.get("content", "")
            encoding = data.get("encoding", "base64")
            if encoding == "base64":
                import base64
                return base64.b64decode(content).decode("utf-8", errors="replace")
            return content

    if response.status_code == 403:
        rate_remaining = response.headers.get("X-RateLimit-Remaining", "unknown")
        raise ValueError(
            f"GitHub API rate limit exceeded (remaining: {rate_remaining}). "
            f"Set GITHUB_TOKEN to increase limits."
        )
    if response.status_code == 404:
        with tempfile.TemporaryDirectory() as tmpdir:
            clone_url = f"https://github.com/{owner}/{repo}.git"
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, tmpdir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if clone_result.returncode != 0:
                raise ValueError(
                    f"Git clone failed for {owner}/{repo}: {clone_result.stderr}"
                )
            root = Path(tmpdir)
            if ref:
                subprocess.run(
                    ["git", "checkout", ref],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            candidates = _search_skill_files(root)
            if not candidates:
                raise ValueError(f"No skill file found in repository {owner}/{repo}")
            return candidates[0].read_text(encoding="utf-8")

    raise ValueError(
        f"Failed to fetch from GitHub API for {owner}/{repo}: {response.status_code} {response.text}"
    )


def fetch_local(path: str) -> str:
    """Read and return the content of a local file."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"Local file not found: {file_path}")
    return file_path.read_text(encoding="utf-8")


def fetch_stdin() -> str:
    """Read and return all content from stdin."""
    return sys.stdin.read()


def fetch(source: str) -> str:
    """Auto-detect the source type and fetch the skill content."""
    if is_github_url(source):
        return fetch_github(source)
    if is_local_file(source):
        return fetch_local(source)
    if is_stdin():
        return fetch_stdin()
    raise ValueError(
        f"Unable to detect source type for: {source}\n"
        "Expected a GitHub URL, local file path, or piped stdin."
    )
