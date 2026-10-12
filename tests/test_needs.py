"""Every module bitlaForge imports is in docs/PACKAGING.md, so the package's depends=() can't fall behind the
code (Javier, 2026-10-11: "check all Forge Suite apps for all dependencies needed to build and run them")."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
CODE = ['bitlaforge', 'main.py']
SKIP = {"tests", "testing", "scripts", "tools", "__pycache__", "docs"}


def ours() -> set[str]:
    names = set()
    for c in CODE:
        base = HERE / c
        for p in (base.rglob("*.py") if base.is_dir() else [base]):
            names.add(p.stem)
        if base.is_dir():
            names.update(p.name for p in base.rglob("*") if p.is_dir())
            names.add(base.name)
    return names


def sources():
    for c in CODE:
        base = HERE / c
        if base.is_file():
            yield base
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or SKIP & set(p.relative_to(HERE).parts):
                continue
            head = p.read_bytes()[:60]
            if p.suffix == ".py" or (not p.suffix and head.startswith(b"#!") and b"python" in head):
                yield p


def imported() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    own = ours()
    for f in sources():
        text = f.read_text(errors="replace")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.module and not node.level else []
            for n in names:
                top = n.split(".")[0]
                if top not in sys.stdlib_module_names and top not in own and top != "__future__":
                    found.setdefault(top, set()).add(f.name)
        for ns in re.findall(r'require_version\(\s*["\']([A-Za-z]+)["\']', text):
            found.setdefault(ns, set()).add(f.name)
    return found


class Needs(unittest.TestCase):
    def test_every_import_is_listed(self):
        doc = (HERE / "docs/PACKAGING.md").read_text()
        found = imported()
        self.assertTrue(found, "the scan found the app's imports")
        for module, files in sorted(found.items()):
            with self.subTest(module=module):
                self.assertRegex(doc, rf"\b{re.escape(module)}\b",
                                 f"{module} (used in {', '.join(sorted(files))}) isn't in docs/PACKAGING.md")


if __name__ == "__main__":
    unittest.main()
