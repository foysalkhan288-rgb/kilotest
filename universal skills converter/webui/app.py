from __future__ import annotations

import sys

from flask import Flask, jsonify, render_template, request

try:
    from usc.converter import convert as convert_skill
    from usc.tools_registry import TOOLS, get_tool, list_tools
    from usc.fetcher import fetch, is_github_url
except ImportError:  # pragma: no cover - optional dependency
    convert_skill = None
    TOOLS = {}
    list_tools = lambda: []
    get_tool = lambda key: {}
    fetch = None
    is_github_url = lambda url: False

app = Flask(__name__)


@app.route('/')
def index():
    tools = list_tools()
    return render_template('index.html', tools=tools)


@app.route('/api/tools')
def api_tools():
    items = []
    for key in list_tools():
        tool = get_tool(key)
        items.append({
            'key': key,
            'name': tool.get('name', key),
            'skills_dir': tool.get('skills_dir', ''),
            'config_file': tool.get('config_file', ''),
            'binary': tool.get('binary', ''),
        })
    return jsonify(items)


@app.route('/api/convert', methods=['POST'])
def api_convert():
    data = request.get_json(silent=True) or {}
    content = data.get('content', '')
    target = data.get('target', '')
    source = data.get('source', '')

    if not content and not source:
        return jsonify({'error': 'Content or source is required'}), 400

    if not target:
        return jsonify({'error': 'Target is required'}), 400

    original_content = content

    if not original_content and source:
        if not is_github_url(source):
            return jsonify({'error': 'Only GitHub URLs are supported for fetching'}), 400
        if fetch is None:
            return jsonify({'error': 'Fetcher is not available'}), 500
        try:
            original_content = fetch(source)
        except Exception as exc:
            return jsonify({'error': str(exc)}), 400

    if convert_skill is None:
        return jsonify({'error': 'Converter is not available. Install universal-skills-converter.'}), 500

    try:
        converted = convert_skill(original_content)
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400

    original_size = len(original_content)
    converted_size = len(converted)
    chars_changed = converted_size - original_size

    return jsonify({
        'converted': converted,
        'original_size': original_size,
        'converted_size': converted_size,
        'changes': [{'chars_changed': chars_changed}],
    })
