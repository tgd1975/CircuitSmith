"""
Markdown ` ```circuit ` block scanner and rewriter.

A ` ```circuit ` fenced block holds an inline `.circuit.yml` snippet.
The block is rendered to an SVG and the source block is replaced with
an embed pointing at the generated artefact. Filenames carry an
8-char hex hash of the source YAML so stale embeds are detected by
file-name lookup alone — no contents diff required.

The block fence supports two info-string forms:

  ```circuit               → embed only (default)
  ```circuit show_source   → embed wrapped in a <details> block that
                             reveals the source YAML (TASK-037).

The output sits next to the source `.md` in a sibling directory named
`<docname>.circuits/`. A doc at `docs/guide.md` with two blocks emits
`docs/guide.circuits/{hash1}.svg` and `docs/guide.circuits/{hash2}.svg`.

Two operating modes:

  rewrite — overwrite each block with the corresponding image embed.
  check   — verify every `.md` has its blocks rewritten to current
            hashes; non-zero exit on any drift. Used by CI.

This module is the EPIC-005 / IDEA-001 §Phase 5 implementation. While
IDEA-022 (MkDocs site) has not landed, the workflow at
`.github/workflows/generate-circuits.yml` runs the rewriter on push.
When IDEA-022 lands, this module's `find_blocks` + `compute_hash`
remain the canonical scanner; a `pymdownx.superfences` formatter
calls the same helpers and the workflow retires.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from circuitsmith.renderer import RenderError, render

HASH_LEN = 8
FENCE_RE = re.compile(
    r"^(?P<fence>```+)circuit(?P<flags>[^\n]*)\n(?P<body>.*?)\n(?P=fence)\s*$",
    re.DOTALL | re.MULTILINE,
)


@dataclass(frozen=True)
class Block:
    """One ` ```circuit ` block found in a Markdown file."""

    source: str
    flags: tuple[str, ...]
    span: tuple[int, int]
    fence: str

    @property
    def hash(self) -> str:
        return compute_hash(self.source)

    @property
    def show_source(self) -> bool:
        return "show_source" in self.flags


def compute_hash(yaml_source: str) -> str:
    """8-char hex SHA-256 prefix of the YAML body.

    The body is hashed verbatim — same bytes in, same hash out — so two
    documents sharing an identical snippet share one rendered SVG.
    """
    digest = hashlib.sha256(yaml_source.encode("utf-8")).hexdigest()
    return digest[:HASH_LEN]


def find_blocks(markdown: str) -> list[Block]:
    """Return every ` ```circuit ` block in `markdown`, in document order."""
    blocks: list[Block] = []
    for match in FENCE_RE.finditer(markdown):
        flags_raw = match.group("flags").strip()
        flags = tuple(f for f in flags_raw.split() if f)
        blocks.append(
            Block(
                source=match.group("body"),
                flags=flags,
                span=match.span(),
                fence=match.group("fence"),
            )
        )
    return blocks


def render_block_to_svg(yaml_source: str, out_dir: Path, name: str) -> Path:
    """Render a single block's YAML to `<out_dir>/<name>.svg`.

    Writes the YAML to a temp file next to the SVG so the existing
    `circuitsmith.renderer.render` pipeline runs unmodified. The
    layout + meta sidecars are co-located; the embed only references
    the SVG.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    yml_path = out_dir / f"{name}.circuit.yml"
    yml_path.write_text(yaml_source)
    svg_path = out_dir / f"{name}.svg"
    layout_path = out_dir / f"{name}.layout.yml"
    meta_path = out_dir / f"{name}.meta.yml"
    render(
        circuit_path=yml_path,
        layout_path=layout_path if layout_path.exists() else None,
        out_svg=svg_path,
        out_layout=layout_path,
        out_meta=meta_path,
    )
    return svg_path


def format_embed(block: Block, svg_relpath: str) -> str:
    """Build the Markdown replacement for one block.

    Without `show_source`: a plain image embed. With `show_source`: a
    `<details>` block wrapping the image and the verbatim YAML. The
    `<details>` form is native to GitHub Markdown and to MkDocs, so
    the same output works in both renderers.
    """
    img = f"![circuit]({svg_relpath})"
    if not block.show_source:
        return img
    fence = block.fence
    return (
        "<details>\n"
        "<summary>circuit source</summary>\n\n"
        f"{img}\n\n"
        f"{fence}yaml\n"
        f"{block.source}\n"
        f"{fence}\n"
        "</details>"
    )


def rewrite_markdown(md_path: Path, *, check: bool = False) -> tuple[bool, list[str]]:
    """Rewrite blocks in `md_path` to image embeds.

    Returns `(changed, messages)`. In `check` mode, no files are
    modified; `changed` reports whether a rewrite *would* happen.
    """
    text = md_path.read_text()
    blocks = find_blocks(text)
    if not blocks:
        return False, []

    out_dir = md_path.with_suffix("").with_name(md_path.stem + ".circuits")
    rel_out = out_dir.name

    pieces: list[str] = []
    cursor = 0
    messages: list[str] = []
    for block in blocks:
        h = block.hash
        svg_path = out_dir / f"{h}.svg"
        svg_relpath = f"{rel_out}/{h}.svg"
        embed = format_embed(block, svg_relpath)
        pieces.append(text[cursor : block.span[0]])
        pieces.append(embed)
        cursor = block.span[1]

        if not check:
            if not svg_path.exists():
                try:
                    render_block_to_svg(block.source, out_dir, h)
                    messages.append(f"rendered {svg_relpath}")
                except RenderError as exc:
                    messages.append(f"FAIL {md_path}: render error in block {h}: {exc.summary}")
                    return False, messages
            else:
                messages.append(f"reused {svg_relpath}")
        else:
            if not svg_path.exists():
                messages.append(f"MISSING {svg_relpath}")
    pieces.append(text[cursor:])
    new_text = "".join(pieces)

    changed = new_text != text
    if changed and not check:
        md_path.write_text(new_text)
        messages.append(f"rewrote {md_path}")
    return changed, messages


def walk(root: Path) -> list[Path]:
    """All `.md` files under `root`, sorted, excluding obvious junk."""
    skip_parts = {"node_modules", ".venv", ".git", "site"}
    out: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in skip_parts for part in path.parts):
            continue
        out.append(path)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m circuitsmith.markdown",
        description="Scan Markdown files for ```circuit blocks and render to SVG embeds.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Markdown files or directories to scan.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not modify files; exit non-zero if any rewrite is needed.",
    )
    args = parser.parse_args(argv)

    targets: list[Path] = []
    for p in args.paths:
        if p.is_dir():
            targets.extend(walk(p))
        elif p.is_file() and p.suffix == ".md":
            targets.append(p)

    any_drift = False
    any_fail = False
    out = io.StringIO()
    for md in targets:
        changed, messages = rewrite_markdown(md, check=args.check)
        if args.check and changed:
            any_drift = True
            out.write(f"DRIFT {md}\n")
        for m in messages:
            out.write(f"  {m}\n")
            if m.startswith("FAIL ") or m.startswith("MISSING "):
                any_fail = True

    sys.stdout.write(out.getvalue())
    if any_fail:
        return 2
    if args.check and any_drift:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
