# Tools of cicada-petersen

Reference of the lab analysis tools (moved from the cicada-tools reference of cicada-analysis, revision B4). Import them from their module: `from <module> import <function>`.

--------

## `cicada_petersen.tools.behavior_plots`

  - #### `analysis_1st_whisker_against_time`

```python
analysis_1st_whisker_against_time(session_data, verbose, rwd_wh_table, nn_rwd_wh_table, last_rwd_wh_table, last_nn_rwd_wh_table)
```

_No description yet._

  - #### `plot_1st_whisker_against_time`

```python
plot_1st_whisker_against_time(save_path, save_formats, transition_full_dataset)
```

_No description yet._

  - #### `plot_average_mice_across_context_days`

```python
plot_average_mice_across_context_days(combine_bhv_data, aligning_value, figure_size, dpi, context_hue, link_mice, ...)
```

_No description yet._

  - #### `plot_average_mice_over_session`

```python
plot_average_mice_over_session(combine_bhv_data, block_size, results_path, save_formats)
```

_No description yet._

  - #### `plot_average_mice_time_to_switch`

```python
plot_average_mice_time_to_switch(combine_bhv_data, block_size_sessions, n_wh_trials, figsize, saving_path, save_formats, ...)
```

_No description yet._

  - #### `plot_mice_average_across_days`

```python
plot_mice_average_across_days(combine_bhv_data, aligning_value, color_palette, figure_size, dpi, background_color, ...)
```

_No description yet._

  - #### `plot_reaction_time_general_data`

```python
plot_reaction_time_general_data(combine_bhv_data, figsize, saving_path, save_formats, verbose=False)
```

_No description yet._

  - #### `plot_single_mouse_across_context_days`

```python
plot_single_mouse_across_context_days(combine_bhv_data, block_size_sessions, color_palette, figure_size, dpi, context_hue, ...)
```

_No description yet._

  - #### `plot_single_mouse_across_days`

```python
plot_single_mouse_across_days(combine_bhv_data, color_palette, figure_size, dpi, background_color, labels_color, ...)
```

_No description yet._

  - #### `plot_single_mouse_psychometrics_across_days`

```python
plot_single_mouse_psychometrics_across_days(combine_bhv_data, saving_path, save_formats, verbose=False)
```

_No description yet._

  - #### `plot_single_mouse_reaction_time_across_days`

```python
plot_single_mouse_reaction_time_across_days(combine_bhv_data, color_palette, figsize, saving_path, save_formats, verbose=False)
```

_No description yet._

  - #### `plot_single_mouse_time_to_switch`

```python
plot_single_mouse_time_to_switch(combine_bhv_data, block_size_sessions, n_wh_trials, figsize, saving_path, save_formats, ...)
```

_No description yet._

  - #### `plot_single_session`

```python
plot_single_session(combine_bhv_data, sessions_list, block_size_sessions, color_palette, context_colors, figure_size, ...)
```

_No description yet._

  - #### `plot_single_session_time_to_switch`

```python
plot_single_session_time_to_switch(combine_bhv_data, block_size_sessions, n_wh_trials, figsize, saving_path, save_formats, ...)
```

_No description yet._

  - #### `set_seaborn_context`

```python
set_seaborn_context(sns_context, page_color, lw)
```

_No description yet._

--------

## `cicada_petersen.tools.behavior_utils`

  - #### `build_standard_behavior_table`

```python
build_standard_behavior_table(nwb_list, cut_session, session_cutoffs, yaml_file_path, result_path) -> pd.DataFrame
```

Build a combined behavior table from a list of NWB sessions.

**Returns:** `pd.DataFrame` — Combined behavior table

  - #### `get_standard_single_session_table`

```python
get_standard_single_session_table(combine_bhv_data, session, block_sizes=None, block_size=20) -> pd.DataFrame
```

Extract and format a single-session behavior table with trial metadata.

For context sessions the block length is inferred from the context switches. For other sessions it is taken from `block_sizes` (a `{session_id: block_size}` dict, typically built from the NWB metadata via `petersen.get_experimental_block_size()`), falling back on the hard-coded `block_size` when it is missing or invalid.

**Returns:** `pd.DataFrame` — Single-session behavior table

  - #### `get_block_size_from_table`

