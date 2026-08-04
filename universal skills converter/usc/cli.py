import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import click

from usc.batch import batch_convert, find_skill_files, print_batch_results
from usc.converter import convert as convert_skill, convert_file, set_verbose
from usc.detector import detect_tool
from usc.fetcher import fetch, is_github_url, is_local_file
from usc.installer import install_skill, sanitize_name
from usc.tools_registry import list_tools, get_tool
from usc.validator import find_tool_specific_references, validate_skill, format_validation_report


def derive_skill_name(source: str) -> str:
    if is_github_url(source):
        parsed = urlparse(source)
        parts = [p for p in parsed.path.split("/") if p]
        if "raw.githubusercontent.com" in parsed.netloc:
            # raw URL: /owner/repo/branch/path/to/file.md
            if len(parts) >= 4:
                return sanitize_name(parts[-1].replace(".md", "").replace(".skill.md", ""))
            return "github-skill"
        # github.com URL: /owner/repo[/tree/branch/path]
        if len(parts) >= 1:
            # Use the last meaningful path component
            # Filter out 'tree' and 'blob' and branch names
            meaningful = [p for p in parts if p not in ("tree", "blob", "main", "master")]
            if meaningful:
                return sanitize_name(meaningful[-1])
            return sanitize_name(parts[0])
        return "github-skill"
    if is_local_file(source):
        return sanitize_name(Path(source).stem)
    return "pasted-skill"


@click.group()
def cli():
    """Universal Skills Converter — convert skills between AI coding tools."""
    pass


@cli.command()
@click.argument("source", required=False, default="-")
@click.option("--target", help="Target tool (e.g., opencode, cursor, claude-code)")
@click.option("--install", is_flag=True, help="Install the converted skill to the target tool's skills directory")
@click.option("--output", "output_path", type=click.Path(), help="Write converted skill to this file path")
@click.option("--force", is_flag=True, help="Overwrite existing skill file if it already exists")
@click.option("--dry-run", is_flag=True, help="Print converted skill to stdout without writing to disk")
@click.option("--verbose", is_flag=True, help="Show detailed transformation logs")
@click.option("--name", "skill_name", help="Custom name for the skill file (without .md extension)")
@click.pass_context
def convert(ctx, source, target, install, output_path, force, dry_run, verbose, skill_name):
    """Convert a skill from a GitHub URL, local file, or stdin.

    SOURCE can be a GitHub URL, a local file path, or '-' for stdin.
    If SOURCE is omitted, stdin is used.
    """
    try:
        # 1. Detect target tool
        tool_key = detect_tool(target)
        tool_name = get_tool(tool_key)['name']

        if verbose:
            click.echo(f"Target tool: {tool_name} ({tool_key})")

        # 2. Fetch source
        if source == "-":
            if sys.stdin.isatty():
                click.echo("Reading from stdin (Ctrl+D to finish)...", err=True)
            from usc.fetcher import fetch_stdin
            content = fetch_stdin()
        else:
            if verbose:
                click.echo(f"Fetching from: {source}")
            content = fetch(source)

        if verbose:
            click.echo(f"Fetched {len(content)} characters")

        # 3. Convert
        if verbose:
            set_verbose(True)
        converted = convert_skill(content)

        if verbose:
            click.echo(f"Converted to {len(converted)} characters")

        # 4. Output handling
        if dry_run:
            click.echo(converted)
            return

        if output_path:
            Path(output_path).write_text(converted, encoding="utf-8")
            click.echo(f"Converted skill written to: {output_path}")

        # 5. Install
        if install:
            name = skill_name or derive_skill_name(source)
            try:
                dest = install_skill(converted, name, tool_key, force=force)
                click.echo(f"Skill installed to: {dest}")
            except FileExistsError as e:
                click.echo(f"Error: {e}", err=True)
                sys.exit(1)

        if not output_path and not install:
            # Default: print to stdout
            click.echo(converted)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command(name="detect")
def detect_cmd():
    """Detect the currently active AI coding tool."""
    try:
        tool_key = detect_tool()
        tool = get_tool(tool_key)
        click.echo(f"Detected tool: {tool['name']} ({tool_key})")
        click.echo(f"Skills directory: {tool['skills_dir']}")
        click.echo(f"Config file: {tool['config_file']}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command(name="list-tools")
def list_tools_cmd():
    """List all supported AI coding tools."""
    click.echo("Supported tools:")
    click.echo("")
    for key in list_tools():
        tool = get_tool(key)
        click.echo(f"  {key}")
        click.echo(f"    Name: {tool['name']}")
        click.echo(f"    Skills dir: {tool['skills_dir']}")
        click.echo(f"    Config: {tool['config_file']}")
        click.echo(f"    Binary: {tool['binary']}")
        click.echo("")


@cli.command(name="check")
@click.argument("source", required=False, default="-")
@click.option("--target", help="Target tool (for tool-specific patterns)")
@click.option("--strict", is_flag=True, help="Fail on any tool-specific reference")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def check_cmd(source, target, strict, json_output):
    """Validate a skill for tool-specific references.

    SOURCE can be a local file path or '-' for stdin.
    If SOURCE is omitted, stdin is used.
    """
    try:
        if source == "-":
            if sys.stdin.isatty():
                click.echo("Reading from stdin (Ctrl+D to finish)...", err=True)
            from usc.fetcher import fetch_stdin
            content = fetch_stdin()
        else:
            path = Path(source)
            if not path.exists():
                click.echo(f"Error: file not found: {source}", err=True)
                sys.exit(1)
            content = path.read_text(encoding="utf-8")

        tools_list = [target] if target else None
        findings = find_tool_specific_references(content, tools=tools_list)
        report = validate_skill(content, strict=strict, tools=tools_list)
        # findings already set by validate_skill with same filter, no need to overwrite

        if json_output:
            click.echo(json.dumps(report, indent=2))
        else:
            click.echo(format_validation_report(report))

        if not report['is_clean']:
            sys.exit(1)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.command(name="batch")
@click.argument("paths", nargs=-1, required=True)
@click.option("--target", required=True, help="Target tool")
@click.option("--output-dir", help="Output directory for converted skills")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--dry-run", is_flag=True, help="Preview without writing")
@click.option("--no-recursive", is_flag=True, help="Don't search subdirectories")
def batch_cmd(paths, target, output_dir, force, dry_run, no_recursive):
    """Convert multiple skills in bulk."""
    try:
        files = find_skill_files(list(paths), recursive=not no_recursive)

        if not files:
            click.echo("No .md skill files found for the given paths.", err=True)
            sys.exit(1)

        click.echo(f"Found {len(files)} skill file(s).")

        results = batch_convert(
            list(paths),
            target=target,
            output_dir=output_dir,
            force=force,
            dry_run=dry_run,
        )

        print_batch_results(results)

        failed = sum(1 for r in results if not r["success"])
        if failed:
            sys.exit(1)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


def cli_entry():
    cli()
