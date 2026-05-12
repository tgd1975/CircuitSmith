"""Tests for scripts/portability_lint.py — use synthetic fixture trees."""

import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import portability_lint as pl


def _write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestEmptyAndMissing(unittest.TestCase):

    def test_missing_directory_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp) / "does-not-exist"
            self.assertEqual(pl.lint(t), [])

    def test_empty_directory_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            self.assertEqual(pl.lint(t), [])

    def test_directory_with_only_dotfiles_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / ".portability-allow.txt", "")
            self.assertEqual(pl.lint(t), [])


class TestForbiddenPatterns(unittest.TestCase):

    def test_absolute_linux_home_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "renderer.py", 'DATA = "/home/tobias/notes/foo.json"\n')
            findings = pl.lint(t)
            self.assertTrue(any("absolute path" in f for f in findings),
                            f"got: {findings}")

    def test_user_home_dokumente_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "renderer.py", 'P = "~/Dokumente/Projekte/foo"\n')
            findings = pl.lint(t)
            self.assertTrue(any("user-home path" in f for f in findings),
                            f"got: {findings}")

    def test_import_from_scripts(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "erc.py", "from scripts.housekeep import foo\n")
            findings = pl.lint(t)
            self.assertTrue(
                any("`scripts.`" in f for f in findings),
                f"got: {findings}",
            )

    def test_import_from_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "erc.py", "from data.config import settings\n")
            findings = pl.lint(t)
            self.assertTrue(any("`data.`" in f for f in findings),
                            f"got: {findings}")

    def test_docs_builders_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "renderer.py", 'PATH = "docs/builders/wiring/x.md"\n')
            findings = pl.lint(t)
            self.assertTrue(any("docs/builders/" in f for f in findings),
                            f"got: {findings}")

    def test_circuitsmith_name_in_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "renderer.py", "# loaded by CircuitSmith\n")
            findings = pl.lint(t)
            self.assertTrue(
                any("CircuitSmith" in f for f in findings),
                f"got: {findings}",
            )


class TestDocsException(unittest.TestCase):

    def test_sibling_name_in_code_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "renderer.py",
                   '# inherited from AwesomeStudioPedal\n')
            findings = pl.lint(t)
            self.assertTrue(
                any("AwesomeStudioPedal" in f for f in findings),
                f"got: {findings}",
            )

    def test_sibling_name_under_docs_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(
                t / "docs" / "history.md",
                "Inherited from AwesomeStudioPedal IDEA-027.\n",
            )
            findings = pl.lint(t)
            self.assertEqual(findings, [])

    def test_partsledger_under_docs_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "docs" / "neighbours.md",
                   "PartsLedger is the inventory sibling.\n")
            findings = pl.lint(t)
            self.assertEqual(findings, [])

    def test_circuitsmith_under_docs_still_flagged(self):
        # CircuitSmith (host project name) has NO docs exception —
        # the skill should not refer to its host project even in docs.
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "docs" / "x.md", "Used by CircuitSmith.\n")
            findings = pl.lint(t)
            self.assertTrue(any("CircuitSmith" in f for f in findings),
                            f"got: {findings}")


class TestAllowList(unittest.TestCase):

    def test_allow_list_suppresses_matching_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "shim.py", 'DEFAULT = "/home/ci/cache"\n')
            _write(
                t / ".portability-allow.txt",
                "shim.py:absolute path:legacy CI cache path, removed in v0.2\n",
            )
            findings = pl.lint(t)
            self.assertEqual(findings, [])

    def test_allow_list_misses_other_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "a.py", 'PATH = "/home/tobias/x"\n')
            _write(t / "b.py", 'PATH = "/home/tobias/y"\n')
            _write(
                t / ".portability-allow.txt",
                "a.py:absolute path:legacy\n",
            )
            findings = pl.lint(t)
            # a.py is allowed, b.py is not
            self.assertTrue(any("b.py" in f for f in findings))
            self.assertFalse(any("a.py" in f for f in findings))

    def test_allow_list_comments_and_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "a.py", 'PATH = "/home/x/y"\n')
            _write(
                t / ".portability-allow.txt",
                "# this is a comment\n"
                "\n"
                "a.py:absolute path:legacy\n",
            )
            findings = pl.lint(t)
            self.assertEqual(findings, [])

    def test_malformed_allow_lines_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "a.py", 'PATH = "/home/x/y"\n')
            _write(
                t / ".portability-allow.txt",
                "this is not a valid line\n"
                "a.py:absolute path:legacy\n",
            )
            findings = pl.lint(t)
            self.assertEqual(findings, [])


class TestCleanFixture(unittest.TestCase):

    def test_clean_tree_returns_no_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = pathlib.Path(tmp)
            _write(t / "netgraph.py", "def build():\n    pass\n")
            _write(t / "schema" / "circuit.schema.json", "{}\n")
            _write(t / "docs" / "intro.md", "# Intro\n\nHello.\n")
            findings = pl.lint(t)
            self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
