TOOLS = {
    'claude-code': {
        'name': 'Claude Code',
        'skills_dir': '~/.claude/skills/',
        'config_file': '~/.claude/settings.json',
        'binary': 'claude',
    },
    'opencode': {
        'name': 'OpenCode',
        'skills_dir': '~/.config/opencode/skills/',
        'config_file': '~/.config/opencode/config.json',
        'binary': 'opencode',
    },
    'cursor': {
        'name': 'Cursor',
        'skills_dir': '~/.cursor/skills/',
        'config_file': '~/.cursor/settings.json',
        'binary': 'cursor',
    },
    'codex': {
        'name': 'Codex',
        'skills_dir': '~/.codex/skills/',
        'config_file': '~/.codex/config.json',
        'binary': 'codex',
    },
    'antigravity': {
        'name': 'Antigravity IDE',
        'skills_dir': '~/.antigravity/skills/',
        'config_file': '~/.antigravity/config.json',
        'binary': 'antigravity',
    },
    'gemini': {
        'name': 'Gemini CLI',
        'skills_dir': '~/.gemini/skills/',
        'config_file': '~/.gemini/config.json',
        'binary': 'gemini',
    },
    'windsurf': {
        'name': 'Windsurf',
        'skills_dir': '~/.windsurf/skills/',
        'config_file': '~/.windsurf/config.json',
        'binary': 'windsurf',
    },
    'aide': {
        'name': 'Aide',
        'skills_dir': '~/.aide/skills/',
        'config_file': '~/.aide/config.json',
        'binary': 'aide',
    },
}


def get_tool(key):
    return TOOLS[key]


def list_tools():
    return list(TOOLS.keys())


def get_pattern_file(key):
    return TOOLS[key].get('pattern_file', '')
