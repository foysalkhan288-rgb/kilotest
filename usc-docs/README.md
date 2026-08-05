# Universal Skills Converter

A command-line tool that normalizes AI assistant skills so they work across different tools.

![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)

## What is this?

AI assistant skills are typically written for a single tool — Claude Code, Cursor, OpenCode, etc. GitHub hosts hundreds of community skills, but they rarely transfer between tools. This tool converts skills into a universal format that any supported tool can use, eliminating the need to rewrite or fork skills for every platform.

## How it works

```
Fetch → Detect → Convert → Install
```

- **Fetch** — Retrieve a skill from a local path, GitHub URL, or stdin.
- **Detect** — Automatically identify the user's active tool from running processes or config files.
- **Convert** — Normalize the skill into a universal format, stripping tool-specific references.
- **Install** — Optionally write the converted skill directly into the target tool's skills directory.

## Installation

```bash
cd "universal skills converter"
pip install -e .
```

## Quick Start

```bash
# Convert a GitHub skill and install to OpenCode
usc convert https://github.com/anthropics/skills/tree/main/advanced-prompting --target opencode --install

# Convert a local file
usc convert ~/Downloads/claude-skill.md --target cursor

# Preview without installing
usc convert skill.md --target codex --dry-run

# Create a new skill from template
usc init "My New Skill" --target opencode --output my-skill.md

# Validate a skill for tool-specific references
usc check skill.md --target opencode

# Batch convert a directory
usc batch ./skills/ --target cursor --output-dir ./converted/

# Search GitHub for skills
usc search "claude code prompting"

# Inspect skill metadata
usc info skill.md --target opencode

# Update an installed skill
usc update my-skill --source https://github.com/user/repo

# Start web UI
python3 -m webui.run
```

## Commands

### `usc convert <source>`

Convert a skill from a GitHub URL, local file, or stdin.

```
usc convert <source> [OPTIONS]

Arguments:
  SOURCE  GitHub URL, local file path, or '-' for stdin

Options:
  --target TEXT       Target tool (e.g., opencode, cursor, claude-code)
  --install           Install to target tool's skills directory
  --output PATH       Write converted skill to file
  --force             Overwrite existing skill file
  --dry-run           Print converted skill without writing
  --verbose           Show detailed transformation logs
  --name TEXT         Custom name for skill file (without .md)
  --diff              Show unified diff of changes
  --json              Output result as JSON
```

### `usc init <name>`

Create a new universal skill from a template.

```
usc init <name> [OPTIONS]

Arguments:
  NAME  Skill name

Options:
  --target TEXT   Target tool (optional)
  --output PATH   Write skill to file
```

### `usc detect`

Detect the currently active AI coding tool.

### `usc version`

Show the installed version.

### `usc list-tools`

List all supported AI coding tools and their configuration paths.

### `usc list-installed`

List installed skills for a tool.

```
usc list-installed [OPTIONS]

Options:
  --target TEXT   Target tool (default: auto-detect)
  --json          Output as JSON
```

### `usc check <source>`

Validate a skill for tool-specific references.

```
usc check <source> [OPTIONS]

Options:
  --target TEXT   Target tool for tool-specific patterns
  --strict        Fail on any tool-specific reference
  --json          Output as JSON
```

### `usc batch <paths>...`

Convert multiple skills in bulk.

```
usc batch <PATHS>... [OPTIONS]

Options:
  --target TEXT       Target tool (required)
  --output-dir PATH   Output directory for converted skills
  --force             Overwrite existing files
  --dry-run           Preview without writing
  --no-recursive      Don't search subdirectories
```

### `usc search <query>`

Search GitHub for skills.

```
usc search <QUERY> [OPTIONS]

Options:
  --max-results INTEGER   Maximum number of results
  --json                  Output as JSON
```

### `usc info <source>`

Show metadata and validation info for a skill.

```
usc info <SOURCE> [OPTIONS]

Options:
  --target TEXT   Target tool for validation context
```

### `usc update <skill-name>`

Update an installed skill from its source.

```
usc update <SKILL_NAME> [OPTIONS]

Options:
  --target TEXT   Target tool (if different from installed location)
  --source TEXT   GitHub URL to re-fetch from
  --force         Force update even if no source URL
```

## Supported Tools

| Tool Name       | Key          | Skills Directory                                      |
|-----------------|--------------|--------------------------------------------------------|
| Claude Code     | `claude-code`| `~/.claude/skills/`                                   |
| Cursor          | `cursor`     | `~/.cursor/skills/`                                   |
| OpenCode        | `opencode`   | `~/.config/opencode/skills/`                          |
| Codex           | `codex`      | `~/.codex/skills/`                                    |
| Antigravity IDE | `antigravity`| `~/.antigravity/skills/`                              |
| Gemini CLI      | `gemini`     | `~/.gemini/skills/`                                   |
| Windsurf        | `windsurf`   | `~/.windsurf/skills/`                                 |
| Aide            | `aide`       | `~/.aide/skills/`                                     |

## What gets converted

- Tool names (e.g. "Claude Code" → "your AI assistant")
- Tool-specific CLI commands and flags
- File paths referencing tool-specific directories
- Model names (e.g. "Opus" → "the best available model")
- Built-in tool references (e.g. `Bash`, `Read`, `Glob`)
- UI hints and keyboard shortcuts
- YAML frontmatter fields (`model`, `allowed-tools`, tool-specific keys)

## Code block preservation

Code inside triple backticks is **not modified**. This means example commands, scripts, and configuration snippets inside your skill remain exactly as written — only the surrounding descriptive text is normalized.

## Validation

After conversion, use `usc check` to verify no tool-specific references remain:

```bash
usc check converted-skill.md --target opencode
```

The validator scores skills 0-100 and reports any findings with line numbers.

## Configuration

You can customize behavior with a config file. Place it at one of these locations (checked in order):

- `~/.config/usc/config.yaml`
- `~/.usc.yaml`
- `./.usc.yaml` (project-local)

Example `usc_config.example.yaml`:

```yaml
# Custom regex patterns (applied after base patterns)
patterns:
  - regex: '\bMyCustomTool\b'
    replacement: 'your AI assistant'
  - regex: '~/.mytool/'
    replacement: ''

# Only enable these tools (leave empty for all)
# enabled_tools:
#   - claude-code
#   - opencode
#   - cursor
```

## Web UI

For a browser-based interface:

```bash
pip install -e ".[webui]"
python3 -m webui.run
```

Then open http://localhost:5000 in your browser.

## Batch Conversion

Convert multiple skills at once:

```bash
usc batch ./my-skills/ --target cursor --output-dir ./converted/
usc batch "skills/*.md" --target opencode --dry-run
```

## Limitations

- **Regex-based, not AI-based** — Conversions rely on pattern matching and may miss subtle or context-dependent references.
- **No pairwise mapping** — The tool strips tool-specific references rather than translating them to exact equivalents in the target tool.
- **Requires Python 3.10+**
- **GitHub API rate limits** — Unauthenticated requests are limited to 60 requests per hour. Use a `GITHUB_TOKEN` environment variable for higher limits.
- **No skill validation** — Converted skills are not automatically validated against the target tool's schema.

## Contributing

Contributions are welcome. To add support for a new tool or detection pattern, see the source code in `usc/` and follow the existing registry structure.

## License

MIT — see the [LICENSE](LICENSE) file for details.
