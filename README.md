# cicada-petersen

Petersen lab extensions for [CICADA](https://cicada-analysis.readthedocs.io/): the lab's NWB conventions, analysis
tools and analysis plugins, installed next to the core packages (cicada-nwb, cicada-analysis, cicada-gui) and
found by them automatically.

Contents: the Petersen lab plugins ([catalogue](docs/plugins.md)), the lab analysis tools
([reference](docs/tools.md)) and `session.petersen` (below), moved from cicada-nwb and cicada-analysis.

## Clone the repo

```bash
git clone https://github.com/LSENS-BMI-EPFL/cicada_petersen.git /path/to/cicada_petersen
```

## Install

Run this from the repo folder. It installs the lab extension in editable mode, and pip installs the core CICADA
packages it depends on (`cicada-nwb`, `cicada-analysis`) from PyPI.

```bash
conda create -n cicada_lab python=3.11
conda activate cicada_lab
cd /path/to/cicada_petersen
pip install -e .            # headless: cicada-nwb + cicada-analysis
pip install -e ".[gui]"     # same, plus the CICADA GUI (cicada-gui)
```

Pick one of the two `pip install` lines. Optional extras, combined with commas (e.g. `".[gui,brain_atlas]"`):

- `brain_atlas`: the 3D brain view of the units (plugin "Unit 3D brain"): `iblatlas`, `plotly`
- `dev`: the tests (`pytest`)

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

