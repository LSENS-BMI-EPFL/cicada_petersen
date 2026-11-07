import os
import warnings
import numpy as np
from time import time

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.core import print_info_dict, find_nearest, filter_events_based_on_epochs
from cicada_analysis.cicada_tools.imaging import get_avg_frames_by_epoch
from cicada_petersen.tools.widefield_utils import plot_wf_avg


class CicadaWidefieldTimeCourses(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        long_description = '<p align="center"><b>Widefield Time Courses</b></p>'
        long_description = long_description + 'Main parameters:<br>'
        long_description = long_description + (' - Box "plot type": Choose whether you want to plot a full average '
                                               'timecourse, an average timecourse grouped by mouse, or a timecourse '
                                               'grouped by session.<br>')
        long_description = long_description + (' - Box "events": Choose the type of trial on which you want to center '
                                               'the analysis (auditory hit, whisker miss, ...).<br>')
        long_description = long_description + (' - Box" main epochs": You can filter the trials chosen based on the '
                                               'epoch and you can use epoch transitions as events.<br><br>')
        long_description = long_description + "Dict saved: All single session results."
        CicadaAnalysis.__init__(self, name="Widefield Time Courses", family_id="Widefield",
                                short_description="Plot widefield activity time course after selected events",
                                long_description=long_description,
                                config_handler=config_handler,
                                accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaWidefieldTimeCourses(config_handler=self.config_handler)
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

        self.add_widefield_acquisitions_dict_for_gui(short_description="Widefield movie (DFF) to use",
                                                     long_description=None,
                                                     arg_name='widefield_acquisition',
                                                     family_widget="Widefield movie to use")

        plots_list = ['widefield_timecourse', 'wf_timecourse_avg_by_mouse', 'wf_timecourse_avg_all_mice']
        self.add_choices_arg_for_gui(arg_name="plots_to_do", choices=plots_list,
                                     default_value="widefield_timecourse", short_description="Plot(s) to do",
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
                                     short_description="use epoch transition as center",
                                     long_description=None, family_widget='main epochs')

        self.add_choices_arg_for_gui(arg_name="trials_list", choices=all_trials,
                                     default_value=False,
                                     short_description="Events",
                                     long_description="Select events for which you want to do widefield analysis",
                                     multiple_choices=True,
                                     family_widget="events")

        self.add_int_values_arg_for_gui(arg_name="widefield_start", min_value=50, max_value=20000,
                                        short_description="Range of widefield (ms) before event",
                                        default_value=100, family_widget="widefield_config")
        self.add_int_values_arg_for_gui(arg_name="widefield_stop", min_value=50, max_value=20000,
                                        short_description="Range of widefield (ms) after event",
                                        default_value=100, family_widget="widefield_config")
        self.add_int_values_arg_for_gui(arg_name="n_frames_averaged", min_value=1, max_value=100,
                                        short_description="number of frames to be averaged in 1 image",
                                        default_value=5, family_widget="widefield_config")

        self.add_int_values_arg_for_gui(arg_name="baseline", min_value=10, max_value=20000,
                                        short_description="Range of baseline (ms)",
                                        long_description="(currently unused — not yet wired into the analysis; "
                                                         "the actual baseline window used for subtraction comes "
                                                         "from 'widefield_start' instead)",
                                        default_value=25, family_widget="widefield_config")

        self.add_bool_option_for_gui(arg_name="remove_baseline", true_by_default=True,
                                     short_description="Do baseline subtraction",
                                     long_description=None, family_widget='widefield_config')

        self.add_choices_arg_for_gui(arg_name="color_map", choices=['hotcold', 'seismic'],
                                     default_value='hotcold',
                                     short_description="Select the color map",
                                     long_description="",
                                     multiple_choices=False,
                                     family_widget="colorbar")

        self.add_field_text_option_for_gui(arg_name="colorbar_scale_min", default_value='-0.005',
                                           short_description="Minimal value for colorbar",
                                           long_description="",
                                           family_widget="colorbar")

        self.add_field_text_option_for_gui(arg_name="colorbar_scale_max", default_value='0.02',
                                           short_description="Maximal value for colorbar",
                                           long_description="",
                                           family_widget="colorbar")

        self.add_field_text_option_for_gui(arg_name="context_diff_c_scale", default_value='0.01',
                                           short_description="Color scale for context difference",
                                           long_description="",
                                           family_widget="colorbar")

        self.add_bool_option_for_gui(arg_name="plot_context_difference", true_by_default=True,
                                     short_description="Plot context difference image (rewarded - non-rewarded)",
                                     long_description="Computes a context difference image using the trial types "
                                                      "specified below. Skipped if either key is absent. Note: "
                                                      "when 'epochs_to_do' is non-empty, the internal data keys "
                                                      "become '{epoch}_{trial_type}' — the default (or any "
                                                      "un-prefixed) 'rewarded_trial_type'/'non_rewarded_trial_type' "
                                                      "value will then never match, and this plot is silently "
                                                      "skipped.",
                                     family_widget='context difference')

        self.add_field_text_option_for_gui(arg_name="rewarded_trial_type",
                                           default_value='rewarded_whisker_hit_trial',
                                           short_description="Trial type for rewarded context (correct trials)",
                                           long_description="",
                                           family_widget="context difference")

        self.add_field_text_option_for_gui(arg_name="non_rewarded_trial_type",
                                           default_value='non-rewarded_whisker_miss_trial',
                                           short_description="Trial type for non-rewarded context (correct trials)",
                                           long_description="",
                                           family_widget="context difference")

        self.add_image_format_package_for_gui()

        self.add_verbose_arg_for_gui()

    def update_original_data(self):
        """
        To be called if the data to analyse should be updated after the analysis has been run.
        :return: boolean: return True if the data has been modified
        """
        pass

    def run_analysis(self, **kwargs):
        """Plot widefield activity time course after selected events."""
        CicadaAnalysis.run_analysis(self, **kwargs)

        widefield_acquisition_dict = kwargs["widefield_acquisition"]

        verbose = kwargs.get("verbose", True)

        plots = kwargs.get('plots_to_do')

        epochs_to_do = kwargs.get("epochs_to_do")
        trials_list = kwargs.get("trials_list")

        widefield_start_in_ms = kwargs.get("widefield_start")
        widefield_start_in_sec = widefield_start_in_ms / 1000
        widefield_stop_in_ms = kwargs.get("widefield_stop")
        widefield_stop_in_sec = widefield_stop_in_ms / 1000

        n_frames_averaged = kwargs.get("n_frames_averaged")

        baseline_in_ms = kwargs.get("baseline")
        baseline_in_sec = baseline_in_ms / 1000

        remove_baseline = kwargs.get('remove_baseline')

        color_map = kwargs.get('color_map')
        color_scale = (float(kwargs.get('colorbar_scale_min')), float(kwargs.get('colorbar_scale_max')))

        context_diff_c_scale = float(kwargs.get('context_diff_c_scale'))

        center_on_epochs = kwargs.get('center_on_epochs')

        plot_context_difference = kwargs.get('plot_context_difference', True)
        rewarded_trial_type = kwargs.get('rewarded_trial_type', 'rewarded_whisker_hit_trial')
        non_rewarded_trial_type = kwargs.get('non_rewarded_trial_type', 'non-rewarded_whisker_miss_trial')

        # ------- figures config part -------
        save_formats = kwargs["save_formats"]
        if save_formats is None:
            save_formats = "pdf"

        dpi = kwargs.get("dpi", 100)

        width_fig = kwargs.get("width_fig")

        height_fig = kwargs.get("height_fig")

        output_path = self.get_results_path()

        n_sessions = len(self._data_to_analyse)

        general_data_dict = dict()
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

            if not trials_list:
                print("no events, no analysis")
                return

            mouse_id = session_data.subject_id
            session_id = session_data.session_id

            if isinstance(widefield_acquisition_dict, dict):
                keys_ophys_dff0 = widefield_acquisition_dict[session_identifier]
            else:
                keys_ophys_dff0 = widefield_acquisition_dict

            # get wf timestamps
            wf_timestamps = session_data.widefield.get_widefield_timestamps(keys_ophys_dff0)
            if wf_timestamps is None or len(wf_timestamps) == 0:
                print("no wf_timestamps, skip")
                continue

            wf_sampling_rate = 1 / np.median(np.diff(wf_timestamps[:200]))
            center_frame_pre = int(widefield_start_in_sec * wf_sampling_rate)
            wf_data = session_data.widefield.get_widefield_dff0_mmap(keys_ophys_dff0)

            # add wf timecourse data to general_data_dict
            if epochs_to_do:
                for epoch in epochs_to_do:
                    if verbose:
                        print(f"Epoch: {epoch}")
                    epoch_times = session_data.behavior.get_behavioral_epochs_times(epoch_name=epoch)

                    # data centered on trials filtered by epoch (epochs and trials from GUI)
                    for trial_type in trials_list:
                        if verbose:
                            print(f"Trial type: {trial_type}")
                        trials = session_data.behavior.get_behavioral_events_times(event_name=trial_type)
                        if trials is None:
                            print(f"No events found for {trial_type}, skipping")
                            continue
                        trials = trials[0, :]
                        trials_kept = filter_events_based_on_epochs(trials, epoch_times)
                        if len(trials_kept) == 0:
                            print("No trials in this condition, skipping")
                            continue

                        epoch_frames = [
                            (find_nearest(wf_timestamps, t - widefield_start_in_sec),
                             find_nearest(wf_timestamps, t + widefield_stop_in_sec))
                            for t in trials_kept if t >= widefield_start_in_sec
                        ]
                        avg_data, center_frame, n_frames_post_stim = get_avg_frames_by_epoch(
                            wf_data, epoch_frames, subtract_baseline=remove_baseline,
                            baseline_end_frame=center_frame_pre)
                        key = f'{epoch}_{trial_type}'
                        general_data_dict.setdefault(mouse_id, {})
                        general_data_dict[mouse_id].setdefault(key, []).append((session_id, avg_data))

                    # data centered on epochs
                    if center_on_epochs:
                        epoch_frames = [
                            (find_nearest(wf_timestamps, t - widefield_start_in_sec),
                             find_nearest(wf_timestamps, t + widefield_stop_in_sec))
                            for t in epoch_times[0] if t >= widefield_start_in_sec
                        ]
                        avg_data, center_frame, n_frames_post_stim = get_avg_frames_by_epoch(
                            wf_data, epoch_frames, subtract_baseline=remove_baseline,
                            baseline_end_frame=center_frame_pre)
                        general_data_dict.setdefault(mouse_id, {})
                        general_data_dict[mouse_id].setdefault(epoch, []).append((session_id, avg_data))

            else:
                # data centered on trials
                for trial_type in trials_list:
                    trials = session_data.behavior.get_behavioral_events_times(event_name=trial_type)
                    if trials is None:
                        print(f"No events found for {trial_type}, skipping")
                        continue
                    trials = trials[0, :]
                    if len(trials) == 0:
                        print("No trials in this condition, skipping")
                        continue

                    epoch_frames = [
                        (find_nearest(wf_timestamps, t - widefield_start_in_sec),
                         find_nearest(wf_timestamps, t + widefield_stop_in_sec))
                        for t in trials if t >= widefield_start_in_sec
                    ]
                    avg_data, center_frame, n_frames_post_stim = get_avg_frames_by_epoch(
                        wf_data, epoch_frames, subtract_baseline=remove_baseline,
                        baseline_end_frame=center_frame_pre)
                    general_data_dict.setdefault(mouse_id, {})
                    general_data_dict[mouse_id].setdefault(trial_type, []).append((session_id, avg_data))

            self.update_progressbar(time_started=self.analysis_start_time, increment_value=100 / n_sessions)

        # save general_data_dict in result_path
        # Note: np.load(..., allow_pickle=True) is required to reload this dict.
        result_path = self.get_results_path()
        print()
        print('Saving results')
        np.save(os.path.join(result_path, f"general_data_dict.npy"), general_data_dict)

        # wf timecourse plots
        if 'widefield_timecourse' in plots:
            print(' ')
            print('Do the plots for each session')
            for mouse_id, mouse_trial_avg_data in general_data_dict.items():
                for key, data in mouse_trial_avg_data.items():
                    for session_data in data:
                        save_path = os.path.join(output_path, f"{mouse_id}", f"{session_data[0]}")
                        if verbose:
                            print(f'Session: {session_data[0]}')
                        plot_wf_avg(session_data[1], save_path,
                                    n_frames_post_stim, n_frames_averaged, key,
                                    center_frame, f"{key}", save_formats, subdir=f"{key}_wf_timecourse",
                                    do_single_plots=False, c_scale=color_scale, colormap=color_map,
                                    img_size=width_fig, dpi=dpi)

        # wf timecourse avg plots
        if 'wf_timecourse_avg_by_mouse' in plots or 'wf_timecourse_avg_all_mice' in plots:
            if verbose:
                print()
                print('Do the average plots')
            # general_data_dict contains every key data grouped my mouse
            all_mice = []

            for mouse_id, mouse_trial_avg_data in general_data_dict.items():
                avg_mice_data = {}
                for key, data in mouse_trial_avg_data.items():
                    data = np.stack([x[1] for x in data])
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        avg_data = np.nanmean(data, axis=0)

                    # wf tc avg by mouse plots
                    if 'wf_timecourse_avg_by_mouse' in plots:
                        if verbose:
                            print(f"Do the {key} plots for mouse {mouse_id}")
                        figure_name = f'{mouse_id}_{key}'
                        plot_wf_avg(avg_data, output_path, n_frames_post_stim, n_frames_averaged, key,
                                    center_frame, figure_name, save_formats, subdir=mouse_id, do_single_plots=False,
                                    c_scale=color_scale, colormap=color_map, img_size=width_fig, dpi=dpi)

                    avg_mice_data[key] = avg_data
                all_mice.append(avg_mice_data)

            # all_mice is a list of dicts that contain every key data grouped my mouse and averaged by mouse
            general_data_dict_group_by_key = {key: [] for key in all_mice[0].keys()}

            for avg_mice_data in all_mice:
                for key, avg_data in avg_mice_data.items():
                    general_data_dict_group_by_key[key].append(avg_data)

            # general_data_dict_group_by_key contains every key data averaged by mouse
            for key, data in general_data_dict_group_by_key.items():
                if verbose:
                    print()
                    print('Do the averaged across mice')
                    print(f"Key: {key}, Data shape : {len(data)} mice, with {data[0].shape} shape")
                data = np.stack(data)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    avg_data = np.nanmean(data, axis=0)

                # wf tc avg by trial plots
                if 'wf_timecourse_avg_all_mice' in plots:
                    figure_name = f'all_mice_{key}'
                    plot_wf_avg(avg_data, output_path, n_frames_post_stim, n_frames_averaged, key, center_frame,
                                figure_name, save_formats, c_scale=color_scale, colormap=color_map, subdir=key,
                                do_single_plots=False, img_size=width_fig, dpi=dpi)

        # Context difference image: rewarded average minus non-rewarded average.
        # Rewarded / non-rewarded trial types are detected automatically from the trial type names
        # (keys containing 'rewarded' but not 'non' → rewarded context; keys containing 'non-rewarded' → non-rewarded).
        if plot_context_difference:
            mice = list(general_data_dict.keys())
            diff_activity_dict = dict()

            for mouse in mice:
                mouse_data = general_data_dict[mouse]
                if rewarded_trial_type not in mouse_data or non_rewarded_trial_type not in mouse_data:
                    if verbose:
                        print(f"Mouse {mouse}: skipping context difference "
                              f"('{rewarded_trial_type}' or '{non_rewarded_trial_type}' "
                              f"not found in {list(mouse_data.keys())})")
                    continue

                rwd_sessions = mouse_data[rewarded_trial_type]
                non_rwd_sessions = mouse_data[non_rewarded_trial_type]
                n_sessions_mouse = min(len(rwd_sessions), len(non_rwd_sessions))
                diff_activity_dict[mouse] = []
                for s in range(n_sessions_mouse):
                    session_id = rwd_sessions[s][0]
                    diff_activity_dict[mouse].append([session_id, rwd_sessions[s][1] - non_rwd_sessions[s][1]])

            if not diff_activity_dict:
                if verbose:
                    print("No context difference data to save or plot.")
            else:
                # Note: np.load(..., allow_pickle=True) is required to reload this dict.
                np.save(os.path.join(result_path, f"context_diff_data_dict.npy"), diff_activity_dict)

                # Go to general average
                # First average across sessions for each mouse
                mice_with_data = list(diff_activity_dict.keys())
                mouse_avg_diff_dict = dict()
                for mouse in mice_with_data:
                    data = diff_activity_dict[mouse]
                    data = np.stack([x[1] for x in data])
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", category=RuntimeWarning)
                        avg_data = np.nanmean(data, axis=0)
                    mouse_avg_diff_dict[mouse] = avg_data

                # Average across mice
                general_avg = np.stack([mouse_avg_diff_dict[mouse] for mouse in mice_with_data])
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    full_avg_data = np.nanmean(general_avg, axis=0)
                key = 'context_difference'
                figure_name = f'all_mice_{key}'
                plot_wf_avg(full_avg_data, output_path, n_frames_post_stim, n_frames_averaged, key, center_frame,
                            figure_name, save_formats, subdir=key, do_single_plots=False,
                            halfrange=context_diff_c_scale, colormap='seismic', dpi=dpi)

        print()
        print(f"Widefield Timecourse analysis run in {time() - self.analysis_start_time} sec")
