PATTERNS = [
    (r'\bClaude Code\b', 'your AI assistant'),
    (r'\bclaude-code\b', 'your AI assistant'),
    (r'\bclaude\b', 'your AI assistant'),
    (r'/\.claude/', ''),
    (r'/\.claude-code/', ''),
    (r'--model\s+\S+', ''),
    (r'\bANTHROPIC_API_KEY\b', ''),
    (r'\bclaude\.md\b', ''),
    (r'\bartifacts?\b', ''),
    (r'\bsubagents?\b', ''),
    (r'\bpermissions?\b', ''),
]
