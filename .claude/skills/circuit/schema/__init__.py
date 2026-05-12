"""
.circuit.yml schema validation.

Two phases per `idea-001.yaml-format.md` §"Schema Validation":

1. JSON Schema (`circuit.schema.json`) enforces structural shape — required
   sections, the three connection forms, identifier patterns. Static, no
   knowledge of the component library.
2. Post-schema validator (`validator.validate`) walks
   `.claude/skills/circuit/components/*.py`, builds the registry of valid
   `type:` strings and per-profile pin sets, and emits S4 / S5 findings.

Usage:

    from circuit.schema import validate
    findings = validate(circuit_dict)  # list[Finding]; empty == valid
"""

from .validator import Finding, validate, validate_file

__all__ = ["Finding", "validate", "validate_file"]
