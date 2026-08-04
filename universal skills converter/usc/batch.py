from __future__ import annotations

import glob
from pathlib import Path
from typing import Optional

from usc.converter import convert
from usc.installer import sanitize_name


def find_skill_files(paths: list[str], recursive: bool = True) -> list[Path]:
    found: set[Path] = set()

    for raw in paths:
        path = Path(raw)

        if glob.has_magic(str(path)):
            matches = glob.glob(str(path), recursive=recursive)
            for match in matches:
                p = Path(match)
                if p.is_file() and p.suffix == ".md":
                    found.add(p.resolve())
            continue

        if path.is_file():
            if path.suffix == ".md":
                found.add(path.resolve())
            continue

        if path.is_dir():
            pattern = "**/*.md" if recursive else "*.md"
            for md_file in path.glob(pattern):
                if md_file.is_file():
                    found.add(md_file.resolve())
            continue

    return sorted(found)


def batch_convert(
    paths: list[str],
    target: str,
    output_dir: str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> list[dict]:
    from usc.detector import detect_tool
    from usc.tools_registry import get_tool

    detect_tool(target)
    files = find_skill_files(paths)
    results: list[dict] = []

    for file_path in files:
        input_path = file_path
        original_size = input_path.stat().st_size
        error: Optional[str] = None
        success = False
        output_path: Optional[str] = None
        converted_size = 0

        try:
            content = input_path.read_text(encoding="utf-8")
            converted = convert(content)
            converted_size = len(converted.encode("utf-8"))

            stem = sanitize_name(input_path.stem)
            filename = f"{stem}.md"

            if output_dir:
                out = Path(output_dir).expanduser().resolve()
                out.mkdir(parents=True, exist_ok=True)
                output_path = str(out / filename)
            else:
                output_path = str(input_path.parent / f"{input_path.stem}.converted.md")

            if not dry_run:
                dest = Path(output_path)
                if dest.exists() and not force:
                    raise FileExistsError(
                        f"Output file '{output_path}' already exists. Use --force to overwrite."
                    )
                dest.write_text(converted, encoding="utf-8")
                success = True
            else:
                success = True
                output_path = str(output_path)

        except Exception as e:
            error = str(e)
            output_path = None
            success = False

        results.append(
            {
                "input": str(input_path),
                "output": output_path,
                "success": success,
                "error": error,
                "original_size": original_size,
                "converted_size": converted_size,
            }
        )

    return results


def print_batch_results(results: list[dict]) -> None:
    if not results:
        return

    input_width = max(len(r["input"]) for r in results)
    input_width = max(input_width, 6)

    output_width = max(len(str(r["output"])) for r in results)
    output_width = max(output_width, 7)

    header = f"{'Input':<{input_width}}  {'Output':<{output_width}}  {'Size':>12}  {'Status'}"
    click = __import__("click")
    click.echo(header)
    click.echo("-" * len(header))

    for r in results:
        if r["success"]:
            size_change = f"{r['original_size']} -> {r['converted_size']}"
            status = "OK"
            output_display = str(r["output"]) if r["output"] else ""
        else:
            size_change = f"{r['original_size']} -> -"
            status = f"ERROR: {r['error']}"
            output_display = "ERROR"

        click.echo(
            f"{r['input']:<{input_width}}  {output_display:<{output_width}}  {size_change:>12}  {status}"
        )
