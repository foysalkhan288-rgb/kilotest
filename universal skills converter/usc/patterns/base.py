import re

TOOL_NAMES = (
    re.compile(r'\b(?:Claude Code|OpenCode|Cursor|Codex|Antigravity IDE|Gemini CLI|Windsurf IDE|Aide)\b', re.IGNORECASE),
    'your AI assistant'
)

COMMANDS = (
    re.compile(r'^\s*(?:claude|opencode|cursor|codex|antigravity|gemini|windsurf|aide)\s+.*$', re.IGNORECASE | re.MULTILINE),
    ''
)

PATHS = (
    re.compile(r'(?:~/.claude/[^\s]*|~/.config/opencode/[^\s]*|~/.cursor/[^\s]*|~/.codex/[^\s]*|~/.antigravity/[^\s]*|~/.gemini/[^\s]*|~/.windsurf/[^\s]*|~/.aide/[^\s]*)', re.IGNORECASE),
    ''
)

MODELS = (
    re.compile(r'\b(?:Opus|Sonnet|Haiku|GPT-4o|Gemini Pro)\b', re.IGNORECASE),
    'the best available model'
)

BUILTIN_TOOLS = (
    re.compile(r'the (Edit|Read|Bash|Write|Glob|Grep) tool', re.IGNORECASE),
    r'your \1 capability'
)

UI_HINTS = (
    re.compile(r'(?:Press\s+(?:Cmd|Ctrl)\+\w+|Use\s+slash\s+commands)', re.IGNORECASE),
    ''
)

PATTERN_CATEGORIES = [
    ('TOOL_NAMES', *TOOL_NAMES),
    ('COMMANDS', *COMMANDS),
    ('PATHS', *PATHS),
    ('MODELS', *MODELS),
    ('BUILTIN_TOOLS', *BUILTIN_TOOLS),
    ('UI_HINTS', *UI_HINTS),
]


def get_all_patterns():
    return [(regex, replacement) for _, regex, replacement in PATTERN_CATEGORIES]
