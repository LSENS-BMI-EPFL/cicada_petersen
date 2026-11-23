# cicada-nwb API Reference

**Package:** `cicada-nwb`  
**Main import:** `from cicada_nwb import NWBSession`

Main `cicada-nwb` getters, with return shapes. Not complete: see `cicada_claude.md` for the fallback rules.

---

## NWBSession — setup

```python
from cicada_nwb import NWBSession

# Context manager (closes the file)
with NWBSession("/path/to/file.nwb") as session:
    ...

# Manual open/close
session = NWBSession("/path/to/file.nwb")
session.load_data()
...
session.close()
```

**Constructor:** `NWBSession(data_ref: str, load_data: bool = True, dandi_mode: str = None)`  
- `data_ref`: absolute path to the `.nwb` file, or a DANDI address:
  `dandi://000728@0.240827.1809/sub-x/sub-x_ses-y.nwb` (version optional: latest published), a
  `https://dandiarchive.org/dandiset/<id>/<version>/files?location=<path>` link, a
  `https://api.dandiarchive.org/api/assets/<asset_id>/download/` link, or any `.nwb` URL  
- `load_data=False`: defer opening (call `.load_data()` manually)  
- `dandi_mode`: `"stream"` (default, reads only what is used), `"download"` (whole file into a cache folder, reused next time) or `"auto"` (download up to 1 GB)  
- After opening a DANDI file, `session.data_ref` is the version-pinned `dandi://` address and `session.source` a dict (dandiset_id, version, asset_path, asset_id, size, sha256, mode, local_path)

**Submodules** auto-attached on open:

| Attribute | Type | Data domain |
|---|---|---|
| `session.metadata` | `NWBMetadata` | Subject/session info |
| `session.calcium_imaging` | `NWBCalciumImaging` | ROI traces, masks, movies |
| `session.behavior` | `NWBBehavior` | Epochs, events, speed, trials |
| `session.electrophysiology` | `NWBElectrophysiology` | Spike times, units |
| `session.widefield` | `NWBWidefield` | Widefield dF/F0 |
| `session.cossart` | `NWBCossartLab` | Cossart lab extensions (when installed) |
| `session.petersen` | `NWBPetersenLab` | Petersen lab extensions (when installed) |

---

## session.metadata

These properties are also available directly on `session` (e.g. `session.age`).

```python
session.metadata.identifier             # str
session.metadata.age                    # int | None  (numeric value)
session.metadata.age_unit               # str | None  ('D' = days, 'M' = months)
session.metadata.genotype               # str | None
session.metadata.species                # str | None
session.metadata.subject_id             # str | None
session.metadata.session_id             # str | None
session.metadata.weight                 # str | None
session.metadata.sex                    # str | None
session.metadata.lab                    # str | None
session.metadata.institution            # str | None
session.metadata.protocol               # str | None
session.metadata.experimenter           # str | None  (first experimenter)
session.metadata.session_description    # str | None
session.metadata.experiment_description # str | None

session.metadata.get_sessions_info()
# → dict: {identifier, subject_id, session_id, age (int), age_unit (str), weight (float)}

session.get_timestamps_range()
# → (start, end) in s: earliest to latest time of every TimeSeries (acquisition, processing, stimulus) and of the
#   units' spikes, read without loading the timestamps; None if nothing in the file has times
```

---

## session.calcium_imaging

### Step 1 — discover available data

```python
# Full nested dict of all ROI response series
session.calcium_imaging.get_roi_response_series()
# → {module_name: {interface_name: [rrs_name, ...]}}

# Flat sorted list of all RRS names
session.calcium_imaging.get_roi_response_series_list()
# → np.ndarray of strings

# All available segmentations
session.calcium_imaging.get_segmentations()
# → {module_name: {image_seg_name: [plane_seg_name, ...]}}
```

### Step 2 — access traces and timestamps

`keys` is always `[module_name, interface_name, rrs_name]` — values come from `get_roi_response_series()`.

```python
session.calcium_imaging.get_roi_response_serie_data(keys: list[str])
# → np.ndarray (n_cells, n_times) | None

session.calcium_imaging.get_roi_response_serie_timestamps(keys: list[str], verbose: bool = True)
# → np.ndarray (n_times,) | None
# Reconstructed from starting_time+rate if timestamps not stored explicitly.

session.calcium_imaging.get_rrs_sampling_rate(keys: list[str])
# → float | None  (Hz, estimated from first 100 timestamps if needed)
```

Search across all RRS by keyword:
```python
session.calcium_imaging.get_roi_response_serie_data_by_keyword(
    keys: list[str],   # [module_name, interface_name] — 2-element
    keyword: str | list[str]
)
# → {rrs_name: np.ndarray} for all matching RRS, or empty dict
```

### Cell types

