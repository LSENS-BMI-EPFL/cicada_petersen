"""The package imports, and its parts follow the rules of the README."""
import importlib
import importlib.util
import pkgutil

import cicada_petersen


def test_package_imports():
    assert cicada_petersen.__version__
    for name in ("nwb", "tools", "plugins"):
        importlib.import_module(f"cicada_petersen.{name}")


def test_nwb_part_does_not_import_cicada_analysis():
    nwb = importlib.import_module("cicada_petersen.nwb")
    for info in pkgutil.walk_packages(nwb.__path__, prefix="cicada_petersen.nwb."):
        source = importlib.util.find_spec(info.name).origin
        with open(source, encoding="utf-8") as f:
            assert "cicada_analysis" not in f.read(), info.name
