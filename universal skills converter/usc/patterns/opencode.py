PATTERNS = [
    (r'\bOpenCode\b', 'your AI assistant'),
    (r'\bopencode-cli\b', 'your AI assistant'),
    (r'\bopencode\b', 'your AI assistant'),
    (r'/\.config/opencode/', ''),
    (r'/\.opencode/', ''),
    (r'--model\s+\S+', ''),
    (r'\bOPENAI_API_KEY\b', ''),
    (r'\bsessions?\b', ''),
    (r'\bthreads?\b', ''),
]
