# cicada-tools API Reference

**Package:** `cicada-analysis`  
**Base import path:** `from cicada_analysis.cicada_tools.<module> import <function>`

Main `cicada_tools` functions: parameters and return shapes. Load and fallback rules: `cicada_claude.md`.

---

## Event Alignment

**Module:** `cicada_analysis.cicada_tools.core.event_alignment`

```python
from cicada_analysis.cicada_tools.core.event_alignment import (
    align_array_to_events,
    align_array_to_timestamps,
    event_aligned_array_to_long_format_df,
)

align_array_to_events(
    data: np.ndarray,          # (n_cells, n_times) traces, or (n_frames, H, W) for widefield
    event_frames: list,        # list of frame indices (int)
    window_frames: tuple,      # (n_frames_before, n_frames_after)
    subtract_baseline: bool = False
)
# → np.ndarray
#   If data is 2D (n_cells, n_times): returns (n_cells, n_events, n_t)
#   If data is 3D (n_frames, H, W):  returns (n_events, n_t, H, W)

align_array_to_timestamps(
    data: np.ndarray,              # (n_cells, n_times)
    event_timestamps: np.ndarray,  # (N,) event times in seconds — extract row 0 from (2,N) NWB output
    frame_timestamps: np.ndarray,  # (n_times,) trace timestamps in seconds
    window_s: tuple,               # (seconds_before, seconds_after)
    subtract_baseline: bool = False,
    time_axis: int = 1,            # 0: time-first data (n_times,) or (n_times, n_features), e.g. DLC / Facemap
    drop_outside: bool = False     # True: drop events whose window leaves the recording (default NaN)
)
# → np.ndarray (n_cells, n_events, n_t); with time_axis=0: (n_events, n_t) or (n_events, n_t, n_features)
# Timestamp-based wrapper around align_array_to_events. The only alignment function on event times.

event_aligned_array_to_long_format_df(
    array: np.ndarray,   # (n_events, n_times) or (n_events, n_times, n_samples)
    time_range: tuple,   # (t_start, t_end) of the window around the event, in seconds, e.g. (-1.0, 2.0)
    time_step: float     # time between two frames, in seconds
)
# → pd.DataFrame  (long format: columns data, event, time, sample; sorted by sample, event, time)
#   sample = index along the last axis (0 for a 2-D array)
```

---

## PSTH — Calcium Imaging

**Module:** `cicada_analysis.cicada_tools.imaging.psth_utils`

```python
from cicada_analysis.cicada_tools.imaging.psth_utils import (
    build_population_psth,
    combine_population_psth,
    build_psth_dataframe,
    align_single_cell_to_epochs,
)

build_population_psth(
    data: np.ndarray,               # (n_cells, n_times)
    epochs: list,                   # list of (start_frame, stop_frame) tuples, or a flat list of reference frames
    ref_in_epoch: str,              # 'start' | 'end' | 'middle' — reference point within epoch (no default)
    range_value: tuple,             # (n_frames_before, n_frames_after); the window_to_frames output
    fcts_to_apply: list,            # exactly 3 functions [central, low, high], each taking the list of the values
                                    #   of all the events at one time offset and returning a number; low / high
                                    #   return the absolute bounds of the band (e.g. mean - sem), never widths:
                                    #   never [np.mean, np.std]
    data_type: str = 'traces',      # 'traces' | 'raster'
    cell_reduction: str = 'mean',   # traces: 'mean' | 'median'; raster: 'mean' | 'proportion' | 'count'
    baseline_subtraction: bool = False  # subtract the mean of the frames before each event
)
# → tuple (frames_indices, psth_values): frames_indices = offsets -n_before ... +n_after (np.ndarray);
#   psth_values = [central, low, high], three lists of n_before + n_after + 1 values
# Lightweight summary PSTH — does not produce a DataFrame.

combine_population_psth(
    session_data_list: list,           # one (psth_times, psth_values) per session: times in the unit of bins_edges
                                       #   (convert the frame offsets, e.g. divide by the rate), psth_values = [central, low, high]
    bins_edges: np.ndarray,            # edges of the common time bins
    session_fcts: list | None = None   # [central, low, high] functions of the values of the sessions at one time bin
                                       #   (default: median, 5th and 95th percentile)
)
# → tuple (time_x_values, [central, low, high])

build_psth_dataframe(
    data: np.ndarray,                                    # (n_cells, n_times) traces
    event_timestamps: np.ndarray,                        # (N,) event times in seconds
    frame_timestamps: np.ndarray,                        # (n_times,) trace timestamps in seconds
    window_s: tuple,                                     # (seconds_before, seconds_after)
    subtract_baseline: bool = False,
    baseline_event_timestamps: np.ndarray | None = None, # alternative timestamps for baseline
    roi_indices: np.ndarray | None = None,               # value written in the 'roi' column for each row of data
    session_id: str | None = None,
    mouse_id: str | None = None,
    trial_type: str | None = None,
    extra_metadata: dict | None = None                   # {col_name: value} added to every row
)
# → pd.DataFrame  (long format: one row per cell × trial × timepoint; columns activity, time, event, roi
#   + the metadata columns given)
# This is NOT a wrapper around build_population_psth — it calls align_array_to_events
# internally and builds a tidy DataFrame (e.g. for stats.line_and_band and plot_psth_lines).

align_single_cell_to_epochs(
    cell_data,           # 1D array (n_times,)
    epochs,              # list of (start_frame, stop_frame) tuples
    ref_in_epoch,        # 'start' | 'end' | 'middle'
    range_frames,        # (n_frames_before, n_frames_after)
    n_total_frames,
    filter_consecutive: bool = False,
    fcts_to_apply=None,
    low_percentile: int = 25,
    high_percentile: int = 75,
    psth_range_in_ms=None,
    verbose: bool = False,
    baseline_subtraction: bool = False   # traces: each trial minus the mean of its frames before the event
)
# → dict  per-trial windows and summary stats for a single cell
```

---

## PSTH — Electrophysiology

**Module:** `cicada_analysis.cicada_tools.ephys.psth_utils`

```python
from cicada_analysis.cicada_tools.ephys.psth_utils import (
    compute_psth,
    baseline_indices,
    apply_baseline,
    unit_psth_table,
    spikes_around_events,
)

compute_psth(
    spike_times: list[np.ndarray],   # list of 1D arrays, one per unit, each sorted
    event_times: np.ndarray,         # (N,) event times in seconds — extract row 0 from (2,N) NWB output
    window_start: float,             # window start relative to the event, s (negative: -0.5 = 0.5 s before)
    window_end: float,               # window end relative to the event, s
    bin_size: float                  # bin size in seconds
)
# → tuple (psth: np.ndarray (n_events, n_bins, n_units), time: np.ndarray (n_bins,))
# Output is in Hz.

baseline_indices(time: np.ndarray, baseline_duration: float)
# → np.ndarray  — indices of bins in [-baseline_duration, 0]

apply_baseline(
    peth_matrix: np.ndarray,      # (n_bins, n_units): the PSTH of each unit (not per event)
    time: np.ndarray,             # (n_bins,) bin right edges, from compute_psth
    baseline_duration: float,     # seconds of pre-event baseline to subtract
    zscore: bool = False
)
# → tuple (corrected: np.ndarray, bl_std: np.ndarray)

unit_psth_table(
    binned: np.ndarray,              # (n_events, n_bins, n_units), from compute_psth
    time: np.ndarray,                # bin right edges, from compute_psth
    unit_ids: list,
    reduction="median", band="percentiles", low_percentile=25, high_percentile=75,   # as stats.line_and_band
    baseline_duration=0.0, baseline_correction=False, zscore=False                    # as apply_baseline, per unit
)
# → pd.DataFrame  — one row per unit and bin: unit_id, time, line, low, high (band over the events), n_events

spikes_around_events(spikes: np.ndarray, event_times: np.ndarray, t_before: float, t_after: float)
# → list[np.ndarray]  — one unit's spikes in [t - t_before, t + t_after) of each event, relative to it (rasters)
```