```python
get_block_size_from_table(trial_table, fallback=20) -> int
```

Compute block size (trials per context epoch) dynamically from transition indices.
Falls back to `fallback` if no transitions found.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trial_table` | pd.DataFrame | | Trial table |
| `fallback` | int | 20 | Fallback block size |

**Returns:** `int` — Block size

  - #### `get_n_trials_per_block_from_table`

```python
get_n_trials_per_block_from_table(trial_table, trial_type='whisker_trial', fallback=8) -> int
```

Count trials of a given type per block. Distinct from block size (which includes all trial types).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `trial_table` | pd.DataFrame | | Trial table |
| `trial_type` | str | 'whisker_trial' | Trial type to count |
| `fallback` | int | 8 | Fallback trial count |

**Returns:** `int` — Number of trials per block

> `filter_events_based_on_epochs(events_ts, epochs)` (keep the events within epochs) is in [`cicada_tools.core.period_utils`](core.md).

  - #### `get_all_quiet_windows`

```python
get_all_quiet_windows(table, reference_ts, quiet_window_mode) -> list
```

Extract quiet (pre-stimulus) window frame ranges from a behavior table.

| Parameter | Type | Description |
|-----------|------|-------------|
| `table` | pd.DataFrame | Behavior table |
| `reference_ts` | np.ndarray | Reference timestamps |
| `quiet_window_mode` | str | Quiet window mode |

**Returns:** `list` — List of quiet window frame ranges

  - #### `add_correct_choice_to_table`

```python
add_correct_choice_to_table(table, colname='correct_choice')
```

_No description yet._

  - #### `get_iti_frames`

```python
get_iti_frames(reference_ts, trial_table=None, epoch_times=None, stim_names=..., trial_duration=5)
```

Return a boolean array marking inter-trial interval (ITI) frames.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reference_ts` | np.ndarray | | Reference timestamps |
| `trial_table` | pd.DataFrame | None | Trial table |
| `epoch_times` | np.ndarray | None | Epoch times |
| `stim_names` | list | | Stimulus names |
| `trial_duration` | float | 5 | Trial duration in seconds |

**Returns:** `np.ndarray` — Boolean ITI array

--------

## `cicada_petersen.tools.ccf_plots`

  - #### `build_brain_surface`

```python
build_brain_surface(ba, decimate=3) -> tuple
```

Build a left-hemisphere brain surface mesh via marching cubes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ba` | BrainAtlas | | Brain atlas |
| `decimate` | int | 3 | Decimation factor |

**Returns:** `tuple` — Brain surface mesh

  - #### `collect_coordinates`

```python
collect_coordinates(units_tables, quality_labels) -> pd.DataFrame
```

Extract bregma-relative CCF coordinates from a dict of units DataFrames.

| Parameter | Type | Description |
|-----------|------|-------------|
| `units_tables` | dict | Units tables dictionary |
| `quality_labels` | list | Quality labels |

**Returns:** `pd.DataFrame` — Coordinates DataFrame

  - #### `make_plotly_figure`

```python
make_plotly_figure(df, mesh, color_by='region', title_tag='')
```

Build an interactive Plotly 3D scatter of unit CCF coordinates.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | | Coordinates DataFrame |
| `mesh` | any | | Mesh data |
| `color_by` | str | 'region' | Column to color by |
| `title_tag` | str | '' | Title tag |

**Returns:** `plotly.graph_objects.Figure` — Plotly figure

  - #### `make_rotation_animation`

```python
make_rotation_animation(df, mesh, color_by='region', title_tag='', n_frames=120, fps=30) -> tuple
```

Build a rotating matplotlib 3D animation of unit CCF coordinates.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `df` | pd.DataFrame | | Coordinates DataFrame |
| `mesh` | any | | Mesh data |
| `color_by` | str | 'region' | Column to color by |
| `title_tag` | str | '' | Title tag |
| `n_frames` | int | 120 | Number of frames |
| `fps` | int | 30 | Frames per second |

**Returns:** `tuple` — Animation data

--------

## `cicada_petersen.tools.widefield_utils` (widefield imaging)
`from cicada_petersen.tools.widefield_utils import <function>`

--------

  - #### `get_allen_ccf`

```python
get_allen_ccf(bregma=(528, 315), root=...) -> tuple[np.ndarray, np.ndarray, np.ndarray]
```

Load Allen CCF atlas masks aligned to bregma coordinates. Returns `(iso_mask, atlas_mask, bregma_coords)` — all `(500, 640)` arrays. NAS path default: `sv-nas1/.../Parameters/Widefield/allen_brain`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `bregma` | tuple | (528, 315) | Bregma coordinates |
| `root` | str | | Root path |

**Returns:** `tuple[np.ndarray, np.ndarray, np.ndarray]` — (iso_mask, atlas_mask, bregma_coords)

  - #### `get_wf_scalebar`

```python
get_wf_scalebar(scale=1) -> int
```

Compute scalebar length in pixels for a given scale factor.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scale` | float | 1 | Scale factor |

