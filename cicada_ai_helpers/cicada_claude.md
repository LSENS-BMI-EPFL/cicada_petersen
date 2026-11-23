# CICADA — Claude Code Context

## About these helper files

**Who they are for.** For an AI coding assistant used by a lab developer who pip-installs CICADA. Core developers use each repository's `CLAUDE.md`.

**How to load them.**

1. Copy the `cicada_ai_helpers/` folder into the root of your project.
2. Add these three lines to the `CLAUDE.md` of your project (create it if it does not exist):

   ```
   @cicada_ai_helpers/cicada_claude.md
   @cicada_ai_helpers/cicada_nwb_api.md
   @cicada_ai_helpers/cicada_tools_api.md
   ```

Order: `cicada_claude.md` first.

**Where the full reference is.** The two API files summarise the main functions. The complete reference, with every function, parameter and default, is the documentation site: the cicada-tools reference (https://cicada-analysis.readthedocs.io/en/latest/analysis/cicada_tools/) and the cicada-nwb API reference (https://cicada-analysis.readthedocs.io/en/latest/nwb/api/nwb_session/).

---

## How to use the API reference files

`cicada_nwb_api.md` and `cicada_tools_api.md` are loaded into your context alongside this file. They are the **authoritative source for all method signatures, parameter names, and return shapes**. Before writing any CICADA code:

- Look up the exact signature in the relevant API file; never rely on memory or inference.
- Use the router below to identify which file and which section to consult.
- If a method name or parameter is not in the API files, check the full reference (links above) or the source (see Source code fallback); if it is still not found, say so explicitly rather than guessing.

**Preference rule:** Before writing any custom numeric/statistical/display code:
1. Check the Level 3 table and `cicada_tools_api.md` for a matching function.
2. If not found there, **grep the installed cicada_tools source before concluding nothing exists** — the API doc may be incomplete. Locate the source via the Source code fallback section below, then Grep inside `cicada_tools/` for relevant terms (e.g. `correlation`, `similarity`, `psth`, `detect`, `cluster`, `raster`, `connectivity`).
3. Only proceed with a custom implementation if the source grep also finds nothing.

---

## Source code fallback

If the API files don't cover a method or you need to verify a signature, follow this sequence:

**Step 1 — detect active Python / conda env:**
```bash
where python        # PowerShell / cmd
# or
which python        # bash
```
If the path contains `envs/<name>/` or `envs\<name>\`, the conda env name is `<name>`.

**Step 2 — get the package location:**
- If an env name was found: `conda run -n <env_name> pip show cicada-analysis`
- Otherwise: `pip show cicada-analysis`

Look at the `Location:` line — the source is at `<Location>/cicada_analysis/`.

**Step 3 — only if Step 2 gives no clear Location:** ask the user: "What is your conda environment name?"

---

## What is CICADA

CICADA is a neuroscience analysis pipeline for NWB files, in three core packages plus one package per lab:

- **`cicada-nwb`** — read-only data access. Entry point: `NWBSession`. Never computes, never writes.
- **`cicada-analysis`** — **`cicada_tools`** (computation and display functions), the **`CicadaAnalysis`** plugin system, the core plugins, the headless runner and the demo data.
- **`cicada-gui`** — the graphical interface (optional).
- **Lab packages** (`cicada-cossart`, `cicada-petersen`, yours from the template) — a lab's NWB conventions (`session.<lab>`), tools and plugins. The core packages find them through entry points once installed.

**Package layout (installed code):**
```
cicada_nwb/
├── nwb_session.py           # NWBSession (opens local files and DANDI assets)
├── submodules/              # NWBCalciumImaging, NWBBehavior, NWBElectrophysiology,
│                            #   NWBWidefield, NWBMetadata, NWBOptogenetic
├── lab_submodules/base.py   # NWBLabSubmodule: base class of the lab submodules, which live in the lab packages
├── dandi.py, cli.py         # DANDI access; `cicada-dandi` command
└── testing/                 # synthetic NWB files for tests

cicada_analysis/
├── base/cicada_analysis.py  # CicadaAnalysis ABC
├── base/cicada_groups_base.py, cicada_events_base.py, cicada_psth_base.py   # family bases (groups, events, PSTH)
├── base/argument_schema.py  # AnalysisArgument, AnalysisArgumentsHandler
├── base/plugin_registry.py  # finds the plugins (entry points + extra folders)
├── config/runner.py         # run_from_config(), run_from_combined(), generate_config()
├── config/cli.py            # `cicada-run`, `cicada-config` commands
├── core_analysis/           # core plugins (standard NWB data only)
├── cicada_tools/            # computation + display functions — see cicada_tools_api.md
└── demo/                    # 9 small real NWB files (demo.names(), demo.path(name)) and the configs that run on them

cicada_<lab>/                # a lab package (template: cicada_lab_package_template)
├── nwb/                     # NWB<Lab>(NWBLabSubmodule) → session.<lab>   (entry-point group cicada_nwb.lab_submodules)
├── tools/                   # the lab's computations, arrays in / results out
└── plugins/                 # the lab's CicadaAnalysis plugins              (entry-point group cicada_analysis.plugins)
```

---

## Critical invariants

1. `NWBSession` must always be closed after use. Choose the pattern based on the requirements:

   **Default — process one session at a time and aggregate** (memory-efficient; use whenever per-session results can be merged after the loop):
   ```python
   from cicada_nwb import NWBSession
   results = []
   for path in nwb_paths:
       with NWBSession(path) as session:
           results.append(session.calcium_imaging.get_roi_response_serie_data(keys=[...]))
   # merge results after the loop
   ```

   **All sessions open simultaneously** — use only when the computation cannot be decomposed per session, e.g. cross-session normalization, computing a common reference across all sessions at once:
   ```python
   from cicada_nwb import NWBSession
   sessions = [NWBSession(path) for path in nwb_paths]
   try:
       # work across all open sessions
       ...
   finally:
       for s in sessions:
           s.close()
   ```
2. **cicada-nwb always returns epochs and events as `(2, N)`**: row 0 = start times, row 1 = stop times. However, many cicada-tools functions expect event timestamps as a flat `(N,)` array. Extract the relevant row before passing:
   ```python
   epochs = session.behavior.get_behavioral_epochs_times("running")  # (2, N)
   events = session.behavior.get_behavioral_events_times("reward")   # (2, N)

   # cicada-tools that take full epoch intervals: pass (2, N) as-is
   # e.g. from_timestamps_to_frame_epochs, filter_epoch_timestamps, filter_events_based_on_epochs

   # cicada-tools that take a list of event times: extract row 0 (start times)
   # e.g. align_array_to_timestamps, compute_psth
   event_times = events[0]   # (N,)
   ```
   Check each cicada-tools function's signature in `cicada_tools_api.md` to confirm expected shape.
3. The `keys` argument for calcium imaging methods is a 3-element list `[module_name, interface_name, rrs_name]`. Always discover valid keys first with `session.calcium_imaging.get_roi_response_series()`.
4. Do **not** store `get_widefield_dff0_mmap()` results outside the `with` block — the HDF5 handle closes.
5. A lab submodule (`session.cossart`, `session.petersen`, `session.<lab>`) is attached to every `NWBSession` **when that lab package is installed** (entry-point group `cicada_nwb.lab_submodules`); no import needed, but check the package is installed (`pip show cicada-<lab>`) before relying on it. Core plugins must not use them.

---

## Router — top-down resolution protocol

Always resolve top-down. At each level, if the needed information is missing or ambiguous, ask **one** clarifying question before proceeding. If the request is specific enough that modality and data type are clear, skip directly to the relevant level. **If a clarifying answer changes a previous assumption, restart from Level 1.**

---

### Level 0 — Classify the request by intent

Classify by what the user is trying to accomplish, not by the verb used:

| Request type | Indicators | How to proceed |
|---|---|---|
| **Conceptual / design** | Describes a scientific goal without naming data types or methods | Ask targeted questions to gather the minimum context needed: (1) what type of neural recording? (2) what behavioral or experimental variable? (3) what output is expected? Then resolve each component through Levels 1–3. |
| **Data extraction** | Wants to retrieve specific data from NWB files | Level 1 → Level 2 |
| **Computation / analysis / display** | Wants to process, transform, or visualize data | Level 1 (confirm modality) → Level 3 |
| **Compound** | Involves both extraction and computation, or neural + behavioral data together | Resolve each component independently. For neural + behavioral: establish neural modality and behavioral modality separately at Level 1, extract each at Level 2, then compose at Level 3. Extraction always before computation. |

---

### Level 1 — Establish data modality

**Principle:** a term is modality-ambiguous if it could plausibly apply to more than one row in the table below. When in doubt, treat it as ambiguous. Do not infer modality from surrounding context alone — only a term that directly maps to a unique row below counts as unambiguous.

Ambiguous terms include but are not limited to: `timestamps` · `traces` · `data` · `signal` · `activity` · `recording` · `frames` · `rate` · `events` · `response` · `onset` · `baseline` · `population` · `epoch-aligned` · `trial-averaged`

| If the description unambiguously refers to… | Modality → Submodule |
|---|---|
| Fluorescence, dF/F0, calcium, ROI, optically imaged cells, two-photon, one-photon, GCaMP | Calcium imaging → `session.calcium_imaging` |
| Running, licking, reward, movement, trial, stimulus, locomotion, position, speed, behavioral state | Behavior → `session.behavior` |
| Spikes, units, electrodes, LFP, extracellular, multi-unit, Neuropixels, tetrode | Electrophysiology → `session.electrophysiology` |
| Widefield, mesoscale, dorsal cortical imaging | Widefield → `session.widefield` |
| Optogenetic stimulation, light pulses, opto trials | Optogenetics → `session.optogenetic` |
| Animal info, age, genotype, sex, weight, experimenter, lab, session description | Metadata → `session.metadata` (properties: `age`, `age_unit`, `genotype`, `sex`, `species`, `subject_id`, `session_id`, `weight`, `lab`, `experimenter`, `session_description`; `get_sessions_info()` for a dict) |
| Lab-specific conventions (a lab's own tables, labels, naming) | Lab submodule → `session.<lab>` (only with the lab package installed, see invariant 5) |

If still ambiguous: **"Is this data from calcium imaging, electrophysiology, behavior, widefield imaging, or optogenetic stimulation?"**

---

### Level 2 — Identify specific data within the modality

When names are unknown, always run discovery first and **show the results to the user to confirm which to use** before calling any data accessor.

**Calcium imaging**

Discovery:
```python
session.calcium_imaging.get_roi_response_series()
# → nested dict {module: {interface: [rrs_name, ...]}}
# If multiple series exist, present the options and ask which to use.
```
Build `keys = [module_name, interface_name, rrs_name]` from the chosen series, then:

| User wants… | Method | Returns |
|---|---|---|
| Fluorescence / activity values | `get_roi_response_serie_data(keys)` | `(n_cells, n_times)` |
| What kind of activity a series holds (traces, raster dur, binary raster, spike counts, event amplitudes) | `get_roi_response_serie_kind(keys)`, or the questions `is_traces(keys)`, `is_raster_dur(keys)`, `is_binary_raster(keys)`, `is_spike_counts(keys)`, `is_sparse_activity(keys)`; `get_roi_response_series_by_kind(kind)` lists the series of a kind | str / bool / `[[module, interface, name], ...]` |
| Time axis for traces | `get_roi_response_serie_timestamps(keys)` | `(n_times,)` |
| Sampling rate | `get_rrs_sampling_rate(keys)` | float Hz |
| Cell types or indices per type | `get_cell_indices_by_cell_type(keys)` | `{type: indices}` |
| Cells passing quality control (`good_cells` / suite2p `iscell` column) | `has_good_cells(keys)`, `get_good_cells(keys)` | bool / `(n_cells,)` bool array or None |
| Per-cell SNR (if present in ROI table) | `get_cell_snr(keys)` | `[float, ...]` or `[]` |
| Spatial footprints / masks | `get_segmentations()` → build `seg_info`, then `get_pixel_mask(seg_info)` or `get_image_mask(seg_info)` | list of arrays |
| Raw movie frames or movie info | `get_ci_movies(only_2_photons)`, `get_ci_movie_dimension(only_2_photons=False, ci_movie_name=None)`, `get_ci_movie_sampling_rate(only_2_photons=False, ci_movie_name=None)`, `get_ci_movie_time_stamps(ci_movie_name=None)` | — |

**Behavior**

Discovery:
```python
session.behavior.get_behavioral_epochs_names()        # on/off state periods with duration (BehavioralEpochs)
session.behavior.get_behavioral_events_names()        # discrete events (BehavioralEvents, ndx-events, EventsTable with pynwb >= 4)
session.behavior.get_behavioral_time_series_names()   # continuous signals (speed, position, pupil...)
session.behavior.get_intervals_names()                # interval tables: trials, epochs, stimulus presentations...
session.behavior.has_trial_table()                    # structured trial table
```
If the user says "events" or "epochs" without specifying which kind, ask: **"Is it a state with duration (epoch = start/stop interval) or a discrete instant (event = single timestamp)?"**

| User wants… | Method | Returns |
|---|---|---|
| On/off state periods (duration) | `get_behavioral_epochs_times(name)` | `(2, N)` |
| Discrete timestamps (no duration) | `get_behavioral_events_times(name)` | `(2, N)`, both rows identical |
| Times of a name of any of these kinds (interval table, epoch, event, epoch-table label), looked up in that order | `get_event_times(name)` | `(2, N)` or None |
| Continuous signal | `get_behavioral_time_series_data(name, in_unit=False)`, `get_behavioral_time_series_timestamps(name)`, `get_behavioral_time_series_unit(name)`; shortcuts `get_mouse_speed_info()` / `get_mouse_position_info()` | `(n_samples,)` or `(n_samples, n_columns)`; `(data, timestamps)` for the shortcuts |
| Structured trials with metadata | `get_trial_table()`, `get_trials_names_from_table()` (selectable columns and their values) | DataFrame / `{column: values}` |
| Epoch table (`epochs` with labels) | `has_epoch_table()`, `get_epoch_table()`, `get_epochs_names_from_table()` | DataFrame / `{column: values}` |
| Any interval table | `get_interval_times(name)`, `get_interval_as_data_frame(name)`, `get_table_choices(name)` | `(2, N)` / DataFrame / `{column: values}` |

**Electrophysiology**

| User wants… | Method | Returns |
|---|---|---|
| Is there a units table, how many, their ids | `has_units()`, `get_n_units()`, `get_unit_ids()` | bool / int / list |
| Spike times for one unit | `get_single_unit_spike_times(unit_id)` | `(n_spikes,)` seconds |
| Spike trains of all units, filtered on quality labels | `get_spike_times(col_name, labels=['all'], label_col=None, return_ids=False)`; `col_name` from `get_spiketimes_col()`, label columns from `get_unit_label_columns()` / `get_unit_labels(label_col)` | array of arrays (units table order), or `(trains, unit_ids)` |
| Spike trains of the units of a brain region | `get_spiketimes_group(spkst_col='spike_times', col_name=None, target=None, labels=['all'], label_col=None, return_ids=False)` | array of arrays, or `(trains, unit_ids)` |
| All units + metadata | `get_units_table(extra_columns=None)` | DataFrame |
| Brain region per unit | `get_units_location(col_name=None)` → unique locations; `get_units_location_map(col_name=None)` → per unit | `(locs, col_name)` / `({unit_id: location}, col_name)` |
| Cell type per unit (if a cell-type column exists) | `get_unit_cell_types()`, `get_unit_cell_type_map()` | list / `{unit_id: type}` |
| Electrode geometry | `get_electrode_info()`, `get_units_coordinates()` | DataFrame |
| LFP / raw signals (ElectricalSeries) | discovery `get_electrical_series()` → `{location: {container: [series, ...]}}`, keys `[location, container, series]`; then `get_electrical_series_data(keys, start=None, stop=None, channels=None)` (window in seconds, only those samples read), `get_electrical_series_rate(keys)`, `get_electrical_series_channels(keys)`, `get_electrical_series_locations(keys)` | `(data (n_channels, n_times) in volts, times (n_times,))` / float Hz / DataFrame / `(locations, col_name)` |

**Optogenetics**

| User wants… | Method | Returns |
|---|---|---|
| Is there a stimulation record (acquisition `ogen_stim`) | `has_opto_stimulation()` | bool |
| Stimulation periods | `get_opto_stimulation_times()` | `(2, N)` start/stop of each run of non-zero values, or None |
| The raw stimulation signal | `get_opto_stimulation_time_serie()` | `(data, timestamps)` or None |

**Widefield**

Discovery:
```python
session.widefield.get_wf_acquisition_dict()
# → {module: [acquisition_name, ...]}
# If multiple acquisitions exist, show options and ask which to use.
```
Build `keys = [module_name, interface_name]`, then:

| User wants… | Method | Returns |
|---|---|---|
| dF/F0 pixel data (slice) | `get_widefield_dff0(keys, start, stop)` | `(n_frames, H, W)` |
| dF/F0 lazy full access | `get_widefield_dff0_mmap(keys)` — inside session context only | H5 dataset |
| Time axis | `get_widefield_timestamps(keys)` | `(n_frames,)` |

---

### Level 3 — Computation and display (cicada-tools)

Carry the modality from Level 1. Full signatures in `cicada_tools_api.md` — section references given below for direct lookup.

**Modality-dependent tools:**

| Goal | Calcium imaging | Electrophysiology | Widefield | Section in cicada_tools_api.md |
|---|---|---|---|---|
| Extract fixed windows around events | events in **seconds** → `align_array_to_timestamps(data, event_timestamps, frame_timestamps, window_s, subtract_baseline=False)` / events as **frame indices** → `align_array_to_events(data, event_frames, window_frames, subtract_baseline=False)`; `data` is `(n_cells, n_frames)` → `(n_cells, n_events, n_t)` | `compute_psth()` (spike times) | same functions on `(n_frames, H, W)` data → `(n_events, n_t, H, W)`, or slice `get_widefield_dff0(keys, start, stop)` per event window | §Event Alignment |
| PSTH | `build_psth_dataframe()` or `build_population_psth()` | `compute_psth()` | — | §PSTH — Calcium Imaging / §PSTH — Electrophysiology |
| Detect transients in neural signal | `detect_small_transients()` | — | — | §Signal Processing |
| Detect population synchrony (SCE) | `detect_sce_traces()` (from raw traces) / `detect_sce_raster()` (from raster) | — | — | §Population Burst / SCE Detection |
| Render traces / heatmap | `render_traces()` / `render_traces_heatmap()` | `render_spikes()` | — | §Calcium Imaging — Display / §Ephys Display |
| Load / slice movie frames | `as_sliceable_movie()`, `TiffMovieView` | — | `get_widefield_dff0_mmap()` (NWB) | §Tiff Movie Handling |
| Average frames by epoch | `get_avg_frames_by_epoch()` | — | — | §Tiff Movie Handling |

**Modality-independent tools:**

| Goal | Function | Section in cicada_tools_api.md |
|---|---|---|
| Convert epoch timestamps (s) → frame indices | `from_timestamps_to_frame_epochs(time_stamps_array_2N, frames_timestamps_1D, as_list, keep_if="whole")` (`as_list` is required: True → `list[(start, stop)]`, False → `(2, N)` array) | §Period Utilities |
| Filter epochs by invalid/artifact periods | `filter_epoch_timestamps()` | §Period Utilities |
| Keep only events inside epoch windows | `filter_events_based_on_epochs(events_1D, epochs_2N)` | §Period Utilities |
| Nearest index in array | `find_nearest()` | §Array Utilities |
| Save a figure | `save_figure()` | §Display — Figure |
| Custom colormaps (hotcold, cyanmagenta…) | `get_colormap()` | §Display — Figure |
| Raster visualization | `plot_raster()` | §Display — Raster |
| Box plot / categorical (strip, swarm, violin, box, bar) / histogram | `plot_box_plots()` / `categorical_plot()` / `plot_hist_distribution()` | §Display — Distributions |
| PSTH visualization | `plot_psth_lines()` / `plot_raster_and_psth()` | §Display — PSTH Plots |
| Graph visualization | `plot_graph()` / `plot_connectivity_graphs()` | §Display — Graphs |
| Pairwise similarity / correlation matrix between neurons | `compute_similarity_matrix()` (Pearson/Hamming/Jaccard/Cosine), `build_pearson_adjacency_matrix()`, `plot_similarity_matrix()` | §Pairwise Cell Similarity, §Display — Connectivity |
| Spike-based connectivity graph | `build_connectivity_graphs()` | §Graphs & Connectivity |
| Hub cell detection | `detect_hub_cells()` | §Graphs & Connectivity |
| Putative monosynaptic connections (spike CCGs) | `bz_detect_connections()`, `plot_pair_ccg()` | §Cross-Correlogram (CCG) Utilities, §Display — Connectivity |
| Leader/follower coupling (spike-triggered population rate) | `compute_stpr()` / `compute_stpr_cross()` (cross-area), `plot_stpr_scatter()`, `plot_stpr_heatmap()` | §Spike-Triggered Population Rate (stPR), §Display — Connectivity |
| Peri-SCE triggered-average / "Christmas tree" plots | `compute_triggered_average_raster()`, `plot_christmas_tree_heatmap()`, `plot_christmas_tree_crosscorr()` | §Peri-SCE Triggered Average ("Christmas Tree"), §Display — Connectivity |
| K-means clustering | `find_best_kmeans()`, `plot_silhouettes()` | §Clustering |
| Sequence detection (PCA-based) | `step1_pca_off_memory()`, `covnorm_vectorized()` | §Sequences Detection |
| Statistical tests, FDR | `compare_two_distributions()`, `bh_reject()`, `multiple_comparison_one_factor_effect()` | §Stats |
| Trial / epoch table utilities, saving tables | `filter_table_with_dict()`, `table_time_columns()`, `save_tables()` | §Table Utilities |
| DLC trace preprocessing / PSTH | `preprocess_dlc_trace()`, `build_dlc_psth_df()` | §Behavior Analysis |
| SCE k-means cell assemblies (Malvache) | `detect_and_plot_cell_assemblies()` | §Cell Assemblies |

---

## When to offer plugin conversion

If a script or analysis session shows **two or more** of the following signals, proactively offer to convert it into a `CicadaAnalysis` plugin:

| Signal | Examples |
|---|---|
| Multiple cicada-tools calls chained together | alignment → PSTH → display |
| Parameters the user is iterating or tuning | "let me try threshold=0.3 instead", "what if I change the window?" |
| Running the same logic across multiple sessions | loop over NWB files, aggregating results |
| Interest in saving or reproducing the result | "save this", "I want to rerun this later" |
| Exploration of a parameter space | varying bin size, comparing methods |
| Script is growing beyond ~40 lines of analysis logic | |

**How to offer:**

> "This is getting complex enough that a CicadaAnalysis plugin would be a better fit — it gives you GUI parameter tuning, headless batch execution, and automatic reproducibility via combined YAML. Want me to convert the current script into a plugin?"

If the user agrees, use the plugin shell in the section below. Map every tunable value to the appropriate parameter helper (`add_int_values_arg_for_gui`, `add_bool_option_for_gui`, etc.), and wrap the existing analysis logic inside `run_analysis`. Do not change the logic itself — only restructure it into the plugin pattern.

---

## Writing a CicadaAnalysis plugin

**File placement** (the templates are in the cicada-analysis repository, not in the pip package: https://gitlab.com/cossartlab/cicada_analysis/-/tree/master/templates):
- Your own: any folder given to CICADA (GUI *Manage plugins → Add plugin folder*, `cicada-run --plugin-dir`, `extra_plugin_dirs=` of the runner). Start from `templates/new_plugin_template.py`, which runs as it is on the demo files.
- A lab package: `cicada_<lab>/plugins/cicada_<name>_analysis.py`, declared once under the entry-point group `cicada_analysis.plugins` in its `pyproject.toml` (start from `templates/cicada_lab_package_template/`, one working example of each part). Installed, it is found everywhere without a folder to give, and its version is recorded in every run.
- Core (cicada-analysis developers only): `cicada_analysis/core_analysis/cicada_<name>_analysis.py`; standard NWB data only.

Any concrete `CicadaAnalysis` subclass found in those places is a plugin: the file and class names are free (by convention `cicada_<name>_analysis.py` and `Cicada<Name>Analysis`), no registration needed. Lab-specific data (`session.<lab>`) belongs in the lab package's plugins, never in a core plugin.

### Plugin shell

```python
from cicada_analysis import CicadaAnalysis

class CicadaMyAnalysis(CicadaAnalysis):
    def __init__(self, config_handler=None):
        super().__init__(
            name="My Analysis",              # GUI display name
            short_description="Brief description",
            accepted_data_formats=["CI_DATA"],
            family_id="Category",            # GUI grouping; None = standalone
            long_description="<p>HTML for GUI tooltip</p>",
            config_handler=config_handler
        )

    def copy(self):
        # Required: a fresh instance with the same data (the runner and the GUI call it)
        analysis_copy = CicadaMyAnalysis(config_handler=self.config_handler)
        self.transfer_attributes_to_tabula_rasa_copy(analysis_copy=analysis_copy)
        return analysis_copy

    def check_data(self):
        # super() first; return False + set self.invalid_data_help to grey the plugin out in the GUI
        super().check_data()
        for session in self._data_to_analyse:
            if not session.calcium_imaging.get_roi_response_series():
                self.invalid_data_help = f"No ROI response series in {session.identifier}"
                return False
        return True

    def setup_parameters(self):
        super().setup_parameters()   # REQUIRED — registers results_path parameter

        # Data selectors (auto-populated from loaded sessions; the kwargs value is {session identifier: choice})
        self.add_roi_response_series_arg_for_gui(short_description="ROI Series", family_widget="Data",
                                                 kinds=None, optional=False)   # kinds=("traces",) to offer traces only
        self.add_good_cells_arg_for_gui()                 # 'keep_good_cells' when a ROI table has a quality column
        self.add_spiketimes_series_arg_for_gui(short_description="Spike times", family_widget="Data")
        self.add_unit_label_args_for_gui()                # 'unit_label_column', 'unit_labels' (quality filter of units)
        self.add_electrical_series_arg_for_gui(short_description="LFP")          # [location, container, series]
        self.add_segmentation_arg_for_gui()
        self.add_ci_movie_arg_for_gui()
        self.add_epoch_dict_arg_for_gui(short_description="Epochs", arg_name="epoch_names")
        self.add_trial_dict_arg_for_gui(short_description="Trials", family_widget="Data")   # groups built in the GUI
        self.add_intervals_arg_for_gui(short_description="Intervals", arg_name="interval_names")
        self.add_widefield_acquisitions_dict_for_gui(short_description="WF acquisition", family_widget="Data")

        # Scalar parameters
        self.add_int_values_arg_for_gui(
            arg_name="window_size", min_value=1, max_value=1000, default_value=50,
            short_description="Window (frames)", family_widget="Parameters"
        )
        self.add_field_float_option_for_gui(
            arg_name="threshold", default_value=0.5, mandatory=False, min_value=0, max_value=1,
            short_description="Threshold", family_widget="Parameters"
        )
        self.add_bool_option_for_gui(
            arg_name="normalize", true_by_default=True,
            short_description="Normalize", family_widget="Parameters"
        )
        self.add_field_text_option_for_gui(
            arg_name="label", default_value="",
            short_description="Label", family_widget="Parameters"
        )
        self.add_choices_arg_for_gui(arg_name="method", choices=["a", "b", "c"], default_value="a",
                                     multiple_choices=False, short_description="Method", family_widget="Parameters")
        self.add_color_arg_for_gui(arg_name="color", default_value=(1, 0, 0, 1),
                                   short_description="Color")
        self.add_open_file_dialog_arg_for_gui(arg_name="mapping_file", extensions=["csv"], mandatory=False,
                                              short_description="Mapping file")   # also add_open_dir_dialog_arg_for_gui

        # Generic (use when no dedicated helper exists)
        self.add_argument_for_gui(
            arg_name="my_param",
            value_type="str",           # 'str' (one line) | 'text' (multi-line) | 'int' | 'float' | 'bool' | 'file' | 'dir' | 'color' | 'color_with_alpha'
            default_value=None,
            short_description="My param",
            mandatory=True,
            choices=["a", "b", "c"],    # optional — restricts to a dropdown (multiple_choices=True: check list)
            multiple_choices=False,
            family_widget="Group"
        )

        # Group/color selection (named groups of choices, each with a colour)
        self.add_choices_for_groups_for_gui(
            arg_name="groups", choices=["cond_a", "cond_b"],
            with_color=True, short_description="Groups", family_widget="Group"
        )

        # Output helpers
        self.add_image_format_package_for_gui()           # = add_save_formats_arg_for_gui + add_dpi_arg_for_gui
        self.add_verbose_arg_for_gui()
        self.add_analysis_description_for_gui("Optional annotation saved with results")
        # Figures with a style preset, sizes, fonts, colours (read with self.figure_style(**kwargs)):
        # self.add_figure_style_args_for_gui()

        # Parameter dependencies are declared, not handled silently: the GUI greys the parameter out and
        # the parameter files record why it is unused. Declare them after the parameters are added.
        self.set_parameter_rules("threshold", enabled_if={"normalize": True})
        self.set_parameter_rules("window_size", requires_data=["roi_response_series"])

    def validate_parameters(self, **kwargs):
        # Optional: checks across parameters, run before the analysis (GUI and headless); one message per problem
        problems = super().validate_parameters(**kwargs)
        if kwargs.get("window_size", 50) > 500 and kwargs.get("normalize"):
            problems.append("Normalisation needs a window under 500 frames")
        return problems

    def run_analysis(self, **kwargs):
        super().run_analysis(**kwargs)  # REQUIRED — sets self._results_path

        roi_series   = kwargs.get('roi_response_series', {})
        window_size  = kwargs.get('window_size', 50)
        save_formats = kwargs.get('save_formats', ['pdf'])

        for session in self.get_data_to_analyse():
            sid = session.identifier
            if sid in roi_series:
                keys = roi_series[sid]
                traces = session.calcium_imaging.get_roi_response_serie_data(keys)
                good = self.good_cells(session, keys, **kwargs)   # bool mask from 'keep_good_cells', or None
                # ... analysis code: read the data here, compute with cicada_tools functions on arrays ...

        # Save figures (always through save_figure: it also writes the .mplfig file the GUI's Interactive viewing
        # tab shows when "Interactive viewing of the figures" is ticked, a checkbox added with save_formats):
        # from cicada_analysis.cicada_tools.display.core_plots import save_figure
        # save_figure(fig, self._results_path, "figname", save_formats=save_formats)

        # Anything random (surrogates, shuffles, random cells): declare the seed in setup_parameters with
        # self.add_random_seed_arg_for_gui(used_for="the surrogates"), then draw from
        # rng = self.random_generator(**kwargs)   (or self.random_generators(n, **kwargs): one per random step)
        # and pass it on (cicada_tools functions take seed=rng). Never np.random.* or random.* directly.
```

- `self.selected_series(kwargs.get("roi_response_series"))` gives `[(session, keys), ...]` for the sessions with a series selected: use it instead of testing the dict by hand.
- `requires_data=` keys (`set_parameter_rules`): `units`, `spike_times`, `roi_response_series`, `traces`, `sparse_activity`, `raster_like`, `spike_raster`, `rows_of_cells`, `cell_types`, `good_cells`, `imaging_movie`, `background_image`, `electrical_series`, `behavioral_time_series`, `trial_table`, `epoch_table`, `intervals`, `epochs`, `speed`, `position` (`cicada_analysis/base/data_requirements.py`). A parameter whose data no loaded session has is hidden.
- **Family base classes** (`cicada_analysis.base`), to inherit from instead of `CicadaAnalysis` when the plugin compares groups or aligns on events, so that it shares the parameters and figures of the core plugins of the same family: `CicadaGroupsBase` (epoch, session, cell-type, cell-index and area groups, group figures), `CicadaEventsBase` (adds trial groups of a table at one of its time columns and optogenetic stimulations as event sources), `CicadaPsthBase` (adds the PSTH events, window, reduction and figure parameters). Read their docstrings before writing a PSTH or a group-comparison plugin.
- `plt.xkcd()` only as a context manager; no `plt.show()` in a plugin.

---

## Headless runner

Every task exists as a command (`cicada-run`, `cicada-config`, installed with cicada-analysis), as Python, and in the GUI; the command and the Python call take the same options.

```bash
cicada-config sessions /data/mouse1 -o sessions.yaml [-r]        # list the .nwb files of a folder (or a DANDI address)
cicada-config params CicadaMyAnalysis -s sessions.yaml -o params.yaml --results-path /results [--plugin-dir DIR]
cicada-run -s sessions.yaml -p params.yaml [params2.yaml ...] [--results-path DIR] [--plugin-dir DIR]
cicada-run --replay combined_CicadaMyAnalysis_2026-06-14T10-30-00.yaml
```

```python
from cicada_analysis.config.runner import run_from_config, run_from_combined, generate_config

# 1. Generate a filled parameter YAML (defaults, and the choices available in the sessions: the files are opened)
generate_config(
    analysis_class=CicadaMyAnalysis,   # subclass, not an instance (cicada-config params takes the class name)
    output_yaml_path="params.yaml",
    sessions_yaml="sessions.yaml",
    result_path="/results",            # written as results_path (created if needed; None: set it before the run)
    overrides={"window_size": 100}     # optional: pre-fill specific parameters
)

# 2a. Run from one params file — returns a single CicadaAnalysis instance
result = run_from_config(
    sessions="sessions.yaml",
    params="params.yaml",
    save_combined=True,                # default: True — writes combined_*.yaml in the results folder
    extra_plugin_dirs=None,            # list of folders with your own plugins (not needed for installed lab packages)
    results_path=None,                 # overrides results_path from the YAML if set
    hash_inputs=False,                 # True: sha256 of the local input files in the combined YAML (slow on large files)
    dandi_mode=None                    # DANDI files: "stream" (default), "download" or "auto"; dandi_download_dir=...
)

# 2b. Run from multiple params files — sessions loaded ONCE, analyses run sequentially
#     Returns a list of CicadaAnalysis instances (one per params file)
results = run_from_config(
    sessions="sessions.yaml",
    params=["params_analysis1.yaml", "params_analysis2.yaml"]
)

# 2c. Alternative: pass a combined YAML directly (equivalent to run_from_combined)
result = run_from_config(combined_config="combined_CicadaMyAnalysis_2026-06-14T10-30-00.yaml")

# 3. Replay an exact previous run from its combined YAML (same options as run_from_config)
result = run_from_combined(
    "combined_CicadaMyAnalysis_2026-06-14T10-30-00.yaml",
    save_combined=True,                # default: True
    extra_plugin_dirs=None,            # the same folders as the original run
    results_path="/new/output/path"    # redirect outputs without editing YAML
)
```

**sessions.yaml** (top-level `sessions:` key; a relative `path` is resolved against the folder of the YAML file; a DANDI address such as `dandi://000728/sub-.../file.nwb` is accepted; `identifier` is a label for the reader only, the runs name the sessions by the identifier stored in each NWB file):
```yaml
sessions:
  - identifier: mouse1_day1
    path: /data/mouse1_day1.nwb
  - identifier: mouse2_day1
    path: ../data/mouse2_day1.nwb
```

**Demo data** to try a plugin or a config: `from cicada_analysis import demo`; `demo.names()` lists the 9 trimmed real NWB files shipped with cicada-analysis (Allen, IBL, DANDI, Cossart, Giocomo, Petersen...), `demo.path(name)` gives one, `demo.paths()` all of them, `demo.SESSIONS` is a sessions YAML listing them all, and `demo.figure_config(class_name, session_path)` returns the shipped Figure 3 config of a core plugin on a demo file (`demo/figure_configs/`), to replay or to start from.

**params.yaml:**
```yaml
analysis_class: "CicadaMyAnalysis"
analysis_module: "cicada_my_analysis"     # module of the class (here a file of an extra_plugin_dirs folder)
results_path: "/results"
roi_response_series: {}
window_size: 50
normalize: true
save_formats: ["pdf", "png"]
```

The **combined_*.yaml** is written in the results folder after every run (filename: `combined_{ClassName}_{timestamp}.yaml`). It embeds the sessions, the class, all final parameter values, the run duration and the provenance: version, git commit and "uncommitted changes" flag of each CICADA package and lab package installed (plus the sha256 of the inputs with `hash_inputs=True`). Replay warns when the installed versions differ. Use `run_from_combined()` / `cicada-run --replay` to replay exactly. `analysis_module` is optional in params.yaml — the runner finds the class by name among the installed plugins (entry-point group `cicada_analysis.plugins`: core and lab packages) and the `extra_plugin_dirs` / `--plugin-dir` folders.

---

## Key constraints

- **No parallel execution on the same NWB files** — `NWBSession` holds HDF5 file handles open. Run analyses sequentially.
- **`super().setup_parameters()` must be called first** in `setup_parameters` — it registers the mandatory `results_path` parameter.
- **`super().run_analysis()` must be called first** in `run_analysis` — it resolves `self._results_path` from kwargs.
- **`copy()` must return a fresh independent instance** — the headless runner calls it to create isolated instances per session group.
