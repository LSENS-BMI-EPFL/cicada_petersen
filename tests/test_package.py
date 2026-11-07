"""The package imports, and its parts follow the rules of the README."""
import ast
import importlib
import importlib.util
import pkgutil
from pathlib import Path

import cicada_petersen


def _imported_modules(path):
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def test_package_imports():
    assert cicada_petersen.__version__
    for name in ("nwb", "tools", "plugins"):
        importlib.import_module(f"cicada_petersen.{name}")


def test_nwb_part_does_not_import_cicada_analysis():
    nwb = importlib.import_module("cicada_petersen.nwb")
    for info in [None, *pkgutil.walk_packages(nwb.__path__, prefix="cicada_petersen.nwb.")]:
        name = "cicada_petersen.nwb" if info is None else info.name
        for module in _imported_modules(importlib.util.find_spec(name).origin):
            assert module.split(".")[0] != "cicada_analysis", f"{name} imports {module}"
