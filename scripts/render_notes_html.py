#!/usr/bin/env python3
"""Render Markdown notes to styled HTML (run from repo root: python3 scripts/render_notes_html.py)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from markdown import Markdown
from pymdownx.slugs import slugify

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def write_pygments_css() -> bool:
    try:
        from pygments.formatters import HtmlFormatter
    except ImportError:
        return False
    css = HtmlFormatter(style="monokai").get_style_defs(".codehilite")
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "pygments-monokai.css").write_text(css + "\n", encoding="utf-8")
    return True


def css_href(out_file: Path) -> str:
    rel = Path(os_path_relpath(ASSETS / "notes-theme.css", out_file.parent))
    return rel.as_posix()


def pygments_href(out_file: Path) -> str:
    rel = Path(os_path_relpath(ASSETS / "pygments-monokai.css", out_file.parent))
    return rel.as_posix()


def os_path_relpath(target: Path, start: Path) -> str:
    import os

    return os.path.relpath(target, start)


def split_title(md: str) -> tuple[str, str]:
    lines = md.splitlines()
    if lines and lines[0].startswith("# ") and not lines[0].startswith("##"):
        title = lines[0][2:].strip()
        body = "\n".join(lines[1:]).lstrip("\n")
        return title, body
    return "", md


def page_template(
    *,
    title: str,
    kicker: str,
    subtitle: str,
    pills: list[str],
    body_html: str,
    out_file: Path,
    include_pygments: bool,
) -> str:
    ch = css_href(out_file)
    ph = pygments_href(out_file) if include_pygments else ""
    pyg_link = f'  <link rel="stylesheet" href="{ph}">\n' if ph else ""
    pills_html = "".join(f'<span class="doc-pill">{_esc(p)}</span>' for p in pills)
    pills_block = f'<div class="doc-meta">{pills_html}</div>' if pills else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#080c14">
  <title>{_esc(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,600;1,400&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{ch}">
{pyg_link}</head>
<body>
  <div class="doc-shell">
    <header class="doc-header">
      <div class="doc-header-inner">
        <p class="doc-kicker">{_esc(kicker)}</p>
        <h1 class="doc-title">{_esc(title)}</h1>
        <p class="doc-subtitle">{_esc(subtitle)}</p>
        {pills_block}
      </div>
    </header>
    <article class="content">
{body_html}

    </article>
    <footer class="doc-footer">
      Rendered from Markdown — <a href="https://github.com/anuragreddygv323/causal_inference">causal_inference</a>
    </footer>
  </div>
</body>
</html>
"""


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_markdown(use_pygments: bool) -> Markdown:
    exts = [
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.toc",
    ]
    ext_configs: dict = {
        "toc": {
            "slugify": slugify(case="lower"),
            "title": "",
            "toc_depth": "1-6",
        }
    }
    if use_pygments:
        exts.insert(2, "markdown.extensions.codehilite")
        ext_configs["codehilite"] = {
            "css_class": "codehilite",
            "guess_lang": True,
            "pygments_style": "monokai",
            "use_pygments": True,
        }
    return Markdown(extensions=exts, extension_configs=ext_configs)


def render_pair(
    md: Markdown,
    md_path: Path,
    html_path: Path,
    *,
    kicker: str,
    subtitle: str,
    pills: list[str],
    include_pygments: bool,
) -> None:
    raw = md_path.read_text(encoding="utf-8")
    title, body = split_title(raw)
    if not title:
        title = md_path.stem.replace("-", " ").replace("_", " ").title()

    md.reset()
    body_html = md.convert(body).strip()
    html = page_template(
        title=title.replace(" -- ", " — "),
        kicker=kicker,
        subtitle=subtitle,
        pills=pills,
        body_html=body_html,
        out_file=html_path,
        include_pygments=include_pygments,
    )
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    print(f"Wrote {html_path.relative_to(ROOT)}")


def main() -> int:
    if Path.cwd() != ROOT:
        print("Hint: run from repository root for consistent paths:", file=sys.stderr)
        print("  cd causal_inference && python3 scripts/render_notes_html.py", file=sys.stderr)

    include_pygments = write_pygments_css()
    if not include_pygments:
        print("Warning: pygments not installed; code blocks will not be syntax-highlighted.", file=sys.stderr)
    md = build_markdown(include_pygments)

    # Main living documents
    render_pair(
        md,
        ROOT / "causal-inference-notes.md",
        ROOT / "causal-inference-notes.html",
        kicker="Causal inference",
        subtitle="Methods, assumptions, decision frameworks, and links to runnable notebooks.",
        pills=["Observational & quasi-experimental", "Industry-flavored examples"],
        include_pygments=include_pygments,
    )
    render_pair(
        md,
        ROOT / "causal-inference-use-cases.md",
        ROOT / "causal-inference-use-cases.html",
        kicker="End-to-end playbooks",
        subtitle="Structured use cases: problem framing, data needs, methodology, code sketches, and pitfalls.",
        pills=["PSM · DiD · SC · ITS · IV · RDD", "HTE · Uplift · CACE · Attribution"],
        include_pygments=include_pygments,
    )

    # Method READMEs
    for md_path in sorted((ROOT / "methods").glob("*/README.md")):
        slug = md_path.parent.name
        num = re.match(r"^(\d+)", slug)
        label = f"Method {num.group(1)}" if num else "Method"
        render_pair(
            md,
            md_path,
            md_path.parent / "README.html",
            kicker=label,
            subtitle="When to use it, assumptions, checks, and alternatives.",
            pills=["Companion notebooks in repo"],
            include_pygments=include_pygments,
        )

    py_readme = ROOT / "causal-inference-in-python-code-main" / "README.md"
    if py_readme.is_file():
        render_pair(
            md,
            py_readme,
            py_readme.parent / "README.html",
            kicker="Python code",
            subtitle="O'Reilly Causal Inference in Python — companion implementation.",
            pills=["Book-linked examples"],
            include_pygments=include_pygments,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
