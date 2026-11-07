import os
import warnings
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.display.core_plots import save_figure
from cicada_petersen.tools.behavior_utils import add_correct_choice_to_table, get_block_size_from_table
from cicada_analysis.cicada_tools.core import print_info_dict, find_nearest
from cicada_petersen.tools.widefield_utils import plot_wf_single_frame, get_session_average_wf_baseline_images


class CicadaWidefieldBaselineDiffPostTransition(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        long_description = '<p align="center"><b>Compare Baseline</b></p>'
        long_description = long_description + 'Main parameters:<br>'
        long_description = long_description + (' - Box "Analysis type": Choose the type of analysis you want to perform'
                                               ' (Compare image baseline or compare trace baseline).<br>')
        long_description = long_description + (' - Box "plot type": Choose whether you want to plot a full average, an '
                                               'average grouped by mouse, or an average grouped by brain region.<br>')
        long_description = long_description + ' - Box "cell type": Select the cell type to use for the PSTH.<br><br>'
        long_description = long_description + "Table saved: All single session results.<br>"
        CicadaAnalysis.__init__(self, name="Post-transition baseline differences", family_id="Widefield",
                                short_description="Baseline differences over time following context transition",
                                long_description=long_description,
                                config_handler=config_handler,
                                accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaWidefieldBaselineDiffPostTransition(config_handler=self.config_handler)
        self.transfer_attributes_to_tabula_rasa_copy(analysis_copy=analysis_copy)
        return analysis_copy

    def check_data(self):
        """
        Check the data given one initiating the class and return True if the data given allows the analysis
        implemented, False otherwise.
        :return: a boolean
        """
        super().check_data()

        for session_index, session_data in enumerate(self._data_to_analyse):
            if session_data.DATA_FORMAT != "CI_DATA":
                self.invalid_data_help = f"Non CI_DATA format compatibility not yet implemented: " \
                                         f"{session_data.DATA_FORMAT}"
                return False

            # files without Petersen session metadata have no session type (None): not widefield
            if 'wf' not in (session_data.petersen.get_session_type() or ''):
                self.invalid_data_help = f"No widefield data in {session_data.identifier}"
                return False

        return True

    def setup_parameters(self):
        """

        Returns:

        """
        CicadaAnalysis.setup_parameters(self)

        self.add_widefield_acquisitions_dict_for_gui(short_description=" ", long_description=None,
                                                     arg_name='widefield_acquisition',
                                                     family_widget="Widefield movie to use")

        self.add_bool_option_for_gui(arg_name="only_correct_trials", true_by_default=True,
                                     short_description="Keep only correct trials in trial table",
                                     long_description=None, family_widget='Compare baseline config')

        self.add_choices_arg_for_gui(arg_name="quiet_window_mode", choices=['last 2s', 'last 0.5s', 'full quiet window'],
                                     default_value='last 2s',
                                     short_description="Define the quiet window to extract data at each trial",
                                     long_description="",
                                     multiple_choices=False,
                                     family_widget="Compare baseline config")

        self.add_int_values_arg_for_gui(arg_name="binsize", min_value=5, max_value=300,
                                        short_description="Bin size in seconds for time-in-context axis",
                                        long_description="Time bin size (in seconds) used to digitize the "
                                                         "time-in-context column for grouping baseline images.",
                                        default_value=10, family_widget="Compare baseline config")

        self.add_choices_arg_for_gui(arg_name="color_map", choices=['hotcold', 'seismic'],
                                     default_value='seismic',
                                     short_description="Select the color map for the difference image",
                                     long_description="",
                                     multiple_choices=False,
                                     family_widget="colorbar")

        self.add_field_text_option_for_gui(arg_name="colorbar_scale_min", default_value='-0.005',
                                           short_description="Minimal value for 'hotcold' colorbar",
                                           long_description="",
                                           family_widget="colorbar")

        self.add_field_text_option_for_gui(arg_name="colorbar_scale_max", default_value='0.04',
                                           short_description="Maximal value for 'hotcold' colorbar",
                                           long_description="",
                                           family_widget="colorbar")

        self.add_field_text_option_for_gui(arg_name="halfrange", default_value='0.01',
                                           short_description="Halfrange for 'seismic' colorbar",
                                           long_description="",
                                           family_widget="colorbar")

        self.add_image_format_package_for_gui()

        self.add_verbose_arg_for_gui()

    def update_original_data(self):
        """
        To be called if the data to analyse should be updated after the analysis has been run.
        :return: boolean: return True if the data has been modified
        """
        pass

    def run_analysis(self, **kwargs):
        """Baseline differences over time following context transition."""
        CicadaAnalysis.run_analysis(self, **kwargs)

        widefield_acquisition_dict = kwargs["widefield_acquisition"]

        only_correct_trials = kwargs.get("only_correct_trials")

        quiet_window_mode = kwargs.get("quiet_window_mode")

        binsize = kwargs.get('binsize')

        color_map = kwargs.get('color_map')

        color_scale = (float(kwargs.get('colorbar_scale_min')), float(kwargs.get('colorbar_scale_max')))

        halfrange = float(kwargs.get('halfrange'))

        verbose = kwargs.get("verbose", True)

        save_formats = kwargs["save_formats"]
        if save_formats is None:
            save_formats = "pdf"

        results_path = self.get_results_path()

        # Define dict for data saving
        non_rew_data_dict = dict()
        rew_data_dict = dict()
        rew_data_bin_dict = dict()
        baseline_bin_diff_dict = dict()
        correlation_tables = []

        for session_index, session_data in enumerate(self._data_to_analyse):

            # Get Session Info
            info_dict = session_data.metadata.get_sessions_info()
            session_identifier = info_dict['identifier']

            if verbose:
                print()
                print(f"------------------ ONGOING SESSION: {session_identifier} -------------------- ")
                print(f"----------------------------- SESSION INFO ---------------------------------- ")
                print_info_dict(info_dict)
                print()

            mouse_id = session_data.subject_id
            session_id = session_data.session_id

            # WF info
            if isinstance(widefield_acquisition_dict, dict):
                keys_ophys_dff0 = widefield_acquisition_dict[session_identifier]
            else:
                keys_ophys_dff0 = widefield_acquisition_dict
            wf_ts = session_data.widefield.get_widefield_timestamps(keys=keys_ophys_dff0)
            if wf_ts is None or len(wf_ts) == 0:
                print(f'Session {session_id} has no activity_ts - skipping.')
                continue

            # WF data as h5
            wf_session_data = session_data.widefield.get_widefield_dff0_mmap
            # Get trial table
            trial_table = session_data.behavior.get_trial_table()

            # Add column 'correct trial' (0 or 1) to filter it if needed
            trial_table = add_correct_choice_to_table(trial_table, colname='correct_trial')

            # Compute block size dynamically (fallback = 20)
            block_size = get_block_size_from_table(trial_table)

            # Add the block index column
            trial_table['trial_id'] = trial_table.index
            trial_table['block_index'] = (trial_table.trial_id // block_size).astype(int)

            # Add time in context
            rew_starts = session_data.behavior.get_behavioral_epochs_times(epoch_name='rewarded')[0]
            nn_rew_starts = session_data.behavior.get_behavioral_epochs_times(epoch_name='non-rewarded')[0]
            epoch_starts = np.sort(np.concatenate((rew_starts, nn_rew_starts)))
            epoch_starts = np.repeat(epoch_starts, block_size)
            epoch_starts = epoch_starts[0: len(trial_table)]
            trial_table['epoch_start'] = epoch_starts
            trial_table['time_in_context'] = trial_table['start_time'] - trial_table['epoch_start']
            trial_table['context_time_bin'] = np.digitize(trial_table['time_in_context'],
                                                          bins=np.arange(0, 300, binsize)) - 1

            # Exclude block index 0 as it doesn't come from a transition
            trial_table = trial_table.loc[trial_table.block_index > 0]

            # Option to keep only correct trials
            if only_correct_trials:
                trial_table = trial_table.loc[trial_table.correct_trial == True]

            # Average all R- baseline images
            non_rew_data_dict.setdefault(mouse_id, [])
            non_rew_table = trial_table.loc[trial_table.context == 0]
            non_rew_table = non_rew_table.reset_index()
            session_avg_nn_rew = get_session_average_wf_baseline_images(trial_table=non_rew_table,
                                                                        session_data=wf_session_data,
                                                                        wf_ts=wf_ts,
                                                                        quiet_window_mode=quiet_window_mode)
            non_rew_data_dict[mouse_id].append(session_avg_nn_rew)

            # Average all R+ baseline images
            rew_data_dict.setdefault(mouse_id, [])
            rew_table = trial_table.loc[trial_table.context == 1]
            rew_table = rew_table.reset_index()
            session_avg_rew = get_session_average_wf_baseline_images(trial_table=rew_table,
                                                                     session_data=wf_session_data,
                                                                     wf_ts=wf_ts,
                                                                     quiet_window_mode=quiet_window_mode)
            rew_data_dict[mouse_id].append(session_avg_rew)

            # Average R+ data by bin
            context_bins = list(rew_table.context_time_bin.unique())
            rew_data_bin_dict.setdefault(mouse_id, {})
            baseline_bin_diff_dict.setdefault(mouse_id, {})
            for context_bin in context_bins:
                # Average data for that bin
                rew_data_bin_dict[mouse_id].setdefault(context_bin, [])
                df = rew_table.loc[rew_table.context_time_bin == context_bin]
                df = df.reset_index()
                avg_tmp_bin_data = get_session_average_wf_baseline_images(trial_table=df,
                                                                          session_data=wf_session_data,
                                                                          wf_ts=wf_ts,
                                                                          quiet_window_mode=quiet_window_mode)
                rew_data_bin_dict[mouse_id][context_bin].append(avg_tmp_bin_data)

                # Subtract session averaged R- to this session averaged bin
                baseline_bin_diff_dict[mouse_id].setdefault(context_bin, [])
                baseline_bin_diff_dict[mouse_id][context_bin].append(avg_tmp_bin_data - session_avg_nn_rew)

            # For each trial get baseline, subtract the other context, correlate to baseline difference, update table
            session_avg_baseline_diff = session_avg_rew - session_avg_nn_rew
            session_avg_baseline_diff = session_avg_baseline_diff.flatten()
            rho_list = []
            for trial in range(len(trial_table)):
                quiet_start = trial_table.iloc[trial].abort_window_start_time
                stim_time = trial_table.iloc[trial].start_time
                if quiet_window_mode == 'last 2s':
                    start_frame = find_nearest(wf_ts, stim_time - 2)
                elif quiet_window_mode == 'last 0.5s':
                    start_frame = find_nearest(wf_ts, stim_time - 0.5)
                else:
                    start_frame = find_nearest(wf_ts, quiet_start)
                end_frame = find_nearest(wf_ts, stim_time)
                data = session_data.widefield.get_widefield_dff0(keys_ophys_dff0, start_frame, end_frame)

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    avg_data = np.nanmean(data, axis=0)

                if trial_table.iloc[trial].context == 1:
                    trial_diff = avg_data - session_avg_nn_rew
                    trial_diff = trial_diff.flatten()
                    session_diff = session_avg_baseline_diff
                else:
                    trial_diff = avg_data - session_avg_rew
                    trial_diff = trial_diff.flatten()
                    # Non-rewarded context: flip sign so correlation is relative to the same R+−R− reference
                    session_diff = session_avg_baseline_diff * (-1)

                mask = ~np.isnan(session_diff) & ~np.isnan(trial_diff)
                rho_list.append(np.corrcoef(np.squeeze(session_diff)[mask], np.squeeze(trial_diff)[mask])[0, 1])

            trial_table['corr'] = rho_list
            trial_table['mouse_id'] = mouse_id
            trial_table['session_id'] = session_id

            # Keep only a few columns
            cols = ['mouse_id', 'session_id', 'context',
                    'time_in_context', 'context_time_bin', 'corr']
            trial_table = trial_table[cols]
            correlation_tables.append(trial_table)

        correlation_tables = pd.concat(correlation_tables, axis=0)

        np.save(os.path.join(results_path, f"rewarded_data_dict.npy"), rew_data_dict)
        np.save(os.path.join(results_path, f"rewarded_bin_data_dict.npy"), rew_data_bin_dict)
        np.save(os.path.join(results_path, f"non_rewarded_data_dict.npy"), non_rew_data_dict)
        np.save(os.path.join(results_path, f"diff_bin_data_dict.npy"), baseline_bin_diff_dict)
        correlation_tables.to_csv(os.path.join(results_path, f"correlation_tables.csv"))

        diff_bin_data_dict = dict()
        for mouse_id, diff_by_bin_data in baseline_bin_diff_dict.items():
            for bin_idx, sessions_data in diff_by_bin_data.items():
                diff_bin_data_dict.setdefault(bin_idx, [])
                data = np.stack(sessions_data)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    avg_data = np.nanmean(data, axis=0)
                diff_bin_data_dict[bin_idx].append(avg_data)
        np.save(os.path.join(results_path, f"figure_ready_diff_bin_data_dict.npy"), diff_bin_data_dict)

        # Do the plots R+ - R- over time after transition
        fig, axes = plt.subplots(3, int(np.ceil(len(list(diff_bin_data_dict.keys())) / 3)),
                                 figsize=(int(5 * np.ceil(len(list(diff_bin_data_dict.keys())) / 3)), 15),
                                 sharey=True, sharex=True)
        path = results_path

        for bin_idx, data in diff_bin_data_dict.items():
            data_to_plot = np.stack(data)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                data_to_plot = np.nanmean(data_to_plot, axis=0)
            plot_wf_single_frame(frame=data_to_plot, title=f'Baseline_diff_bin#{bin_idx}', figure=fig,
                                 ax_to_plot=axes.flatten()[int(bin_idx)], suptitle=' ', saving_path=path,
                                 save_formats=save_formats, colormap=color_map,
                                 vmin=color_scale[0], vmax=color_scale[1],
                                 halfrange=halfrange, cbar_shrink=1.0, separated_plots=True)

        save_figure(results_path=path, save_formats=save_formats, figure=fig,
                           figname=f'baseline_diff_average')

        # Do the correlation average plots
        session_avg_corr_df = correlation_tables.groupby(['mouse_id', 'session_id', 'context', 'context_time_bin'],
                                                         as_index=False).agg('mean')
        mouse_avg_corr_df = session_avg_corr_df.drop('session_id', axis=1)
        mouse_avg_corr_df = mouse_avg_corr_df.groupby(['mouse_id', 'context', 'context_time_bin'],
                                                      as_index=False).agg('mean')
        fig, ax = plt.subplots(1, 1, figsize=(8, 4))
        sns.stripplot(data=mouse_avg_corr_df, x='context_time_bin', y='corr', hue='context', dodge=True, ax=ax)
        sns.pointplot(data=mouse_avg_corr_df, x='context_time_bin', y='corr', hue='context',
                      dodge=True, linestyles='none', ax=ax)
        sns.despine()
        fig.tight_layout()
        save_figure(results_path=path, save_formats=save_formats, figure=fig,
                           figname=f'correlation_over_time')

