"""The lab's plugins and NWB submodule are found by the core packages once this package is installed, and every
plugin sets up its parameters on the demo files it accepts (cicada_analysis.demo)."""
import pytest

from cicada_analysis import demo
from cicada_analysis.base.plugin_registry import discover_plugins
from cicada_nwb import NWBSession
from cicada_nwb.nwb_session import lab_submodule_classes

from cicada_petersen.nwb.petersen import NWBPetersenLab

N_PLUGINS = 11
REGISTRY = discover_plugins()
PLUGINS = sorted((p for p in REGISTRY.plugins.values() if p.source == "petersen"), key=lambda p: p.module)


def test_plugins_found_without_errors():
    assert not REGISTRY.errors
    assert len(PLUGINS) == N_PLUGINS
    assert all(p.module.startswith("cicada_petersen.plugins.") for p in PLUGINS)


def test_lab_submodule_attached():
    classes, errors = lab_submodule_classes()
    assert not errors and classes["petersen"] is NWBPetersenLab
    with NWBSession(str(demo.path(demo.names()[0]))) as session:
        assert isinstance(session.petersen, NWBPetersenLab)


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.cls.__name__)
def test_plugin_sets_up_on_demo_files(plugin):
    accepted = 0
    for name in demo.names():
        with NWBSession(str(demo.path(name))) as session:
            analysis = plugin.cls()
            analysis.set_data([session])
            if analysis.check_data():
                analysis.setup_parameters()
                accepted += 1
            else:
                assert analysis.invalid_data_help, f"{name}: refused without a message"
    print(f"{plugin.cls.__name__}: {accepted} demo file(s) accepted")
