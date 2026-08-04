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
pip install -e .
```

## Usage

```bash
usc convert <source>
usc convert <source> --target opencode --install
usc convert <source> --output skill.md
usc detect
usc list-tools
cat skill.md | usc convert --target cursor --install
```

- `usc convert <source>` — Convert a skill and print to stdout.
- `usc convert <source> --target opencode --install` — Convert and install directly into OpenCode's skills directory.
- `usc convert <source> --output skill.md` — Write the converted skill to a file.
- `usc detect` — Detect the active AI assistant tool from the current environment.
- `usc list-tools` — List all supported tools and their keys.
- `cat skill.md | usc convert --target cursor --install` — Convert from stdin and install into Cursor.

## Supported Tools

| Tool Name       | Key          | Skills Directory                                      |
|-----------------|--------------|--------------------------------------------------------|
| Claude Code     | `claude-code`| `~/.claude/skills/`                                   |
| Cursor          | `cursor`     | `~/.cursor/skills/`                                   |
| OpenCode        | `opencode`   | `~/.config/opencode/skills/`                          |
| Codex           | `codex`      | `~/.codex/skills/`                                    |
| Antigravity IDE | `antigravity`| `~/.antigravity/skills/`                              |
| Gemini CLI      | `gemini`     | `~/.gemini/skills/`                                   |

## What gets converted

- Tool names (e.g. "Claude Code" → "your AI assistant")
- Tool-specific CLI commands and flags
- File paths referencing tool-specific directories
- Model names
- Built-in tool references (e.g. `Bash`, `Read`, `Glob`)
- UI hints and frontmatter fields

## Code block preservation

Code inside triple backticks is **not modified**. This means example commands, scripts, and configuration snippets inside your skill remain exactly as written — only the surrounding descriptive text is normalized.

## Limitations

- **Regex-based, not AI-based** — Conversions rely on pattern matching and may miss subtle or context-dependent references.
- **No pairwise mapping** — The tool strips tool-specific references rather than translating them to exact equivalents in the target tool.
- **Requires Python 3.10+**
- **GitHub API rate limits** — Unauthenticated requests are limited to 60 requests per hour. Use a `GITHUB_TOKEN` environment variable for higher limits.
- **No skill validation** — Converted skills are not automatically validated against the target tool's schema.

## Contributing

Contributions are welcome. To add support for a new tool or detection pattern, see the source code in `universal_skills_converter/` and follow the existing registry structure.

## License

MIT — see the [LICENSE](LICENSE) file for details.