---

## Signal Processing

**Module:** `cicada_analysis.cicada_tools.imaging.calcium_signal_processing`

```python
from cicada_analysis.cicada_tools.imaging.calcium_signal_processing import (
    norm01,
    median_normalization,
    zscore_normalization,
    bleaching_correction,
    savitzky_golay_filt,
    gauss_blur_1d,
    gauss_blur,
    detect_small_transients,
    give_unique_id_to_each_transient_of_raster_dur,
    transient_amplitudes,
)

norm01(data)
# → np.ndarray  global min-max normalization to [0, 1]

median_normalization(traces: np.ndarray)   # (n_cells, n_frames)
# → np.ndarray (n_cells, n_frames)  (trace - median) / median for each cell; a cell with a median of 0 is unchanged

zscore_normalization(traces: np.ndarray)   # (n_cells, n_frames)
# → np.ndarray (n_cells, n_frames)  z-score each cell (subtract mean, divide by std)

transient_amplitudes(raster, traces, peak_minus_onset=True, max_negative_fraction=0.05)
# → (cells, onsets, amplitudes): one entry per transient (run of 1s of raster) measured on traces;
#   peak_minus_onset: trace at the last two frames minus at the frame before and the onset (transients at frame 0
#   left out), else the trace maximum over the transient; negative amplitudes NaN, warning above the fraction

bleaching_correction(traces: np.ndarray)   # (n_cells, n_frames)
# → np.ndarray (n_cells, n_frames)  each cell divided by its cubic polynomial fit (not subtracted)

savitzky_golay_filt(traces: np.ndarray, sr: float)
# → np.ndarray (n_cells, n_frames)

gauss_blur_1d(data, dw, dim)
# → np.ndarray  Gaussian blur along one dimension (Fourier domain)

gauss_blur(data, dw)
# → np.ndarray  isotropic 2D Gaussian blur (Fourier domain)

detect_small_transients(
    traces: np.ndarray,                          # (n_cells, n_frames)
    speed=None,
    use_speed: bool = False,
    speed_threshold=None,
    detection_method: str = 'rolling-window',
    window_size=None,
    min_small_transient_amp: float = 0,
    imaging_rate: float = 10,
    frames_mask=None            # bool per frame: where transients may be detected (e.g. an epoch); None: all
)
# → tuple (raster: np.ndarray (n_cells, n_frames), activity: list per cell of trace snippets)
# Detects small calcium transients per cell.

give_unique_id_to_each_transient_of_raster_dur(raster_dur: np.ndarray)
# → np.ndarray (n_cells, n_frames)  — each transient gets a unique integer ID
```

---

## Population Burst / SCE Detection

**Module:** `cicada_analysis.cicada_tools.imaging.detect_population_burst`

```python
from cicada_analysis.cicada_tools.imaging.detect_population_burst import (
    get_sce_raster_threshold,
    detect_sce_raster,
    detect_sce_traces,
)

get_sce_raster_threshold(
    rasterdur: np.ndarray,      # (n_cells, n_times) binary raster
    n_surrogates: int = 100,
    percentile: int = 95,
    verbose: bool = False,
    n_jobs: int = 4,
    seed=0                      # int or np.random.Generator: same seed, same threshold (whatever n_jobs)
)
# → tuple (rnd_rasters: np.ndarray, cell_threshold: int)
# rnd_rasters: surrogate population activity distributions
# cell_threshold: minimum co-active cells to call an SCE

detect_sce_raster(
    raster: np.ndarray,         # (n_cells, n_times) raster, active where > 0 (already computed)
    n_synchronous_frames: int,  # window of co-activity, in frames
    sce_n_cells_threshold: int, # min co-active cells (from get_sce_raster_threshold)
    sce_min_distance: int,      # min frames between SCE peaks ("Peaks")
    method: str = "Peaks",      # "Peaks": one SCE per peak; "All frames": each run of windows above threshold
    frames_mask=None,           # bool per frame: where SCEs may start (epoch, immobility); frames stay the raster's
    participation_margin: int = 1  # "Peaks": cell in the SCE if active within ± this many frames of the peak
)
# → tuple (cells_in_sce: np.ndarray (n_cells, n_sce), sce_windows: [(start, end), ...] inclusive, threshold)
# Lower-level: use when raster is already available.

detect_sce_traces(
    raw_traces: np.ndarray,              # (n_cells, n_times)
    speed=None,
    use_speed: bool = False,
    speed_threshold=None,
    sce_n_cells_threshold: int = 5,
    transient_method: str = 'rolling-window',
    window_size: float = 4,              # seconds (length of the window of the transient detection)
    sce_min_distance: int = 4,
    n_synchronous_frames: int = 2,
    small_transient_amp: float = 0,
    imaging_sampling_rate: float = 10,
    use_median_norm: bool = True,
    use_bleaching_correction: bool = False,
    use_savitzky_golay_filt: bool = False,
    frames_mask=None                     # bool per frame: where transients and SCEs may be (e.g. an epoch)
)
# → tuple (sce_cells_matrix, sce_loc (1-D peak frames), raster, small_transients_activity)
# Full pipeline: raw traces → transient detection → SCE detection.
# Use when you do not have a raster yet (calls detect_small_transients internally).
```

---

## Calcium Imaging — Display

**Module:** `cicada_analysis.cicada_tools.imaging.imaging_plots`

```python
from cicada_analysis.cicada_tools.imaging.imaging_plots import (
    render_traces,
    render_traces_heatmap,
    plot_small_transients,
)

render_traces(
    ax,                              # matplotlib Axes
    traces: np.ndarray,              # (n_cells, n_times)
    frame_times: np.ndarray,         # (n_times,)
    traces_lw: float = 0.3,
    cell_spikes_color: str = 'white',
    use_brewer_colors_for_traces: bool = False,
    cells_to_highlight=None,         # list of cell indices
    cells_to_highlight_colors=None,
    scatters_on_traces=None,
    show_y_scale: bool = False,
    show_x_scale: bool = False,
    figure_background_color: str = 'black',
    ...                              # additional style kwargs
)
# → float  — returns the y-axis offset used (useful when composing multi-panel figures)

render_traces_heatmap(
    raster: np.ndarray,              # (n_cells, n_times) — 2D array to render as heatmap
    path_results=None,
    file_name=None,
    n_subplots: int = 4,
    axes_list=None,
    speed_array=None,
    fig=None,
    show_color_bar: bool = False,
    vmin: float = 0.5,
    vmax=None,
    cmap: str = "hot",
    save_formats: str = "pdf",
    background_color: str = "black",
    first_frame: int = 0,            # recording frame of raster's first column (x tick labels of a time slice)
    ...                              # extensive style kwargs
)
# → None

plot_small_transients(
    small_transients,    # transient data from detect_small_transients
    window_size,
    sampling_rate,
    title,
    path_results,
    filename,
    save_formats
)
# → None
```

---

## Tiff Movie Handling

**Module:** `cicada_analysis.cicada_tools.imaging.images_handling`

