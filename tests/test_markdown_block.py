"""
Tests for the Markdown ```circuit block rewriter (TASK-036).

Covers:
  1. A ```circuit block rewrites to an image embed pointing at a
     hash-named SVG that exists on disk.
  2. The hash is deterministic across two renders of the same source
     and the embed path is identical.
  3. Stale-hash detection: --check exits non-zero when a block's
     current hash has no matching SVG on disk.

The show_source flag (TASK-037) is exercised in test_markdown_block_show_source.py.
"""
from __future__ import annotations

from pathlib import Path

from circuitsmith.markdown import (
    compute_hash,
    find_blocks,
    main,
    rewrite_markdown,
)


def _esp32_block_body() -> str:
    return (
        "meta:\n"
        "  title: ESP32 LED demo\n"
        "  target: esp32\n"
        "components:\n"
        "  U1:  { type: mcu/esp32 }\n"
        "  R1:  { type: passives/resistor, value: 220 }\n"
        "  D1:  { type: passives/led, color: green }\n"
        "  SW1: { type: passives/pushbutton }\n"
        "connections:\n"
        "  - net: PWR_LED\n"
        "    path: [U1.D25, R1.1, R1.2, D1.A, D1.K, GND]\n"
        "  - net: BTN_A\n"
        "    path: [U1.D13, SW1.1, SW1.2, GND]\n"
        "    pull: firmware\n"
        "  - net: GND\n"
        "    pins: [U1.GNDL]\n"
    )


def _wrap_block(body: str, flags: str = "") -> str:
    suffix = f" {flags}" if flags else ""
    return f"# Title\n\nIntro paragraph.\n\n```circuit{suffix}\n{body}\n```\n\nOutro paragraph.\n"


def test_compute_hash_is_deterministic_and_8_chars():
    body = _esp32_block_body()
    h1 = compute_hash(body)
    h2 = compute_hash(body)
    assert h1 == h2
    assert len(h1) == 8
    assert all(c in "0123456789abcdef" for c in h1)


def test_find_blocks_returns_each_block_in_order():
    body_a = "meta: { title: a, target: esp32 }\ncomponents: {}\nconnections: []\n"
    body_b = "meta: { title: b, target: esp32 }\ncomponents: {}\nconnections: []\n"
    md = (
        f"intro\n\n```circuit\n{body_a}\n```\n\nmid\n\n```circuit show_source\n{body_b}\n```\nend\n"
    )
    blocks = find_blocks(md)
    assert len(blocks) == 2
    assert blocks[0].source == body_a
    assert blocks[0].show_source is False
    assert blocks[1].source == body_b
    assert blocks[1].show_source is True


def test_rewrite_produces_image_embed_with_hash_in_filename(tmp_path: Path):
    body = _esp32_block_body()
    md_path = tmp_path / "guide.md"
    md_path.write_text(_wrap_block(body))

    changed, _messages = rewrite_markdown(md_path)
    assert changed

    expected_hash = compute_hash(body)
    out = md_path.read_text()
    expected_relpath = f"guide.circuits/{expected_hash}.svg"
    assert f"![circuit]({expected_relpath})" in out
    assert (tmp_path / "guide.circuits" / f"{expected_hash}.svg").exists()


def test_rewrite_is_idempotent_when_svg_already_exists(tmp_path: Path):
    body = _esp32_block_body()
    md_path = tmp_path / "guide.md"
    md_path.write_text(_wrap_block(body))

    rewrite_markdown(md_path)
    md_after_first = md_path.read_text()

    # Re-running on the already-rewritten file does nothing — there are
    # no remaining ```circuit blocks to rewrite.
    changed, _messages = rewrite_markdown(md_path)
    assert not changed
    assert md_path.read_text() == md_after_first


def test_check_mode_exits_nonzero_when_block_unrewritten(tmp_path: Path, capsys):
    body = _esp32_block_body()
    md_path = tmp_path / "guide.md"
    md_path.write_text(_wrap_block(body))

    code = main(["--check", str(md_path)])
    # block has not been rendered yet — SVG is missing → exit 2 (FAIL).
    assert code == 2
    captured = capsys.readouterr()
    assert "MISSING" in captured.out


def test_check_mode_passes_after_rewrite(tmp_path: Path):
    body = _esp32_block_body()
    md_path = tmp_path / "guide.md"
    md_path.write_text(_wrap_block(body))

    # Render the SVG once …
    assert main([str(md_path)]) == 0
    # … and confirm --check sees no drift.
    assert main(["--check", str(md_path)]) == 0


# ── TASK-037: show_source flag ─────────────────────────────────────────────


def test_show_source_wraps_embed_in_details_block(tmp_path: Path):
    body = _esp32_block_body()
    md_path = tmp_path / "guide.md"
    md_path.write_text(_wrap_block(body, flags="show_source"))

    rewrite_markdown(md_path)
    out = md_path.read_text()

    # The <details> wrapper, the summary, the embed, and the verbatim YAML
    # all land in the rewrite.
    assert "<details>" in out
    assert "<summary>circuit source</summary>" in out
    assert "</details>" in out
    # The verbatim YAML survives the round-trip inside a fenced yaml block.
    assert "```yaml" in out
    assert "meta:\n  title: ESP32 LED demo" in out


def test_show_source_absent_yields_plain_embed(tmp_path: Path):
    body = _esp32_block_body()
    md_path = tmp_path / "guide.md"
    md_path.write_text(_wrap_block(body))  # no flags

    rewrite_markdown(md_path)
    out = md_path.read_text()

    # No <details> wrapper when the flag is absent — TASK-036 baseline.
    assert "<details>" not in out
    assert "<summary>" not in out
    # Just the image embed.
    expected_hash = compute_hash(body)
    assert f"![circuit](guide.circuits/{expected_hash}.svg)" in out
