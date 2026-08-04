# Universal Skills Converter — V1 Plan

## 1. Problem Statement

### 1.1 The Core Problem
Modern AI coding tools (Claude Code, OpenCode, Cursor, Codex, Antigravity IDE, Gemini CLI) all support "skills" — reusable prompt/instruction files that customize the AI's behavior. However, these skills are **tool-specific**. A skill written for Claude Code will:

- Reference Claude Code by name throughout the instructions
- Use Claude Code's built-in tool names (Edit, Read, Bash, etc.)
- Reference Claude Code's file paths (`~/.claude/`, skill directory structures)
- Use Claude Code-specific CLI commands and flags
- Reference Anthropic model names (Opus, Sonnet, Haiku)
- Include UI-specific instructions (e.g., "Press Cmd+K in Cursor")

When a user copies a Claude Code skill into OpenCode or Cursor, the AI reads those references and either:
1. **Fails to recognize** the instructions as relevant (because it's looking for OpenCode-specific patterns)
2. **Attempts to use** Claude Code tools that don't exist in OpenCode/Cursor, causing errors
3. **Gets confused** by conflicting instructions about which tool to use

### 1.2 The Pain Point
- GitHub has hundreds of skills, but most are locked to one tool
- Users manually edit skills to replace tool names — tedious and error-prone
- No universal format exists that all tools can understand natively
- Each tool's skill ecosystem is siloed; skills don't transfer

### 1.3 Why This Matters
Skills represent collective knowledge. If a user can't freely move skills between tools, they're locked into one ecosystem. A universal converter breaks that lock-in and lets users mix-and-match the best skills regardless of which tool they're using.

---

## 2. Solution Overview

### 2.1 What We're Building
A **CLI tool** (`usc` — Universal Skills Converter) that:

1. **Fetches** a skill from a GitHub URL, local file, or stdin
2. **Detects** the user's active tool (or accepts `--target` flag)
3. **Converts** the skill by stripping/replacing tool-specific references with generic equivalents
4. **Installs** the converted skill into the target tool's skills directory

### 2.2 V1 Scope
- **Input:** GitHub URL, local file path, or piped stdin
- **Output:** Converted skill file (written to disk or stdout)
- **Installation:** Optionally place in the correct skills directory
- **Conversion method:** Regex-based pattern matching (no LLM dependency)
- **Supported tools:** Claude Code, OpenCode, Cursor, Codex, Antigravity IDE, Gemini CLI
- **Interface:** CLI only (web UI deferred to v2)

### 2.3 What V1 Does NOT Do
- No LLM-based "smart conversion" (regex only)
- No pairwise mapping (e.g., "Claude Code Edit tool" → "OpenCode Edit tool")
- No web UI
- No skill validation or testing after conversion
- No GitHub API auth for private repos
- No automatic updates or version management for skills

---

## 3. Architecture

### 3.1 System Components

```
usc/
├── cli.py              # CLI entry point (argparse/click)
├── fetcher.py          # Download/read skill from source
├── detector.py         # Detect active tool from config/process
├── converter.py        # Apply regex transformations
├── installer.py        # Write to correct skills directory
├── tools_registry.py   # Tool metadata (names, paths, patterns)
└── patterns/           # Regex patterns per tool (extensible)
    ├── claude_code.py
    ├── opencode.py
    ├── cursor.py
    ├── codex.py
    ├── antigravity.py
    └── gemini.py
```

### 3.2 Data Flow

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

---

## 4. CLI Interface

### 4.1 Commands

```bash
# Convert and install (auto-detect target tool)
usc convert <github-url-or-file-path> --install

# Convert and install for specific tool
usc convert <github-url-or-file-path> --target opencode --install

# Convert only, output to stdout
usc convert <github-url-or-file-path>

# Convert only, output to file
usc convert <github-url-or-file-path> --output converted_skill.md

# Detect current tool
usc detect

# List supported tools and their config paths
usc list-tools
```

### 4.2 Options

| Flag | Description | Default |
|------|-------------|--------|
| `--target <tool>` | Explicitly set target tool | Auto-detect |
| `--install` | Install to target tool's skills directory | False |
| `--output <path>` | Write converted skill to file | stdout |
| `--force` | Overwrite existing skill file | False |
| `--dry-run` | Show what would be converted without writing | False |
| `--verbose` | Show detailed transformation logs | False |

---

## 5. Supported Tools (V1)

### 5.1 Tool Registry

| Tool | Skills Directory | Config Detection | CLI Binary |
|------|-----------------|------------------|------------|
| Claude Code | `~/.claude/skills/` | `~/.claude/settings.json` | `claude` |
| OpenCode | `~/.config/opencode/skills/` | `~/.config/opencode/config.json` | `opencode` |
| Cursor | `~/.cursor/skills/` | `~/.cursor/settings.json` | `cursor` |
| Codex | `~/.codex/skills/` | `~/.codex/config.json` | `codex` |
| Antigravity IDE | `~/.antigravity/skills/` | `~/.antigravity/config.json` | `antigravity` |
| Gemini CLI | `~/.gemini/skills/` | `~/.gemini/config.json` | `gemini` |

### 5.2 Tool Detection Logic

1. Check if `--target` flag is provided → use that
2. Check running processes for known tool binaries (`claude`, `opencode`, etc.)
3. Check for config files in common locations
4. If multiple found, prompt user or use first match
5. If none found, error with helpful message

---

## 6. Conversion Rules (Regex-Based)

### 6.1 Core Transformation Patterns

The converter applies these transformations in order:

#### 6.1.1 Tool Name Replacement
**Patterns:**
- `Claude Code` → `your AI assistant`
- `OpenCode` → `your AI assistant`
- `Cursor` → `your AI assistant`
- `Codex` → `your AI assistant`
- `Antigravity IDE` → `your AI assistant`
- `Gemini CLI` → `your AI assistant`
- `claude` (as tool reference) → `your assistant`
- `opencode` → `your assistant`
- `cursor` → `your assistant`

**Regex examples:**
```python
r'\bClaude Code\b' → 'your AI assistant'
r'\bOpenCode\b' → 'your AI assistant'
r'\bCursor\b' → 'your AI assistant'
```

#### 6.1.2 Tool-Specific Commands
**Patterns:**
- `claude --dangerously-skip-permissions` → removed
- `opencode --model` → removed
- `cursor --allow` → removed
- Any line starting with tool binary name → removed or commented

**Regex example:**
```python
r'^\s*(claude|opencode|cursor|codex|antigravity|gemini)\s+.*$' → ''
```

#### 6.1.3 File Path Removal
**Patterns:**
- `~/.claude/` → removed
- `/claude-code/` → removed
- `~/.config/opencode/` → removed
- `~/.cursor/` → removed
- Any absolute path specific to a tool → removed or replaced with `[SKILL_DIR]`

**Regex example:**
```python
r'~/.claude/' → ''
r'~/.config/opencode/' → ''
```

#### 6.1.4 Model Name Normalization
**Patterns:**
- `Opus` → `the best available model`
- `Sonnet` → `the best available model`
- `Haiku` → `the best available model`
- `GPT-4o` → `the best available model`
- `Gemini Pro` → `the best available model`

**Regex example:**
```python
r'\b(Opus|Sonnet|Haiku|GPT-4o|Gemini Pro)\b' → 'the best available model'
```

#### 6.1.5 Built-in Tool Reference Normalization
**Patterns:**
- `the Edit tool` → `your editor`
- `the Read tool` → `your file reading capability`
- `the Bash tool` → `your shell/command execution capability`
- `Use the MCP server` → `use available integrations/MCP servers`
- `Use the [ToolName] tool` → `use your [capability]`

**Regex example:**
```python
r'the (Edit|Read|Bash|Write|Glob|Grep) tool' → r'your \1 capability'
```

#### 6.1.6 UI/Interaction Hints
**Patterns:**
- `Press Cmd+K` → removed
- `Use slash commands` → removed
- `Right-click and select` → removed (tool-specific UI)
- Any keyboard shortcut specific to a tool → removed

**Regex example:**
```python
r'Press\s+(Cmd|Ctrl)\+\w+' → ''
r'Use\s+slash\s+commands' → ''
```

### 6.2 Transformation Order

Transformations are applied in this sequence to avoid conflicts:

1. **Escape markdown** — preserve formatting, don't touch code blocks yet
2. **Tool name replacement** — replace tool names with generic terms
3. **Command removal** — strip tool-specific CLI commands
4. **Path removal** — strip tool-specific file paths
5. **Model normalization** — replace model names
6. **Tool reference normalization** — replace built-in tool names
7. **UI hint removal** — strip UI-specific instructions
8. **Cleanup** — remove empty lines, normalize whitespace

### 6.3 Code Block Handling

Skills often contain code examples. The converter must:
- **Preserve code blocks** (triple-backtick sections) unchanged
- Only transform text **outside** code blocks
- This prevents breaking example commands or code snippets

**Implementation:**
```python
def convert(content: str) -> str:
    # Split into code blocks and text
    parts = split_code_blocks(content)
    # Only transform text parts
    transformed = [transform_text(p) if is_text else p for p in parts]
    return ''.join(transformed)
```

---

## 7. Fetcher Module

### 7.1 Input Sources

| Source | Format | Detection |
|--------|--------|-----------|
| GitHub URL | `https://github.com/user/repo` or `https://github.com/user/repo/tree/main/skills` | Starts with `https://github.com/` |
| GitHub raw file | `https://raw.githubusercontent.com/...` | Starts with `https://raw.githubusercontent.com/` |
| Local file | Path to `.md` or `.skill` file | Exists as local file |
| Stdin | Piped content | `sys.stdin.isatty() == False` |

### 7.2 GitHub Fetching Logic

```python
def fetch_github(url: str) -> str:
    # 1. Parse URL to extract user/repo/branch/path
    # 2. If URL points to directory, list files and find skill files
    # 3. If URL points to file, fetch directly
    # 4. If URL is repo root, check common skill locations:
    #    - /skills/
    #    - /SKILLS/
    #    - /docs/skills/
    #    - Root .md files
    # 5. Download content
    # 6. Return raw skill content
```

**GitHub API (no auth):**
- Use `https://api.github.com/repos/{owner}/{repo}/contents/{path}` for directory listings
- Use `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}` for file content
- No authentication required for public repos
- Rate limit: 60 requests/hour (sufficient for single skill download)

**Alternative: `git clone`**
- If GitHub API fails or repo is complex, fallback to `git clone --depth 1`
- Parse local filesystem to find skill files
- Clean up temp directory after

### 7.3 Skill File Detection

When fetching a repo/directory, look for these patterns:
- Files named `SKILL.md`, `skill.md`, `*.skill.md`
- Directories containing `SKILL.md` (skill bundle)
- Any `.md` file in a `skills/` directory

---

## 8. Detector Module

### 8.1 Detection Strategy

**Priority order:**
1. `--target` CLI flag (explicit)
2. Active process matching (running tool binary)
3. Config file presence
4. Environment variables
5. Interactive prompt if still ambiguous

### 8.2 Process Detection

```python
import psutil

def detect_running_tool() -> Optional[str]:
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in TOOL_BINARIES:
            return TOOL_BINARIES[proc.info['name']]
    return None
```

**Supported binaries:**
- `claude` → Claude Code
- `opencode` → OpenCode
- `cursor` → Cursor
- `codex` → Codex
- `antigravity` → Antigravity IDE
- `gemini` → Gemini CLI

### 8.3 Config File Detection

```python
def detect_from_config() -> Optional[str]:
    for tool_name, config_path in TOOL_CONFIGS.items():
        if os.path.exists(config_path):
            return tool_name
    return None
```

---

## 9. Installer Module

### 9.1 Installation Logic

```python
def install(skill_content: str, skill_name: str, target_tool: str, force: bool = False):
    skills_dir = TOOL_REGISTRY[target_tool]['skills_dir']
    os.makedirs(skills_dir, exist_ok=True)
    
    dest_path = os.path.join(skills_dir, f"{skill_name}.md")
    
    if os.path.exists(dest_path) and not force:
        raise FileExistsError(f"Skill already exists at {dest_path}. Use --force to overwrite.")
    
    with open(dest_path, 'w') as f:
        f.write(skill_content)
    
    return dest_path
```

### 9.2 Skill Naming

- Derive name from source: filename, repo name, or directory name
- Sanitize: lowercase, hyphens instead of spaces, remove special chars
- Example: `claude-code-advanced-prompting.md` → `advanced-prompting.md`

---

## 10. Error Handling

### 10.1 Error Categories

| Error | Cause | Recovery |
|-------|-------|----------|
| `FetchError` | Invalid URL, network issue, repo not found | Retry once, then exit with clear message |
| `SkillNotFound` | No skill files found in repo | List found files, suggest manual path |
| `ToolDetectionError` | No tool detected and no `--target` provided | List supported tools, ask for `--target` |
| `InstallationError` | Cannot write to skills directory | Suggest manual install with `--output` |
| `ConversionError` | Skill content is malformed | Save raw content, warn user |
| `FileExistsError` | Skill already installed | Suggest `--force` or different name |

### 10.2 Error Message Format

```
ERROR: [ErrorType]
Message: [Human-readable explanation]
Suggestion: [How to fix]
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

**Components to test:**
- `fetcher.py` — mock GitHub API responses, test URL parsing
- `detector.py` — mock process list, mock config files
- `converter.py` — test each regex pattern independently, test ordering
- `installer.py` — test directory creation, file writing, force flag
- `tools_registry.py` — test tool metadata lookup

**Test cases for converter:**
```python
def test_tool_name_replacement():
    assert convert("Use Claude Code's Edit tool") == "Use your AI assistant's Edit capability"

def test_command_removal():
    assert convert("Run: claude --dangerously-skip-permissions") == "Run:"

def test_path_removal():
    assert convert("Located at ~/.claude/skills/") == "Located at"

def test_model_normalization():
    assert convert("Use Opus for best results") == "Use the best available model for best results"

def test_code_block_preservation():
    input_text = "Here is an example:\n```bash\nclaude --flag\n```\nEnd"
    assert "claude --flag" in convert(input_text)  # Inside code block, preserved
```

### 11.2 Integration Tests

- End-to-end test: fetch a real skill, convert, verify no tool-specific references remain
- Install test: convert and install to temp directory, verify file exists
- Detection test: mock environment, verify correct tool detection

### 11.3 Manual Testing Checklist

- [ ] Convert a Claude Code skill to OpenCode
- [ ] Convert an OpenCode skill to Cursor
- [ ] Convert a skill from GitHub URL
- [ ] Convert a local file
- [ ] Test with `--target` flag
- [ ] Test with `--install` flag
- [ ] Test with `--force` flag
- [ ] Test error cases (invalid URL, no tool detected, etc.)

---

## 12. Limitations (V1)

### 12.1 Known Limitations

1. **Regex cannot understand context**
   - May strip important content if it matches a pattern
   - Cannot handle nuanced references (e.g., "Claude Code as a concept" vs "Claude Code the tool")
   - May miss tool-specific references that don't match known patterns

2. **No semantic understanding**
   - Cannot determine if a reference is actually important to the skill's logic
   - May remove instructions that are critical but phrased unusually

3. **Limited tool support**
   - Only 6 tools supported in v1
   - New tools require adding patterns manually

4. **No skill validation**
   - Cannot verify the converted skill actually works in the target tool
   - User must test manually

5. **GitHub rate limits**
   - 60 requests/hour unauthenticated
   - May hit limit if converting many skills in sequence

6. **No skill versioning**
   - Overwrites existing skills without tracking changes
   - No way to revert or update installed skills

7. **No bundled skill management**
   - Cannot update skills after installation
   - No dependency resolution for skills that reference other skills

### 12.2 Edge Cases Not Handled

- Skills with nested code blocks or unusual markdown
- Skills in languages other than English
- Skills with tool-specific embedded scripts or binaries
- Skills that intentionally mix multiple tool references
- Skills with images or attachments

---

## 13. Future Enhancements (V2+)

### 13.1 Smart Mode (LLM-Based)
- Optional `--smart` flag that uses an LLM API for complex conversions
- Requires API key (Anthropic Claude, OpenAI, etc.)
- Better context understanding, fewer false positives/negatives
- Can be configured to use the target tool's own model (if accessible via API)

### 13.2 Web UI
- Browser-based interface for non-technical users
- Paste skill, select target tool, preview conversion, download
- Hosted version or local web server

### 13.3 Skill Registry
- Index of known skills with metadata (source tool, quality rating, tags)
- Search and browse from CLI
- Community contributions

### 13.4 Skill Bundles
- Support for multi-file skills (templates, scripts, etc.)
- Preserve directory structure in target tool's skills directory

### 13.5 Validation
- Run converted skill through target tool's skill validator (if available)
- Syntax checking, reference validation
- Preview mode showing what was changed

### 13.6 Update Management
- Track installed skill versions
- Check for updates from source repos
- Automatic or manual update mechanism

---

## 14. Implementation Details

### 14.1 Technology Stack

- **Language:** Python 3.10+
- **CLI framework:** `click` or `argparse` (built-in)
- **HTTP:** `requests` (for GitHub API)
- **Process detection:** `psutil`
- **Testing:** `pytest`
- **Packaging:** `pyproject.toml` for pip-installable package

### 14.2 Project Structure

```
universal-skills-converter/
├── usc/
│   ├── __init__.py
│   ├── cli.py
│   ├── fetcher.py
│   ├── detector.py
│   ├── converter.py
│   ├── installer.py
│   ├── tools_registry.py
│   └── patterns/
│       ├── __init__.py
│       ├── base.py
│       ├── claude_code.py
│       ├── opencode.py
│       ├── cursor.py
│       ├── codex.py
│       ├── antigravity.py
│       └── gemini.py
├── tests/
│   ├── __init__.py
│   ├── test_fetcher.py
│   ├── test_detector.py
│   ├── test_converter.py
│   ├── test_installer.py
│   └── test_integration.py
├── pyproject.toml
├── README.md
└── PLAN.md (this file)
```

### 14.3 Key Design Decisions

1. **Regex-only conversion** — No LLM dependency, works offline, fast
2. **Generic normalization** — Strip tool-specific references, don't map between tools
3. **Code block preservation** — Don't transform content inside triple-backtick blocks
4. **Extensible patterns** — Each tool has its own pattern file; easy to add new tools
5. **No skill modification tracking** — Simple overwrite model for v1
6. **CLI-first** — Web UI is v2

---

## 15. Success Criteria

### 15.1 V1 Success Criteria

- [ ] Successfully fetches a skill from a GitHub URL
- [ ] Successfully fetches a skill from a local file
- [ ] Successfully fetches a skill from stdin
- [ ] Correctly detects active tool when possible
- [ ] Accepts `--target` flag to override detection
- [ ] Removes all tool name references (Claude Code, OpenCode, etc.)
- [ ] Removes tool-specific CLI commands
- [ ] Removes tool-specific file paths
- [ ] Normalizes model names to generic terms
- [ ] Preserves code blocks unchanged
- [ ] Installs converted skill to correct directory
- [ ] Handles errors gracefully with helpful messages
- [ ] Unit test coverage > 80%
- [ ] CLI is intuitive with `--help` documentation

### 15.2 Quality Metrics

- **False positive rate:** < 10% (removing content that shouldn't be removed)
- **False negative rate:** < 20% (missing tool-specific references)
- **Conversion speed:** < 1 second per skill file
- **Installation success:** 100% when target directory is writable

---

## 16. Risks and Mitigations

### 16.1 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Regex breaks skill content | High — skill becomes unusable | Extensive testing, preserve code blocks, allow `--dry-run` |
| Tool detection fails | Medium — user must manually specify | Clear error message, `--target` flag always works |
| GitHub API rate limits | Low — only affects bulk conversions | Cache responses, suggest `git clone` fallback |
| Skills vary too much in structure | Medium — some skills don't convert well | Document limitations, suggest manual review |
| Tool directory structure changes | Low — breaks installation | Version check, configurable paths |

### 16.2 Assumptions

- Users have Python 3.10+ installed
- Target tools are installed and their config directories exist
- Skills are markdown files with standard formatting
- Tool-specific references follow predictable patterns
- Users have internet access for GitHub fetches (unless using local files)

---

## 17. Open Questions (To Resolve Before Implementation)

1. **Skill naming convention:** Should we preserve original name or normalize (lowercase, hyphens)?
   - **Recommended:** Normalize to lowercase-hyphens for consistency across tools

2. **Multiple skills in repo:** If a repo has multiple skills, should we convert all or prompt user?
   - **Recommended:** Convert all found skills, list what was installed

3. **Overwrite behavior:** Should `usc convert --install` overwrite existing skills by default?
   - **Recommended:** No, require `--force` flag for safety

4. **Code block transformation:** Should we transform comments inside code blocks?
   - **Recommended:** No, preserve code blocks entirely to avoid breaking examples

5. **Skill metadata:** Should we add a header comment noting the conversion?
   - **Recommended:** Yes, add `<!-- Converted by Universal Skills Converter -->` at top

---

## 18. Milestones

### Milestone 1: Core Engine (Week 1)
- [ ] Project setup (structure, dependencies, tests)
- [ ] `tools_registry.py` — define tool metadata
- [ ] `converter.py` — implement core regex transformations
- [ ] `patterns/` — create pattern files for all 6 tools
- [ ] Unit tests for converter (80% coverage)

### Milestone 2: Fetcher & Detector (Week 1-2)
- [ ] `fetcher.py` — implement GitHub URL and local file fetching
- [ ] `detector.py` — implement process and config detection
- [ ] Unit tests for fetcher and detector
- [ ] Integration test: fetch → detect → convert

### Milestone 3: Installer & CLI (Week 2)
- [ ] `installer.py` — implement skill installation
- [ ] `cli.py` — implement all commands and flags
- [ ] End-to-end CLI testing
- [ ] Manual testing with real skills

### Milestone 4: Documentation & Polish (Week 2-3)
- [ ] README.md with usage examples
- [ ] CONTRIBUTING.md for adding new tools
- [ ] Error message refinement
- [ ] Performance testing
- [ ] Final QA and bug fixes

---

## 19. Example Usage

### 19.1 Basic Usage

```bash
# Install usc
pip install universal-skills-converter

# Convert a Claude Code skill from GitHub and install to OpenCode
usc convert https://github.com/anthropics/skills/tree/main/advanced-prompting --target opencode --install

# Convert a local file and preview
usc convert ~/Downloads/claude-skill.md --target cursor

# Convert from stdin
cat skill.md | usc convert --target codex --install

# List supported tools
usc list-tools

# Detect current tool
usc detect
```

### 19.2 Example Conversion

**Input (Claude Code skill):**
```markdown
# Advanced Prompting

Use Claude Code's Opus model for best results.

## Instructions

1. Use the Edit tool to modify files
2. Run `claude --dangerously-skip-permissions` for automation
3. Save to ~/.claude/skills/advanced-prompting.md
```

**Output (Generic skill):**
```markdown
# Advanced Prompting

Use the best available model for best results.

## Instructions

1. Use your editor capability to modify files
2. 
3. Save to
```

---

## 20. Contributing Guidelines

### 20.1 Adding a New Tool

To add support for a new tool:

1. Add tool metadata to `tools_registry.py`:
   ```python
   NEW_TOOL = {
       'name': 'newtool',
       'skills_dir': '~/.newtool/skills/',
       'config_file': '~/.newtool/config.json',
       'binary': 'newtool',
       'patterns': 'patterns/newtool.py'
   }
   ```

2. Create `patterns/newtool.py`:
   ```python
   PATTERNS = [
       (r'\bNewTool\b', 'your AI assistant'),
       (r'~/.newtool/', ''),
       # ... more patterns
   ]
   ```

3. Add tests in `tests/test_converter.py`
4. Update README with new tool

### 20.2 Adding New Patterns

1. Identify the tool-specific reference in a skill
2. Add regex pattern to the appropriate tool's pattern file
3. Add test case
4. Document the pattern in this plan

---

## 21. Maintenance

### 21.1 Pattern Updates

- Review GitHub issues for missed patterns
- Update pattern files monthly or as new tools emerge
- Keep pattern files small and focused (one tool per file)

### 21.2 Tool Support

- Add new tools as they become popular
- Deprecate tools that are no longer maintained
- Maintain backward compatibility for old tool versions

---

## Appendix A: Regex Pattern Library

### A.1 Tool Names
```python
TOOL_NAMES = [
    (r'\bClaude Code\b', 'your AI assistant'),
    (r'\bOpenCode\b', 'your AI assistant'),
    (r'\bCursor\b', 'your AI assistant'),
    (r'\bCodex\b', 'your AI assistant'),
    (r'\bAntigravity IDE\b', 'your AI assistant'),
    (r'\bGemini CLI\b', 'your AI assistant'),
]
```

### A.2 Commands
```python
COMMANDS = [
    (r'^\s*(claude|opencode|cursor|codex|antigravity|gemini)\s+.*$', ''),
]
```

### A.3 Paths
```python
PATHS = [
    (r'~/.claude/', ''),
    (r'~/.config/opencode/', ''),
    (r'~/.cursor/', ''),
    (r'~/.codex/', ''),
    (r'~/.antigravity/', ''),
    (r'~/.gemini/', ''),
]
```

### A.4 Models
```python
MODELS = [
    (r'\b(Opus|Sonnet|Haiku)\b', 'the best available model'),
    (r'\bGPT-4o\b', 'the best available model'),
    (r'\bGemini Pro\b', 'the best available model'),
]
```

### A.5 Built-in Tools
```python
BUILTIN_TOOLS = [
    (r'the (Edit|Read|Bash|Write|Glob|Grep) tool', r'your \1 capability'),
    (r'Use the MCP server', 'use available integrations'),
]
```

### A.6 UI Hints
```python
UI_HINTS = [
    (r'Press\s+(Cmd|Ctrl)\+\w+', ''),
    (r'Use\s+slash\s+commands', ''),
    (r'Right-click\s+and\s+select', ''),
]
```

---

## Appendix B: Tools Registry

```python
TOOLS = {
    'claude-code': {
        'name': 'Claude Code',
        'skills_dir': '~/.claude/skills/',
        'config_file': '~/.claude/settings.json',
        'binary': 'claude',
        'pattern_file': 'patterns/claude_code.py'
    },
    'opencode': {
        'name': 'OpenCode',
        'skills_dir': '~/.config/opencode/skills/',
        'config_file': '~/.config/opencode/config.json',
        'binary': 'opencode',
        'pattern_file': 'patterns/opencode.py'
    },
    'cursor': {
        'name': 'Cursor',
        'skills_dir': '~/.cursor/skills/',
        'config_file': '~/.cursor/settings.json',
        'binary': 'cursor',
        'pattern_file': 'patterns/cursor.py'
    },
    'codex': {
        'name': 'Codex',
        'skills_dir': '~/.codex/skills/',
        'config_file': '~/.codex/config.json',
        'binary': 'codex',
        'pattern_file': 'patterns/codex.py'
    },
    'antigravity': {
        'name': 'Antigravity IDE',
        'skills_dir': '~/.antigravity/skills/',
        'config_file': '~/.antigravity/config.json',
        'binary': 'antigravity',
        'pattern_file': 'patterns/antigravity.py'
    },
    'gemini': {
        'name': 'Gemini CLI',
        'skills_dir': '~/.gemini/skills/',
        'config_file': '~/.gemini/config.json',
        'binary': 'gemini',
        'pattern_file': 'patterns/gemini.py'
    }
}
```

---

## Appendix C: Sample Skill Conversion

### Before (Claude Code Skill)
```markdown
# Code Review Skill

This skill helps Claude Code perform thorough code reviews using Opus.

## Usage

Invoke this skill when asked to review code.

### Tools to Use

1. Use the Read tool to examine files
2. Use the Glob tool to find related files
3. Use the Bash tool to run tests: `claude --test`
4. Save findings to ~/.claude/reviews/

## Model

Always use Opus for this skill.
```

### After (Generic Skill)
```markdown
# Code Review Skill

This skill helps your AI assistant perform thorough code reviews using the best available model.

## Usage

Invoke this skill when asked to review code.

### Tools to Use

1. Use your Read capability to examine files
2. Use your file-finding capability to find related files
3. Use your shell/command execution capability to run tests: 
4. Save findings to

## Model

Always use the best available model for this skill.
```

---

*Document Version: 1.0*  
*Date: 2026-08-04*  
*Status: Ready for Implementation*