```python
from cicada_analysis.cicada_tools.imaging.images_handling import (
    TiffMovieView,
    as_sliceable_movie,
    load_tiff_movie,
    read_tiff_movie_frames,
    get_avg_frames_by_epoch,
    reduce_image_dimensions,
    map_coordinates_to_image,
)

# TiffMovieView — off-memory sliceable view; valid as long as paths exist
# memory-mapped when possible (frames back to back, or at a constant distance as in raw ScanImage tiffs)
tiff_view = TiffMovieView(paths)    # paths: str or list of str
frames = tiff_view[0:100]           # → np.ndarray (100, H, W)

as_sliceable_movie(session_ci_movie_data)
# → TiffMovieView | np.ndarray  — normalizes session movie data to (n_frames, H, W) sliceable
# Use on the dict returned by session.calcium_imaging.get_ci_movies()

load_tiff_movie(tiff_file_name, first_frame=None, last_frame=None)
# → np.ndarray (n_frames, H, W)  — loads into memory; use TiffMovieView for large files

read_tiff_movie_frames(tiff_filename)
# → int  — number of frames without loading the movie

get_avg_frames_by_epoch(
    data_3d: np.ndarray,                  # (n_frames, H, W)
    epoch_frames: list,                   # list of (start_frame, stop_frame) tuples
    subtract_baseline: bool = False,
    baseline_end_frame: int | None = None # frame index marking end of baseline within epoch
)
# → tuple (avg_data: np.ndarray, center_frame: int, n_frames_post: int)

reduce_image_dimensions(image: np.ndarray, factor: float = 2.0, anti_aliasing: bool = True)
# → np.ndarray  — spatially downsampled

map_coordinates_to_image(image_values: np.ndarray, coords: list)
# → pd.DataFrame  — per-ROI values mapped to pixel coordinates
```

---

## Period Utilities

**Module:** `cicada_analysis.cicada_tools.core.period_utils`

```python
from cicada_analysis.cicada_tools.core.period_utils import (
    get_continous_time_periods,
    from_timestamps_to_frame_epochs,
    from_timestamps_array_to_list,
    get_complementary_frames,
    fill_gaps_in_continuous_periods,
    extend_invalid_times,
    filter_epoch_timestamps,
    filter_events_based_on_epochs,
    get_epoch_frames,
)

get_continous_time_periods(binary_array: np.ndarray)
# → list[tuple[int, int]]  — (start_frame, stop_frame inclusive) for each run of 1s

from_timestamps_to_frame_epochs(
    time_stamps_array: np.ndarray,   # (2, N) epoch array in seconds (NWB output)
    frames_timestamps: np.ndarray,   # (n_times,) trace timestamps in seconds
    as_list: bool,                   # required: True → list of tuples, False → (2, N) array
    keep_if: str = "whole"           # "whole": epochs entirely in the recording; "start" | "end" | "middle": keep the
                                     #   epochs whose start / end / middle is in it (to align on that time)
)
# → list[tuple[int, int]] if as_list else np.ndarray (2, N) of frame indices
# time_stamps_array must be (2, N): row 0 starts, row 1 ends (transpose a list of pairs)

from_timestamps_array_to_list(
    time_stamps_array: np.ndarray,   # (2, N)
    frames_timestamps: np.ndarray    # (n_times,)
)
# → list[tuple[float, float]]  — the epochs entirely inside the recording range, as pairs of times

get_complementary_frames(
    total_frames: int,
    active_periods: list[tuple[int, int]]    # list of (start, stop) frame pairs
)
# → tuple (bool_array: np.ndarray, int_array: np.ndarray)
# Returns the complement — i.e. frames NOT in any active period.

fill_gaps_in_continuous_periods(
    boolean_serie: np.ndarray,   # 1D binary
    max_gap_size: int            # a gap of fewer than this number of frames is filled
)
# → np.ndarray (bool)

extend_invalid_times(
    invalid_times: np.ndarray,            # (2, N)
    padding: float | tuple[float, float]  # seconds; scalar=symmetric, tuple=(before, after)
)
# → np.ndarray (2, N)

filter_epoch_timestamps(
    epochs_timestamps: np.ndarray,              # (2, N) to filter
    extended_invalid_times: np.ndarray | None,  # (2, M) regions to exclude
    epochs_are_sorted: bool,
    invalid_times_are_sorted: bool,
    filter_consecutive: bool = False,
    use_main_epoch: bool = False,
    main_epoch_timestamps: np.ndarray | None = None,
    main_epoch_name: str = "",
    baseline_length: float = 0.0,
    verbose: bool = False,
    epoch_name: str = ""
)
# → np.ndarray (2, K)  — filtered epochs (K ≤ N)

filter_events_based_on_epochs(
    events_ts: np.ndarray,   # (N,) event timestamps in seconds
    epochs: np.ndarray       # (2, M) epoch windows
)
# → np.ndarray  — events that fall inside at least one epoch window

get_epoch_frames(
    epoch_times: np.ndarray,    # (2, n_epochs) start / stop times
    reference_ts: np.ndarray,   # timestamps of the frames
    max_idx: int                # frames above it are left out
)
# → np.ndarray  — per epoch, the frames from the one nearest its start to the one nearest its stop (excluded)
```

---

## Array Utilities

**Module:** `cicada_analysis.cicada_tools.core.array_utils`

```python
from cicada_analysis.cicada_tools.core.array_utils import (
    find_nearest,
    validate_indices_in_string_format,
    extract_indices_from_string,
    flatten,
)

find_nearest(array: np.ndarray, value: float, is_sorted: bool = True)
# → int  — index of element closest to value. Sorted array: 0 if value is below array[0], len(array)
#   (not a valid index) if above array[-1]; -1 for an empty array

validate_indices_in_string_format(str_indices: str)   # e.g. "1-3 25 6"
# → bool

extract_indices_from_string(str_indices: str)
# → list[int]

flatten(lst)
# → list  — recursively flattens nested iterables
```

---

## Table Utilities

**Module:** `cicada_analysis.cicada_tools.core.table_utils`

Saving the data of results and figures as the core plugins do (tables as .csv, sampled series as .npy), and selecting rows and time columns of trial / epoch tables. Also importable from `cicada_analysis.cicada_tools.core`.

```python
from cicada_analysis.cicada_tools.core.table_utils import (
    save_tables,
    save_samples,
    flat_columns,
    ragged_to_arrays,
    intervals_table,
    filter_table_with_dict,
    table_time_columns,
    table_column_times,
)

save_tables(tables: dict[str, pd.DataFrame], folder: str)   # {file name without extension: table}; None skipped
# → list[str]  — paths of the <folder>/<name>.csv written (no index); folder created if missing

save_samples(
    name: str,                           # common start of the file names, e.g. '<session>_raster'
    folder: str,
    rows: pd.DataFrame | None = None,    # one row per row of the arrays, in their order
    **arrays                             # arrays by key (data=, times=, ...); None skipped
)
# → list[str]  — paths written: <name>_<key>.npy per array, <name>_rows.csv for rows

flat_columns(table: pd.DataFrame)
# → pd.DataFrame  — grouped table (e.g. groupby(...).agg([...])) as plain columns: index reset, multi-level
#   column names joined with '_' (('tau', 'mean') -> 'tau_mean'); a new table

ragged_to_arrays(trains: list[array-like])   # one array per row, e.g. the spike times of each unit
# → tuple (rows: np.ndarray, values: np.ndarray)  — row index of each value, and the values; for save_samples

intervals_table(
    intervals_by_group: list[list[tuple]],   # per group, its (start, stop) intervals
    names: list[str]                         # name of each group
)
# → pd.DataFrame  — columns group, start, stop; one row per interval

filter_table_with_dict(table: pd.DataFrame, filtering_dict: dict)   # {column: [allowed values]}
# → pd.DataFrame  — rows whose value in each column is allowed (any of them for a column with several
#   values per row, e.g. tags); filtering_dict is not modified

table_time_columns(table: pd.DataFrame)
# → list  — columns holding times (name containing 'time', numbers, one or several per row), 'start_time'
#   first: what a PSTH can be aligned on. Align with align_array_to_timestamps(..., table_column_times(table, col), ...)

table_column_times(table: pd.DataFrame, column: str)   # a column of table_time_columns
# → np.ndarray (n_rows,)  — one time per row: the first value for a row holding several (e.g. Allen
#   'lick_times'), NaN for a row without a time
```

---

## Display — Figure

**Module:** `cicada_analysis.cicada_tools.display.core_plots`

