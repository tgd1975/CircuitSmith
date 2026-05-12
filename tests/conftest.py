"""
Make `.claude/skills/circuit/` importable as `circuit` for the test suite.

The skill directory is the library (ADR-0007); during development it
lives at `.claude/skills/circuit/`, which is not on `sys.path` by
default. This conftest splices it in so tests can `import circuit.schema`
the same way an extracted standalone-repo consumer would.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SKILL_PARENT = Path(__file__).resolve().parents[1] / ".claude" / "skills"
if str(_SKILL_PARENT) not in sys.path:
    sys.path.insert(0, str(_SKILL_PARENT))
