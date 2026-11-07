# cicada-petersen

Petersen lab extensions for [CICADA](https://cicada-analysis.readthedocs.io/): the lab's NWB conventions, analysis
tools and analysis plugins, installed next to the core packages (cicada-nwb, cicada-analysis, cicada-gui) and
found by them automatically.

Contents: the Petersen lab plugins ([catalogue](docs/plugins.md)), the lab analysis tools
([reference](docs/tools.md)) and `session.petersen` (below), moved from cicada-nwb and cicada-analysis in revision
item B4 (2026-11-07).

## Install

From the folder containing the CICADA repos (core packages installed first, in editable mode for development):

```bash
pip install -e ./cicada_petersen --no-deps
```

`--no-deps` keeps the core packages you installed instead of fetching them again.

The 3D brain view of the units (plugin "Unit 3D brain") also needs the packages of the optional extra
`brain_atlas`; in a development install: `pip install iblatlas "plotly>=5.0"`.

## Layout

| Folder | Content | Found by |
|---|---|---|
| `cicada_petersen/nwb/` | `NWBPetersenLab`: methods reading the lab's NWB conventions, available as `session.petersen` | entry-point group `cicada_nwb.lab_submodules` |
| `cicada_petersen/tools/` | lab analysis tools (arrays and tables in, results out) | imported by the plugins |
| `cicada_petersen/plugins/` | `CicadaAnalysis` plugins shown in the GUI and run headless | entry-point group `cicada_analysis.plugins` |
| `tests/` | tests of this package, on the CICADA demo files (`cicada_analysis.demo`) | pytest |

## `session.petersen`: NWB conventions of the Petersen lab

```python
# Session metadata encoded as a Python dict in experiment_description
meta = session.petersen.get_session_metadata()   # dict or None

# Session type
session.petersen.get_session_type()              # str or None
session.petersen.session_type()                  # str, 'NS' if absent

# Behavior type and training day (parsed from session_description)
bhv_type, day = session.petersen.get_bhv_type_and_training_day_index()
session.petersen.behavior_session_type()         # str, 'NS' if absent

# Whisker reward
session.petersen.get_whisker_rewarded_sessions() # 'whisker rewarded' / 'whisker not rewarded' / None
session.petersen.whisker_rewarded()              # str, 'NS' if absent

# Facemap motion data (series 'motion_energy' / 'motion_svd', SVD images in an Images acquisition)
facemap = session.petersen.get_facemap_data(image_acquisition_name="facemap_svd_images")
# facemap: dict with keys 'motion_energy', 'motion_svd', 'timestamps', 'svd_images'
```

## Rules

- `nwb/` never imports `cicada_analysis` (it only builds on cicada-nwb).
- Plugins reach the lab NWB methods through the session (`session.petersen.<method>()`), never by importing `nwb/`.
- `tools/` reads no NWB: plugins read the data and pass arrays, tables or values.
- Generic tools stay in the core `cicada_tools`; import them from there rather than copying them.
- Lab code is tested here, not in the core repos.

## Versions and provenance

Installed from git with a tag (PyPI optional). The combined YAML of a run records this package's version and
commit.