**Always use `save_figure` instead of `plt.savefig`** — it handles PDF font embedding, tight layout, safe file
names, and the interactive figure files (`.mplfig`) shown in the GUI's Interactive viewing tab when the run's "Interactive viewing
of the figures" is ticked.

```python
from cicada_analysis.cicada_tools.display.core_plots import (
    save_figure,
    style_axes,
    FIGURE_STYLE,
    split_into_separate_figures,
    create_and_configure_plot,
    get_colormap,
    is_light_color,
    add_scale_bar,
)

save_figure(
    figure,                                   # matplotlib Figure
    results_path: str,                        # directory
    figname: str,                             # filename without extension
    save_formats: tuple | list = ('pdf', 'png'),
    dpi: int | str = 300,                     # or 'figure': the figure's own
    tight_layout: bool = True,
    close: bool = True,
    bbox_inches: str | None = None
)
# → None  — saves to results_path/figname.{ext} for each format (+ figname.mplfig with interactive figures on);
#   closes this figure by default

style_axes(ax, v_line=False, xlim=None, ylim=None, xlabel=None, ylabel=None, despine=False, **style)
# → None  — sets the limits / labels given (None: unchanged), despine: removes top and right borders, then
#   applies only the FIGURE_STYLE keys given (background of axes + figure, tick / label sizes and colours,
#   borders); v_line: dashed line at 0

split_into_separate_figures(data: pd.DataFrame, columns: list, file_name: str)
# → [(rows of the figure, file name)]  — one figure per combination of the values of `columns`

create_and_configure_plot(n_lines, n_cols, size_fig, background_color)
# → tuple (fig, axes)

get_colormap(cmap: str = 'hotcold')
# → matplotlib.colors.Colormap
# Built-in custom colormaps: 'hotcold', 'cyanmagenta', 'whitemagenta'

is_light_color(color)
# → bool  — True if perceptual brightness > 0.5

add_scale_bar(ax, length, label, color, fontproperties=None, axis="x", shown=None, loc=2, anchor=(0., 1.),
              label_top=True, zorder=None)
# → AnchoredSizeBar | None  — `length` data units along 'x' (time) or 'y' (signal), thickness a fixed fraction of
#   the axes; None (not drawn, with a message) when longer than `shown` (time window / signal range shown)
```

---

## Display — Raster

**Module:** `cicada_analysis.cicada_tools.display.raster_plots`

```python
from cicada_analysis.cicada_tools.display.raster_plots import plot_raster

plot_raster(
    spike_nums=None,                    # (n_cells, n_times) binary raster
    title=None,
    file_name=None,                     # without extension
    frame_times=None,                   # (n_times,) timestamps for x-axis
    times_format: str = "sec",          # 'sec' | 'ms'
    spike_train_format: bool = False,
    figure_background_color: str = "black",
    raster_face_color: str = 'black',
    cell_spikes_color: str = 'white',
    spike_shape: str = "|",
    spike_shape_size: int = 10,
    save_raster: bool = False,
    save_formats: str = "png",
    path_results: str = None,           # required if save_raster=True (without it, nor axes_list, nothing is saved: the
                                        #   figure is closed and not returned)
    span_area_coords=None,              # list of (start, stop) frame pairs to shade
    span_area_colors=None,
    span_area_only_on_raster: bool = True,
    alpha_span_area: float = 0.5,
    span_line_width=None,               # pt, lines of spans without duration (start = stop); None: matplotlib's
    without_activity_sum: bool = False,
    mouse_speed=None,
    behavioral_ts_list=None,
    axes_list=None,                     # pre-created axes to embed in a larger figure
    size_fig=None,
    traces=None,
    display_traces: bool = False,
    display_spike_nums: bool = True,
    traces_lw: float = 0.3,
    dpi: int = 100,
    ...                                 # many additional style kwargs
)
# → None
```

---

## Display — Distributions

**Module:** `cicada_analysis.cicada_tools.display.distribution_plots`

```python
from cicada_analysis.cicada_tools.display.distribution_plots import (
    plot_box_plots,
    plot_hist_distribution,
    categorical_plot,
    plot_groups,
)

plot_box_plots(
    data_dict: dict,               # {group_label: array or list of values}
    title: str,
    filename: str,                 # without extension
    y_label: str,
    scatter_text_dict=None,
    colors=None,
    path_results: str = None,
    y_lim=None,
    x_label=None,
    with_scatters: bool = True,
    scatter_size: int = 20,
    scatter_alpha: float = 0.5,
    background_color: str = "black",
    labels_color: str = "white",
    link_medians: bool = False,
    save_formats: str = "pdf",
    with_timestamp_in_file_name: bool = False,
    ...
)
# → None

plot_hist_distribution(
    distribution_data,             # array or list of values
    filename=None,
    values_to_scatter=None,
    n_bins=None,
    use_log: bool = False,
    x_range=None,
    labels=None,
    background_color: str = "black",
    path_results=None,
    save_formats: str = "pdf",
    ax_to_use=None,
    density: bool = False,
    ...
)
# → None

categorical_plot(
    kind: str,                     # 'strip', 'swarm', 'violin', 'box', 'bar' or 'boxen'
    ax,                            # existing axes (sns.catplot ignores ax: use this instead)
    **kwargs,                      # seaborn arguments: data=, x=, y=, hue=, order=, palette=...
)
# → ax  (strip jitter / bar bootstrap seeded: same figure at every run)

plot_groups(
    table: pd.DataFrame,           # one row per observation (e.g. cell) with the group columns
    value: str, y_label: str,      # column plotted, its axis label
    path: str, file_name: str,     # figures suffixed with their groups
    x=None, hue=None,              # group columns on the x axis / in colour
    separate=(),                   # group columns drawn in separate figures
    levels=(),                     # also one figure per value of these columns, e.g. ('session', 'mouse')
    palette=None,                  # {group: colour} of the hue groups, else of the x groups
    representation="box", x_label="", legend_title=None, style=None,   # style: style_axes keys
    figsize=(10, 8), save_formats="pdf", dpi=100, save=True,
    do_stats=False, pvalue=0.05,   # compare the x groups within each hue group (stats.compare_groups, printed)
    skip_label="all",              # group name left out of the titles
)
# → None
```

---

## Display — PSTH Plots

**Module:** `cicada_analysis.cicada_tools.display.psth_plots`

```python
from cicada_analysis.cicada_tools.display.psth_plots import (
    plot_psth_lines,
    plot_raster_and_psth,
    common_y_limits,
    psth_legend_counts,
)
# split_into_separate_figures, style_axes, FIGURE_STYLE: display.core_plots (any figure)

plot_psth_lines(
    summary: pd.DataFrame,      # line_and_band table: x, 'line', 'low', 'high' + the row / col / hue / style columns
    x='time', row=None, col=None, hue=None, style=None,
    palette=None,               # {hue level: color}; others from the matplotlib cycle
    x_label="Time (s)", y_label="", title="",
    labels=None,                # {hue level: legend text}
    y_lim=None,                 # (bottom, top) of every panel
    width_fig=15, height_fig=8, dpi=300, xkcd_mode=False,
    save_path=None, save_formats="pdf", file_name="psth",
    share_y="row",              # as matplotlib's sharey; False when the panels show different quantities
    **figure_style              # keys of FIGURE_STYLE (text sizes, ticks, colours, line at 0)
)
# panels (row x col) sharing a width_fig x height_fig figure, one line + band per hue level (colour) and style level
# (line style), legend outside. Lines and bands of each level: stats.line_and_band, then stats.reduce_psth_level

plot_raster_and_psth(
    rasters,                    # [(hue level, style level, [spike times relative to each event])]
    summary: pd.DataFrame,      # the unit's lines and bands, as for plot_psth_lines
    x='time', hue=None, style=None, palette=None, x_label="Time (s)", y_label="", title="", labels=None,
    width_fig=15, height_fig=8, dpi=300, xkcd_mode=False, save_path=None, save_formats="pdf", file_name="unit",
    **figure_style
)
# width_fig x height_fig figure: raster (one row per event, coloured like its line) above the PSTH

common_y_limits(tables: list[pd.DataFrame])
# → (bottom, top) covering 'line', 'low', 'high' of every table (figures sharing one y scale)

psth_legend_counts(session_rows, figure_rows, hue, separate, group_columns=("cell_group",), count_column="n_cells",
                   count_name="cells")
# → {hue level: "group\nN=mice, n=sessions\ncells, events"} for plot_psth_lines' labels

```

