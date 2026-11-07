import os
import warnings
import numpy as np
import pandas as pd
from time import time
import seaborn as sns
from matplotlib import pyplot as plt

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.display.core_plots import save_figure
from cicada_petersen.tools.behavior_utils import add_correct_choice_to_table
from cicada_analysis.cicada_tools.core import print_info_dict, find_nearest
from cicada_petersen.tools.widefield_utils import trial_type_baseline, average_images_from_dict, plot_wf_single_frame


class CicadaCompareBaseline(CicadaAnalysis):
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
        CicadaAnalysis.__init__(self, name="Compare Baseline", family_id="Widefield",
                                short_description="Compare baseline fluorescence across epochs",
                                long_description=long_description,
                                config_handler=config_handler,
                                accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaCompareBaseline(config_handler=self.config_handler)
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

        analysis_list = ['Compare baseline images', 'Compare baseline dff']
        self.add_choices_arg_for_gui(arg_name="analysis_to_do", choices=analysis_list,
                                     default_value="Compare baseline dff", short_description="Analysis to do",
                                     multiple_choices=False,
                                     family_widget="Analysis type")

        self.add_roi_response_series_arg_for_gui(short_description="Neural activity (DFF traces) to use",
                                                 long_description=None,
                                                 family_widget="Neural activity to use")

        self.add_widefield_acquisitions_dict_for_gui(short_description="Widefield movie (DFF) to use",
                                                     long_description=None,
                                                     arg_name='widefield_acquisition',
                                                     family_widget="Widefield movie to use")

        plots_list = ['Baseline dff over context time', 'Single trial dff projection',
                      'Baseline image by session', 'Baseline image by mouse',
                      'Baseline image full average', 'Single trial image projection']
        self.add_choices_arg_for_gui(arg_name="plots_to_do", choices=plots_list,
                                     default_value=False,
                                     short_description="Plot(s) to do",
                                     multiple_choices=True, family_widget="Plots")
        self.add_bool_option_for_gui(arg_name="display_points", true_by_default=True,
                                     short_description="Display points",
                                     long_description=None, family_widget='Plots')
        self.add_int_values_arg_for_gui(arg_name="context_time_lim", min_value=0, max_value=300,
                                        short_description="Maximal time in context in plots",
                                        long_description="",
                                        default_value=250, family_widget="Plots")

        self.add_open_file_dialog_arg_for_gui(arg_name='img_dict_path', extensions='npy', mandatory=False,
                                              short_description='Path to images results without trial type',
                                              long_description='Used to built baseline difference map by subtracting '
                                                               'baseline in non rewarded context '
                                                               'to baseline in rewarded context (R+ - R-)',
                                              key_names=None, family_widget='Plots')

        self.add_open_file_dialog_arg_for_gui(arg_name='img_dict_path_all', extensions='npy', mandatory=False,
                                              short_description='Path to images results with trial type',
                                              long_description='Used to project all individual trials onto the '
                                                               'difference between context',
                                              key_names=None, family_widget='Plots')

        self.add_open_file_dialog_arg_for_gui(arg_name='time_in_context_dict_path_all', extensions='npy',
                                              mandatory=False,
                                              short_description='Path to time in context with trial type dictionary',
                                              long_description='Used to project all individual trials onto the '
                                                               'difference between context',
                                              key_names=None, family_widget='Plots')

        all_cell_types = []
        all_trials = []
        all_epochs = []
        for data_to_analyse in self._data_to_analyse:
            all_cell_types.extend(data_to_analyse.calcium_imaging.get_all_cell_types())
            all_epochs.extend(data_to_analyse.behavior.get_behavioral_epochs_names())
            all_trials.extend(data_to_analyse.behavior.get_behavioral_events_names())
        all_cell_types = list(set(all_cell_types))
        all_trials = list(np.unique(all_trials))
        all_trials = [trial for trial in all_trials if "dlc" not in trial]
        all_epochs = list(np.unique(all_epochs))
        all_epochs = [epoch for epoch in all_epochs if "rewarded" in epoch]

        self.add_choices_arg_for_gui(arg_name="epochs_to_do", choices=all_epochs,
                                     default_value=False,
                                     short_description="Select epoch(s) to do widefield analysis",
                                     long_description="epochs selected are used to filter events",
                                     multiple_choices=True,
                                     family_widget="Epoch - Image comparison")

        self.add_choices_arg_for_gui(arg_name="trials_list", choices=all_trials,
                                     default_value=False,
                                     short_description="Events",
                                     long_description="Select events for which you want to do widefield analysis",
                                     multiple_choices=True,
                                     family_widget="Trials - Image comparison")

        self.add_choices_arg_for_gui(arg_name="cell_types_to_do", choices=all_cell_types,
                                     default_value=[], short_description="cell_types_to_do",
                                     long_description="Only filters the 'Baseline dff over context time' plot. "
                                                      "The other 'Compare baseline dff' summary figures always "
                                                      "include every brain region found in the data, regardless "
                                                      "of this selection.",
                                     multiple_choices=True,
                                     family_widget="ROI - Dff comparison")

        self.add_bool_option_for_gui(arg_name="only_correct_trials", true_by_default=False,
                                     short_description="Keep only correct trials in trial table",
                                     long_description=None, family_widget='Compare baseline config')

        self.add_choices_arg_for_gui(arg_name="quiet_window_definition", choices=['last 2s', 'last 0.5s', 'full quiet window'],
                                     default_value='last 2s',
                                     short_description="Define the quiet window to extract data at each trial",
                                     long_description="",
                                     multiple_choices=False,
                                     family_widget="Compare baseline config")

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
        """Compare baseline fluorescence across epochs."""
        CicadaAnalysis.run_analysis(self, **kwargs)

        roi_response_series_dict = kwargs["roi_response_series"]

        cell_types_to_do = kwargs["cell_types_to_do"]

        widefield_acquisition_dict = kwargs["widefield_acquisition"]

        verbose = kwargs.get("verbose", True)

        analysis_to_do = kwargs.get('analysis_to_do')

        plots = kwargs.get('plots_to_do')

        display_points = kwargs.get('display_points')

        epochs_to_do = kwargs.get("epochs_to_do")
        trials_list = kwargs.get("trials_list")

        quiet_window_mode = kwargs.get("quiet_window_definition")

        only_correct_trials = kwargs.get("only_correct_trials")

        context_time_lim = kwargs.get('context_time_lim')

        color_map = kwargs.get('color_map')
        color_scale = (float(kwargs.get('colorbar_scale_min')), float(kwargs.get('colorbar_scale_max')))
        halfrange = float(kwargs.get('halfrange'))

        img_dict_path = kwargs.get('img_dict_path')
        img_dict_path_all = kwargs.get('img_dict_path_all')
        time_in_context_dict_path_all = kwargs.get('time_in_context_dict_path_all')

        # ------- figures config part -------
        save_formats = kwargs["save_formats"]
        if save_formats is None:
            save_formats = "pdf"

        results_path = self.get_results_path()

        n_sessions = len(self._data_to_analyse)

        dfs_list = []

        general_img_dict = {}
        general_img_transition_time_dict = {}
        general_img_dict_without_trial_type = {}
        general_img_transition_time_no_type_dict = {}
        if img_dict_path is not None and os.path.exists(img_dict_path):
            if verbose:
                print('Load images results from file for baseline difference')
            general_img_dict_without_trial_type = np.load(img_dict_path, allow_pickle=True).item()

        if img_dict_path_all is not None and os.path.exists(img_dict_path_all):
            if verbose:
                print('Load images results from file with trial type info')
            general_img_dict = np.load(img_dict_path_all, allow_pickle=True).item()

        if time_in_context_dict_path_all is not None and os.path.exists(time_in_context_dict_path_all):
            if verbose:
                print('Load time in context results from file with trial type info')
            general_img_transition_time_dict = np.load(time_in_context_dict_path_all, allow_pickle=True).item()

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

            # Get trial table
            trial_table = session_data.behavior.get_trial_table()

            # Add column 'correct trial' (0 or 1) to filter it if needed
            trial_table = add_correct_choice_to_table(trial_table, colname='correct_trial')

            if 'Compare baseline images' in analysis_to_do:
                trial_table['context'] = trial_table['context'].map({0: "Non-Rewarded", 1: "Rewarded"})
            n_trials = len(trial_table)

            # Get neural data timestamps
            if isinstance(roi_response_series_dict, dict):
                roi_response_serie_info = roi_response_series_dict[session_identifier]
            else:
                roi_response_serie_info = roi_response_series_dict

            rrs_ts = session_data.calcium_imaging.get_roi_response_serie_timestamps(keys=roi_response_serie_info)
            if rrs_ts is None or len(rrs_ts) == 0:
                print(f'Session {session_id} has no activity_ts - skipping.')
                continue

            # Get WF session data (h5 pointer):
            wf_session_data = session_data.widefield.get_widefield_dff0_mmap

            # Compare baseline dff
            if 'Compare baseline dff' in analysis_to_do:
                # Get all quiet windows
                quiet_window_frames = []
                for trial in range(n_trials):
                    quiet_start = trial_table.iloc[trial].abort_window_start_time
                    stim_time = trial_table.iloc[trial].start_time
                    if quiet_window_mode == 'last 2s':
                        start_frame = find_nearest(rrs_ts, stim_time - 2)
                    elif quiet_window_mode == 'last 0.5s':
                        start_frame = find_nearest(rrs_ts, stim_time - 0.5)
                    else:
                        start_frame = find_nearest(rrs_ts, quiet_start)
                    end_frame = find_nearest(rrs_ts, stim_time)
                    quiet_window_frames.append(np.arange(start_frame, end_frame))

                # Get activity and brain region ROIs
                rrs_array = session_data.calcium_imaging.get_roi_response_serie_data(keys=roi_response_serie_info)
                rrs_cell_type_dict = session_data.calcium_imaging.get_cell_indices_by_cell_type(roi_response_serie_info)
                n_cell_types = len(rrs_cell_type_dict.keys())

                # Get average activity in each ROIs for each trial
                trial_by_type = np.zeros((n_trials, n_cell_types))
                for trial in range(n_trials):
                    activity = rrs_array[:, quiet_window_frames[trial]]
                    mean_activity = np.mean(activity, axis=1)
                    trial_by_type[trial, :] = mean_activity

                # Keep only a few relevant columns
                cols = ['start_time', 'trial_type', 'reward_available', 'lick_flag', 'correct_trial',
                        'context', 'context_background']
                sub_trial_table = trial_table[cols]
                session_df = sub_trial_table.copy(deep=True)

                # Add to trial table the average baseline dff for each brain region ROI
                for area, area_index in rrs_cell_type_dict.items():
                    session_df[f'{area}_baseline_dff'] = trial_by_type[:, area_index]

                # Add context transition column
                transitions = list(np.diff(session_df['context']))
                transitions.insert(0, 0)
                block_size = np.where(transitions)[0][0]

                # Get context start timestamps and time in context at each trial
                rewarded_context_start_timestamps = \
                    session_data.behavior.get_behavioral_epochs_times(epoch_name='rewarded')[0]
                non_rewarded_context_start_timestamps = \
                    session_data.behavior.get_behavioral_epochs_times(epoch_name='non-rewarded')[0]
                if min(non_rewarded_context_start_timestamps) < min(rewarded_context_start_timestamps):
                    context_starts = np.concatenate(
                        (non_rewarded_context_start_timestamps, rewarded_context_start_timestamps))
                else:
                    context_starts = np.concatenate(
                        (rewarded_context_start_timestamps, non_rewarded_context_start_timestamps))
                context_starts = np.sort(context_starts)
                context_starts = np.repeat(context_starts, block_size)
                context_starts = context_starts[0: len(session_df)]
                session_df['context_start'] = context_starts
                session_df['time_in_context'] = session_df['start_time'] - session_df['context_start']

                # Add mouseID and sessionID
                session_df['mouse_id'] = mouse_id
                session_df['session_id'] = session_id

                if only_correct_trials:
                    print('Use only correct trials')
                    session_df = session_df.loc[session_df.correct_trial == True]

                dfs_list.append(session_df)

            if 'Compare baseline images' in analysis_to_do and len(epochs_to_do) != 2:
                print('Incorrect epochs selected. Select rewarded and non rewarded epochs to perform this analysis\n')

            if 'Compare baseline images' in analysis_to_do and len(epochs_to_do) == 2:
                if img_dict_path is not None and os.path.exists(img_dict_path):
                    if verbose:
                        print('Images loaded from results from file')
                else:
                    if verbose:
                        print('Compute baseline images')
                    # Get wf timestamps
                    if isinstance(widefield_acquisition_dict, dict):
                        keys_ophys_dff0 = widefield_acquisition_dict[session_identifier]
                    else:
                        keys_ophys_dff0 = widefield_acquisition_dict

                    # get shape of img
                    (n_frames, shape_x, shape_y) = session_data.widefield.get_widefield_dff0(keys_ophys_dff0, 0, 1).shape

                    # add keys to dict
                    # Dictionaries for image data
                    general_img_dict.setdefault(mouse_id, {})
                    general_img_dict_without_trial_type.setdefault(mouse_id, {})
                    general_img_dict[mouse_id].setdefault(session_id, {})
                    general_img_dict_without_trial_type[mouse_id].setdefault(session_id, {})

                    # Dictionaries for time after transition
                    general_img_transition_time_dict.setdefault(mouse_id, {})
                    general_img_transition_time_no_type_dict.setdefault(mouse_id, {})
                    general_img_transition_time_dict[mouse_id].setdefault(session_id, {})
                    general_img_transition_time_no_type_dict[mouse_id].setdefault(session_id, {})

                    # keep only correct trials
                    if only_correct_trials:
                        print('Use only correct trials')
                        trial_table = trial_table.loc[trial_table.correct_trial == True]

                    # add wf baseline image to general_img_dict
                    if epochs_to_do:
                        for epoch in epochs_to_do:
                            print(f"Epoch: {epoch}")
                            epoch_starts = session_data.behavior.get_behavioral_epochs_times(epoch_name=epoch)[0]

                            general_img_dict[mouse_id][session_id].setdefault(epoch, {})
                            general_img_dict_without_trial_type[mouse_id][session_id].setdefault(epoch, [])

                            general_img_transition_time_dict[mouse_id][session_id].setdefault(epoch, {})
                            general_img_transition_time_no_type_dict[mouse_id][session_id].setdefault(epoch, [])

                            # baseline centered on trials filtered by epoch (epochs and trials from GUI)
                            for trial_type in trials_list:
                                print(f"Trial type : {trial_type}")
                                general_img_dict[mouse_id][session_id][epoch].setdefault(trial_type, [])
                                general_img_transition_time_dict[mouse_id][session_id][epoch].setdefault(trial_type, [])

                                trial_type_baseline(trial_type, trial_table=trial_table, rrs_ts=rrs_ts,
                                                    session_data=wf_session_data,
                                                    quiet_window_mode=quiet_window_mode,
                                                    general_img_dict_without_trial_type=general_img_dict_without_trial_type,
                                                    general_img_dict=general_img_dict,
                                                    general_img_transition_time_no_type_dict=general_img_transition_time_no_type_dict,
                                                    general_img_transition_time_dict=general_img_transition_time_dict,
                                                    mouse_id=mouse_id, session_id=session_id,
                                                    epoch=epoch, epoch_starts=epoch_starts,
                                                    shape_x=shape_x, shape_y=shape_y)

            self.update_progressbar(time_started=self.analysis_start_time, increment_value=100 / n_sessions)

        # ------------------------------------------------------------------------------------------------------------ #
        # ----------------------------------------------MAKE FIGURES-------------------------------------------------- #
        if 'Compare baseline images' in analysis_to_do and len(epochs_to_do) == 2:
            # Some savings
            if verbose:
                print()
                print('Save the dataset')
            np.save(os.path.join(results_path, f"general_img_dict.npy"), general_img_dict)
            np.save(os.path.join(results_path, f"general_img_dict_without_trial_type.npy"),
                    general_img_dict_without_trial_type)
            np.save(os.path.join(results_path, f"general_img_transition_time_dict.npy"),
                    general_img_transition_time_dict)
            np.save(os.path.join(results_path, f"general_img_transition_time_no_type_dict.npy"),
                    general_img_transition_time_no_type_dict)
            if verbose:
                print()
                print('Do some plots')

            # Data reorganization
            rewarded_epoch = epochs_to_do[1] if 'no' not in epochs_to_do[1] else epochs_to_do[0]
            non_rewarded_epoch = epochs_to_do[0] if 'no' in epochs_to_do[0] else epochs_to_do[1]
            mouse_averages = {rewarded_epoch: {}, non_rewarded_epoch: {}}
            for mouse, sessions in general_img_dict_without_trial_type.items():
                mouse_averages[rewarded_epoch][mouse] = []
                mouse_averages[non_rewarded_epoch][mouse] = []
                for session, epochs in sessions.items():
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        avg_data_rewarded_epoch = np.nanmean(np.concatenate(epochs[rewarded_epoch], axis=0), axis=0)
                        avg_data_non_rewarded_epoch = np.nanmean(np.concatenate(epochs[non_rewarded_epoch], axis=0), axis=0)
                    mouse_averages[rewarded_epoch][mouse].append(avg_data_rewarded_epoch)
                    mouse_averages[non_rewarded_epoch][mouse].append(avg_data_non_rewarded_epoch)

                    # Session_plots
                    session_avg_data_diff = avg_data_rewarded_epoch - avg_data_non_rewarded_epoch
                    if 'Baseline image by session' in plots:
                        print(f'Do the session plot: {session}')
                        fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True, sharex=True)
                        path = os.path.join(results_path, mouse)
                        plot_wf_single_frame(frame=avg_data_rewarded_epoch,
                                             title=f'{session}_{rewarded_epoch}_baseline',
                                             figure=fig, ax_to_plot=axes.flatten()[0], suptitle=' ', saving_path=path,
                                             save_formats=save_formats, colormap='hotcold',
                                             vmin=color_scale[0], vmax=color_scale[1],
                                             halfrange=halfrange, cbar_shrink=1.0)
                        plot_wf_single_frame(frame=avg_data_non_rewarded_epoch,
                                             title=f'{session}_{non_rewarded_epoch}_baseline', figure=fig,
                                             ax_to_plot=axes.flatten()[1], suptitle=' ', saving_path=path,
                                             save_formats=save_formats, colormap='hotcold',
                                             vmin=color_scale[0], vmax=color_scale[1],
                                             halfrange=halfrange, cbar_shrink=1.0)
                        plot_wf_single_frame(frame=session_avg_data_diff, title=f'{session}_baseline_diff', figure=fig,
                                             ax_to_plot=axes.flatten()[2], suptitle=' ', saving_path=path,
                                             save_formats=save_formats, colormap=color_map,
                                             vmin=color_scale[0], vmax=color_scale[1],
                                             halfrange=halfrange, cbar_shrink=1.0)
                        save_figure(results_path=path, save_formats=save_formats, figure=fig,
                                           figname=f'{session}')

            if 'Baseline image by mouse' in plots:
                # Mouse plots
                for mouse, sessions in general_img_dict.items():
                    print(f'Do the mouse plot: {mouse}')
                    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True, sharex=True)
                    path = os.path.join(results_path, mouse)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        avg_data_rewarded = np.nanmean(mouse_averages[rewarded_epoch][mouse], axis=0)
                    plot_wf_single_frame(frame=avg_data_rewarded,  title=f'{mouse}_rewarded_baseline',
                                         figure=fig, ax_to_plot=axes.flatten()[0], suptitle=' ', saving_path=path,
                                         save_formats=save_formats, colormap='hotcold',
                                         vmin=color_scale[0], vmax=color_scale[1],
                                         halfrange=halfrange, cbar_shrink=1.0)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        avg_data_non_rewarded = np.nanmean(mouse_averages[non_rewarded_epoch][mouse], axis=0)
                    plot_wf_single_frame(frame=avg_data_non_rewarded, title=f'{mouse}_non_rewarded_baseline',
                                         figure=fig, ax_to_plot=axes.flatten()[1], suptitle=' ', saving_path=path,
                                         save_formats=save_formats, colormap='hotcold',
                                         vmin=color_scale[0], vmax=color_scale[1],
                                         halfrange=halfrange, cbar_shrink=1.0)
                    mouse_avg_data_diff = avg_data_rewarded - avg_data_non_rewarded
                    plot_wf_single_frame(frame=mouse_avg_data_diff, title=f'{mouse}_baseline_diff', figure=fig,
                                         ax_to_plot=axes.flatten()[2], suptitle=' ', saving_path=path,
                                         save_formats=save_formats, colormap=color_map,
                                         vmin=color_scale[0], vmax=color_scale[1],
                                         halfrange=halfrange, cbar_shrink=1.0)
                    save_figure(results_path=path, save_formats=save_formats, figure=fig,
                                       figname=f'{mouse}')

            full_avg_data_diff = None
            if 'Baseline image full average' in plots:
                print(f'Do the overall average')
                fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True, sharex=True)
                path = os.path.join(results_path)
                avg_data_rewarded = average_images_from_dict(mouse_averages[rewarded_epoch])
                plot_wf_single_frame(frame=avg_data_rewarded, title=f'rewarded_baseline',
                                     figure=fig, ax_to_plot=axes.flatten()[0], suptitle=' ', saving_path=path,
                                     save_formats=save_formats, colormap='hotcold',
                                     vmin=color_scale[0], vmax=color_scale[1],
                                     halfrange=halfrange, cbar_shrink=1.0)
                avg_data_non_rewarded = average_images_from_dict(mouse_averages[non_rewarded_epoch])
                plot_wf_single_frame(frame=avg_data_non_rewarded, title=f'non_rewarded_baseline',
                                     figure=fig, ax_to_plot=axes.flatten()[1], suptitle=' ', saving_path=path,
                                     save_formats=save_formats, colormap='hotcold',
                                     vmin=color_scale[0], vmax=color_scale[1],
                                     halfrange=halfrange, cbar_shrink=1.0)
                full_avg_data_diff = avg_data_rewarded - avg_data_non_rewarded
                plot_wf_single_frame(frame=full_avg_data_diff, title=f'baseline_diff', figure=fig,
                                     ax_to_plot=axes.flatten()[2], suptitle=' ', saving_path=path,
                                     save_formats=save_formats, colormap=color_map,
                                     vmin=color_scale[0], vmax=color_scale[1],
                                     halfrange=halfrange, cbar_shrink=1.0)
                save_figure(results_path=path, save_formats=save_formats, figure=fig,
                                   figname=f'general_average')

            if 'Single trial image projection' in plots and full_avg_data_diff is not None:
                image_correlation_to_context_df = pd.DataFrame(columns=['mouse_id', 'session_id', 'context',
                                                                        'trial_type', 'time_in_context', 'correlation'])
                context_img_diff = list(full_avg_data_diff.flatten())
                for mouse, session_data in general_img_dict.items():
                    for session, epoch_data in session_data.items():
                        for epoch, trial_data in epoch_data.items():
                            for trial_type, image_list in trial_data.items():
                                if len(general_img_transition_time_dict[mouse][session][epoch][trial_type]) > 0:
                                    time_in_context = general_img_transition_time_dict[mouse][session][epoch][trial_type][0]
                                    for img_index in range(image_list[0].shape[0]):
                                        trial_img = list(image_list[0][img_index, :, :].flatten())
                                        mask = ~np.isnan(context_img_diff) & ~np.isnan(trial_img)
                                        rho = np.corrcoef(np.array(context_img_diff)[mask],
                                                          np.array(trial_img)[mask])[0, 1]
                                        new_row = pd.Series({'mouse_id': mouse, 'session_id': session, 'context': epoch,
                                                             'trial_type': trial_type,
                                                             'time_in_context': time_in_context[img_index],
                                                             'correlation': rho})
                                        image_correlation_to_context_df = pd.concat([image_correlation_to_context_df,
                                                                                     new_row.to_frame().T],
                                                                                    ignore_index=True)
                # Just format
                replacement_dict = {'rewarded': 1, 'non-rewarded': 0}
                image_correlation_to_context_df['context'] = image_correlation_to_context_df['context'].replace(replacement_dict)
                image_correlation_to_context_df['correlation'] = pd.to_numeric(image_correlation_to_context_df['correlation'],
                                                                            errors='coerce')
                image_correlation_to_context_df['time_in_context'] = pd.to_numeric(image_correlation_to_context_df['time_in_context'],
                                                                            errors='coerce')
                # Save dataset
                image_correlation_to_context_df.to_csv(os.path.join(results_path, 'image_correlation_dataset.csv'))

                # Make figures
                # Figure 1
                fig = sns.lmplot(data=image_correlation_to_context_df.loc[image_correlation_to_context_df.
                                 time_in_context < context_time_lim],
                                 y='correlation', x='time_in_context',
                                 hue='context',
                                 palette=['red', 'green'], hue_order=[0, 1], height=3, aspect=2,
                                 scatter=display_points)
                fig.axes.flatten()[0].axhline(y=0, xmin=0, xmax=1, c='k', linestyle='--')
                fig.axes.flatten()[0].set_ylabel('Correlation to context difference')
                fig.axes.flatten()[0].set_xlabel('Time after context transition (s)')
                save_figure(results_path=results_path, save_formats=save_formats,
                                   figure=fig, figname=f'context_time_image_projection')

        if 'Compare baseline dff' in analysis_to_do:
            if verbose:
                print()
                print('Save the dataset')
            dfs_list = pd.concat(dfs_list, ignore_index=True)

            # Save dataset
            dfs_list.to_csv(os.path.join(results_path, 'Compare_baseline_traces_dataset.csv'))
            brain_regions = [col for col in dfs_list.columns if col.endswith('_baseline_dff')]

            # Plots
            if verbose:
                print()
                print('Do some plots')

            # Main figures
            # Set plot parameters.
            plt.rcParams['pdf.fonttype'] = 42
            plt.rcParams['ps.fonttype'] = 42
            plt.rcParams['svg.fonttype'] = 'none'

            # Average data
            df = dfs_list.drop(['start_time', 'trial_type', 'correct_trial', 'reward_available',
                                'lick_flag', 'time_in_context', 'context_start', 'context_background'], axis=1)

            brain_colors = ['cyan', 'grey', 'pink', 'darkred', 'red', 'green', 'darkgreen', 'orange', 'magenta']

            session_df = df.groupby(['context', 'mouse_id', 'session_id'],
                                    as_index=False).agg('mean')
            mouse_df = session_df
            mouse_df = mouse_df.drop(['session_id'], axis=1)
            mouse_df = mouse_df.groupby(['context', 'mouse_id'],
                                        as_index=False).agg('mean')

            color_palette = [(129 / 255, 0 / 255, 129 / 255), (0 / 255, 135 / 255, 0 / 255)]

            # Plot all region R+ vs R- raw df/f
            fig, axes = plt.subplots(1, len(brain_regions), figsize=(8, 4), sharey=True)
            for idx, ax in enumerate(axes.flatten()):
                sns.pointplot(mouse_df, y=brain_regions[idx], hue='context', hue_order=[0, 1], palette=color_palette,
                              dodge=True, legend=False, ax=ax)
                sns.stripplot(mouse_df, y=brain_regions[idx], hue='context', hue_order=[0, 1], palette=color_palette,
                              dodge=True, legend=False, ax=ax)
                ax.set_ylabel('Baseline df/f0')
                ax.set_ylim(0.01, 0.04)
                ax.set_title(brain_regions[idx].split('_')[0])
            sns.despine()
            fig.tight_layout()
            path = os.path.join(results_path, 'general_plots')
            if not os.path.exists(path):
                os.makedirs(path)
            save_figure(results_path=path, save_formats=save_formats,
                               figure=fig, figname=f'raw_baseline_dff')

            # X/Y plot R+ vs R- plus diagonal
            fig, ax = plt.subplots(1, 1, figsize=(4, 4))
            for idx, roi in enumerate(brain_regions):
                group_stats = mouse_df.groupby('context')[roi].agg(['mean', 'std'])
                x_mean, y_mean = group_stats.loc[0, 'mean'], group_stats.loc[1, 'mean']
                x_err, y_err = group_stats.loc[0, 'std'], group_stats.loc[1, 'std']
                plt.errorbar(x_mean, y_mean, xerr=x_err, yerr=y_err,
                             fmt='o', markersize=8, capsize=5, color=brain_colors[idx])

            ax.plot([0.01, 0.04], [0.01, 0.04], linestyle='dashed', color='red')
            ax.set_xlim(0.015, 0.04)
            ax.set_ylim(0.015, 0.04)
            ax.set_xlabel("R-")
            ax.set_ylabel("R+")
            sns.despine()
            fig.tight_layout()
            path = os.path.join(results_path, 'general_plots')
            if not os.path.exists(path):
                os.makedirs(path)
            save_figure(results_path=path, save_formats=save_formats,
                               figure=fig, figname=f'raw_baseline_dff_scatter')

            # Plot (R+ - R-) / R+ : normalized df/f change between context for each region
            # Identify data columns
            data_cols = [col for col in session_df.columns if col not in ['mouse_id', 'session_id',
                                                                          'context']]

            # Pivot to separate context 0 and context 1
            session_df_pivot = session_df.pivot(index=['mouse_id', 'session_id'],
                                                columns='context')[data_cols]

            # Compute difference (context 1 - context 0)
            session_df_diff = (session_df_pivot.xs(1, axis=1, level=1) -
                               session_df_pivot.xs(0, axis=1, level=1)) / session_df_pivot.xs(1, axis=1, level=1)

            # Reset index and rename columns
            session_df_diff.columns = [f'{col}_diff' for col in session_df_diff.columns]
            session_df_diff = session_df_diff.reset_index()
            mouse_df_diff = session_df_diff.drop(['session_id'], axis=1)
            mouse_df_diff = mouse_df_diff.groupby(['mouse_id'],
                                                  as_index=False).agg('mean')
            mouse_df_diff['context_background'] = pd.Series(dtype='str')
            for mouse in mouse_df_diff.mouse_id.unique():
                mouse_df_diff.loc[mouse_df_diff.mouse_id == mouse, 'context_background'] = \
                    dfs_list.loc[(dfs_list.mouse_id == mouse) & (dfs_list.context == 1), 'context_background'].iloc[0]

            # Plots
            fig, axes = plt.subplots(1, len(data_cols), figsize=(6, 3), sharey=True)
            for idx, ax in enumerate(axes.flatten()):
                sns.pointplot(mouse_df_diff, y=f'{data_cols[idx]}_diff',
                              color='grey',
                              dodge=True, legend=False, ax=ax)
                sns.stripplot(mouse_df_diff, y=f'{data_cols[idx]}_diff',
                              hue='context_background',
                              hue_order=['pink', 'brown'], palette=['pink', 'sienna'],
                              dodge=False, legend=False, ax=ax)
                ax.set_ylabel('Relative baseline change df/f0')
                ax.axhline(y=0, xmin=0, xmax=1, linestyle='--', c='k')
                ax.set_ylim(-0.45, 0.45)
                ax.set_title(brain_regions[idx].split('_')[0])
            sns.despine()
            fig.tight_layout()
            path = os.path.join(results_path, 'general_plots')
            if not os.path.exists(path):
                os.makedirs(path)
            save_figure(results_path=path, save_formats=save_formats,
                               figure=fig, figname=f'normalized_change_baseline_dff')

            for brain_region in brain_regions:
                brain_region = brain_region.replace('_baseline_dff', '')
                if brain_region not in cell_types_to_do:
                    continue
                if 'Baseline dff over context time' in plots:
                    if verbose:
                        print(' ')
                        print(f'Plot for: {brain_region}')
                    # All data together
                    fig = sns.lmplot(data=dfs_list.loc[dfs_list.time_in_context < context_time_lim],
                                     y=brain_region + '_baseline_dff', x='time_in_context',
                                     hue='context', palette=['darkmagenta', 'green'], hue_order=[0, 1],
                                     height=3, aspect=3, scatter=display_points)
                    path = os.path.join(results_path, 'over_context_time', 'brain_region')
                    if not os.path.exists(path):
                        os.makedirs(path)
                    save_figure(results_path=path, save_formats=save_formats,
                                       figure=fig, figname=f'{brain_region}_in_context')

                    # Do one figure by mouse and split by session
                    for mouse in dfs_list.mouse_id.unique():
                        if verbose:
                            print(' ')
                            print(f'Do the mouse plot: {mouse}')
                        fig = sns.lmplot(data=dfs_list.loc[(dfs_list.mouse_id == mouse) &
                                                           (dfs_list.time_in_context < context_time_lim)],
                                         y=brain_region + '_baseline_dff',
                                         x='time_in_context', hue='context', palette=['darkmagenta', 'green'],
                                         hue_order=[0, 1], col='session_id', scatter=display_points)
                        path = os.path.join(results_path, 'over_context_time', mouse)
                        if not os.path.exists(path):
                            os.makedirs(path)
                        save_figure(results_path=path, save_formats=save_formats,
                                           figure=fig, figname=f'{brain_region}_in_context')

            if 'Single trial dff projection' in plots:
                cols = list(np.copy(brain_regions))
                cols.insert(0, 'context')
                cols.insert(0, 'session_id')
                cols.insert(0, 'mouse_id')

                # Keep only correct trial to compute difference between context
                dfs_list_correct = dfs_list.loc[dfs_list.correct_trial == True, cols]

                # Successive average across 1-session, 2-mouse, 3-context for each area
                session_avg_df = dfs_list_correct.groupby(['mouse_id', 'session_id', 'context'],
                                                          as_index=False).agg('mean')
                mouse_avg_df = session_avg_df.drop('session_id', axis=1)
                mouse_avg_df = mouse_avg_df.groupby(['mouse_id', 'context'], as_index=False).agg('mean')
                context_avg_df = mouse_avg_df.drop('mouse_id', axis=1)
                context_avg_df = context_avg_df.groupby('context', as_index=False).agg('mean')

                # Compute difference between context for each area
                context_diff = list((context_avg_df.loc[context_avg_df.context == 1].values -
                                     context_avg_df.loc[context_avg_df.context == 0].values)[0][1:])

                # Correlate each trial from the main df with the mean context difference on correct trials
                rho_list = []
                for i_trial in range(len(dfs_list)):
                    roi_data = list(dfs_list.iloc[i_trial][brain_regions].values[:])
                    rho_list.append(np.corrcoef(roi_data, context_diff)[0, 1])

                # Add it to the dfs list
                dfs_list['correlation_to_context_diff'] = rho_list
                dfs_list.to_csv(os.path.join(results_path, 'ROIs_correlation_to_context_diff.csv'))

                # Make figure
                fig = sns.lmplot(data=dfs_list.loc[dfs_list.time_in_context < context_time_lim],
                                 y='correlation_to_context_diff', x='time_in_context', hue='context',
                                 palette=['darkmagenta', 'green'], hue_order=[0, 1], height=3, aspect=2,
                                 scatter=display_points)
                fig.axes.flatten()[0].set_ylim(-0.3, 0.3)
                fig.axes.flatten()[0].axhline(y=0, xmin=0, xmax=1, c='k', linestyle='--')
                fig.axes.flatten()[0].set_ylabel('Correlation to context difference')
                fig.axes.flatten()[0].set_xlabel('Time after context transition (s)')
                path = os.path.join(results_path, 'over_context_time')
                if not os.path.exists(path):
                    os.makedirs(path)
                save_figure(results_path=path, save_formats=save_formats,
                                   figure=fig, figname=f'context_time_projection')

        print(f"Compare baseline analysis run in {time() - self.analysis_start_time} sec")
