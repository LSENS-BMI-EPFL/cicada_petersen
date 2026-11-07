# Plugins of cicada-petersen

Catalogue of the lab plugins (moved from the plugin catalogue of cicada-analysis, revision B4). The common parameters (output and display, data selection, PSTH parameters) are described in the [cicada-analysis catalogue](https://cicada-analysis.readthedocs.io/).

## Behavior quantification

* #### Single mouse behavior plots : [`cicada_single_mouse_bhv_plots`](../cicada_petersen/plugins/Behavior/cicada_single_mouse_bhv_plots.py)

_**Description :**_ Produce behavioral performance plots for a single mouse — per session and across days — from trial table data (Petersen lab task).  
_**Requires :**_ Trial table  
_**Key features :**_ Six plot types: single session / across days / psychometrics / across context days / context switch / reaction time | Per trial-type color customization (auditory hit/miss, whisker hit/miss, false alarm, correct rejection) | Context grouping by background noise or rewarded/non-rewarded  
_**Output :**_ Behavioral performance figures (pdf / png / svg / eps)

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| plots_to_do | Plot(s) to do | choice (multi-select) | "single_session" | single_session, across_days, psycho, across_context_days, context_switch, reaction_time | Selects which figures are generated. Every plot-specific parameter below (colors, `context_hue`, `context_plot_type`, `show_single_bloc`, `whisker_switch`, `n_whisker_trials`) only has an effect if its matching plot name is included here. |
| auditory_hit_color | Color of auditory hit trials | color (RGBA) | (0.13, 0.37, 0.66, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Part of the shared 6-color trial-outcome palette. Only affects rendering when `plots_to_do` includes `single_session`, `across_days`, `across_context_days`, or `reaction_time`; no effect if only `context_switch`/`psycho` are selected. |
| auditory_miss_color | Color of auditory miss trials | color (RGBA) | (0, 1, 1, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same `plots_to_do` scope as `auditory_hit_color`. |
| whisker_hit_color | Color of whisker hit trials | color (RGBA) | (0.14, 0.52, 0.26, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same `plots_to_do` scope as `auditory_hit_color`. |
| whisker_miss_color | Color of whisker miss trials | color (RGBA) | (0.84, 0.1, 0.11, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same `plots_to_do` scope as `auditory_hit_color`. |
| nostim_miss_color | Color of correct rejection trials | color (RGBA) | (0.8, 0.8, 0.8, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Labeled "correct rejection" color (no-stim trial, no lick). Same `plots_to_do` scope as `auditory_hit_color`. |
| nostim_hit_color | Color of false alarm trials | color (RGBA) | (0, 0, 0, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Labeled "false alarm" color (no-stim trial, licked). Same `plots_to_do` scope as `auditory_hit_color`. |
| rewarded_context_color | Background color for rewarded context | color (RGBA) | (0, 0.5, 0, 0.25) | R, G, B, A — each a float in [0.0, 1.0] | Background shading for rewarded-context blocks. Only passed to the `single_session` plot; not used by any other plot in `plots_to_do`. |
| non_rewarded_context_color | Background color for non-rewarded context | color (RGBA) | (0.7, 0.13, 0.13, 0.25) | R, G, B, A — each a float in [0.0, 1.0] | Background shading for non-rewarded blocks; same `single_session`-only scope as `rewarded_context_color`. |
| bckgrnd_color | Background color for figure | color (RGBA) | (1, 1, 1, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Figure background color. Only takes effect for `single_session`, `across_days`, `across_context_days`; ignored for `context_switch`, `psycho`, `reaction_time`. |
| axes_color | Color axe label for figure | color (RGBA) | (0, 0, 0, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Axis label color; same `plots_to_do` scope as `bckgrnd_color`. |
| context_hue | Group for context plot | choice | "rewarded or not" | background noise, rewarded or not | Only used when `plots_to_do` includes `across_context_days`. |
| context_plot_type | Type of plot for context hit rates across days | choice | "point-plot" | strip-plot, box-plot, point-plot | Only used when `plots_to_do` includes `across_context_days`. Also gates `show_single_bloc` (see below). |
| show_single_bloc | Show each bloc in plot if point-plot is selected | bool | False | True / False | Only takes effect when `plots_to_do` includes `across_context_days` **and** `context_plot_type='point-plot'`; ignored for `box-plot`/`strip-plot`. |
| whisker_switch | Counting whisker trials around transitions | choice | "defined" | full block, defined | Only relevant if `plots_to_do` includes `context_switch`. Gates `n_whisker_trials`: when `whisker_switch='full block'`, `n_whisker_trials` is ignored (forced to "all trials"); honored only when `whisker_switch='defined'`. |
| n_whisker_trials | Number of whisker trials to plot around context switch | int | 4 | 1–8 | Only used if `plots_to_do` includes `context_switch` and `whisker_switch='defined'`. |
| cut_session | Cut(s) to do | choice | "no_cut" | no_cut, manual_cutting, adaptive_cutting, from_yaml | Determines trial cutting before any plot is built (applies regardless of `plots_to_do`). Gates `yaml_path` (used only if `cut_session='from_yaml'`) and `first_trial`/`last_trial` (used only if `cut_session='manual_cutting'`). |
| yaml_path | Select path to yaml file | file (yaml/yml) | None | — | Maps session_id → [first_trial, last_trial]. Only read when `cut_session='from_yaml'`. Impossible for both this and `first_trial`/`last_trial` to apply simultaneously — `cut_session` selects exactly one cutting mode. |
| first_trial | Manual: First trail to take | int | 0 | 0–100 | Only applied when `cut_session='manual_cutting'`; ignored for all other `cut_session` values. |
| last_trial | Manual: Last trial to take | int | 500 | 100–700 | Same gating as `first_trial` (`cut_session='manual_cutting'` only). |
| sns_context | Seaborn context | choice | "poster" | paper, notebook, talk, poster | Seaborn plotting context, applied globally to every figure regardless of `plots_to_do`. |

</details>

* #### Average mice behavior : [`cicada_average_mice_behavior`](../cicada_petersen/plugins/Behavior/cicada_average_mice_behavior.py)

_**Description :**_ Produce group-level behavioral performance plots averaged across mice from trial table data (Petersen lab task).  
_**Requires :**_ Trial table | Multiple mice (≥ 2 subjects)  
_**Key features :**_ Five plot types: average across days / across context days / switch time / reaction time / first whisker trial timing | Optional individual mouse linking in plots | Per trial-type and context color customization  
_**Output :**_ Group behavioral performance figures (pdf / png / svg / eps) | Whisker transition table (CSV, for `1st_whisker_time` plot only)

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| plots_to_do | Plot(s) to do | choice (multi-select) | "average_across_days" | average_across_days, average_across_context_days, average_switch_time, reaction_time, 1st_whisker_time | Selects which figures are generated; see each plot-specific row below for scope. |
| link_mice | Link mice in the plot | bool | False | True / False | Draws lines connecting the same mouse across days. Only used when `plots_to_do` includes `average_across_days` or `average_across_context_days`. |
| auditory_hit_color | Color of auditory hit trials | color (RGBA) | (0.13, 0.37, 0.66, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Part of the 6-color trial-outcome palette. Only affects the `average_across_days` plot — the only plot in this file that receives it. |
| auditory_miss_color | Color of auditory miss trials | color (RGBA) | (0, 1, 1, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same scope as `auditory_hit_color`. |
| whisker_hit_color | Color of whisker hit trials | color (RGBA) | (0.14, 0.52, 0.26, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same scope as `auditory_hit_color`. |
| whisker_miss_color | Color of whisker miss trials | color (RGBA) | (0.84, 0.1, 0.11, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same scope as `auditory_hit_color`. |
| nostim_miss_color | Color of correct rejection trials | color (RGBA) | (0.8, 0.8, 0.8, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same scope as `auditory_hit_color`. |
| nostim_hit_color | Color of false alarm trials | color (RGBA) | (0, 0, 0, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same scope as `auditory_hit_color`. |
| rewarded_context_color | Background color for rewarded context | color (RGBA) | (0, 0.5, 0, 0.25) | R, G, B, A — each a float in [0.0, 1.0] | ⚠ Dead parameter: read but never passed to any plotting function in this file — has no visible effect. |
| non_rewarded_context_color | Background color for non-rewarded context | color (RGBA) | (0.7, 0.13, 0.13, 0.25) | R, G, B, A — each a float in [0.0, 1.0] | (currently unused — not yet wired into the analysis) |
| bckgrnd_color | Background color for figure | color (RGBA) | (1, 1, 1, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Only affects `average_across_days`; the other plot functions called in this file don't accept a background-color argument. |
| axes_color | Color axe label for figure | color (RGBA) | (0, 0, 0, 1.0) | R, G, B, A — each a float in [0.0, 1.0] | Same scope as `bckgrnd_color`. |
| context_hue | Group for context plot | choice | "rewarded or not" | background noise, rewarded or not | Only used when `plots_to_do` includes `average_across_context_days`. |
| context_plot_type | Type of plot for context hit rates across days | choice | "point-plot" | strip-plot, box-plot, point-plot | ⚠ Dead parameter: unlike the equivalent parameter in `cicada_single_mouse_bhv_plots.py`, it has no effect on any plot here. |
| whisker_switch | Counting whisker trials around transitions | choice | "defined" | full block, defined | Only relevant when `plots_to_do` includes `average_switch_time`. Gates `n_whisker_trials` exactly as in the single-mouse plugin. |
| n_whisker_trials | Number of whisker trials to plot around context switch | int | 4 | 1–8 | Only used if `plots_to_do` includes `average_switch_time` and `whisker_switch='defined'`. |
| alignment_mode | How to align selected sessions across mice | choice | "day" | day, first_session | Only used when `plots_to_do` includes `average_across_days` or `average_across_context_days`; not passed to the other three plots. |
| cut_session | Cut(s) to do | choice | "no_cut" | no_cut, manual_cutting, adaptive_cutting, from_yaml | Applies before any `plots_to_do` branch (global). Gates `yaml_path` (`from_yaml`) and `first_trial`/`last_trial` (`manual_cutting`). |
| yaml_path | Select path to yaml file | file (yaml/yml) | None | — | Only read when `cut_session='from_yaml'`. Mutually exclusive in effect with `first_trial`/`last_trial`. |
| first_trial | Manual: First trail to take | int | 0 | 0–100 | Only applied when `cut_session='manual_cutting'`. |
| last_trial | Manual: Last trial to take | int | 500 | 100–700 | Same gating as `first_trial`. |
| fig_scale_factor | Figure size scaling factor | int | 1 | 1–6 | Scales figure size for `average_across_days`, `average_across_context_days`, `average_switch_time`, and `reaction_time`. ⚠ Not used for `1st_whisker_time`, which is drawn with no size argument. |
| sns_context | Seaborn context | choice | "notebook" | paper, notebook, talk, poster | Seaborn context, applied globally regardless of `plots_to_do`. |

</details>

* #### Facemap movement analysis : [`cicada_movement_quantification`](../cicada_petersen/plugins/Behavior/cicada_movement_quantification.py)

_**Description :**_ Quantify Facemap-derived movement signals — baseline comparison and PSTH — aligned to behavioral events or context transitions.  
_**Requires :**_ Facemap motion energy or SVD time series | Trial table (optional)  
_**Key features :**_ Two analyses: baseline comparison / event-aligned PSTH | Motion energy PSTH and/or per-SVD PSTH | Optional alignment on context transitions | Three plot levels: per session / per mouse / grand average | Configurable quiet window for baseline extraction  
_**Output :**_ Movement PSTH figures (pdf / png / svg / eps) | CSV tables

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| analysis_to_do | Analysis to do | choice (multi-select) | "baseline analysis" | baseline analysis, psth analysis | Gates `only_correct_trials`/`quiet_window_mode` (`baseline analysis` only) and `mot_psth`/`mot_svd_psth`/`context_alignment`/`t_before`/`t_after`/`n_svd_images` (`psth analysis` only). The `session_plot` output in `plots_to_do` additionally requires **both** values to be selected — see `plots_to_do`. |
| mot_psth | Do PSTH on motion energy | bool | True | True / False | Enables the face-motion-energy PSTH within `psth analysis` (no effect unless `analysis_to_do` includes `psth analysis`); also gates the corresponding sub-plot within `session_plot`. |
| mot_svd_psth | Do PSTH on motion energy for each SVD | bool | False | True / False | Enables per-SVD-component PSTH within `psth analysis`; also unconditionally produces one extra SVD-images figure per session whenever `psth analysis` is selected, independent of `plots_to_do`. Also gates the corresponding sub-plot within `session_plot`. |
| context_alignment | Also align PSTHs on context transitions | bool | False | True / False | Additionally aligns PSTHs on rewarded/non-rewarded context transitions, within `psth analysis`; also gates the context-transition sub-plots within `session_plot`. Final CSV export of the context-aligned tables is further gated: written for the energy version only if `mot_psth=True`, and for the SVD version only if `mot_svd_psth=True`. |
| plots_to_do | Plot(s) to do | choice (multi-select) | "session_plot" | session_plot, mouse_plot, grand_average_plot | ⚠ `mouse_plot` and `grand_average_plot` are not yet implemented — `run_analysis` only has a branch for `session_plot`; no figure is produced for the other two. `session_plot` requires `analysis_to_do` to include **both** `baseline analysis` and `psth analysis`; each of its 4 sub-plots (face-motion PSTH, SVD PSTH, context-transition PSTH, SVD-context PSTH) is individually gated by its corresponding `mot_psth`/`mot_svd_psth`/`context_alignment` flag rather than requiring all three. |
| only_correct_trials | Keep only correct trials in trial table | bool | False | True / False | Only used within the `baseline analysis` branch of `analysis_to_do`. |
| quiet_window_mode | Define the quiet window to extract data at each trial | choice | "last 2s" | last 2s, last 0.5s, full quiet window | Only used within the `baseline analysis` branch of `analysis_to_do`. |
| normalized_motion_energy | Do Min Max normalization on facemotion energy | bool | False | True / False | Applied to the motion-energy trace before either `analysis_to_do` branch runs, so it affects both `baseline analysis` and `psth analysis` outputs whenever facemap data is available. |
| n_svd_images | N SVD to keep | int | 100 | 0–500 | Caps how many SVD components are kept/plotted; only meaningful when `mot_svd_psth=True` and `analysis_to_do` includes `psth analysis`. SVD grids use a square-root-based row/column count, so non-perfect-square values silently show fewer components than requested (e.g. 50 → a 7×7 grid = only 49 shown). |
| t_before | Time before stimulus or context transition (ms) | int | 500 | 0–2000 (ms) | Only used within the `psth analysis` branch (including `context_alignment` sub-block); ignored for `baseline analysis`. |
| t_after | Time after stimulus or context transition (ms) | int | 1000 | 0–5000 (ms) | Same gating as `t_before`. |

</details>

## Extracellular electrophysiology

* #### Unit 3D brain map : [`cicada_unit_3d_brain.py`](../cicada_petersen/plugins/Ephys/cicada_unit_3d_brain.py)

_**Description :**_ 3D scatter plot of spike-sorted unit CCF coordinates across sessions, with optional coarse area grouping and an animated rotating movie export.  
_**Requires :**_ Units table with CCF coordinates  
_**Key features :**_ Color by arbitrary units-table column or by custom area group | Combine units across multiple sessions | Optional `.mp4` rotation movie (requires ffmpeg; export is skipped with a warning if ffmpeg is missing)  
_**Output :**_ 3D scatter figure (pdf / png / svg / eps) | Optional rotation movie (mp4)

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| color_by | Column to color units by | choice | Dynamic — priority match: `ccf_atlas_acronym` > `ccf_atlas_parent_acronym` > `ccf_acronym` > `ccf_location` > `location` > first available | Dynamic — units-table columns containing "ccf", "location", "atlas", or "region" (excluding `_ap`/`_ml`/`_dv` coordinate columns); fallback `ccf_atlas_acronym` if none found | Column used to color/label units. Interacts with `use_area_groups`: see below. |
| use_area_groups | Group colors by broad area (Motor, Hippocampus, etc.) | bool | True | True / False | When True **and** `color_by` is present as a column in the collected coordinates, values are remapped into broad groups (e.g. "Motor", "Hippocampus"; unmapped → "Other") using a canonical Allen-style palette, and that grouped column (not `color_by`) drives the plot. When False, or when `color_by` is missing from the collected data, the raw `color_by` values are used directly with a generic palette. |
| quality_labels | Unit quality labels to include | choice (multi) | Dynamic — all `bc_label` values found across loaded sessions; fallback `good`, `mua` if none found | Dynamic — same set as default | Filters units by `bc_label` membership, applied per session; sessions lacking a `bc_label` column entirely are left unfiltered rather than raising an error. |
| output_type | Output format | choice | "html_only" | html_only, mp4_only, both | Selects output(s): `html_only` → Plotly HTML (skipped with a warning if `plotly` isn't installed); `mp4_only` → rotating matplotlib MP4 (skipped with a warning if `ffmpeg` isn't found); `both` → both. Gates `n_frames` and `fps`, which are only read inside the MP4-producing branch — both are ignored for `html_only`. |
| show_brain_surface | Overlay brain surface mesh (requires iblatlas) | bool | True | True / False | When True, builds a brain-surface mesh (requires `iblatlas`) overlaid on both HTML and MP4 outputs. If `iblatlas` isn't installed, a warning is printed and the mesh is simply omitted (no crash). Gates `decimate`: the mesh-building call (and its `decimate` argument) is only reached inside this branch, so `decimate` has no effect when `show_brain_surface=False`. |
| decimate | Surface mesh decimation factor (higher = faster, coarser) | int | 3 | 1–10 | Stride applied to the atlas label volume along all 3 axes before marching-cubes mesh extraction; higher = coarser/faster. Only used when `show_brain_surface=True` and `iblatlas` is installed. |
| n_frames | Number of frames in rotation animation | int | 120 | 30–360 | Number of frames in the rotating MP4 animation. Only used when `output_type` is `mp4_only` or `both`; no effect for `html_only`. |
| fps | Animation frame rate (fps) | int | 30 | 10–60 | Frame rate for the MP4 animation. Only used when `output_type` is `mp4_only` or `both`; no effect for `html_only`. |

</details>

## Widefield imaging analysis

* #### Raw fluorescence and F0 plots : [`cicada_widefield_fraw_fnull_plots`](../cicada_petersen/plugins/Widefield/cicada_widefield_fraw_fnull_plots.py)

_**Description :**_ Plot raw fluorescence (Fraw) and baseline (F0) time courses for widefield ROIs over a configurable time window.  
_**Requires :**_ Widefield acquisition (F raw) | Segmentation (ROI masks)  
_**Key features :**_ Configurable display window end (seconds) | RAM-aware data loading  
_**Output :**_ Fraw and F0 time course figures per ROI (pdf / png / svg / eps)

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| stop_time_s | Display window end (s) | int | 7200 | 60–36000 | End of the display window in seconds from recording start; clipped to the recording length if larger. This is the only non-boilerplate parameter in this plugin — no cross-parameter interactions exist. |

</details>

#### Widefield movie average : [`cicada_widefield_movie_average`](../cicada_petersen/plugins/Widefield/cicada_widefield_movie_average.py)

_**Description :**_ Compute trial-averaged widefield movies centered on behavioral events or epoch transitions, with optional baseline subtraction.  
_**Requires :**_ Widefield acquisition movie | Behavioral events or epochs  
_**Key features :**_ Two modes: trial-averaged movie / save F0 baseline image | Filter trials by epoch | Center on event onset or epoch transition | Configurable pre / post event window (ms) | Optional baseline subtraction  
_**Output :**_ Averaged widefield movie (TIFF) | F0 baseline image (TIFF)

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| analysis_to_do | Analysis to do | multi-choice | "wf_movie_avg" | wf_movie_avg, save_f0 | Gates two independent code paths that both run if both are selected. `save_f0` computes a whole-recording F0 percentile image and ignores every parameter below (`epochs_to_do`, `center_on_epochs`, `trials_list`, `widefield_start_in_ms`, `widefield_stop_in_ms`, `subtract_baseline`). `wf_movie_avg` uses all of them. |
| epochs_to_do | Select epoch(s) to do widefield analysis | multi-choice | none selected | behavioral epoch names found in the data | Only read when `analysis_to_do` includes `wf_movie_avg`. Empty: `trials_list` events are centered directly over the whole session and `center_on_epochs` is never reached. Non-empty: events are filtered per epoch, and `center_on_epochs` becomes active. |
| center_on_epochs | use epoch transition as center | bool | False | True / False | Only takes effect when `epochs_to_do` is non-empty. When active, an additional movie average centered on each selected epoch's transition time is saved, on top of the per-trial-type averages. |
| trials_list | Events | multi-choice | none selected | behavioral event names found in the data | Required whenever `analysis_to_do` includes `wf_movie_avg`: if left empty, the analysis aborts immediately on the very first session (no output for any session), not just a skip. Not used at all when only `save_f0` is selected. |
| widefield_start_in_ms | Window before event (ms) | int | 100 | 50–20000 | Only relevant when `wf_movie_avg` is selected. Defines the pre-event window edge and (via the baseline window) the region subtracted when `subtract_baseline=True`. |
| widefield_stop_in_ms | Window after event (ms) | int | 200 | 50–20000 | Only relevant when `wf_movie_avg` is selected; defines the post-event window edge of the averaged clip. |
| subtract_baseline | Subtract baseline | bool | True | True / False | Only relevant when `wf_movie_avg` is selected. Subtracts the mean of the frames before the event (window defined by `widefield_start_in_ms`) from the averaged movie. |

</details>

* #### Widefield time courses : [`cicada_widefield_time_courses`](../cicada_petersen/plugins/Widefield/cicada_widefield_time_courses.py)

_**Description :**_ Plot dF/F widefield time courses (image series) aligned to behavioral events or epoch transitions, with optional baseline subtraction.  
_**Requires :**_ Widefield dF/F acquisition | Behavioral events or epochs  
_**Key features :**_ Three plot levels: per session / averaged by mouse / averaged across all mice | Filter trials by epoch | Center on event onset or epoch transition | Configurable pre / post window and frame averaging | Baseline subtraction and colormap selection  
_**Output :**_ Widefield time course image series figures (pdf / png / svg / eps) | Nested event-aligned data dict per trial / mouse / session saved as `.npy` for re-plotting

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| plots_to_do | Plot(s) to do | multi-choice | "widefield_timecourse" | widefield_timecourse, wf_timecourse_avg_by_mouse, wf_timecourse_avg_all_mice | Gates which figure block(s) run; independent of each other. |
| epochs_to_do | Select epoch(s) to do widefield analysis | multi-choice | none selected | behavioral epoch names found in the data | Empty: `trials_list` events are centered directly (no epoch filtering) and `center_on_epochs` is unreachable. Non-empty: events are filtered per epoch, and `center_on_epochs` becomes active. |
| center_on_epochs | use epoch transition as center | bool | False | True / False | Only takes effect when `epochs_to_do` is non-empty. Adds an epoch-transition-centered timecourse (stored under the plain epoch name as key) to the saved data dict. |
| trials_list | Events | multi-choice | none selected | behavioral event names found in the data | Mandatory: if empty, the analysis aborts immediately on the first session, aborting the whole run. |
| widefield_start | Range of widefield (ms) before event | int | 100 | 50–20000 | Pre-event window (ms); also defines the baseline window boundary used by `remove_baseline`. |
| widefield_stop | Range of widefield (ms) after event | int | 100 | 50–20000 | Post-event window (ms). |
| n_frames_averaged | number of frames to be averaged in 1 image | int | 5 | 1–100 | Number of consecutive frames merged into one displayed tile; applied identically across every `plots_to_do` figure. |
| baseline | Range of baseline (ms) | int | 25 | 10–20000 | ⚠ **Dead parameter.** Computed but never referenced again anywhere in `run_analysis` — it has no effect on the analysis, plots, or baseline subtraction. The actual baseline window used for subtraction comes from `widefield_start`, not from this parameter. (Confirms the earlier min-value fix is otherwise correctly applied — default 25 is in-range — but the parameter itself does nothing.) |
| remove_baseline | Do baseline subtraction | bool | True | True / False | Passed through as the baseline-subtraction flag; when True, subtracts the mean of the pre-event frames (window set by `widefield_start`, **not** by `baseline`) from every averaged timecourse. |
| color_map | Select the color map | choice | "hotcold" | hotcold, seismic | Colormap for all `plots_to_do` figures. Only affects appearance of these; the context-difference figure (see `plot_context_difference`) always uses "seismic" regardless of this choice. |
| colorbar_scale_min | Minimal value for colorbar | text (float) | "-0.005" | — | Only applies to the main `plots_to_do` figures, and only when `color_map='hotcold'` (used as vmin). Ignored when `color_map='seismic'`. |
| colorbar_scale_max | Maximal value for colorbar | text (float) | "0.02" | — | Only applies to the main `plots_to_do` figures, and only when `color_map='hotcold'` (used as vmax). Ignored when `color_map='seismic'` — in that case neither this, `colorbar_scale_min`, nor `context_diff_c_scale` apply; a hardcoded default half-range is used instead. |
| context_diff_c_scale | Color scale for context difference | text (float) | "0.01" | — | Only used for the auto-generated context-difference figure (rewarded − non-rewarded), which is always drawn with the "seismic" colormap irrespective of `color_map`. Irrelevant if `plot_context_difference=False`. |
| plot_context_difference | Plot context difference image (rewarded - non-rewarded) | bool | True | True / False | Gates the whole context-difference block. ⚠ **Likely-broken combination**: requires `rewarded_trial_type` and `non_rewarded_trial_type` to exactly match keys in the per-mouse data dict. When `epochs_to_do` is empty, the key is simply the trial-type name (defaults work if that trial type is in `trials_list`). When `epochs_to_do` is non-empty, keys become `"{epoch}_{trial_type}"` instead, so the default (or any un-prefixed) trial-type value will never match, and the figure is silently skipped. |
| rewarded_trial_type | Trial type for rewarded context (correct trials) | text | "rewarded_whisker_hit_trial" | — | Only used when `plot_context_difference=True`; must match an actual key in the data dict — see interaction above. |
| non_rewarded_trial_type | Trial type for non-rewarded context (correct trials) | text | "non-rewarded_whisker_miss_trial" | — | Only used when `plot_context_difference=True`; must match an actual key in the data dict — see interaction above. |

</details>

* #### Widefield PSTH : [`cicada_widefield_psth`](../cicada_petersen/plugins/Widefield/cicada_widefield_psth.py)

_**Description :**_ Build ROI-based widefield dF/F PSTHs aligned to behavioral events or epoch transitions.  
_**Requires :**_ Widefield RoiResponseSeries | Behavioral events or epochs  
_**Key features :**_ Three plot levels: per session / per mouse / grand average | Align to stimulus onset or lick time | Filter by epoch / cell type | Optional merging of selected trial types | Optional peak response bar plot over configurable post-stimulus window | Optional baseline subtraction  
_**Output :**_ PSTH figures (pdf / png / svg / eps) | Per-event data table (mouse ID / session / ROI / cell type / trial type / epoch) as CSV

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| plots_to_do | Plot(s) to do | multi-choice | "wf_psth_full_plot" | wf_psth_session_plot, wf_psth_mouse_plot, wf_psth_full_plot | Gates independent figure blocks. The context-transition figure and the whole peak/half-max response analysis additionally require `wf_psth_full_plot` to be selected (see `center_on_epochs`). |
| epochs_to_do | Select epoch(s) to do widefield analysis | multi-choice | none selected | behavioral epoch names found in the data | Empty: events centered directly, `center_on_epochs` unreachable. Non-empty: per-epoch filtering applied (or, with `align_to="Lick"`, filtering by trial-table context), and `center_on_epochs` becomes reachable. |
| center_on_epochs | Center on epoch transitions | bool | False | True / False | Only takes effect when `epochs_to_do` is non-empty. When True, an additional epoch-transition PSTH is built per epoch. Its context-transition figure and the entire peak/half-max response analysis (driven by `peak_window_start_ms`/`peak_window_stop_ms`) further require `plots_to_do` to include `wf_psth_full_plot` **and** `merge_trial_type=False` — if `merge_trial_type=True`, this whole downstream output is skipped even though the transition data was computed. **`center_on_epochs` and `merge_trial_type=True` are mutually exclusive for this output.** |
| trials_list | Events | multi-choice | none selected | behavioral event names found in the data | Mandatory: empty → analysis aborts, aborting the whole run. |
| align_to | Align on | choice | "Stim" | Stim, Lick | "Lick" switches the event source to the trial table's lick-time/context columns, deriving a lick flag and stim-type string by substring match on the `trials_list` entry name; when `epochs_to_do` is also set, rows are further filtered by trial-table context matching the epoch. Only `trials_list` values containing "whisker" or "auditory" map correctly; anything else falls into "no_stim". |
| merge_trial_type | Merge all events | bool | False | True / False | Collapses the trial-type dimension across all groupbys and plots. Mutually exclusive with the `center_on_epochs` peak/context-transition output (see above), since that code filters on a trial-type column that no longer exists per-type once merged. |
| cell_types_to_do | cell_types_to_do | multi-choice | none selected | cell types found in the data | Filters plotted rows in the session/mouse/full-average blocks. |
| psth_start | Range of psth (ms) before event | int | 100 | 50–20000 | Pre-event window (ms) → seconds, used as the time range for every branch. |
| psth_stop | Range of psth (ms) after event | int | 200 | 50–20000 | Post-event window (ms) → seconds, same as above. |
| subtract_baseline | Subtract baseline | bool | True | True / False | When `align_to='Lick'`, the baseline is computed relative to the stimulus time rather than the lick time itself. |
| peak_window_start_ms | Peak window start (ms post-stim) | int | 80 | 0–500 | Only used inside the `wf_psth_full_plot` + `center_on_epochs=True` + `merge_trial_type=False` branch; independent of `psth_start`/`psth_stop`. |
| peak_window_stop_ms | Peak window stop (ms post-stim) | int | 180 | 0–500 | Same gating as `peak_window_start_ms`; independent of `psth_start`/`psth_stop`. |

</details>

* #### Widefield error response : [`cicada_widefield_error_response`](../cicada_petersen/plugins/Widefield/cicada_widefield_error_response.py)

_**Description :**_ Compute widefield dF/F PSTH of the cortical response to error trials, with configurable session trimming.  
_**Requires :**_ Widefield RoiResponseSeries | Trial table with error trial labels  
_**Key features :**_ Four session cutting modes: none / manual trial range / adaptive / from YAML | Filter by cell type | Three plot levels: per session / per mouse / grand average | Align to stimulus onset or lick time | Optional baseline subtraction  
_**Output :**_ Error response PSTH figures (pdf / png / svg / eps)

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| cut_session | Cut(s) to do | choice | "no_cut" | no_cut, manual_cutting, adaptive_cutting, from_yaml | Gates the other trimming parameters: `manual_cutting` uses `first_trial`/`last_trial`; `from_yaml` uses `yaml_path`; `adaptive_cutting` computes its own cutoff automatically and ignores both; `no_cut` ignores both. |
| yaml_path | Select path to yaml file | file (yaml/yml) | None (not mandatory) | — | Only used when `cut_session="from_yaml"`. |
| first_trial | Manual: First trail to take | int | 0 | 0–100 | Only used when `cut_session="manual_cutting"`. |
| last_trial | Manual: Last trial to take | int | 500 | 100–700 | Only used when `cut_session="manual_cutting"`. |
| cell_types_to_do | cell_types_to_do | multi-choice | none selected | cell types found in the data | ROIs not in `cell_types_to_do` are excluded before reaching any plot; unlike the other Widefield plugins, the selection is applied once, upstream, not at plot time. |
| plots_to_do | Plot(s) to do | multi-choice | "wf_psth_full_plot" | wf_psth_session_plot, wf_psth_mouse_plot, wf_psth_full_plot | Gates which figure block(s) run. |
| alignment | Alignment mode | choice | "stim. time" | stim. time, lick | Selects the time column used to build the PSTH: `whisker_stim_time` when "stim. time", `lick_time` otherwise. |
| psth_start | Range of psth (ms) before event | int | 100 | 50–20000 | Pre-event window (ms) → seconds, used as the time range. |
| psth_stop | Range of psth (ms) after event | int | 200 | 50–20000 | Post-event window (ms) → seconds, same as above. |
| subtract_baseline | Subtract baseline | bool | True | True / False | Applied to all trials regardless of other settings. |

</details>

* #### Compare baseline : [`cicada_compare_baseline`](../cicada_petersen/plugins/Widefield/cicada_compare_baseline.py)

_**Description :**_ Compare pre-trial baseline fluorescence (dF/F traces or widefield images) between rewarded and non-rewarded behavioral contexts.  
_**Requires :**_ Widefield RoiResponseSeries | Widefield dF/F acquisition | Trial table with context labels  
_**Key features :**_ Two analysis modes: dF/F trace baseline / widefield image baseline | Configurable pre-trial quiet window: last 2s / last 0.5s / full quiet window | Single trial projection: correlate each trial's baseline ROI pattern to the rewarded vs non-rewarded context difference | Filter by epoch / trial type / cell type / correct trials only | Three plot levels: per session / per mouse / grand average  
_**Output :**_ Per-trial baseline dF/F dataset as CSV | Baseline comparison figures (pdf / png / svg / eps) | Intermediary image data as .npy

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| analysis_to_do | Analysis to do | choice | "Compare baseline dff" | Compare baseline images, Compare baseline dff | Single-select, so exactly one mode runs per call. `Compare baseline images` uses `epochs_to_do`, `trials_list`, `img_dict_path*`, `color_map`/`colorbar_scale_min`/`colorbar_scale_max`/`halfrange`, and the image entries of `plots_to_do`. `Compare baseline dff` uses `cell_types_to_do` and the dff entries of `plots_to_do`. `only_correct_trials` and `quiet_window_definition` apply to whichever mode is active. |
| plots_to_do | Plot(s) to do | multi-choice | none selected | Baseline dff over context time, Single trial dff projection, Baseline image by session, Baseline image by mouse, Baseline image full average, Single trial image projection | The first two entries require `analysis_to_do="Compare baseline dff"`; the last four require `analysis_to_do="Compare baseline images"` **and** exactly 2 epochs selected in `epochs_to_do`. Selecting an entry that doesn't match the active `analysis_to_do` produces no figure for it. |
| display_points | Display points | bool | True | True / False | Only affects the three regression-line figures (`Baseline dff over context time`, `Single trial dff projection`, `Single trial image projection`); no effect on the pure image plots. |
| context_time_lim | Maximal time in context in plots | int | 250 | 0–300 | Only affects the same three regression-line figures (bounds/filters the time-in-context x-axis). |
| img_dict_path | Path to images results without trial type | file (.npy) | None (not mandatory) | — | When `analysis_to_do="Compare baseline images"` and `epochs_to_do` has exactly 2 entries: if set and the file exists, per-session image computation is skipped entirely and the loaded dict is used as-is. If not set (or missing), images are recomputed from scratch **even if `img_dict_path_all`/`time_in_context_dict_path_all` were supplied** — recomputation is gated on this parameter only. |
| img_dict_path_all | Path to images results with trial type | file (.npy) | None (not mandatory) | — | Pre-loads the trial-type-resolved image dict before the session loop; used by `Single trial image projection`. By itself does **not** prevent recomputation (see `img_dict_path` above). |
| time_in_context_dict_path_all | Path to time in context with trial type dictionary | file (.npy) | None (not mandatory) | — | Pre-loads the matching "time since transition" dict; used together with `img_dict_path_all` by `Single trial image projection`. |
| epochs_to_do | Select epoch(s) to do widefield analysis | multi-choice | none selected | epoch names containing "rewarded" | `Compare baseline images` requires **exactly 2** epochs selected — otherwise no image data/plots are produced for any session (the rest of the analysis, e.g. `Compare baseline dff`, is unaffected). Not used at all by `Compare baseline dff`. Note the choice list itself is pre-filtered to epoch names containing "rewarded". |
| trials_list | Events | multi-choice | none selected | event names found in the data, excluding any containing "dlc" | Only used inside the `Compare baseline images` + 2-epochs branch, to build per-trial-type image dictionaries. |
| cell_types_to_do | cell_types_to_do | multi-choice | none selected | cell types found in the data | ⚠ Only filters the `Baseline dff over context time` plot loop. The other `Compare baseline dff` summary figures always include **every** brain region found in the data, regardless of this selection. Not used by `Compare baseline images`. |
| only_correct_trials | Keep only correct trials in trial table | bool | False | True / False | Applies to whichever `analysis_to_do` is active: filters the trial table before image computation and/or before dff aggregation. |
| quiet_window_definition | Define the quiet window to extract data at each trial | choice | "last 2s" | last 2s, last 0.5s, full quiet window | Applies to both analysis modes (defines the quiet-window frames for both dff extraction and image extraction). |
| color_map | Select the color map for the difference image | choice | "seismic" | hotcold, seismic | Only relevant to `Compare baseline images` plots. ⚠ In every image figure, the first two panels (the two per-context baseline images) are always drawn with "hotcold" hard-coded — this parameter only changes the colormap of the third panel (the rewarded-minus-non-rewarded difference image). |
| colorbar_scale_min | Minimal value for 'hotcold' colorbar | text (float) | "-0.005" | — | Used as vmin for the two hard-coded "hotcold" panels always, and for the third (difference) panel only when `color_map='hotcold'`. |
| colorbar_scale_max | Maximal value for 'hotcold' colorbar | text (float) | "0.04" | — | Symmetric to `colorbar_scale_min` (vmax), same gating. |
| halfrange | Halfrange for 'seismic' colorbar | text (float) | "0.01" | — | Only used for the third (difference) panel, and only when `color_map='seismic'`; irrelevant to the two hard-coded "hotcold" panels, which always use `colorbar_scale_min`/`colorbar_scale_max` instead. |

</details>

* #### Post-transition baseline differences : [`cicada_widefield_baseline_diff_post_transition`](../cicada_petersen/plugins/Widefield/cicada_widefield_baseline_diff_post_transition.py)

_**Description :**_ Track how pre-trial baseline widefield images evolve as a function of time elapsed after a context transition, comparing rewarded and non-rewarded contexts.  
_**Requires :**_ Widefield dF/F acquisition | Trial table with context labels  
_**Key features :**_ Baseline difference maps (R+ − R−) binned by time in context, with configurable bin size | Per-trial correlation to the session R+−R− reference map, plotted over time | Configurable quiet window: last 2s / last 0.5s / full quiet window | First context block excluded (no preceding transition) | Filter to correct trials only  
_**Output :**_ Baseline difference maps per time bin (pdf / png / svg / eps) | Correlation-over-time figure (pdf / png / svg / eps) | Per-trial correlation table as CSV | Intermediary baseline image data as .npy

<details>
<summary><b>Parameters</b></summary>

| Parameter | GUI label | Type | Default | Range / Choices | Description |
|---|---|---|---|---|---|
| only_correct_trials | Keep only correct trials in trial table | bool | True | True / False | Filters the trial table before all downstream computation (baseline images, binning, correlation). |
| quiet_window_mode | Define the quiet window to extract data at each trial | choice | "last 2s" | last 2s, last 0.5s, full quiet window | Defines the quiet window for every baseline-image extraction and the per-trial correlation loop; applies uniformly, not gated by any other parameter. |
| binsize | Bin size in seconds for time-in-context axis | int | 10 | 5–300 | Bin width (s) for digitizing context time (0–300 s); the resulting number of bins determines the number of panels in the baseline-difference-average figure. |
| color_map | Select the color map for the difference image | choice | "seismic" | hotcold, seismic | Gates whether `colorbar_scale_min`/`colorbar_scale_max` (`hotcold`) or `halfrange` (`seismic`) is used for the single figure this plugin produces — unlike `cicada_compare_baseline.py`, there is only one plotting call site here, so `color_map` fully controls it (no hard-coded panel). |
| colorbar_scale_min | Minimal value for 'hotcold' colorbar | text (float) | "-0.005" | — | Only used when `color_map='hotcold'` (vmin). |
| colorbar_scale_max | Maximal value for 'hotcold' colorbar | text (float) | "0.04" | — | Only used when `color_map='hotcold'` (vmax). |
| halfrange | Halfrange for 'seismic' colorbar | text (float) | "0.01" | — | Only used when `color_map='seismic'`. |

</details>