---

## Display — Graphs

**Module:** `cicada_analysis.cicada_tools.display.graph_plots`

```python
from cicada_analysis.cicada_tools.display.graph_plots import (
    plot_graph,
    plot_connectivity_graphs,
)

plot_graph(
    graph,                          # nx.Graph or nx.DiGraph
    with_fa2: bool = False,         # use ForceAtlas2 layout (requires fa2 package)
    randomized_positions: bool = False,
    filename=None,
    iterations: int = 2000,
    node_color=None,
    edge_color=None,
    background_color=None,
    cmap=None,
    node_size: int = 20,
    with_labels: bool = False,
    title=None,
    ax_to_use=None,
    figure_size: tuple = (5, 5),
    dpi: int = 300,
    save_formats=None,
    save_fig: bool = False,
    path_results=None,
    with_timestamp_in_file_name: bool = False
)
# → None

plot_connectivity_graphs(
    session_id_list,                # list of session IDs
    filename_list=None,
    graph_files_path=None,          # path to saved graph files
    background_color=None,
    node_color=None,
    edge_color=None,
    size_fig=None,
    dpi: int = 300,
    save_formats=None,
    save_fig: bool = False,
    path_results=None,
    with_timestamp_in_file_name: bool = False
)
# → None  — grid of graphs, one per session
```

---

## Display — Connectivity

**Module:** `cicada_analysis.cicada_tools.display.connectivity_plots`

Figures of the connectivity analyses; the computations they plot are in `cicada_analysis.cicada_tools.connectivity` (sections below). Not re-exported by `cicada_tools.display`: import from the module.

```python
from cicada_analysis.cicada_tools.display.connectivity_plots import (
    plot_christmas_tree_heatmap,
    plot_christmas_tree_crosscorr,
    plot_stpr_scatter,
    plot_stpr_heatmap,
    plot_stpr_heatmap_grid,
    plot_pair_ccg,
    plot_similarity_matrix,
)

# Peri-SCE triggered average ("Christmas tree"), from compute_triggered_average_raster
plot_christmas_tree_heatmap(mean_psth, time_axis_s, time_lags_dict, cells_list,
                             data_id: str, path_results: str, save_formats: str = "pdf")
# → None  — heatmap of triggered averages, rows sorted/normalized by each unit's preferred time lag

plot_christmas_tree_crosscorr(mean_psth, time_axis_s, time_lags_dict, cells_list,
                               data_id: str, path_results: str,
                               cells_groups=None, groups_colors=None, ...)
# → None  — per-cell (or per-group mean ± SEM) traces around SCE onset

# Spike-triggered population rate (stPR), from compute_stpr / compute_stpr_cross
# Scatter: coupling strength vs. delay (stPR analogue of the "Christmas tree" scatter above)
plot_stpr_scatter(coupling, delay_s, valid, data_id: str, path_results: str,
                   cells_groups=None, groups_colors=None, save_formats: str = "pdf", ...)
# → None

# Heatmap: z-scored stPR curves sorted by delay
plot_stpr_heatmap(time_axis_s, stpr, delay_s, valid, coupling, data_id: str, path_results: str,
                   save_formats: str = "pdf", ...)
# → None

# Grid of heatmaps (one per group / cross-area pair), shared colorbar
plot_stpr_heatmap_grid(
    entries: list,   # list of (label, stpr, time_axis_s, delay_s, valid) tuples
    data_id: str, path_results: str, max_cols: int = 4, save_formats: str = "pdf", ...
)
# → None

# Plot CCG for a single pair (works for both ephys and imaging)
plot_pair_ccg(
    ia: int, ib: int,                # unit/cell indices
    spike_times_list: list,          # list of 1D arrays (seconds)
    bin_size_ms: float = 0.4,
    max_lag_ms: float = 100.0,
    hollow_ms: float = 10.0, sigma_ms: float = 20.0,
    syn_window: tuple = (1.0, 4.0),
    node_label: str = "unit",        # 'unit' for ephys; 'cell' for imaging
    show_significance: bool = True   # False for imaging (different detection criterion)
)
# → matplotlib.Figure

# Pairwise similarity — plot a matrix from compute_similarity_matrix; single matrix or dict of matrices {label: matrix}
plot_similarity_matrix(
    data: np.ndarray | dict,          # (n_cells, n_cells) or {name: (n_cells, n_cells)}
    filename: str | None = None,
    background_color: str | None = None,
    plt_title: str = ' ',
    colormap: str | None = None,
    size_fig: tuple = (10, 8),
    save_fig: bool = True,
    path_results: str | None = None,
    save_formats: tuple = ('pdf', 'png')
)
# → Figure | None  — seaborn heatmap; vmin=0 vmax=1; dict input produces a multi-panel grid; the Figure is returned
#   when it is not saved (save_fig=False or no path_results)
```

---

## Pairwise Cell Similarity

**Module:** `cicada_analysis.cicada_tools.connectivity.pairwise_cell_similarity`

Use for any correlation or similarity matrix between neurons. Covers Pearson, Hamming, Jaccard, and Cosine — do not reimplement these with numpy/scipy.

```python
from cicada_analysis.cicada_tools.connectivity.pairwise_cell_similarity import (
    compute_similarity_matrix,
    build_pearson_adjacency_matrix,
    get_pairwise_hamming_similarity,
    get_pairwise_jaccard_similarity,
    get_pairwise_cosine_similarity,
)

# Main entry point — unified interface for all methods
compute_similarity_matrix(
    neuronal_data: np.ndarray,       # (n_cells, n_times)
    correlation_axis: int = 0,       # 0 = cells×cells; 1 = times×times (transposes input)
    method: str = None,              # required: 'Pearson' | 'Hamming' | 'Jaccard' | 'Cosine' (None raises ValueError)
    verbose: bool = False
)
# → np.ndarray (n_cells, n_cells)  symmetric similarity matrix (Pearson: plain np.corrcoef, no thresholds)

# Pearson with optional significance thresholding (and optional .npy save)
build_pearson_adjacency_matrix(
    neuronal_data: np.ndarray,            # (n_cells, n_times)
    with_thresholds: bool = True,         # False = fast np.corrcoef; True = loop with p-value filter
    correlation_threshold: float = 0.1,   # entries below this are zeroed
    p_value_threshold: float = 0.05,      # entries with p > this are zeroed
    verbose: bool = False,
    data_id: str = "",
    results_path: str | None = None       # if set, saves matrix as pearson_adjacency_matrix_{data_id}.npy
)
# → np.ndarray (n_cells, n_cells)  — diagonal = 1; off-diagonal = rho or 0

# Binary raster measures (input must be 0/1)
get_pairwise_hamming_similarity(neuronal_data: np.ndarray)   # (n_cells, n_times) → (n_cells, n_cells)
get_pairwise_jaccard_similarity(neuronal_data: np.ndarray)   # (n_cells, n_times) → (n_cells, n_cells)
get_pairwise_cosine_similarity(neuronal_data: np.ndarray)    # (n_cells, n_times) → (n_cells, n_cells)
```

---

## Cross-Correlogram (CCG) Utilities

**Module:** `cicada_analysis.cicada_tools.connectivity.connectivity_utils`

