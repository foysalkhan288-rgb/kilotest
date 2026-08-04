PATTERNS = [
    (r'\bGemini CLI\b', 'your AI assistant'),
    (r'\bgemini-cli\b', 'your AI assistant'),
    (r'\bGemini\b', 'your AI assistant'),
    (r'/\.gemini/', ''),
    (r'--model\s+\S+', ''),
    (r'\bGEMINI_API_KEY\b', ''),
    (r'\bfiles?\b', ''),
    (r'\bgrounding\b', ''),
]
