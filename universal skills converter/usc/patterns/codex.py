PATTERNS = [
    (r'\bCodex\b', 'your AI assistant'),
    (r'\bcodex-cli\b', 'your AI assistant'),
    (r'/\.codex/', ''),
    (r'/\.openai/codex/', ''),
    (r'--model\s+\S+', ''),
    (r'\bOPENAI_API_KEY\b', ''),
    (r'\bagents?\b', ''),
    (r'\bsandbox\b', ''),
]