Ephys monosynaptic connection detection (the time-correlation graph of calcium imaging moved to cicada-cossart).

```python
from cicada_analysis.cicada_tools.connectivity.connectivity_utils import (
    bz_detect_connections,
    hollow_gaussian_baseline,
    ccg_peak_significance,
)


# Ephys: detect putative monosynaptic connections via CCG (English et al. 2017, Neuron)
bz_detect_connections(
    spike_times_list: list,          # list of 1D arrays, spike times in seconds
    unit_ids: list,                  # unit indices to test (subset of range(len(spike_times_list)))
    min_spikes: int = 200,           # skip units with fewer spikes
    bin_size_ms: float = 0.4,
    max_lag_ms: float = 100.0,
    hollow_ms: float = 10.0,         # hollow window in Gaussian baseline (ms)
    sigma_ms: float = 20.0,
    syn_window: tuple = (1.0, 4.0)   # (lo_ms, hi_ms) synaptic window to test
)
# → pd.DataFrame  columns: unit_pre, unit_post, connection_type ('excitatory'|'inhibitory'),
#                          peak_latency_ms, transmission_probability, peak_bin_pvalue, n_significant_bins
# Returns empty DataFrame if no connections found.

# Lower-level helpers used internally by bz_detect_connections
hollow_gaussian_baseline(counts: np.ndarray, bin_size_ms: float, hollow_ms: float = 10.0, sigma_ms: float = 20.0)
# → np.ndarray  — Gaussian-smoothed CCG baseline with a hollow window zeroed around lag 0

ccg_peak_significance(counts: np.ndarray, baseline: np.ndarray, lag_centers: np.ndarray, syn_window: tuple = (1.0, 4.0))
# → dict  — {'excitatory': {...}, 'inhibitory': {...}}, each with significant/n_sig/peak_lat/peak_pval/mask/reject
```

---

## Spike-Triggered Population Rate (stPR)

**Module:** `cicada_analysis.cicada_tools.connectivity.connectivity_utils`

Leader/follower analysis (Bimbard et al. 2026 style): for each unit/cell, cross-correlates its own
activity with the mean-subtracted population rate (excluding itself). Coupling strength = value at
lag 0; delay = centre of mass of the (low-passed) curve. Works for both ephys spike times and
calcium-imaging rasters.

```python
from cicada_analysis.cicada_tools.connectivity.connectivity_utils import (
    compute_stpr,
    compute_stpr_cross,
)

# Within-population stPR — one unit's spikes vs. the rest of the population's mean rate
compute_stpr(
    spike_times_list: list = None,   # list of 1D arrays (seconds); OR pass spike_mat directly
    bin_size_s: float = 0.001,
    window_s: float = 0.08,          # half-window for the cross-correlation
    lp_cutoff_hz: float = 20.0,
    spike_mat: np.ndarray = None     # (n_units, n_bins) binary — alternative to spike_times_list
)
# → (stpr, time_axis, coupling, delay_s, valid)
#   stpr: (n_units, n_lags); coupling/delay_s/valid: (n_units,)

# Cross-area stPR — source units' spikes vs. a disjoint target population's rate (no self-exclusion)
compute_stpr_cross(
    source_spike_times: list, target_spike_times: list,
    bin_size_s: float = 0.001, window_s: float = 0.08, lp_cutoff_hz: float = 20.0
)
# → (stpr, time_axis, coupling, delay_s, valid)  — same shapes as compute_stpr
```

---

## Peri-SCE Triggered Average ("Christmas Tree")

**Module:** `cicada_analysis.cicada_tools.connectivity.connectivity_utils`

Calcium-imaging counterpart to the time-correlation graph, built around detected SCEs (Synchronous
Calcium Events) rather than arbitrary events.

```python
from cicada_analysis.cicada_tools.connectivity.connectivity_utils import (
    compute_triggered_average_raster,
    estimated_autocorrelation,
)

compute_triggered_average_raster(raster: np.ndarray, sce_centers: list, window_frames: int)
# → (mean_response, time_frames)  — peri-SCE triggered average of a binary raster

estimated_autocorrelation(x: np.ndarray)
# → np.ndarray  — normalized autocorrelation estimate of a 1-D signal
```

---

## Graphs & Connectivity

**Module:** `cicada_analysis.cicada_tools.graphs.graph_building`  
**Module:** `cicada_analysis.cicada_tools.graphs.graph_analysis`

```python
from cicada_analysis.cicada_tools.graphs.graph_building import (
    build_connectivity_graphs,
    build_graph_from_adjacency_matrix,
    build_graph_from_transition_dict,
)
from cicada_analysis.cicada_tools.graphs.graph_analysis import (
    detect_hub_cells,
    find_paths_in_a_graph,
    welsh_powell,
)

build_connectivity_graphs(
    spike_data,               # (n_cells, n_times) binary raster or spike times
    sampling_rate: float,     # Hz
    time_delay: float = 500,  # ms — lag window for spike-triggered histogram
    save_graphs: bool = False,
    path_results=None,
    filename=None,
    verbose=None
)
# → nx.DiGraph  — directed graph with edge weights from cross-correlation

build_graph_from_adjacency_matrix(
    adjacency_matrix: np.ndarray,
    weight_on_edges: bool = True,
    directed_graph: bool = True,
    symmetric_matrix: bool = False,
    save_graphs: bool = False,
    path_results=None,
    filename=None
)
# → nx.Graph | nx.DiGraph

build_graph_from_transition_dict(
    transition_dict,
    n_connected_cell_to_add,
    use_longest_path: bool = False,
    with_weight: bool = True,
    cells_to_isolate=None,
    transition_dict_2_nd_order=None,
    spikes_dist_dict=None,
    min_rep_nb=None
)
# → nx.DiGraph

detect_hub_cells(
    graphs_to_analyse: dict,             # {session_id: nx.DiGraph}
    cell_connectivity_threshold: float = 5,
    top_connected_cells: int = 20,   # percent: hubs are among the top 20 % most connected cells of all the graphs
    verbose: bool = True
)
# cell_connectivity_threshold is a percentage too: a hub is linked to at least 5 % of the cells of its graph
# → dict {graph id (the keys of graphs_to_analyse): list of hub cell indices}; a graph without hub is absent

find_paths_in_a_graph(
    graph,
    shortest_path_on_weight,
    with_weight,
    use_longest_path: bool = False,
    debug_mode: bool = False
)
# → tuple (seq_list, isolates_cell)

welsh_powell(graph)
# → dict  — {node: color_int} graph coloring
```

---

## Ephys Signal Processing

**Module:** `cicada_analysis.cicada_tools.ephys.ephys_signal_processing`

```python
from cicada_analysis.cicada_tools.ephys.ephys_signal_processing import (
    bin_raster,
    replace_artifact_spikes,
    render_spike_activity_sum,
    smooth_causal_half_gaussian,
)

bin_raster(raster: np.ndarray, bin_size: int, keep_same_dimension: bool = True)
# → np.ndarray  — binned spike raster (same shape if keep_same_dimension=True)

replace_artifact_spikes(
    spike_times: list[np.ndarray],                    # one array per unit
    event_times: np.ndarray,                          # (N,) event times in seconds
    artifact_window: tuple[float, float] = (-0.01, 0.005),   # window relative to event to blank
    baseline_window: tuple[float, float] = (-0.5, -0.01),    # window to sample replacement spikes from
    seed=None
)
# → list[np.ndarray]  — spike_times with artifact spikes replaced by Poisson surrogates

render_spike_activity_sum(
    ax,                              # matplotlib Axes
    spike_nums_for_activity_sum,     # (n_cells, n_times)
    frame_times,
    n_cells,
    n_times,
    min_time: float = 0,
    max_time: float = 0,
    show_sum_spikes_as_percentage: bool = False,
    activity_threshold=None,
    SCE_times=None,
    color_peaks_activity: bool = False,
    activity_sum_plot_color: str = 'white',
    activity_sum_face_color: str = 'black',
    bin_size_ms_for_spikes_sum: int = 100,
    spike_train_format: bool = False,
    ...
)
# → None  — renders population spike count panel on an axes object

smooth_causal_half_gaussian(
    x: np.ndarray,    # any array
    sigma: float,     # smoothing width in seconds
    dt: float,        # bin size in seconds
    axis: int = 1
)
# → np.ndarray  same shape as x
```