```python
session.calcium_imaging.get_all_cell_types()
# → list[str]  (unique cell type names, empty list if none)

session.calcium_imaging.get_cell_indices_by_cell_type(roi_serie_keys: list[str])
# keys: [module_name, interface_name, rrs_name]
# → {cell_type_name: np.ndarray of indices} | {}

session.calcium_imaging.get_cell_snr(roi_serie_keys: list[str])
# → list[float] | []  (per-cell SNR from a custom '*snr*' column in the ROI table, if present)
```

### Segmentation masks

`segmentation_info` is `[module_name, image_seg_name, plane_seg_name]` — from `get_segmentations()`.

```python
session.calcium_imaging.get_pixel_mask(segmentation_info: list[str])
# → list[np.ndarray] | None
# One entry per cell; each array is (N_pixels, 2) with (x, y) coordinates.
# Falls back to converting image_mask if pixel_mask is absent.

session.calcium_imaging.get_image_mask(segmentation_info: list[str])
# → np.ndarray | list[np.ndarray] | None
# Binary 2D image per cell.
# Falls back to converting pixel_mask if image_mask is absent.

session.calcium_imaging.get_ci_dimension_from_img_mask(segmentation_info: list[str])
# → (n_lines, n_cols) | (None, None)
# Inferred from first mask.
```

### CI movies

```python
session.calcium_imaging.contains_ci_movie(consider_only_2_photons: bool)
# → bool

session.calcium_imaging.get_ci_movies(only_2_photons: bool)
# → {key: file_path_or_data_array}

session.calcium_imaging.get_ci_movie_dimension(only_2_photons: bool = False, ci_movie_name: str | None = None)
# → (n_lines, n_cols) | (None, None)

session.calcium_imaging.get_ci_movie_sampling_rate(only_2_photons: bool = False, ci_movie_name: str | None = None)
# → float | None  (Hz)

session.calcium_imaging.get_ci_movie_time_stamps()
# → np.ndarray | None  (1D, for 'ci_frames' acquisition)

session.calcium_imaging.get_imaging_plan_location(only_2_photons: bool = False, ci_movie_name: str | None = None)
# → str | None
```

---

## session.behavior

### Discovery

```python
session.behavior.get_behavioral_epochs_names()   # → list[str]
session.behavior.get_behavioral_events_names()   # → list[str]
session.behavior.get_behavioral_time_series_names()  # → list[str]
session.behavior.get_intervals_names()           # → list[str]  (interval tables: nwb.intervals and nwb.stimulus)
session.behavior.get_intervals_names(include_trials=False, epoch_labels=True)
# → without the trial table; the epoch table replaced by its labels 'epochs: <label>' (e.g. 'epochs: MazeEpoch')
session.behavior.has_trial_table()               # → bool
session.behavior.has_epoch_table()               # → bool
session.behavior.get_trial_table_name()          # → str | None  (name of the trial table among the interval tables)
```

### Any interval table by name (trials, epochs, stimulus presentations...)

```python
session.behavior.get_interval_as_data_frame(name)   # → pd.DataFrame | None
session.behavior.get_interval_times(name)           # → np.ndarray (2, N) start / stop | None
session.behavior.get_table_choices(name)            # → {column: [values]} to pick rows by | None
session.behavior.get_table_timestamps(name, {"orientation_in_degrees": [90]}, use_stop_time=True)
# → (np.ndarray (2, N), 'seconds' | 'frames') of the matching rows | (None, None)
session.behavior.get_event_times(name)
# → (2, N) of an interval table, behavioral epoch, behavioral event or epoch label 'epochs: <label>'
```

### Epochs (start/stop intervals)

```python
session.behavior.get_behavioral_epochs_times(epoch_name: str)
# → np.ndarray (2, N) | None
# row 0 = start times (s), row 1 = stop times (s)
```

### Events (point timestamps)

```python
session.behavior.get_behavioral_events_times(event_name: str)
# → np.ndarray (2, N) | None
# Both rows contain the same timestamps (point events have no duration).
```

### Continuous signals

```python
session.behavior.get_mouse_speed_info()
# → (transposed_speed: np.ndarray, timestamps: np.ndarray) | (np.ndarray, None) | (None, None)

session.behavior.get_mouse_position_info()
# → (transposed_position: np.ndarray, timestamps: np.ndarray) | (np.ndarray, None) | (None, None)

session.behavior.get_behavioral_time_series_data(serie_name: str)   # → np.ndarray | None
session.behavior.get_behavioral_time_series_timestamps(serie_name: str)  # → np.ndarray | None
session.behavior.get_behavioral_time_series_column_names(serie_name: str)  # → ['x', 'y'(, 'z')] for a position | None
session.behavior.get_behavioral_time_series(serie_name: str)         # → pynwb TimeSeries | None
```

### Trial table

