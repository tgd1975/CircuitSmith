---
id: TASK-018
title: Add --no-ai fallback flag to layout.py
status: open
opened: 2026-05-12
effort: Small (<2h)
complexity: Junior
human-in-loop: No
epic: circuit-renderer-layout
order: 11
prerequisites: [TASK-017]
---

## Description

Add the `--no-ai` flag to `.claude/skills/circuit/layout.py` so
contributors without API access can still render — when `--no-ai` is
set, a `no-canonical-rule` escalation surfaces directly as a fail-loud
diagnostic instead of triggering the AI placer.

This is the contributor-friendly fallback per `layout §13`. It also
serves as the deterministic CI mode for cost-free runs.

## Acceptance Criteria

- [ ] `layout.py --no-ai` runs the kernel + router + rubric without invoking the AI placer.
- [ ] A `no-canonical-rule` escalation under `--no-ai` produces a structured fail-loud diagnostic and non-zero exit code.
- [ ] The CI pipeline uses `--no-ai` by default — only triggered manually for AI-placer runs.
- [ ] Both shipped circuits pass under `--no-ai` (kernel-only path is sufficient).

## Test Plan

Add CLI integration test: `python layout.py --no-ai data/esp32.circuit.yml` produces the expected SVG; a synthetic circuit with no canonical-slot rule produces the expected fail-loud exit code.

## Prerequisites

- **TASK-017** — AI placer must exist so `--no-ai` has something to suppress.

## Notes

See `idea-001.layout-engine-concept.md §13`.