---

## Ephys Display

**Module:** `cicada_analysis.cicada_tools.ephys.ephys_plots`

```python
from cicada_analysis.cicada_tools.ephys.ephys_plots import render_spikes

render_spikes(
    ax,                              # matplotlib Axes
    spike_nums: np.ndarray,          # (n_cells, n_times) binary raster
    frame_times=None,
    spike_train_format: bool = False,
    spike_shape: str = '|',
    spike_shape_size: int = 10,
    cell_spikes_color: str = 'white',
    plot_with_amplitude: bool = False,
    cells_to_highlight=None,
    cells_to_highlight_colors=None,
    horizontal_lines=None,
    display_traces: bool = False,
    traces=None,
    n_cells=None,
    debug_mode: bool = False,
    ...
)
# → dict  — rendering metadata (e.g. scalar_map if amplitude-colored)
```

---

## Behavior Analysis

**Module:** `cicada_analysis.cicada_tools.behavior.behavior_analysis_utils`

DLC trace preprocessing and behavior PSTH tables (trial / epoch table helpers: see Table Utilities; the Petersen lab
task utilities moved to cicada-petersen).

```python
from cicada_analysis.cicada_tools.behavior.behavior_analysis_utils import (
    build_dlc_psth_df,
    preprocess_dlc_trace,
    preprocess_dlc_series,
    remove_outliers_zscore,
    interpolate_nans,
)

build_dlc_psth_df(
    signals: dict,              # {name: (values (n_frames,) or (n_frames, n_columns), timestamps in s)}
    trial_timestamps,           # times to align on (s)
    psth_start_in_sec: float,
    psth_stop_in_sec: float,
    subtract_baseline: bool = True
)
# → pd.DataFrame  — one row per series column and event: 'behavior_movie_data_event' (aligned values), 'time'
#   (their times relative to the event), 'bodypart';
#   events whose window leaves the recording are dropped; the caller adds its own columns

preprocess_dlc_trace(trace: np.ndarray)
# → np.ndarray  — remove_outliers_zscore (threshold 20) → interpolate_nans (no smoothing)

preprocess_dlc_series(values: np.ndarray)
# → np.ndarray (n_frames, n_columns)  — preprocess_dlc_trace on each column

remove_outliers_zscore(trace: np.ndarray, threshold: float = 10)
# → np.ndarray  — outliers replaced with NaN

interpolate_nans(trace: np.ndarray)
# → np.ndarray  — linear interpolation of NaN segments
```

---

## Clustering

**Module:** `cicada_analysis.cicada_tools.clustering`

K-means clustering: best of several KMeans runs by silhouette score, choice of the number of clusters
against shuffled surrogates, ordering by cluster, and the silhouette and clustering plots. Used
internally by cell-assembly detection, but usable standalone.

```python
from cicada_analysis.cicada_tools.clustering import (
    find_best_kmeans,
    surrogate_silhouette_threshold,
    select_n_clusters,
    order_by_cluster,
    plot_silhouettes,
    plot_clustering,
)

find_best_kmeans(
    data: np.ndarray,                # (n_samples, n_features)
    n_cluster: int,
    n_tests: int = 100,              # number of KMeans re-runs
    scoring_fn=np.median,            # per-cluster silhouette reduction; use np.mean for Malvache-paper behavior
    seed=0                           # int or np.random.Generator: same seed, same fit
)
# → (KMeans, float)  — best-scoring fitted estimator and its silhouette score

surrogate_silhouette_threshold(
    data: np.ndarray,                # (n_samples, n_features)
    n_clusters: int,
    n_surrogate: int,                # surrogates: each column of data permuted on its own
    n_trials: int,                   # KMeans fits per surrogate
    perc_threshold: float,
    scoring_fn,                      # np.mean or np.median, keeps the best fit
    n_jobs: int = 4,                 # -1 = all cores
    seed=0                           # int or np.random.Generator: same seed, same result whatever n_jobs
)
# → (float, float)  — percentile over the individual cluster silhouettes, percentile over the
#                     per-surrogate means; NaN when no surrogate could be clustered

select_n_clusters(
    data: np.ndarray,                # (n_points, n_features)
    range_n_clusters,                # numbers of clusters to test
    n_surrogate: int = 1000,
    perc_threshold: float = 95,
    n_trials: int = 100,             # KMeans fits per number of clusters, on the data and on each surrogate
    scoring_fn=np.mean,
    n_jobs: int = 4,
    seed=0
)
# → (best_kmeans_by_n_clusters: dict, surrogate_percentiles_by_n_clusters: dict, n_clusters_best_score: int,
#    significant: bool array over range_n_clusters, best_significant_n_clusters: int | None)
#   a number of clusters is significant when its best score is above the perc_threshold percentile of the
#   surrogates' mean silhouettes

order_by_cluster(labels, clusters=None)
# → (order: np.ndarray, boundaries: list)  — indices of the points grouped by cluster (default: the labels
#   present, sorted, so -1 first) and the positions where each group after the first starts

plot_silhouettes(ax, kmeans, data: np.ndarray, n_clusters: int, surrogate_threshold: float = None)
# → None  — per-cluster silhouette bar chart; clusters above surrogate_threshold get a white outline

plot_clustering(ax_silhouettes, ax_matrix, data: np.ndarray, kmeans, n_clusters: int,
                surrogate_threshold: float = None, title: str = None)
# → None  — silhouettes (ax_silhouettes, None: not drawn) and the square similarity matrix `data` with its
#           rows and columns ordered by cluster, on ax_matrix
```

---

## Sequences Detection

**Module:** `cicada_analysis.cicada_tools.sequences`

PCA-based sequence detection (Villette et al. 2015), used by the `cicada_seq_malvache_analysis` plugin. Not
re-exported at package level — import directly from the submodule (the graph-based sequence detection moved
to cicada-cossart).

```python
from cicada_analysis.cicada_tools.sequences.malvache.utils_malvache_sequences import (
    step1_pca_off_memory,
    convert_position_to_distance,
)

step1_pca_off_memory(data: np.ndarray, n_pc_max: int)
# → (data_centralized (n_cells, n_times), pc_time_course (n_pc_max, n_times - 1))  — PCA on the lag-1 temporal
#   covariance matrix, matrix-free (ARPACK): the n_times × n_times matrix is never formed.
#   Raises an exception if n_times < n_cells

convert_position_to_distance(positions: np.ndarray, loop_length: float)
# → (total_traveled_distance: list, n_laps: int)  — circular-track position → cumulative distance
#   (a new lap when the position drops by more than 100 units between two frames)
```

---

## Cell Assemblies

**Module:** `cicada_analysis.cicada_tools.cell_assemblies.malvache` (submodules `detection`, `plots`, `files`,
`pipeline`; every public name is exported by the package)

SCE-based k-means assembly detection (Malvache et al. 2016), built on `clustering` and
`pairwise_cell_similarity` — used by the `cicada_assemblies_malvache_analysis` plugin. The `_sce_clusters`
figure and `_clusters_stat_k_mean_` file use the closest SCE cluster of each cell (no statistical test); the
`_cell_assemblies` figure and data file use the cell assemblies of the permutation tests:

