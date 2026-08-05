# Universal Skills Converter — Project Summary

**Version:** 0.1.0  
**Python:** 3.10+  
**Test Status:** 159/159 passing  
**Total Files:** 40 source files

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Complete File Structure](#complete-file-structure)
3. [All Commands & Flags](#all-commands--flags)
4. [Architecture](#architecture)
5. [Supported Tools](#supported-tools)
6. [Conversion Patterns](#conversion-patterns)
7. [Test Suite Breakdown](#test-suite-breakdown)
8. [Known Limitations](#known-limitations)
9. [Quick Reference](#quick-reference)

---

## Project Overview

The Universal Skills Converter (`usc`) is a CLI tool that normalizes AI coding assistant skills so they work across different tools. Skills written for Claude Code, Cursor, OpenCode, and others can be converted into a universal format that any supported tool can use.

**Core Flow:** Fetch → Detect → Convert → Install

### Key Features

- **8 supported tools** (Claude Code, Cursor, OpenCode, Codex, Antigravity IDE, Gemini CLI, Windsurf, Aide)
- **GitHub integration** — fetch skills from URLs, search repos, auto-detect default branches
- **YAML frontmatter support** — parse, normalize, and preserve frontmatter
- **Code block preservation** — example commands inside ``` are untouched
- **Batch conversion** — convert entire directories or globs at once
- **Validation engine** — score skills 0-100, find tool-specific references with line numbers
- **Web UI** — Flask-based browser interface
- **Configuration** — custom patterns via YAML config files
- **Multiple output modes** — plain text, JSON, unified diff
- **Verbose logging** — detailed transformation logs

---

## Complete File Structure

```
universal skills converter/
├── .gitignore
├── .kilocode/
│   ├── agent/
│   │   └── default.md
│   ├── command/
│   │   ├── compact.md
│   │   ├── create-new-tool.md
│   │   ├── inline-skill-writer.md
│   │   ├── open-skill.md
│   │   ├── plan-mode.md
│   │   └── ultraplan.md
│   └── rules/
│       └── cloud-agent.md
├── .kilo/
│   ├── agent/
│   │   ├── custom-instructions.md
│   │   ├── product-requirements-document.md
│   │   ├── simple.md
│   │   └── verification-prompt.md
│   ├── commands/
│   │   └── usc/
│   ├── plans/
│   │   └── 1785829630993-universal-skills-converter.md
│   ├── project/
│   │   ├── instructions.md
│   │   └── local-instructions.md
│   └── rules/
│       ├── cloud-agent.md
│       └── coding-style.md
├── LICENSE
├── README.md
├── pyproject.toml
├── universal skills converter/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── converter.py
│   ├── detector.py
│   ├── fetcher.py
│   ├── frontmatter.py
│   ├── installer.py
│   ├── tools_registry.py
│   ├── validator.py
│   ├── batch.py
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── claude_code.py
│   │   ├── opencode.py
│   │   ├── cursor.py
│   │   ├── codex.py
│   │   ├── antigravity.py
│   │   ├── gemini.py
│   │   ├── windsurf.py
│   │   └── aide.py
│   └── webui/
│       ├── __init__.py
│       ├── app.py
│       ├── run.py
│       ├── templates/
│       │   └── index.html
│       └── static/
│           └── style.css
└── tests/
    ├── __init__.py
    ├── test_batch.py
    ├── test_config.py
    ├── test_converter.py
    ├── test_detector.py
    ├── test_fetcher.py
    ├── test_frontmatter.py
    ├── test_info_update.py
    ├── test_init.py
    ├── test_installer.py
    ├── test_integration.py
    ├── test_e2e_workflows.py
    ├── test_new_features.py
    ├── test_validator.py
    └── test_verbose.py
```

---

## All Commands & Flags

### `usc convert <source>`
Convert a skill from GitHub URL, local file, or stdin.

| Flag | Description |
|------|-------------|
| `--target TEXT` | Target tool (e.g., opencode, cursor, claude-code) |
| `--install` | Install to target tool's skills directory |
| `--output PATH` | Write converted skill to file |
| `--force` | Overwrite existing skill file |
| `--dry-run` | Print converted skill without writing |
| `--verbose` | Show detailed transformation logs |
| `--name TEXT` | Custom name for skill file (without .md) |
| `--diff` | Show unified diff of changes |
| `--json` | Output result as JSON |

### `usc init <name>`
Create a new universal skill from a template.

| Flag | Description |
|------|-------------|
| `--target TEXT` | Target tool (optional) |
| `--output PATH` | Write skill to file |

### `usc detect`
Detect the currently active AI coding tool.

### `usc version`
Show the installed version.

### `usc list-tools`
List all supported AI coding tools and their configuration paths.

### `usc list-installed`
List installed skills for a tool.

| Flag | Description |
|------|-------------|
| `--target TEXT` | Target tool (default: auto-detect) |
| `--json` | Output as JSON |

### `usc check <source>`
Validate a skill for tool-specific references.

| Flag | Description |
|------|-------------|
| `--target TEXT` | Target tool for tool-specific patterns |
| `--strict` | Fail on any tool-specific reference |
| `--json` | Output as JSON |

### `usc batch <paths>...`
Convert multiple skills in bulk.

| Flag | Description |
|------|-------------|
| `--target TEXT` | Target tool (required) |
| `--output-dir PATH` | Output directory for converted skills |
| `--force` | Overwrite existing files |
| `--dry-run` | Preview without writing |
| `--no-recursive` | Don't search subdirectories |

### `usc search <query>`
Search GitHub for skills.

| Flag | Description |
|------|-------------|
| `--max-results INTEGER` | Maximum number of results |
| `--json` | Output as JSON |

### `usc info <source>`
Show metadata and validation info for a skill.

| Flag | Description |
|------|-------------|
| `--target TEXT` | Target tool for validation context |

### `usc update <skill-name>`
Update an installed skill from its source.

| Flag | Description |
|------|-------------|
| `--target TEXT` | Target tool (if different from installed location) |
| `--source TEXT` | GitHub URL to re-fetch from |
| `--force` | Force update even if no source URL |

---

## Architecture

### Data Flow

```
[User Input: URL/file/stdin]
            ↓
      [Fetcher]
     raw skill content
            ↓
      [Detector]
  target tool + skills dir
            ↓
      [Converter]
  normalized skill content
            ↓
    [if --install] [Installer]
     writes to skills dir
            ↓
      [Output]
  file path or stdout
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `cli.py` | Click CLI entry point, all commands and flags |
| `converter.py` | Regex engine, code block splitting, frontmatter handling |
| `frontmatter.py` | YAML frontmatter parse/normalize/dump |
| `patterns/base.py` | 7 core regex pattern categories |
| `tools_registry.py` | 8 tool metadata definitions |
| `fetcher.py` | GitHub API + git clone fallback + local/stdin |
| `detector.py` | Auto-detect tool from process/config |
| `installer.py` | Install to correct skills directory |
| `validator.py` | Scan for tool-specific references, score skills |
| `batch.py` | Bulk convert directories/globs |
| `config.py` | Load custom patterns from YAML config |
| `webui/app.py` | Flask web application |

---

## Supported Tools

| Tool | Key | Skills Directory | Config File | Binary |
|------|-----|-----------------|-------------|--------|
| Claude Code | `claude-code` | `~/.claude/skills/` | `~/.claude/settings.json` | `claude` |
| Cursor | `cursor` | `~/.cursor/skills/` | `~/.cursor/settings.json` | `cursor` |
| OpenCode | `opencode` | `~/.config/opencode/skills/` | `~/.config/opencode/config.json` | `opencode` |
| Codex | `codex` | `~/.codex/skills/` | `~/.codex/config.json` | `codex` |
| Antigravity IDE | `antigravity` | `~/.antigravity/skills/` | `~/.antigravity/config.json` | `antigravity` |
| Gemini CLI | `gemini` | `~/.gemini/skills/` | `~/.gemini/config.json` | `gemini` |
| Windsurf | `windsurf` | `~/.windsurf/skills/` | `~/.windsurf/config.json` | `windsurf` |
| Aide | `aide` | `~/.aide/skills/` | `~/.aide/config.json` | `aide` |

---

## Conversion Patterns

### Pattern Categories (7 total)

1. **TOOL_NAMES** — `Claude Code`, `OpenCode`, `Cursor`, etc. → `your AI assistant`
2. **COMMANDS** — `claude --flag`, `opencode --model` → removed
3. **PATHS** — `~/.claude/`, `~/.cursor/`, etc. → removed
4. **MODELS** — `Opus`, `Sonnet`, `Haiku`, `GPT-4o`, `Gemini Pro` → `the best available model`
5. **BUILTIN_TOOLS** — `the Edit tool`, `the Read tool` → `your Edit capability`, etc.
6. **BUILTIN_TOOLS_BARE** — bare `Edit`, `Read`, `Bash` → `your Edit capability`, etc.
7. **UI_HINTS** — `Press Cmd+K`, `Use slash commands` → removed

### Frontmatter Normalization

- `allowed-tools` → `allowed-capabilities`
- `model` → removed
- Keys containing tool keywords → removed
- Values containing tool keywords → removed

### Transformation Order

1. Parse frontmatter
2. Split code blocks
3. Apply patterns to text outside code blocks:
   - TOOL_NAMES
   - COMMANDS
   - PATHS
   - MODELS
   - BUILTIN_TOOLS
   - BUILTIN_TOOLS_BARE
   - UI_HINTS
4. Reassemble with conversion header

---

## Test Suite Breakdown

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_batch.py` | 17 | Batch conversion, file discovery, glob patterns |
| `test_config.py` | 14 | Config loading, custom patterns, tool filtering |
| `test_converter.py` | 14 | Code blocks, text transformation, file I/O |
| `test_detector.py` | 7 | Process detection, config detection, tool validation |
| `test_fetcher.py` | 11 | GitHub API, local files, stdin, search |
| `test_frontmatter.py` | 16 | Parse, normalize, dump, roundtrip |
| `test_info_update.py` | 7 | Info command, update command |
| `test_init.py` | 5 | Skill template generation |
| `test_installer.py` | 5 | Installation, sanitization, force flag |
| `test_integration.py` | 3 | End-to-end conversion and installation |
| `test_e2e_workflows.py` | 27 | Full workflows, realistic skills, edge cases |
| `test_new_features.py` | 14 | Version, list-installed, diff, JSON output |
| `test_validator.py` | 15 | Reference finding, scoring, formatting |
| `test_verbose.py` | 3 | Verbose logging toggle |
| **Total** | **159** | **100% passing** |

### Test Execution Time

- Full suite: ~0.5 seconds
- No external dependencies required for tests
- All network calls mocked

---

## Known Limitations

1. **Regex-based, not AI-based** — Pattern matching may miss subtle references
2. **No pairwise mapping** — Strips references rather than translating them
3. **Requires Python 3.10+**
4. **GitHub API rate limits** — 60 requests/hour unauthenticated
5. **No skill validation** — Doesn't verify converted skills against target tool schemas
6. **Aggressive common-word removal** — Some patterns remove common words like "flow", "context", "memory" (scope limited in v1)

---

## Quick Reference

### Installation

```bash
cd "universal skills converter"
pip install -e .
```

### Most Common Commands

```bash
# Convert and install
usc convert skill.md --target opencode --install

# Convert with diff
usc convert skill.md --target cursor --diff

# Convert to JSON
usc convert skill.md --target codex --json

# Validate
usc check skill.md --target opencode

# Batch convert
usc batch ./skills/ --target cursor --output-dir ./converted/

# Search GitHub
usc search "claude code prompting"

# Create new skill
usc init "My Skill" --output my-skill.md

# Web UI
python3 -m webui.run
```

### Exit Codes

- `0` — Success
- `1` — Error (invalid input, validation failure, etc.)

### Environment Variables

- `GITHUB_TOKEN` — GitHub personal access token for higher API rate limits

### Config File Locations (checked in order)

1. `~/.config/usc/config.yaml`
2. `~/.usc.yaml`
3. `./.usc.yaml` (project-local)

---

## Bug Fixes History

### Critical Fixes
- Validator tool-filter bug — `continue` skipped non-TOOL_NAMES categories
- Dead tool-specific pattern files — 8 files never imported, removed
- Line numbers in validator — changed from chunk-relative to document-level

### High Priority Fixes
- GitHub search URL encoding — added `urllib.parse.urlencode`
- GitHub default branch detection — query API for `default_branch`
- `--force` flag for `--output` — added existence check
- `batch_convert` variable mismatch — added `files` parameter
- COMMANDS regex — changed from start-of-line to word-boundary matching

### Medium Priority Fixes
- Windows line endings in frontmatter — added `\r\n` handling
- Case sensitivity in batch/fetcher — `.md` and `skills` checks now case-insensitive
- Frontmatter value scanning — scan string values for tool keywords
- Frontmatter in convert flow — reconstruct full text before splitting code blocks
- BUILTIN_TOOLS double-replacement — added negative lookbehind

---

## Dependencies

### Required
- `click` — CLI framework
- `requests` — HTTP requests
- `psutil` — Process detection
- `pyyaml` — YAML parsing

### Optional
- `flask` — Web UI

### Dev/Test
- `pytest`
- `pytest-cov`

---

*Project completed: 2026-08-05*  
*Total development time: Multiple sessions*  
*Final test count: 159/159 passing*