**Returns:** `int` — Scalebar length in pixels

  - #### `plot_wf_single_frame`

```python
plot_wf_single_frame(frame, title, figure, ax_to_plot, ...) -> None
```

Plot a single widefield frame with Allen atlas overlay, bregma marker, and scalebar. Hardcoded to Petersen-lab camera geometry (125×160 → scaled to 500×640).

| Parameter | Type | Description |
|-----------|------|-------------|
| `frame` | np.ndarray | Widefield frame |
| `title` | str | Plot title |
| `figure` | Figure | Matplotlib figure |
| `ax_to_plot` | Axes | Matplotlib axes |

**Returns:** `None`

  - #### `plot_wf_avg`

```python
plot_wf_avg(avg_data, output_path, n_frames_post_stim, n_frames_averaged, ...) -> None
```

Save averaged widefield frames as a single multi-panel figure.

| Parameter | Type | Description |
|-----------|------|-------------|
| `avg_data` | np.ndarray | Averaged data |
| `output_path` | str | Output path |
| `n_frames_post_stim` | int | Number of post-stimulus frames |
| `n_frames_averaged` | int | Number of averaged frames |

**Returns:** `None`

  - #### `trial_type_interpreter`

```python
trial_type_interpreter(trial_type) -> tuple[int, str]
```

Parse a trial type string into `(lick_flag, stim_type_string)`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `trial_type` | str | Trial type string |

**Returns:** `tuple[int, str]` — (lick_flag, stim_type_string)
- `lick_flag`: 1 if hit or false alarm, else 0
- `stim_type_string`: `'whisker_stim'` | `'auditory_stim'` | `'no_stim'`

  - #### `trial_type_baseline`

```python
trial_type_baseline(trial_table, session_data, wf_ts, quiet_window_mode) -> None
```

Compute per-trial pre-stimulus baseline images and accumulate into result dicts. Mutates `general_img_dict`, `general_img_dict_without_trial_type`, `general_img_transition_time_dict`, `general_img_transition_time_no_type_dict` in place.

| Parameter | Type | Description |
|-----------|------|-------------|
| `trial_table` | pd.DataFrame | Trial table |
| `session_data` | any | Session data |
| `wf_ts` | np.ndarray | Widefield timestamps |
| `quiet_window_mode` | any | Quiet window mode |

**Returns:** `None`

  - #### `get_session_average_wf_baseline_images`

```python
get_session_average_wf_baseline_images(trial_table, session_data, wf_ts, quiet_window_mode) -> np.ndarray
```

Average pre-stimulus baseline widefield images across all trials in a session. Returns a single `(H, W)` mean image.

| Parameter | Type | Description |
|-----------|------|-------------|
| `trial_table` | pd.DataFrame | Trial table |
| `session_data` | any | Session data |
| `wf_ts` | np.ndarray | Widefield timestamps |
| `quiet_window_mode` | any | Quiet window mode |

**Returns:** `np.ndarray` — `(H, W)` mean baseline image

  - #### `average_images_from_dict`

```python
average_images_from_dict(image_dict) -> np.ndarray
```

Recursively average all leaf arrays in a nested dict structure. Returns a single array with the grand mean.

| Parameter | Type | Description |
|-----------|------|-------------|
| `image_dict` | dict | Nested image dictionary |

**Returns:** `np.ndarray` — Grand mean image