```python
from cicada_analysis.cicada_tools.cell_assemblies.malvache import (
    detect_and_plot_cell_assemblies,                                  # pipeline
    CellAssemblies, sces_clustering, detect_cell_assemblies,          # detection
    participation_permutation_tests, closest_sce_cluster_of_cells, sce_participation_stats,
    plot_cell_assemblies, plot_assemblies_raster, plot_cells_vs_sce,  # plots
    plot_sce_clustering, plot_cells_in_sce_clusters, plot_sce_clusters_figure,
    save_cell_assemblies_data, save_sce_clusters_stats, load_cell_assemblies_data,   # files
)

detect_and_plot_cell_assemblies(
    labels, activity_threshold, range_n_clusters_k_mean: np.ndarray, n_surrogate_k_mean: int,
    spike_nums_to_use: np.ndarray, cellsinpeak: np.ndarray, data_descr: str, path_results: str,
    sliding_window_duration: int, SCE_times, perc_threshold: float,
    n_surrogate_activity_threshold: int, sce_times_bool=None, debug_mode=False,
    keep_only_the_best=True, with_cells_in_cluster_seq_sorted=False, fct_to_keep_best_silhouettes=np.mean,
    save_formats="pdf", seed=0, look=None, save_files=True
)
# → None  — top-level entry point: clusters the SCEs, keeps the numbers of clusters above their surrogates,
#           detects the cell assemblies, then plots the figures and (save_files) writes the data files.

sces_clustering(cells_in_sce: np.ndarray, range_n_clusters, fct_to_keep_best_silhouettes=np.mean,
                n_surrogate=1000, perc_threshold_for_surrogate=95, seed=0)
# → (best_kmeans_by_n_clusters, m_sces, surrogate_percentiles, n_clusters_best_score, significant,
#    best_significant_n_clusters)  — select_n_clusters on the SCE correlation matrix m_sces

detect_cell_assemblies(
    cellsinpeak: np.ndarray, sce_labels_by_n_clusters: dict,          # number of clusters -> cluster of each SCE
    neurons_labels, path_results, sliding_window_duration, SCE_times, data_id, n_surrogate: int,
    cluster_with_best_silhouette_score: int, debug_mode=False, seed=0
)
# → (cluster ids, cluster of each cell, CellAssemblies), each a dict by number of clusters

participation_permutation_tests(cell_assemblies_struct, n_surrogate=1000, debug_mode=False, seed=0)
# → None  — fills the CellAssemblies in place: cells and SCEs significantly in each cluster (permutation
#           tests, Bonferroni), cells and SCEs ordered for the figure

closest_sce_cluster_of_cells(cells_in_peak, cluster_labels, significant_clusters)
# → np.ndarray (int8)  — cluster where each cell is active in the largest share of SCEs (-1: none), no test

sce_participation_stats(sce_id, spike_nums_to_use, SCE_times, sliding_window_duration)
# → (duration_in_frames, max_activity, mean_activity, overall_activity)

plot_cell_assemblies(cas, data_descr, SCE_times, activity_threshold, spike_nums, sce_times_bool=None,
                     display_only_cell_assemblies_on_raster=False, with_cells_in_cluster_seq_sorted=False,
                     save_formats="pdf", look=None)
# → None  — saves <data_descr>_<n_clusters>_cell_assemblies (raster + cells x SCEs heatmap)

plot_sce_clusters_figure(spike_nums, cellsinpeak, labels, cluster_labels_for_neurons, kmeans, m_sces,
                         n_cluster, significant_sce_clusters, surrogate_threshold, SCE_times,
                         activity_threshold, data_descr, path_results, save_formats="pdf", look=None)
# → None  — saves <data_descr>_<n_cluster>_sce_clusters (SCE similarity matrix, cells x SCEs heatmap,
#           silhouettes, raster ordered by cluster)

save_cell_assemblies_data(cas, n_clusters, activity_threshold)
# → None  — writes <data_id>_<n_clusters>_clusters_cell_assemblies_data.txt in cas.path_results

load_cell_assemblies_data(data_file_name: str)
# → [cell_assemblies, sce_times_in_single_cell_assemblies, sce_times_in_multiple_cell_assemblies,
#    sce_times_in_cell_assemblies, sce_times_in_cell_assemblies_by_cell]
```

Also in `plots` (building blocks of the two figures): `plot_assemblies_raster(cas, axes_list, spike_nums, ...)`,
`plot_cells_vs_sce(cas, ax2)`, `plot_sce_clustering(cells_in_peak, m_sces, n_clusters, kmeans,
cluster_labels_for_neurons, significant_sce_clusters, data_str, ...)`,
`plot_cells_in_sce_clusters(ax2, cells_in_peak, sce_labels, n_clusters, significant_sce_clusters,
cluster_labels_for_neurons, neurons_labels=None, look=None)`. In `files`:
`save_sce_clusters_stats(...)` (writes `<data_descr>_<n_cluster>_clusters_stat_k_mean_.txt`).

---

## Stats

**Module:** `cicada_analysis.cicada_tools.stats.stats`

```python
from cicada_analysis.cicada_tools.stats.stats import (
    mean_ci_half_width,
    line_and_band,
    compare_two_distributions,
    multiple_comparison_one_factor_effect,
    compare_groups,
    summarize_by_levels,
    bh_reject,
    chi_square_uniformity_test,
    calculate_statistics,
)

mean_ci_half_width(x: np.ndarray, confidence: float = 0.95, n_resamples: int = 999)
# → float  — bootstrap CI half-width; use as symmetric error band in PSTHs

line_and_band(data: pd.DataFrame, value: str, by: list, reduction="median", band="percentiles",
              low_percentile=25, high_percentile=75)
# → pd.DataFrame  — per group of `by` (e.g. time + groups): 'line' (mean / median) and 'low' / 'high' of the band
#   ('SD', 'SEM', '95% CI' of the mean, 'percentiles', 'none'), 'n'; NaN ignored, no band under 2 values

compare_two_distributions(
    distribution1: np.ndarray,
    distribution2: np.ndarray,
    pvalues: float = 0.05,
    verbose: bool = True
)
# → list[dict]  — the tests run, each {'test', 'statistic', 'p_value'}; printed with verbose=True. Fewer than 25
#   values in one set: Anderson-Darling, else KS and Epps-Singleton; then fewer than 30: Mann-Whitney, else a t-test
#   (Student or Welch) after a normality check

multiple_comparison_one_factor_effect(
    distributions_list: list,    # list of arrays (one per group)
    pvalues: float = 0.05,
    verbose: bool = True,
    sessions_ids=None
)
# → dict {'test', 'statistic', 'p_value', 'posthoc'}  — printed with verbose=True. A group of fewer than 30 values:
#   Kruskal-Wallis; else one-way ANOVA if all the groups are normal and have equal variances, else Kruskal-Wallis.
#   'posthoc': pairwise p-values DataFrame when significant (Dunn/Bonferroni or Student/Holm), else None

compare_groups(rows: pd.DataFrame, value: str, x: str, hue=None, pvalues=0.05, verbose=True, units=None)
# → None  — the groups of column x compared within each group of column hue (2: compare_two_distributions,
#   more: multiple_comparison_one_factor_effect); NaN left out; units: columns of the statistical unit
#   (e.g. ['mouse']): the mean per unit and group is compared

summarize_by_levels(table: pd.DataFrame, value: str, group_columns: list,
                    levels=(("session", ["mouse", "session"]), ("mouse", ["mouse"])))   # (level name, columns) pairs
# → dict  — {level: table of count, mean, std, min, median, max of value per group_columns + level columns}

bh_reject(pvals: np.ndarray, q: float = 0.01)
# → np.ndarray (bool)  — True where H0 rejected (Benjamini-Hochberg FDR)

chi_square_uniformity_test(observed_data, binsize)
# → tuple (chi2_stat: float, p_value: float, uniformity: bool)

calculate_statistics(distribution)
# → tuple (length, mean, median, sigma, iqr)
```
