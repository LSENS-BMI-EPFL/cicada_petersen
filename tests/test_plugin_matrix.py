"""
Plugin matrix: every plugin of this package x every CICADA demo file x parameter sets, as the core plugins are tested.
Set 0 (default values) runs with plain `pytest`; sets 1-19 (values drawn from the parameter schema, ~70 % relevant,
~30 % invalid) run with `pytest -m slow`. A set passes when the plugin refuses the file (check_data), refuses the
parameters with a message, or runs and saves non-empty outputs (or explains why it saved nothing).
One plugin: `pytest -m "slow or not slow" -k CicadaWidefieldPsth tests/test_plugin_matrix.py`.
Run it before committing a change to a plugin or to a tool it uses.
"""
import matplotlib
import pytest

from cicada_analysis import demo
from cicada_analysis.testing import matrix
from cicada_nwb import NWBSession

from cicada_petersen.nwb.petersen import NWBPetersenLab

matplotlib.use("Agg")

N_SETS = 20
# the plugins declared by this package (its entry point in group cicada_analysis.plugins, named as the lab submodule)
PLUGINS = matrix.plugins(NWBPetersenLab.name)
CASES = [pytest.param(cls, name, k, id=f"{cls.__name__}-{name}-set_{k:02d}",
                      marks=[pytest.mark.slow] if k > 0 else [])
         for cls in PLUGINS for name in demo.names() for k in range(N_SETS)]


@pytest.fixture(scope="session")
def sessions():
    """Demo sessions opened once and shared by the cases, {name: session}."""
    opened = {}

    def get(name):
        if name not in opened:
            opened[name] = NWBSession(str(demo.path(name)))
        return opened[name]
    yield get
    for session in opened.values():
        session.close()


def test_plugins_found():
    assert PLUGINS, "no plugin found: is the package installed (pip install -e .) with its entry points?"


@pytest.mark.parametrize("cls, data_name, set_index", CASES)
def test_plugin_set(cls, data_name, set_index, sessions, tmp_path):
    result = matrix.run_set(cls, sessions(data_name), data_name, set_index, tmp_path)
    assert not matrix.problems(result), "\n".join(matrix.problems(result)) + "\n" + matrix.describe(result)
