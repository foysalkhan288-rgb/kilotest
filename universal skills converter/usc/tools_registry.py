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
        'name': 'Antigravity',
        'skills_dir': '~/.antigravity/skills/',
        'config_file': '~/.antigravity/config.json',
        'binary': 'antigravity',
        'pattern_file': 'patterns/antigravity.py'
    },
    'gemini': {
        'name': 'Gemini',
        'skills_dir': '~/.gemini/skills/',
        'config_file': '~/.gemini/config.json',
        'binary': 'gemini',
        'pattern_file': 'patterns/gemini.py'
    }
}


def get_tool(key):
    return TOOLS[key]


def list_tools():
    return list(TOOLS.keys())


def get_pattern_file(key):
    return TOOLS[key]['pattern_file']
