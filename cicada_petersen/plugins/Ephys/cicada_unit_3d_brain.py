"""
Cicada analysis: interactive 3D visualisation of unit CCF coordinates.

Reads unit CCF coordinates directly from NWB files via cicada's electrophysiology
interface, aggregates across all loaded sessions, and writes:
  - an interactive HTML figure (Plotly, optional — requires plotly)
  - a rotating MP4 animation (matplotlib)

Brain surface overlay and HTML output require optional packages:
  pip install iblatlas plotly
"""

from pathlib import Path
from time import time

import matplotlib.pyplot as plt
import matplotlib.animation as animation

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.ephys.anatomy_utils import map_to_area_groups
from cicada_petersen.tools.ccf_plots import (
    collect_coordinates,
    build_brain_surface,
    make_plotly_figure,
    make_rotation_animation,
)

try:
    from iblatlas import atlas as ibl_atlas
    HAS_IBLATLAS = True
except ImportError:
    HAS_IBLATLAS = False

try:
    import plotly  # noqa: F401 — presence check only
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


class CicadaUnit3DBrain(CicadaAnalysis):

    def __init__(self, config_handler=None):
        long_description = '<p align="center"><b>Unit 3D Brain</b></p>'
        long_description += ('Visualises unit CCF coordinates (AP / ML / DV) as an interactive '
                             '3D scatter across all loaded sessions.<br><br>')
        long_description += ('Reads CCF coordinates directly from the NWB units table '
                             '(<code>ccf_atlas_ap/ml/dv</code>).<br>')
        long_description += ('Brain surface overlay requires <code>iblatlas</code>; '
                             'HTML output requires <code>plotly</code>:<br>')
        long_description += '<code>pip install iblatlas plotly</code>'

        CicadaAnalysis.__init__(
            self,
            name='Unit 3D Brain',
            family_id='Ephys',
            short_description='3D scatter of unit CCF coordinates across sessions',
            long_description=long_description,
            config_handler=config_handler,
            accepted_data_formats=['CI_DATA'],
        )

    def copy(self):
        analysis_copy = CicadaUnit3DBrain(config_handler=self.config_handler)
        self.transfer_attributes_to_tabula_rasa_copy(analysis_copy=analysis_copy)
        return analysis_copy

    def check_data(self):
        super().check_data()

        for session in self._data_to_analyse:
            if not session.electrophysiology.has_units():
                self.invalid_data_help = (
                    f'No units table found in session {session.identifier}.'
                )
                return False
            units_df = session.electrophysiology.get_units_table()
            missing = [c for c in ('ccf_atlas_ap', 'ccf_atlas_ml', 'ccf_atlas_dv')
                       if c not in units_df.columns]
            if missing:
                self.invalid_data_help = (
                    f'Missing CCF coordinate columns in {session.identifier}: {missing}'
                )
                return False

        return True

    def setup_parameters(self):
        CicadaAnalysis.setup_parameters(self)

        # Collect quality label choices from all sessions
        all_labels = set()
        for session in self._data_to_analyse:
            units_df = session.electrophysiology.get_units_table()
            if units_df is not None and 'bc_label' in units_df.columns:
                all_labels.update(units_df['bc_label'].dropna().unique())
        quality_choices = sorted(all_labels) if all_labels else ['good', 'mua']

        _coord_suffixes = ('_ap', '_ml', '_dv')
        _keywords = ('ccf', 'location', 'atlas', 'region')
        location_cols = set()
        for session in self._data_to_analyse:
            units_df = session.electrophysiology.get_units_table()
            if units_df is not None:
                for c in units_df.columns:
                    if any(kw in c for kw in _keywords) and not c.endswith(_coord_suffixes):
                        location_cols.add(c)
        color_choices = sorted(location_cols) if location_cols else ['ccf_atlas_acronym']
        _priority = ['ccf_atlas_acronym', 'ccf_atlas_parent_acronym', 'ccf_acronym', 'ccf_location', 'location']
        default_color = next((c for c in _priority if c in location_cols), color_choices[0])

        self.add_choices_arg_for_gui(
            arg_name='color_by',
            choices=color_choices,
            default_value=default_color,
            short_description='Column to color units by',
            multiple_choices=False,
            family_widget='display',
        )

        self.add_bool_option_for_gui(
            arg_name='use_area_groups',
            true_by_default=True,
            short_description='Group colors by broad area (Motor, Hippocampus, etc.)',
            family_widget='display',
        )

        self.add_choices_arg_for_gui(
            arg_name='quality_labels',
            choices=quality_choices,
            default_value=quality_choices,
            short_description='Unit quality labels to include',
            multiple_choices=True,
            family_widget='display',
        )

        self.add_choices_arg_for_gui(
            arg_name='output_type',
            choices=['html_only', 'mp4_only', 'both'],
            default_value='html_only',
            short_description='Output format',
            long_description='MP4 format might require additional toolboxes to work especially on windows computers',
            multiple_choices=False,
            family_widget='output',
        )

        self.add_bool_option_for_gui(
            arg_name='show_brain_surface',
            true_by_default=True,
            short_description='Overlay brain surface mesh (requires iblatlas)',
            family_widget='output',
        )

        self.add_int_values_arg_for_gui(
            arg_name='decimate',
            min_value=1,
            max_value=10,
            default_value=3,
            short_description='Surface mesh decimation factor (higher = faster, coarser)',
            family_widget='output',
        )

        self.add_int_values_arg_for_gui(
            arg_name='n_frames',
            min_value=30,
            max_value=360,
            default_value=120,
            short_description='Number of frames in rotation animation',
            family_widget='animation',
        )

        self.add_int_values_arg_for_gui(
            arg_name='fps',
            min_value=10,
            max_value=60,
            default_value=30,
            short_description='Animation frame rate (fps)',
            family_widget='animation',
        )

    def run_analysis(self, **kwargs):
        CicadaAnalysis.run_analysis(self, **kwargs)

        color_by = kwargs.get('color_by', 'ccf_atlas_acronym')
        use_area_groups = kwargs.get('use_area_groups', True)
        quality_labels = list(kwargs.get('quality_labels', ['good', 'mua']))
        output_type = kwargs.get('output_type', 'html_only')
        show_brain_surface = kwargs.get('show_brain_surface', True)
        decimate = int(kwargs.get('decimate', 3))
        n_frames = int(kwargs.get('n_frames', 120))
        fps = int(kwargs.get('fps', 30))

        results_path = Path(self.get_results_path())
        n_sessions = len(self._data_to_analyse)

        # ── collect coordinates from NWB sessions ────────────────────────────
        units_tables = {
            s.identifier: s.electrophysiology.get_units_table()
            for s in self._data_to_analyse
        }
        df = collect_coordinates(units_tables, quality_labels)
        if df.empty:
            print('[Unit3DBrain] No units matched the quality filter — aborting.')
            return
        print(f'[Unit3DBrain] {len(df):,} units from {n_sessions} session(s)')

        if use_area_groups and color_by in df.columns:
            df['area_group'] = map_to_area_groups(df[color_by])
            plot_col = 'area_group'
        else:
            plot_col = color_by

        self.update_progressbar(time_started=self.analysis_start_time, increment_value=40)

        # ── brain surface ─────────────────────────────────────────────────────
        mesh = None
        if show_brain_surface:
            if HAS_IBLATLAS:
                print('[Unit3DBrain] Loading AllenAtlas …')
                ba = ibl_atlas.AllenAtlas()
                mesh = build_brain_surface(ba, decimate=decimate)
            else:
                print('[Unit3DBrain] WARNING: iblatlas is not installed — brain surface skipped. '
                      'Install with: pip install iblatlas')

        self.update_progressbar(time_started=self.analysis_start_time, increment_value=30)

        title_tag = f'{n_sessions} session{"s" if n_sessions != 1 else ""}'
        stem = f'unit_3d_brain_{plot_col}'

        # ── HTML output ───────────────────────────────────────────────────────
        if output_type in ('html_only', 'both'):
            if HAS_PLOTLY:
                fig_plotly = make_plotly_figure(df, mesh, color_by=plot_col,
                                                title_tag=title_tag)
                html_path = results_path / f'{stem}.html'
                fig_plotly.write_html(str(html_path), include_plotlyjs='cdn')
                print(f'[Unit3DBrain] Saved interactive HTML: {html_path}')
            else:
                print('[Unit3DBrain] WARNING: plotly is not installed — HTML output skipped. '
                      'Install with: pip install plotly')

        self.update_progressbar(time_started=self.analysis_start_time, increment_value=15)

        # ── MP4 output ────────────────────────────────────────────────────────
        if output_type in ('mp4_only', 'both'):
            fig_mpl, anim = make_rotation_animation(
                df, mesh, color_by=plot_col, title_tag=title_tag,
                n_frames=n_frames, fps=fps,
            )
            mp4_path = results_path / f'{stem}.mp4'
            writer = animation.FFMpegWriter(
                fps=fps, bitrate=2000,
                extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p'],
            )
            try:
                anim.save(str(mp4_path), writer=writer)
                print(f'[Unit3DBrain] Saved animation: {mp4_path}')
            except FileNotFoundError:
                print('[Unit3DBrain] WARNING: ffmpeg not found — MP4 output skipped. '
                      'Install ffmpeg and ensure it is on your PATH.')
            finally:
                plt.close(fig_mpl)

        self.update_progressbar(time_started=self.analysis_start_time, increment_value=15)
        print(f'[Unit3DBrain] Done in {time() - self.analysis_start_time:.1f} s')
