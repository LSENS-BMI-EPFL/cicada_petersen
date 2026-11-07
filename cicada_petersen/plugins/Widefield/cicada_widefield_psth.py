import os
import numpy as np
import pandas as pd
import seaborn as sns
from time import time

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.core import print_info_dict, filter_events_based_on_epochs
from cicada_analysis.cicada_tools.imaging import build_psth_dataframe
from cicada_petersen.tools.widefield_utils import trial_type_interpreter
from cicada_analysis.cicada_tools.display.core_plots import save_figure


class CicadaWidefieldPsth(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        long_description = '<p align="center"><b>Widefield PSTH</b></p>'
        long_description = long_description + 'Main parameters:<br>'
        long_description = long_description + (' - Box "plot type": Choose whether you want to plot a full average, an '
                                               'average grouped by mouse, or an average grouped by session.<br>')
        long_description = long_description + (' - Box "events": Choose the type of trial on which you want to center '
                                               'the PSTH (auditory hit, whisker miss, ...).<br>')
        long_description = long_description + (' - Box" main epochs": You can filter the trials chosen based on the '
                                               'epoch and you can use epoch transitions as events.<br>')
        long_description = long_description + ' - Box "cell type": Select the cell type to use for the PSTH.<br><br>'
        long_description = long_description + ("Table saved: All event's data with columns specifying mouse_id, "
                                               "session_id, cell_type, time, trial_name, epoch, roi, "
                                               "behavior_day and behavior_type.<br><br>")
        CicadaAnalysis.__init__(self, name="Widefield PSTH", family_id="Widefield",
                                short_description="Plot widefield PSTHs based on defined ROIs ",
                                long_description=long_description,
                                config_handler=config_handler,
                                accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaWidefieldPsth(config_handler=self.config_handler)
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

        self.add_roi_response_series_arg_for_gui(short_description=" ", long_description=None,
                                                 family_widget="Neural activity to use")

        plots_list = ['wf_psth_session_plot', 'wf_psth_mouse_plot', 'wf_psth_full_plot']
        self.add_choices_arg_for_gui(arg_name="plots_to_do", choices=plots_list,
                                     default_value="wf_psth_full_plot", short_description="Plot(s) to do",
                                     multiple_choices=True,
                                     family_widget="plot type")

        all_trials = []
        all_epochs = []
        for data_to_analyse in self._data_to_analyse:
            all_epochs.extend(data_to_analyse.behavior.get_behavioral_epochs_names())
            all_trials.extend(data_to_analyse.behavior.get_behavioral_events_names())

        all_trials = list(np.unique(all_trials))
        all_epochs = list(np.unique(all_epochs))

        self.add_choices_arg_for_gui(arg_name="epochs_to_do", choices=all_epochs,
                                     default_value=False,
                                     short_description="Select epoch(s) to do widefield analysis",
                                     long_description="epochs selected are used to filter events",
                                     multiple_choices=True,
                                     family_widget="main epochs")
        self.add_bool_option_for_gui(arg_name="center_on_epochs", true_by_default=False,
                                     short_description="Center on epoch transitions",
                                     long_description="Use epoch transition times as alignment events. "
                                                      "When enabled, also generates a peak response bar plot "
                                                      "using the 'peak_response_config' window.",
                                     family_widget='main epochs')

        self.add_choices_arg_for_gui(arg_name="trials_list", choices=all_trials,
                                     default_value=False,
                                     short_description="Events",
                                     long_description="Select events for which you want to do widefield analysis",
                                     multiple_choices=True,
                                     family_widget="events")
        self.add_choices_arg_for_gui(arg_name="align_to", choices=['Stim', 'Lick'],
                                     default_value='Stim',
                                     short_description="Align on",
                                     long_description="Define time 0 in PSTH",
                                     multiple_choices=False,
                                     family_widget="events")
        self.add_bool_option_for_gui(arg_name="merge_trial_type", true_by_default=False,
                                     short_description="Merge all events",
                                     long_description=None, family_widget='events')

        all_cell_types = []
        for data_to_analyse in self._data_to_analyse:
            all_cell_types.extend(data_to_analyse.calcium_imaging.get_all_cell_types())
        all_cell_types = list(set(all_cell_types))
        self.add_choices_arg_for_gui(arg_name="cell_types_to_do", choices=all_cell_types,
                                     default_value=False, short_description="cell_types_to_do",
                                     multiple_choices=True,
                                     family_widget="cell type")

        self.add_int_values_arg_for_gui(arg_name="psth_start", min_value=50, max_value=20000,
                                        short_description="Range of psth (ms) before event",
                                        default_value=100, family_widget="psth_config")
        self.add_int_values_arg_for_gui(arg_name="psth_stop", min_value=50, max_value=20000,
                                        short_description="Range of psth (ms) after event",
                                        default_value=200, family_widget="psth_config")

        self.add_bool_option_for_gui(arg_name="subtract_baseline", true_by_default=True,
                                     short_description="Subtract baseline",
                                     long_description=None, family_widget='psth_config')

        self.add_int_values_arg_for_gui(arg_name="peak_window_start_ms", min_value=0, max_value=500,
                                        short_description="Peak window start (ms post-stim)",
                                        long_description="Start of the time window used to compute the peak "
                                                         "response when 'Center on epoch transitions' is enabled. "
                                                         "Independent from the PSTH display window (psth_start/stop).",
                                        default_value=80, family_widget="peak_response_config")
        self.add_int_values_arg_for_gui(arg_name="peak_window_stop_ms", min_value=0, max_value=500,
                                        short_description="Peak window stop (ms post-stim)",
                                        long_description="End of the time window used to compute the peak "
                                                         "response when 'Center on epoch transitions' is enabled. "
                                                         "Independent from the PSTH display window (psth_start/stop).",
                                        default_value=180, family_widget="peak_response_config")

        self.add_image_format_package_for_gui()

        self.add_verbose_arg_for_gui()

    def update_original_data(self):
        """
        To be called if the data to analyse should be updated after the analysis has been run.
        :return: boolean: return True if the data has been modified
        """
        pass

    def run_analysis(self, **kwargs):
        """Plot widefield PSTHs based on defined ROIs.
        :param kwargs:
          segmentation

        :return:
        """
        CicadaAnalysis.run_analysis(self, **kwargs)

        roi_response_series_dict = kwargs["roi_response_series"]

        cell_types_to_do = list(kwargs["cell_types_to_do"])

        verbose = kwargs.get("verbose", True)

        plots = kwargs.get('plots_to_do')

        epochs = kwargs.get("epochs_to_do")
        events_names = kwargs.get("trials_list")
        align_to = kwargs.get("align_to")
        merge_trial_type = kwargs.get('merge_trial_type')

        time_range = (kwargs.get("psth_start") / 1000, kwargs.get("psth_stop") / 1000)

        subtract_baseline = kwargs.get("subtract_baseline")

        center_on_epochs = kwargs.get('center_on_epochs')

        # Peak response window — used only when center_on_epochs is True
        # Distinct from psth_start/stop which define the full PSTH display window
        peak_window_start_s = kwargs.get("peak_window_start_ms", 80) / 1000
        peak_window_stop_s = kwargs.get("peak_window_stop_ms", 180) / 1000

        # ------- figures config part -------
        save_formats = kwargs["save_formats"]
        if save_formats is None:
            save_formats = "pdf"

        dpi = kwargs.get("dpi", 100)

        width_fig = kwargs.get("width_fig")

        height_fig = kwargs.get("height_fig")

        results_path = self.get_results_path()

        n_sessions = len(self._data_to_analyse)

        dfs_list = []

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

            if not events_names:
                print("no events, no analysis")
                return
            if isinstance(roi_response_series_dict, dict):
                roi_response_serie_info = roi_response_series_dict[session_identifier]
            else:
                roi_response_serie_info = roi_response_series_dict

            # get activity timestamps
            activity_ts = session_data.calcium_imaging.get_roi_response_serie_timestamps(roi_response_serie_info)
            if activity_ts is None or len(activity_ts) == 0:
                print(f'Session {session_id} has no activity_ts - skipping.')
                continue

            # get activity data
            activity = session_data.calcium_imaging.get_roi_response_serie_data(roi_response_serie_info)
            if activity is None or len(activity) == 0:
                print(f'Session {session_id} has no rrs - skipping.')
                continue

            cell_type_dict = session_data.calcium_imaging.get_cell_indices_by_cell_type(roi_response_serie_info)
            behavior_type, behavior_day = session_data.petersen.get_bhv_type_and_training_day_index()

            # Build flat per-ROI cell-type label array for build_psth_dataframe
            n_cells = activity.shape[0]
            cell_type_array = np.full(n_cells, 'na', dtype=object)
            if cell_type_dict:
                for ct, roi_ids in cell_type_dict.items():
                    cell_type_array[roi_ids] = ct

            # Get the trial table (in case we want lick aligned PSTHs)
            trial_table = session_data.behavior.get_trial_table().copy()

            # add wf timecourse data to general_data (dict or df?)
            if epochs:
                for epoch in epochs:
                    epoch_times = session_data.behavior.get_behavioral_epochs_times(epoch_name=epoch)
                    if 'non' in epoch:
                        binary_epoch = 0
                    else:
                        binary_epoch = 1

                    # data centered on trials filtered by epoch (epochs and trials from GUI)
                    for events_name in events_names:
                        if align_to == 'Lick':
                            lick_flag, stim_type_string = trial_type_interpreter(events_name)
                            trial_type_table = trial_table.loc[
                                (trial_table[stim_type_string] == 1) & (trial_table.lick_flag == lick_flag) &
                                (trial_table.context == binary_epoch)]
                            trials_kept = trial_type_table['lick_time'].values
                            stim_times = trial_type_table['start_time'].values
                        else:
                            trials = session_data.behavior.get_behavioral_events_times(event_name=events_name)
                            if trials is None or len(trials[0, :]) == 0:
                                print("No trials in this condition, skipping")
                                continue
                            trials = trials[0, :]
                            trials_kept = filter_events_based_on_epochs(trials, epoch_times)
                            stim_times = trials_kept
                        if len(trials_kept) == 0:
                            print("No trials in this condition, skipping")
                            continue

                        tmp_table = build_psth_dataframe(
                            data=activity, event_timestamps=trials_kept,
                            frame_timestamps=activity_ts, window_s=time_range,
                            subtract_baseline=subtract_baseline,
                            baseline_event_timestamps=stim_times if align_to == 'Lick' else None,
                            trial_type=events_name, session_id=session_id, mouse_id=mouse_id,
                            extra_metadata={'cell_type': cell_type_array,
                                            'behavior_type': behavior_type,
                                            'behavior_day': behavior_day})
                        tmp_table['epoch'] = epoch
                        dfs_list.append(tmp_table)

                    if center_on_epochs:
                        # Epoch-transition alignment: no sensory stimulus — baseline uses pre-transition window
                        tmp_table = build_psth_dataframe(
                            data=activity, event_timestamps=epoch_times[0],
                            frame_timestamps=activity_ts, window_s=time_range,
                            subtract_baseline=subtract_baseline,
                            baseline_event_timestamps=None,
                            trial_type='epoch_transition', session_id=session_id, mouse_id=mouse_id,
                            extra_metadata={'cell_type': cell_type_array,
                                            'behavior_type': behavior_type,
                                            'behavior_day': behavior_day})
                        tmp_table['epoch'] = epoch
                        dfs_list.append(tmp_table)
            else:
                # data centered on trials
                for events_name in events_names:
                    if align_to == 'Lick':
                        lick_flag, stim_type_string = trial_type_interpreter(events_name)
                        trial_type_table = trial_table.loc[
                            (trial_table[stim_type_string] == 1) & (trial_table.lick_flag == lick_flag)]
                        trials = trial_type_table['lick_time'].values
                        stim_times = trial_type_table['start_time'].values
                    else:
                        trials = session_data.behavior.get_behavioral_events_times(event_name=events_name)
                        if trials is None or len(trials[0, :]) == 0:
                            print("No trials in this condition, skipping")
                            continue
                        trials = trials[0, :]
                        stim_times = trials
                    if len(trials) == 0:
                        print("No trials in this condition, skipping")
                        continue

                    tmp_table = build_psth_dataframe(
                        data=activity, event_timestamps=trials,
                        frame_timestamps=activity_ts, window_s=time_range,
                        subtract_baseline=subtract_baseline,
                        baseline_event_timestamps=stim_times if align_to == 'Lick' else None,
                        trial_type=events_name, session_id=session_id, mouse_id=mouse_id,
                        extra_metadata={'cell_type': cell_type_array,
                                        'behavior_type': behavior_type,
                                        'behavior_day': behavior_day})
                    tmp_table['epoch'] = 'not defined'
                    dfs_list.append(tmp_table)

            self.update_progressbar(time_started=self.analysis_start_time, increment_value=100 / n_sessions)

        dfs_list = pd.concat(dfs_list, ignore_index=True)

        # Save dataset
        if verbose:
            print(' ')
            print('Save the dataset')
        dfs_list.to_csv(os.path.join(results_path, 'PSTHs_dataset.csv'), sep=',')

        if verbose:
            print(' ')
            print('Do some plots')

        # Sessions plots
        if 'wf_psth_session_plot' in plots:
            session_list = pd.unique(dfs_list.session_id)
            for session in session_list:
                if verbose:
                    print(' ')
                    print(f'Do the session plot: {session}')
                session_table = dfs_list.loc[(dfs_list['session_id'] == session) &
                                             (dfs_list['cell_type'].isin(cell_types_to_do))]
                if merge_trial_type:
                    fig = sns.relplot(data=session_table, x='time', y='activity', col='epoch',
                                      hue='cell_type', kind='line', height=5, aspect=0.4)
                else:
                    fig = sns.relplot(data=session_table, x='time', y='activity', col='epoch', row='trial_type',
                                      hue='cell_type', kind='line', height=5, aspect=0.4)
                for ax in fig.axes.flatten():
                    ax.axvline(x=0, ymin=0, ymax=1, linestyle='--', color='grey')
                path = os.path.join(results_path, session[:5])
                if not os.path.exists(path):
                    os.makedirs(path)
                save_figure(results_path=path, save_formats=save_formats,
                                   figure=fig, figname=f'{session}_widefield_psth', dpi=dpi)

        # Mice plots
        if merge_trial_type:
            dfs_list_session = dfs_list.drop(['trial_type'], axis=1)
            dfs_list_session = dfs_list_session.groupby(["mouse_id", "session_id", "epoch",
                                                         "behavior_day", "behavior_type", "roi", "cell_type", "time"],
                                                        as_index=False).agg('mean')
        else:
            dfs_list_session = dfs_list.groupby(["mouse_id", "session_id", "trial_type", "epoch",
                                                 "behavior_day", "behavior_type", "roi", "cell_type", "time"],
                                                as_index=False).agg('mean')
        if 'wf_psth_mouse_plot' in plots:
            mouse_list = pd.unique(dfs_list.mouse_id)
            for mouse in mouse_list:
                if verbose:
                    print(' ')
                    print(f'Do the mouse plot: {mouse}')
                mouse_table = dfs_list_session.loc[(dfs_list_session['mouse_id'] == mouse) &
                                                   (dfs_list_session['cell_type'].isin(cell_types_to_do))]
                if merge_trial_type:
                    fig = sns.relplot(data=mouse_table, x='time', y='activity', col='epoch',
                                      hue='cell_type', kind='line',
                                      height=4, aspect=0.5)
                else:
                    fig = sns.relplot(data=mouse_table, x='time', y='activity', col='epoch', row='trial_type',
                                      hue='cell_type', kind='line',
                                      height=4, aspect=0.5)
                for ax in fig.axes.flatten():
                    ax.axvline(x=0, ymin=0, ymax=1, linestyle='--', color='grey')
                path = os.path.join(results_path, mouse)
                if not os.path.exists(path):
                    os.makedirs(path)
                save_figure(results_path=path, save_formats=save_formats,
                                   figure=fig, figname=f'{mouse}_widefield_psth_average', dpi=dpi)

        # Full plot
        if 'wf_psth_full_plot' in plots:
            if verbose:
                print(' ')
                print(f'Do the full plot')
            mice_avg_data = dfs_list_session.drop(['session_id', 'behavior_day'], axis=1)
            if merge_trial_type:
                mice_avg_data = mice_avg_data.groupby(["mouse_id", "epoch",
                                                       "behavior_type", "roi", "cell_type", "time"],
                                                      as_index=False).agg('mean')
            else:
                mice_avg_data = mice_avg_data.groupby(["mouse_id", "trial_type", "epoch",
                                                       "behavior_type", "roi", "cell_type", "time"],
                                                      as_index=False).agg('mean')
            mice_avg_data = mice_avg_data.loc[mice_avg_data.cell_type.isin(cell_types_to_do)]
            # By context & trial type
            if merge_trial_type:
                fig = sns.relplot(data=mice_avg_data, x='time', y='activity', col='epoch',
                                  hue='cell_type', kind='line',
                                  height=4, aspect=0.5)
            else:
                fig = sns.relplot(data=mice_avg_data, x='time', y='activity', col='epoch', row='trial_type',
                                  hue='cell_type', kind='line',
                                  height=4, aspect=0.5)
            for ax in fig.axes.flatten():
                ax.axvline(x=0, ymin=0, ymax=1, linestyle='--', color='grey')
            save_figure(results_path=results_path, save_formats=save_formats,
                               figure=fig, figname='widefield_psth', dpi=dpi)
            # By area
            if merge_trial_type:
                fig_by_area = sns.relplot(data=mice_avg_data, x='time', y='activity', col='cell_type', hue='epoch',
                                          hue_order=['non-rewarded', 'rewarded'], kind='line',
                                          palette=['darkmagenta', 'green'], col_wrap=5,
                                          height=4, aspect=0.5)
            else:
                fig_by_area = sns.relplot(data=mice_avg_data, x='time', y='activity', col='cell_type', hue='epoch',
                                          hue_order=['non-rewarded', 'rewarded'], size='trial_type',
                                          sizes=[3, 1], size_order=['whisker_hit_trial', 'whisker_miss_trial'],
                                          kind='line', palette=['darkmagenta', 'green'], col_wrap=5,
                                          height=4, aspect=0.5)
            for ax in fig_by_area.axes.flatten():
                ax.axvline(x=0, ymin=0, ymax=1, linestyle='--', color='grey')
            save_figure(results_path=results_path, save_formats=save_formats,
                               figure=fig_by_area, figname='widefield_psth_by_area', dpi=dpi)
            # Context transition
            if center_on_epochs and not merge_trial_type:
                transition_df = mice_avg_data.loc[mice_avg_data.trial_type == 'epoch_transition']
                if len(transition_df) > 0:
                    fig_context_transition = sns.relplot(data=transition_df,
                                                         x='time', y='activity', col='cell_type', hue='epoch',
                                                         kind='line',  hue_order=['non-rewarded', 'rewarded'],
                                                         palette=['darkmagenta', 'green'], col_wrap=5,
                                                         height=4, aspect=0.5)
                    for ax in fig_context_transition.axes.flatten():
                        ax.axvline(x=0, ymin=0, ymax=1, linestyle='--', color='grey')
                    save_figure(results_path=results_path, save_formats=save_formats,
                                       figure=fig_context_transition, figname='widefield_psth_context', dpi=dpi)

                # Define the peak response window (configured via peak_window_start/stop_ms params)
                t_start = peak_window_start_s
                t_stop = peak_window_stop_s
                # Find the max value on time interval
                mice_avg_table_response = mice_avg_data.loc[
                    (mice_avg_data.time > t_start) & (mice_avg_data.time < t_stop)]
                max_response_table = mice_avg_table_response.loc[
                    mice_avg_table_response.groupby(["mouse_id", "trial_type",
                                                     "epoch", "behavior_type",
                                                     "roi", "cell_type"])["activity"].idxmax()]

                g = sns.catplot(data=max_response_table, kind="bar", col='cell_type', x='trial_type', y='activity',
                                hue='epoch', palette=['green', 'red'], hue_order=['rewarded', 'non-rewarded'],
                                col_wrap=4, height=3, aspect=1)

                save_figure(results_path=results_path, save_formats=save_formats,
                                   figure=g, figname='PSTHs_peak_values_by_trial', dpi=dpi)

                g = sns.catplot(data=max_response_table, kind="bar", col='cell_type', x='epoch', y='activity',
                                hue='trial_type', palette=['black', 'gray'],
                                hue_order=['whisker_hit_trial', 'whisker_miss_trial'],
                                col_wrap=4, height=3, aspect=1)

                save_figure(results_path=results_path, save_formats=save_formats,
                                   figure=g, figname='PSTHs_peak_values_by_context', dpi=dpi)

                # Find the time needed to get to half of this max value
                mice_avg_table_halfmax = mice_avg_data.loc[
                    (mice_avg_data.time > 0) & (mice_avg_data.time < t_stop)]

                normalized_activity = mice_avg_table_halfmax.groupby(["mouse_id", "trial_type", "epoch", "behavior_type",
                                                                      "roi", "cell_type"])['activity'].\
                    transform(lambda x: (x - np.nanmin(x))/np.nanmax(x))
                mice_avg_table_halfmax.insert(loc=len(mice_avg_table_halfmax.columns),
                                              column='normalized_activity', value=normalized_activity.values[:],
                                              allow_duplicates=False)

                result = mice_avg_table_halfmax[mice_avg_table_halfmax['normalized_activity'] > 0.5].\
                    groupby(["mouse_id", "trial_type", "epoch", "behavior_type", "roi", "cell_type"]).first().reset_index()

                g = sns.catplot(data=result, kind="bar", col='cell_type', x='epoch', y='time',
                                hue='trial_type', palette=['black', 'gray'],
                                hue_order=['whisker_hit_trial', 'whisker_miss_trial'],
                                col_wrap=4, height=3, aspect=1)

                save_figure(results_path=results_path, save_formats=save_formats,
                                   figure=g, figname='PSTHs_halfmax_values_by_context', dpi=dpi)

                g = sns.catplot(data=result, kind="bar", col='cell_type', x='trial_type', y='time',
                                hue='epoch', palette=['green', 'red'], hue_order=['rewarded', 'non-rewarded'],
                                col_wrap=4, height=3, aspect=1)

                save_figure(results_path=results_path, save_formats=save_formats,
                                   figure=g, figname='PSTHs_halfmax_values_by_trial', dpi=dpi)

                g = sns.catplot(data=result, kind="bar", col='epoch', row='trial_type', x='cell_type', y='time',
                                height=3, aspect=1)

                save_figure(results_path=results_path, save_formats=save_formats,
                                   figure=g, figname='PSTHs_halfmax_areas', dpi=dpi)

        print(f"Widefield PSTH analysis run in {time() - self.analysis_start_time} sec")
