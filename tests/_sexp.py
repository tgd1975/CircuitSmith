"""
Minimal S-expression tokeniser + parser for netlist structural tests.

KiCad's intermediate-netlist grammar is a tiny subset of S-expressions:
parentheses, whitespace, quoted strings (with `\\"` escapes), and bare
atoms. A real S-expression library (`sexpdata`, `kiutils`) is overkill
for the structural assertions in `tests/test_netlist_structure.py`
(TASK-049). The dossier §"Round-trip test" pins this trade-off: tests
stay zero-dep.

The output of `parse(text)` is a nested list of strings — atoms are
bare strings, quoted strings are returned with the surrounding quotes
stripped and escapes resolved. Parentheses become list boundaries.
"""
from __future__ import annotations


def tokenise(text: str) -> list[str]:
    """Tokenise a KiCad-flavoured S-expression into a flat token list.

    Tokens:
      - "("           paren-open
      - ")"           paren-close
      - "\"...\""     quoted string (escapes resolved, quotes preserved
                      around the literal so the parser can distinguish
                      strings from bare atoms)
      - otherwise     bare atom (no spaces / no parens)
    """
    tokens: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in "()":
            tokens.append(ch)
            i += 1
        elif ch.isspace():
            i += 1
        elif ch == '"':
            j = i + 1
            chunk: list[str] = []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    chunk.append(text[j + 1])
                    j += 2
                else:
                    chunk.append(text[j])
                    j += 1
            tokens.append('"' + "".join(chunk) + '"')
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "()":
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def parse(text: str):
    """Parse a KiCad S-expression. Returns nested lists / strings.

    Quoted-string atoms are returned **without** the surrounding quotes,
    so a `(name "VCC")` form parses to `["name", "VCC"]`.
    """
    tokens = tokenise(text)
    pos = [0]

    def walk():
        token = tokens[pos[0]]
        pos[0] += 1
        if token == "(":
            items: list = []
            while tokens[pos[0]] != ")":
                items.append(walk())
            pos[0] += 1  # consume ")"
            return items
        if token.startswith('"') and token.endswith('"'):
            return token[1:-1]
        return token

    return walk()


def serialise(node) -> str:
    """Re-serialise a parsed tree. Round-trip equality should hold for
    parse(serialise(parse(text))) == parse(text).
    """
    if isinstance(node, str):
        # Empty strings must be quoted — a bare empty atom is no token at
        # all, so the round-trip drops the slot otherwise. Strings that
        # contain whitespace, parens, or quotes also need quoting.
        if node == "" or any(ch.isspace() or ch in '"()' for ch in node):
            escaped = node.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'
        return node
    return "(" + " ".join(serialise(child) for child in node) + ")"


__all__ = ["tokenise", "parse", "serialise"]