```python
session.behavior.get_trial_table()
# → pd.DataFrame | None
# Standard columns: start_time, stop_time + any custom columns.

session.behavior.get_trials_names_from_table()
# → {col_name: [unique_values, ...]} | None  (variable columns only)

session.behavior.get_table_timestamps(session.behavior.get_trial_table_name(), requirements_dict: dict)
# requirements_dict: {col_name: [accepted values]} to filter rows
# → (np.ndarray (2, N), time_unit: str) | (None, None)
# time_unit is 'seconds' or 'frames'. Requirement keys absent from the trial
# table are skipped (not an error).
```

### Intervals (nwb.intervals)

```python
session.behavior.get_interval_as_data_frame(interval_name: str)  # → pd.DataFrame | None
session.behavior.get_interval_times(interval_name: str)
# → np.ndarray (2, N) | None  (row 0 = start_time, row 1 = stop_time)
```

### Optogenetic stimulation

Submodule `session.optogenetic` (not `session.behavior`):

```python
session.optogenetic.has_opto_stimulation()
# → bool  (True if the file has an optogenetic stimulation series, acquisition 'ogen_stim')

session.optogenetic.get_opto_stimulation_time_serie()
# → (data: np.ndarray, timestamps: np.ndarray) | None

session.optogenetic.get_opto_stimulation_times()
# → np.ndarray (2, n_stimulations) | None  (row 0 = first, row 1 = last timestamp of each run of non-zero values)
```

---

## session.electrophysiology

### Discovery

```python
session.electrophysiology.has_units()       # → bool
session.electrophysiology.get_n_units()     # → int
session.electrophysiology.get_unit_ids()    # → list  (unit IDs as in units table)
session.electrophysiology.get_spiketimes_col()
# → list[str]  (names of spike_times columns in units table)
```

### Spike times

```python
session.electrophysiology.get_single_unit_spike_times(unit_id)
# → np.ndarray (n_spikes,) | None  (seconds)

session.electrophysiology.get_spike_times(
    col_name: str,
    labels: list[str] = ['all'],
    label_col: str = 'bc_label'
)
# → np.ndarray | None  (concatenated spike times filtered by labels)

session.electrophysiology.get_spiketimes_group(
    spkst_col: str = 'spike_times',
    col_name: str | None = None,     # brain region column
    target: list | None = None,      # target region(s)
    labels: list[str] = ['all'],
    label_col: str = 'bc_label'
)
# → np.ndarray | None
```

### Units table and anatomy

```python
session.electrophysiology.get_units_table(extra_columns: dict | None = None)
# → pd.DataFrame | None
# extra_columns: {new_col_name: callable(df) -> Series}

session.electrophysiology.get_units_location(col_name: str | None = None)
# → (locs: np.ndarray, col_name: str) | (None, None)
# locs: unique location values; col_name: the column they came from.
# If col_name arg is None, tries in order: ccf_atlas_acronym → ccf_acronym →
# location → falls back to the units table index (col_name returned as 'index').

session.electrophysiology.get_electrode_info()
# → pd.DataFrame | None
# Columns: location, group, group_name, filtering, imp, x, y, z
```

---

## session.widefield

### Discovery

```python
session.widefield.get_wf_acquisition_dict()
# → {module_name: [acquisition_name, ...]}
```

### Timestamps and data

`keys` is `[module_name, interface_name]` — from `get_wf_acquisition_dict()`.

```python
session.widefield.get_widefield_timestamps(keys: list[str])
# → np.ndarray (n_frames,) | None

session.widefield.get_widefield_dff0(keys: list[str], start: int, stop: int)
# → np.ndarray (stop-start, height, width) | None

session.widefield.get_widefield_dff0_mmap(keys: list[str])
# → h5py.Dataset | np.memmap | None
# Lazy access — valid only while session is open. Slicing returns numpy arrays.
# Shape: (n_frames, height, width)

session.widefield.get_widefield_f0(acquisition_names: list[str])
# acquisition_names: [acquisition_key, image_name]
# → np.ndarray (height, width) | None  (F0 baseline image)
```

---

## session.cossart (Cossart lab — auto-attached)

```python
session.cossart.get_belt_type()       # → 'Uncued belt' | 'Cued belt' | 'NA'
session.cossart.abf_status()          # → 'With ABF' | 'No ABF'
```

## session.petersen (Petersen lab — auto-attached)

```python
session.petersen.get_session_metadata()          # → dict | str | None (parsed experiment_description)
session.petersen.get_session_type()              # → str | None
session.petersen.get_bhv_type_and_training_day_index()  # → (str, int) | (None, None)
session.petersen.get_whisker_rewarded_sessions() # → 'whisker rewarded' | 'whisker not rewarded' | None
session.petersen.get_facemap_data(image_acquisition_name="facemap_svd_images")
# → {'motion_energy', 'motion_svd', 'timestamps', 'svd_images'} | None
```
