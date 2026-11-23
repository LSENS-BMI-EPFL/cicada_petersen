@cicada_ai_helpers/cicada_claude.md
@cicada_ai_helpers/cicada_nwb_api.md
@cicada_ai_helpers/cicada_tools_api.md

# cicada-petersen: notes for Claude Code (lab package developers)

This file is for people who work on **cicada-petersen**, the Petersen lab package for CICADA, and for Claude Code when a session runs in this repo. It works together with `.claude/agents/` and the CICADA helper files imported above.

## Where this repo sits
- A **lab package** for CICADA. It depends on the core packages **as released on PyPI** (`cicada-nwb`, `cicada-analysis`, optionally `cicada-gui`, `>=0.5.0,<0.6`, see `pyproject.toml`). The core packages find it through its entry points: `cicada_nwb.lab_submodules` (`session.petersen`) and `cicada_analysis.plugins` (the plugins).
- Contents: `cicada_petersen/nwb/` (`NWBPetersenLab`: the lab's NWB conventions), `cicada_petersen/tools/` (lab computations and figures), `cicada_petersen/plugins/` (Behavior, Ephys, Widefield), `tests/`, `docs/` (plugin catalogue, tools reference).
- This repo is self-contained. Work here only on cicada-petersen.

## The core is read-only
- **Never edit the CICADA core packages**: not in site-packages, and not in any git clone of the core. Never propose a core patch as the fix.
- When a traceback ends in core code, fix how cicada-petersen calls it. If a core tool was removed or changed in a release, give the lab package its own copy in `cicada_petersen/tools/`, copied verbatim and then fixed if needed.
- A real core bug or a missing feature goes into a short note for the core developer: what fails, a minimal reproduction, the version. The work here continues around it.
- To read core code, use the installed version: `C:\Users\rdard\Anaconda3\envs\cicada_petersen\Lib\site-packages\cicada_analysis\` (and `cicada_nwb\`). The installed version is what users run.

## Setup
- Env: conda `cicada_petersen` (Python 3.11): PyPI core 0.5.0 and this repo in editable mode. Its python is `C:\Users\rdard\Anaconda3\envs\cicada_petersen\python.exe`; use it explicitly from the tools, since the shell's default python is base Anaconda.
- Fresh install: `pip install -e ".[dev]"` (add `gui`, `brain_atlas` as needed). Core packages come from PyPI; never install them from a clone into this env.

## Tests
- `pytest --basetemp C:\t` from the repo root: package rules (`tests/test_package.py`) and plugin discovery and setup on the demo files (`tests/test_plugins_found.py`). Keep `N_PLUGINS` there equal to the number of plugins.
- Plugin matrix (`tests/test_plugin_matrix.py`, from the lab package template): every plugin × every CICADA demo file × parameter sets, run with the core's `cicada_analysis.testing.matrix`. Set 0 (defaults) runs with plain `pytest`; sets 1–19 are `slow`.
  - Before committing a change to a plugin, or to a `tools/` module it uses, run that plugin's matrix:
    `pytest -m "slow or not slow" -k CicadaWidefieldPsth tests/test_plugin_matrix.py --basetemp C:\t`
  - `-k` takes the plugin's class name. A change to a tool shared by several plugins runs the whole matrix (in the background, through cicada-tester).
- A matrix case passes when the plugin either refuses the file (`check_data` with a message), refuses the parameters with a message, or runs and saves non-empty outputs. A run that saves an empty output, or nothing at all, must print why.
- The demo files are trimmed real recordings (`cicada_analysis.demo`): short windows, trial tables that don't start at 0, raw widefield files not linked. Lab code must handle them, refusing with a message where needed.

## Conventions
- **Top-level imports only.** Never import inside a function. An optional dependency (e.g. `iblatlas`, `plotly` for `brain_atlas`) goes in a guarded `try: import` at module top with a `HAS_X` flag.
- **`nwb/` never imports `cicada_analysis`** (tested). Plugins and tools use cicada-nwb only through the session object (its getters and `session.petersen`), never through its module paths or constants, except `NWBSession` in tests.
- **Plugins are thin wrappers.** The plugin handles parameters, the session loop and saving; computation goes in `cicada_petersen/tools/`. **Tools read no NWB**: arrays and tables go in, results come out.
- **Lab data travels with the package.** No network or lab-server paths (`\\sv-nas1...`) in code: reference files go under `cicada_petersen/tools/data/`, declared as package data in `pyproject.toml`, with a README giving their source.
- **Replacing a computation needs proof first.** Before swapping a code path, compare the old path (copied verbatim) with the new one on artificial data covering every branch and edge case: exact equality of outputs and return format. Show the result, then edit. Flag intentional behaviour changes as such. Proof scripts go in the scratchpad, not in the repo.
- **Plugin methods:**
  - `setup_parameters()` and `run_analysis()` call `super()` first.
  - `copy()` returns a fresh instance.
  - `check_data()` sets `self.invalid_data_help` before returning False. When a plugin needs data the session lacks (a trial table, the raw widefield 'F' acquisition, a lab column), `check_data` refuses; the plugin never crashes on it.
  - Defaults match the parameter type: a `multiple_choices=True` parameter defaults to a list (`[]`), never `False`.
  - Parameter dependencies are declared with `set_parameter_rules(name, enabled_if=..., requires_data=...)`. Cross-parameter checks go in `validate_parameters()`.
- **No global randomness**: take a seed (`self.add_random_seed_arg_for_gui`, `self.random_generator(**kwargs)`). **No `plt.show()`**; `plt.xkcd()` only as a context manager. Save figures with the core `save_figure`.
- **Dependencies:** a version range in `pyproject.toml`; ask Robin before adding a heavy one.
- **Docs:** keep `docs/plugins.md` and `docs/tools.md` in line with the code when adding or removing a plugin or tool.
- **Commits:** short imperative message, one fix per commit. Never commit `.vscode/` or local settings. No revision item IDs (B4, A7…) in code, comments, docstrings or tests.

## Who does what: the main session, the agents, the developer
The main session (run it on the strongest model available) and the developer running it make the decisions; the agents in `.claude/agents/` do the legwork.
- **Stays in the main session:** choosing what to change and where, options with a recommendation, reading a proof result, commits, and every edit to plugins and `tools/`. These are made one Edit at a time, so the developer validates each diff inline.
- **Delegate, with a brief that gives the files, the expected result and what not to touch:**
  - `Explore`: where is X, who calls Y. It returns paths and line numbers.
  - `cicada-reader` (read-only): how a plugin, tool or core function works, the path of a value from session to figure, a summary of a long log.
  - `cicada-coder`: tests, proof scripts, docs, docstrings, small edits specified file by file. It never commits.
  - `cicada-tester`: one test command run as given (6 GB cap, `--basetemp C:\t`), with failures and timings reported back and the full output in a log file.
- **Don't delegate** a task whose brief would be longer than doing it, or one that needs the conversation.
- **A delegated result is a claim:** open the file at the line, or run the test, before acting on it.
