import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.core import print_info_dict
from cicada_analysis.cicada_tools.behavior.behavior_analysis_utils import (
    filter_table_with_dict,
    get_epoch_transition_list,
)
from cicada_petersen.tools.behavior_utils import add_correct_choice_to_table, get_all_quiet_windows, get_iti_frames
from cicada_analysis.cicada_tools.core import get_continous_time_periods
from cicada_analysis.cicada_tools.core import align_array_to_timestamps, event_aligned_array_to_long_format_df
from cicada_analysis.cicada_tools.display.core_plots import save_figure
from cicada_analysis.cicada_tools.behavior.behavior_analysis_plots import plot_with_point_and_strip


class CicadaMovementQuantification(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        CicadaAnalysis.__init__(self, name="Facemap movement analysis", family_id="Behavior",
                                short_description="Quantify movements",
                                config_handler=config_handler, accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaMovementQuantification(config_handler=self.config_handler)
        self.transfer_attributes_to_tabula_rasa_copy(analysis_copy=analysis_copy)
        return analysis_copy

    def check_data(self):
        """
        Check the data given one initiating the class and return True if the data given allows the analysis
        implemented, False otherwise.
        :return: a boolean
        """
        super().check_data()

        for session_data in self._data_to_analyse:
            if session_data.DATA_FORMAT != "CI_DATA":
                self.invalid_data_help = f"Non CI_DATA format compatibility not yet implemented: " \
                                         f"{session_data.DATA_FORMAT}"
                return False
            # the run reads facemap's motion energy and SVD (behavioral time series) and the trial table
            series = session_data.behavior.get_behavioral_time_series_names()
            if 'motion_energy' not in series or 'motion_svd' not in series:
                self.invalid_data_help = f"No facemap data (behavioral time series 'motion_energy' and " \
                                         f"'motion_svd') in {session_data.identifier}"
                return False
            if not session_data.behavior.has_trial_table():
                self.invalid_data_help = f"No trial table in {session_data.identifier}"
                return False

        return True

    def setup_parameters(self):
        """

        Returns:

        """
        CicadaAnalysis.setup_parameters(self)

        analysis_list = ['baseline analysis', 'psth analysis']
        self.add_choices_arg_for_gui(arg_name="analysis_to_do", choices=analysis_list,
                                     default_value="baseline analysis", short_description="Analysis to do",
                                     multiple_choices=True,
                                     family_widget="Plot type")

        self.add_bool_option_for_gui(arg_name="mot_psth", true_by_default=True,
                                     short_description="Do PSTH on motion energy",
                                     long_description=None, family_widget='Plot type')

        self.add_bool_option_for_gui(arg_name="mot_svd_psth", true_by_default=False,
                                     short_description="Do PSTH on motion energy for each SVD",
                                     long_description=None, family_widget='Plot type')

        self.add_bool_option_for_gui(arg_name="context_alignment", true_by_default=False,
                                     short_description="Also align PSTHs on context transitions",
                                     long_description=None, family_widget='Plot type')

        plots_list = ['session_plot', 'mouse_plot', 'grand_average_plot']
        self.add_choices_arg_for_gui(arg_name="plots_to_do", choices=plots_list,
                                     default_value="session_plot", short_description="Plot(s) to do",
                                     multiple_choices=True,
                                     family_widget="Average type")

        self.add_bool_option_for_gui(arg_name="only_correct_trials", true_by_default=False,
                                     short_description="Keep only correct trials in trial table",
                                     long_description=None, family_widget='Compare baseline config')

        self.add_choices_arg_for_gui(arg_name="quiet_window_mode",
                                     choices=['last 2s', 'last 0.5s', 'full quiet window'],
                                     default_value='last 2s',
                                     short_description="Define the quiet window to extract data at each trial",
                                     long_description="",
                                     multiple_choices=False,
                                     family_widget="Compare baseline config")

        if all([session_data.behavior.has_trial_table() for session_data in self._data_to_analyse]):
            self.add_trial_dict_arg_for_gui(short_description="Define trial groups from trial table",
                                            long_description=None,
                                            arg_name='trial_requirement_groups', family_widget="Trials selection")

        self.add_bool_option_for_gui(arg_name="normalized_motion_energy", true_by_default=False,
                                     short_description="Do Min Max normalization on facemotion energy",
                                     long_description=None, family_widget='Face motion')

        self.add_int_values_arg_for_gui(arg_name="n_svd_images", min_value=0, max_value=500,
                                        short_description="N SVD to keep",
                                        long_description="SVD grids use a sqrt-based row/column count, so "
                                                         "non-perfect-square values show fewer components than "
                                                         "requested (e.g. 50 -> a 7x7 grid = only 49 shown).",
                                        default_value=100, family_widget="Face motion")

        self.add_int_values_arg_for_gui(arg_name="t_before", min_value=0, max_value=2000,
                                        short_description="Time before stimulus or context transition (ms)",
                                        default_value=500, family_widget="Face motion PSTH")

        self.add_int_values_arg_for_gui(arg_name="t_after", min_value=0, max_value=5000,
                                        short_description="Time after stimulus or context transition (ms)",
                                        default_value=1000, family_widget="Face motion PSTH")

        self.add_image_format_package_for_gui()

        self.add_verbose_arg_for_gui()

    def update_original_data(self):
        """
        To be called if the data to analyse should be updated after the analysis has been run.
        :return: boolean: return True if the data has been modified
        """
        pass

    def run_analysis(self, **kwargs):
        """
        test
        :param kwargs:
          segmentation

        :return:
        """
        CicadaAnalysis.run_analysis(self, **kwargs)

        analysis_to_do = kwargs.get('analysis_to_do')

        mot_energy_psth = kwargs.get('mot_psth')

        svd_psth = kwargs.get('mot_svd_psth')

        context_psth = kwargs.get('context_alignment')

        plots_to_do = kwargs.get("plots_to_do")

        quiet_window_mode = kwargs.get("quiet_window_mode")

        only_correct_trials = kwargs.get("only_correct_trials")

        trial_table_groups = kwargs.get("trial_requirement_groups") or []  # [[name, req_dict, color], ...]

        normalized_motion_energy = kwargs.get("normalized_motion_energy")

        n_svd_images = kwargs.get("n_svd_images")

        t_before = kwargs.get("t_before") / 1000

        t_after = kwargs.get("t_after") / 1000

        save_formats = kwargs.get("save_formats", ["pdf"])
        verbose = kwargs.get("verbose", False)

        # Define list of table to aggregate results
        baseline_data_df = []
        iti_motion_df = []
        full_stim_aligned_motion_df = []
        full_stim_aligned_motion_svd_df = []
        full_context_aligned_motion_df = []
        full_context_aligned_motion_svd_df = []
        for session_data in self._data_to_analyse:
            # Get Session Info
            info_dict = session_data.metadata.get_sessions_info()
            session_identifier = info_dict['identifier']

            if verbose:
                print(f" ")
                print(f"------------------ ONGOING SESSION: {session_identifier} -------------------- ")
                print(f"----------------------------- SESSION INFO ---------------------------------- ")
                print_info_dict(info_dict)
                print(f" ")

            # Get facemap data
            facemap_data = session_data.petersen.get_facemap_data(image_acquisition_name="facemap_svd_images")
            if facemap_data is None:
                if verbose:
                    print(f'No facemap data for {session_identifier}')
                continue
            if 'motion_energy' not in facemap_data.keys() or 'timestamps' not in facemap_data.keys():
                if verbose:
                    print(f'No motion energy or timestamps for {session_identifier}')
                continue

            if normalized_motion_energy:
                motion_energy = (facemap_data['motion_energy'] - np.min(facemap_data['motion_energy'])) / \
                                           np.max(facemap_data['motion_energy'])
            else:
                motion_energy = facemap_data['motion_energy']
            facemap_timestamps = facemap_data['timestamps']
            video_frame_rate = np.round(1 / np.median(np.diff(facemap_timestamps[0: 200])), 3)
            if verbose:
                print(f"Behaviour video frame rate : {video_frame_rate} Hz")

            if len(facemap_timestamps) > len(motion_energy):
                if verbose:
                    print(f'Less video filming frames than timestamps for {session_identifier}')
                continue

            # Get trial table
            trial_table = session_data.behavior.get_trial_table()

            if 'baseline analysis' in analysis_to_do:
                # Add column 'correct trial' (0 or 1) to filter it if needed
                trial_table = add_correct_choice_to_table(trial_table, colname='correct_trial')
                if only_correct_trials:
                    trial_table = trial_table.loc[trial_table.correct_trial == True]
                    trial_table = trial_table.reset_index(drop=True)

                # Get all quiet windows
                quiet_window_frames = get_all_quiet_windows(table=trial_table,
                                                            reference_ts=facemap_timestamps,
                                                            quiet_window_mode=quiet_window_mode)

                # Get averaged face motion energy for each quiet window
                avg_motion_energy = [np.nanmean(motion_energy[quiet_frames]) for quiet_frames in quiet_window_frames]

                # Add it to trial table
                trial_table['BaselineMotionEnergy'] = avg_motion_energy

                # Add mouse / session_info before concatenation
                trial_table['session_id'] = session_identifier
                trial_table['mouse_id'] = session_identifier[0: 5]

                # Filter trial table for baseline face motion energy plot
                cols_to_keep = ['mouse_id', 'session_id', 'trial_type',
                                'correct_trial', 'context', 'BaselineMotionEnergy']
                baseline_trial_table = trial_table[cols_to_keep]

                # Aggregate table with baseline face motion energy
                baseline_data_df.append(baseline_trial_table)

                # Find ITI frames of R+ and R- to average face motion energy
                rewarded_times = session_data.behavior.get_behavioral_epochs_times(epoch_name='rewarded')
                non_rewarded_times = session_data.behavior.get_behavioral_epochs_times(epoch_name='non-rewarded')
                iti_rew_frames = get_iti_frames(reference_ts=facemap_timestamps, trial_table=trial_table,
                                                epoch_times=rewarded_times)
                iti_rew = get_continous_time_periods(iti_rew_frames)
                iti_non_rew_frames = get_iti_frames(reference_ts=facemap_timestamps, trial_table=trial_table,
                                                    epoch_times=non_rewarded_times)
                iti_non_rew = get_continous_time_periods(iti_non_rew_frames)
                iti_table = pd.DataFrame()

                iti_rew_mot = []
                for i_rew in iti_rew:
                    if i_rew[0] == i_rew[1]:
                        continue
                    iti_rew_mot.append(np.nanmean(motion_energy[np.arange(i_rew[0],
                                                                          min(i_rew[1], len(motion_energy)))]))

                iti_non_rew_mot = []
                for i_nnrew in iti_non_rew:
                    if i_nnrew[0] == i_nnrew[1]:
                        continue
                    iti_non_rew_mot.append(np.nanmean(motion_energy[np.arange(i_nnrew[0],
                                                                              min(i_nnrew[1], len(motion_energy)))]))

                context_vec = ['R+'] * len(iti_rew_mot) + ['R-'] * len(iti_non_rew_mot)
                iti_table['motion'] = np.concatenate((iti_rew_mot, iti_non_rew_mot))
                iti_table['context'] = context_vec
                iti_table['session_id'] = session_identifier
                iti_table['mouse_id'] = session_identifier[0: 5]
                iti_motion_df.append(iti_table)

            if 'psth analysis' in analysis_to_do:
                for grp_idx, (_name, req_dict, _color) in enumerate(trial_table_groups):
                    # Get filtered table with specific trials from selection dict
                    sub_table = filter_table_with_dict(table=trial_table, filtering_dict=req_dict)
                    sub_table = sub_table.reset_index(drop=True)
                    if verbose:
                        print(f'{len(sub_table)} trials in group {grp_idx + 1}')
                    if len(sub_table) == 0:
                        if verbose:
                            print('No trial to match selection, skip group')
                        continue

                    if svd_psth:
                        # Align individual SVDs to stim time from filtered table
                        stim_aligned_motion_svd = align_array_to_timestamps(facemap_data['motion_svd'],
                                                                            sub_table['start_time'].values,
                                                                            facemap_timestamps, (t_before, t_after),
                                                                            time_axis=0, drop_outside=True)
                        stim_aligned_motion_svd_df = event_aligned_array_to_long_format_df(array=stim_aligned_motion_svd,
                                                                                           time_range=[-t_before, t_after],
                                                                                           time_step=1 / video_frame_rate)
                        stim_aligned_motion_svd_df['session_id'] = session_identifier
                        stim_aligned_motion_svd_df['mouse_id'] = session_identifier[0: 5]
                        stim_aligned_motion_svd_df = stim_aligned_motion_svd_df.loc[stim_aligned_motion_svd_df['sample'] < n_svd_images]
                        full_stim_aligned_motion_svd_df.append(stim_aligned_motion_svd_df)

                    if mot_energy_psth:
                        # Align face motion energy to stim time from filtered table
                        stim_aligned_motion = align_array_to_timestamps(motion_energy, sub_table['start_time'].values,
                                                                        facemap_timestamps, (t_before, t_after),
                                                                        time_axis=0, drop_outside=True)
                        stim_aligned_motion_df = event_aligned_array_to_long_format_df(array=stim_aligned_motion,
                                                                                       time_range=[-t_before, t_after],
                                                                                       time_step=1 / video_frame_rate)
                        stim_aligned_motion_df['session_id'] = session_identifier
                        stim_aligned_motion_df['mouse_id'] = session_identifier[0: 5]
                        full_stim_aligned_motion_df.append(stim_aligned_motion_df)

                if context_psth:
                    # Get aligned activity around transition to R+ and to R-
                    rewarded_times = session_data.behavior.get_behavioral_epochs_times(epoch_name='rewarded')
                    non_rewarded_times = session_data.behavior.get_behavioral_epochs_times(epoch_name='non-rewarded')
                    to_rewarded_times = get_epoch_transition_list(epoch_times=rewarded_times)
                    to_non_rewarded_times = get_epoch_transition_list(epoch_times=non_rewarded_times)

                    # Transition to R+
                    # Align individual SVDs to R+ transitions
                    to_rew_aligned_motion_svd = align_array_to_timestamps(facemap_data['motion_svd'], to_rewarded_times,
                                                                          facemap_timestamps, (t_before, t_after),
                                                                          time_axis=0, drop_outside=True)
                    to_rew_aligned_motion_svd_df = event_aligned_array_to_long_format_df(array=to_rew_aligned_motion_svd,
                                                                                         time_range=[-t_before, t_after],
                                                                                         time_step=1 / video_frame_rate)
                    to_rew_aligned_motion_svd_df['session_id'] = session_identifier
                    to_rew_aligned_motion_svd_df['mouse_id'] = session_identifier[0: 5]
                    to_rew_aligned_motion_svd_df['transition'] = 'To R+'

                    # Align face motion energy to R+ transitions
                    to_rew_aligned_motion = align_array_to_timestamps(motion_energy, to_rewarded_times,
                                                                      facemap_timestamps, (t_before, t_after),
                                                                      time_axis=0, drop_outside=True)
                    to_rew_aligned_motion_df = event_aligned_array_to_long_format_df(array=to_rew_aligned_motion,
                                                                                     time_range=[-t_before, t_after],
                                                                                     time_step=1 / video_frame_rate)
                    to_rew_aligned_motion_df['session_id'] = session_identifier
                    to_rew_aligned_motion_df['mouse_id'] = session_identifier[0: 5]
                    to_rew_aligned_motion_df['transition'] = 'To R+'

                    # Transition to R-
                    # Align individual SVDs to R- transition
                    to_nn_rew_aligned_motion_svd = align_array_to_timestamps(facemap_data['motion_svd'],
                                                                             to_non_rewarded_times, facemap_timestamps,
                                                                             (t_before, t_after),
                                                                             time_axis=0, drop_outside=True)
                    to_nn_rew_aligned_motion_svd_df = event_aligned_array_to_long_format_df(array=to_nn_rew_aligned_motion_svd,
                                                                                            time_range=[-t_before, t_after],
                                                                                            time_step=1 / video_frame_rate)
                    to_nn_rew_aligned_motion_svd_df['session_id'] = session_identifier
                    to_nn_rew_aligned_motion_svd_df['mouse_id'] = session_identifier[0: 5]
                    to_nn_rew_aligned_motion_svd_df['transition'] = 'To R-'

                    # Align face motion energy to R- transitions
                    to_nn_rew_aligned_motion = align_array_to_timestamps(motion_energy, to_non_rewarded_times,
                                                                         facemap_timestamps, (t_before, t_after),
                                                                         time_axis=0, drop_outside=True)
                    to_nn_rew_aligned_motion_df = event_aligned_array_to_long_format_df(array=to_nn_rew_aligned_motion,
                                                                                        time_range=[-t_before, t_after],
                                                                                        time_step=1 / video_frame_rate)
                    to_nn_rew_aligned_motion_df['session_id'] = session_identifier
                    to_nn_rew_aligned_motion_df['mouse_id'] = session_identifier[0: 5]
                    to_nn_rew_aligned_motion_df['transition'] = 'To R-'

                    # Concatenate df for SVDs & face motion context transitions
                    context_aligned_motion_svd_df = pd.concat((to_rew_aligned_motion_svd_df, to_nn_rew_aligned_motion_svd_df), ignore_index=True)
                    context_aligned_motion_df = pd.concat((to_rew_aligned_motion_df, to_nn_rew_aligned_motion_df), ignore_index=True)

                    context_aligned_motion_svd_df = context_aligned_motion_svd_df.loc[context_aligned_motion_svd_df['sample'] < n_svd_images]
                    full_context_aligned_motion_svd_df.append(context_aligned_motion_svd_df)
                    context_aligned_motion_df = context_aligned_motion_df.loc[context_aligned_motion_df['sample'] < n_svd_images]
                    full_context_aligned_motion_df.append(context_aligned_motion_df)

                if svd_psth:
                    # Make face motion svd images figures
                    n_rows = int(np.sqrt(n_svd_images))
                    n_cols = int(np.sqrt(n_svd_images))
                    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 10), sharex=True, sharey=True)
                    for idx, ax in enumerate(axes.flatten()):
                        ax.imshow(facemap_data['svd_images'][idx, :, :])
                        ax.spines[['left', 'bottom', 'right', 'top']].set_visible(False)
                        ax.set_title(f'SVD {idx}', fontsize=6)
                        ax.tick_params(axis='both', which='both', labelsize=6)
                    save_figure(results_path=os.path.join(self.get_results_path(), info_dict['subject_id']),
                                       save_formats=save_formats,
                                       figure=fig, figname=f'{session_identifier}_motion_svd_images')

            self.update_progressbar(time_started=self.analysis_start_time,
                                    increment_value=100 / len(self._data_to_analyse))

        # Get table from lists
        if 'baseline analysis' in analysis_to_do:
            baseline_data_df = pd.concat(baseline_data_df)
            iti_motion_df = pd.concat(iti_motion_df)
        if 'psth analysis' in analysis_to_do:
            if mot_energy_psth:
                full_stim_aligned_motion_df = pd.concat(full_stim_aligned_motion_df)
            if svd_psth:
                full_stim_aligned_motion_svd_df = pd.concat(full_stim_aligned_motion_svd_df)
            if context_psth:
                if mot_energy_psth:
                    full_context_aligned_motion_df = pd.concat(full_context_aligned_motion_df)
                if svd_psth:
                    full_context_aligned_motion_svd_df = pd.concat(full_context_aligned_motion_svd_df)

        # Save the datasets
        if 'baseline analysis' in analysis_to_do:
            baseline_data_df.to_csv(os.path.join(self.get_results_path(), 'baseline_energy.csv'))
            iti_motion_df.to_csv(os.path.join(self.get_results_path(), 'iti_energy.csv'))
        if 'psth analysis' in analysis_to_do:
            if mot_energy_psth:
                full_stim_aligned_motion_df.to_csv(os.path.join(self.get_results_path(), 'stim_aligned_energy.csv'))
            if svd_psth:
                full_stim_aligned_motion_svd_df.to_csv(os.path.join(self.get_results_path(), 'stim_aligned_svd_energy.csv'))
            if context_psth:
                if mot_energy_psth:
                    full_context_aligned_motion_df.to_csv(os.path.join(self.get_results_path(), 'context_aligned_energy.csv'))
                if svd_psth:
                    full_context_aligned_motion_svd_df.to_csv(os.path.join(self.get_results_path(), 'context_aligned_svd_energy.csv'))
        if verbose:
            print('Dataset saved')

        if verbose:
            print(' ')
            print('Do figures')
        context_palette_dict = {'context': ['darkmagenta', 'green']}
        if ("session_plot" in plots_to_do) and ('psth analysis' in analysis_to_do) and ('baseline analysis' in analysis_to_do):
            for session_id in baseline_data_df.session_id.unique():
                # Face motion energy during quiet window
                baseline_data_to_plot = baseline_data_df.loc[baseline_data_df.session_id == session_id]
                fig, ax = plt.subplots(1, 1, figsize=(5, 5))
                plot_with_point_and_strip(data=baseline_data_to_plot, x_name='trial_type',
                                          y_name='BaselineMotionEnergy', hue='context', legend=True,
                                          palette=context_palette_dict, ax=ax, palette_key='context', link_mice=False)
                sns.despine()
                save_figure(results_path=os.path.join(self.get_results_path(), session_id[0:5]),
                                   save_formats=save_formats,
                                   figure=fig, figname=f'{session_id}_quiet_window_motion_energy')

                if mot_energy_psth:
                    # Face Motion trial based PSTHs
                    face_motion_df_to_plot = full_stim_aligned_motion_df.loc[full_stim_aligned_motion_df.session_id == session_id]
                    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
                    sns.lineplot(data=face_motion_df_to_plot, x='time', y='data', color='grey', ax=ax)
                    sns.despine()
                    ax.axvline(x=0, ymin=0, ymax=1, c='orange', linestyle='--')
                    ax.tick_params(axis='both', which='both', labelsize=6)
                    ax.set_title('Face Motion', fontsize=6)
                    ax.set_ylabel('Face motion energy', fontsize=6)
                    ax.set_xlabel('Time (s)', fontsize=6)
                    save_figure(results_path=os.path.join(self.get_results_path(), session_id[0:5]),
                                       save_formats=save_formats,
                                       figure=fig, figname=f'{session_id}_psth_face_motion_stim')

                if svd_psth:
                    # SVD trial based PSTHs
                    n_rows = int(np.sqrt(n_svd_images))
                    n_cols = int(np.sqrt(n_svd_images))
                    svd_session_df = full_stim_aligned_motion_svd_df.loc[full_stim_aligned_motion_svd_df.session_id == session_id]
                    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 10), sharex=True, sharey=True)
                    for idx, ax in enumerate(axes.flatten()):
                        df_to_plot = svd_session_df.loc[svd_session_df['sample'] == idx]
                        sns.lineplot(data=df_to_plot, x='time', y='data', color='grey', ax=ax)
                        sns.despine()
                        ax.axvline(x=0, ymin=0, ymax=1, c='orange', linestyle='--')
                        ax.spines[['right', 'top']].set_visible(False)
                        ax.set_title(f'SVD {idx}', fontsize=6)
                        ax.set_ylabel('Avg energy', fontsize=6)
                        ax.set_xlabel('Time (s)', fontsize=6)
                        ax.tick_params(axis='both', which='both', labelsize=6)
                    save_figure(results_path=os.path.join(self.get_results_path(), session_id[0:5]),
                                       save_formats=save_formats,
                                       figure=fig, figname=f'{session_id}_psth_svd')

                if context_psth and mot_energy_psth:
                    # Face Motion context transition aligned
                    face_motion_df_to_plot = full_context_aligned_motion_df.loc[full_context_aligned_motion_df.session_id == session_id]
                    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
                    sns.lineplot(data=face_motion_df_to_plot, x='time', y='data', color='grey',
                                 hue='transition', hue_order=['To R-', 'To R+'], palette=context_palette_dict['context'],
                                 ax=ax)
                    sns.despine()
                    ax.axvline(x=0, ymin=0, ymax=1, c='grey', linestyle='--')
                    ax.spines[['right', 'top']].set_visible(False)
                    ax.tick_params(axis='both', which='both', labelsize=6)
                    ax.set_title('Face Motion', fontsize=6)
                    ax.set_ylabel('Avg energy', fontsize=6)
                    ax.set_xlabel('Time (s)', fontsize=6)
                    save_figure(results_path=os.path.join(self.get_results_path(), session_id[0:5]),
                                       save_formats=save_formats,
                                       figure=fig, figname=f'{session_id}_psth_face_motion_context_transition')

                if context_psth and svd_psth:
                    # SVD context transition PSTHs
                    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 10), sharex=True, sharey=True)
                    svd_context_session_df = full_context_aligned_motion_svd_df.loc[full_context_aligned_motion_svd_df.session_id == session_id]
                    for idx, ax in enumerate(axes.flatten()):
                        df_to_plot = svd_context_session_df.loc[svd_context_session_df['sample'] == idx]
                        sns.lineplot(data=df_to_plot, x='time', y='data', color='grey',
                                     hue='transition', hue_order=['To R-', 'To R+'],
                                     palette=context_palette_dict['context'], legend=False,
                                     ax=ax)
                        sns.despine()
                        ax.axvline(x=0, ymin=0, ymax=1, c='grey', linestyle='--')
                        ax.set_title(f'SVD {idx}', fontsize=6)
                        ax.set_ylabel('Avg energy', fontsize=6)
                        ax.set_xlabel('Time (s)', fontsize=6)
                        ax.tick_params(axis='both', which='both', labelsize=6)
                    save_figure(results_path=os.path.join(self.get_results_path(), session_id[0:5]),
                                       save_formats=save_formats,
                                       figure=fig, figname=f'{session_id}_psth_svd_context')

