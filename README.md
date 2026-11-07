# cicada-petersen

Petersen lab extensions for [CICADA](https://cicada-analysis.readthedocs.io/): the lab's NWB conventions, analysis
tools and analysis plugins, installed next to the core packages (cicada-nwb, cicada-analysis, cicada-gui) and
found by them automatically.

> Status: skeleton (revision item B6). The Petersen code moves here from cicada-nwb and cicada-analysis during the
> announced freeze of revision item B4.

## Install

From the folder containing the CICADA repos (core packages installed first, in editable mode for development):

```bash
pip install -e ./cicada_petersen --no-deps
```

`--no-deps` keeps the core packages you installed instead of fetching them again.

## Layout

| Folder | Content | Found by |
|---|---|---|
| `cicada_petersen/nwb/` | `NWBPetersenLab`: methods reading the lab's NWB conventions, available as `session.petersen` | entry-point group `cicada_nwb.lab_submodules` |
| `cicada_petersen/tools/` | lab analysis tools (arrays and tables in, results out) | imported by the plugins |
| `cicada_petersen/plugins/` | `CicadaAnalysis` plugins shown in the GUI and run headless | entry-point group `cicada_analysis.plugins` |
| `tests/` | tests of this package, on the CICADA demo files (`cicada_analysis.demo`) | pytest |

## Rules

- `nwb/` never imports `cicada_analysis` (it only builds on cicada-nwb).
- Plugins reach the lab NWB methods through the session (`session.petersen.<method>()`), never by importing `nwb/`.
- `tools/` reads no NWB: plugins read the data and pass arrays, tables or values.
- Generic tools stay in the core `cicada_tools`; import them from there rather than copying them.
- Lab code is tested here, not in the core repos.

## Versions and provenance

Installed from git with a tag (PyPI optional). The combined YAML of a run records this package's version and
commit.
