import gc
import os
import h5py
import numpy as np
from time import time
import imageio as iio
import tifffile as tiff

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.core import print_info_dict, find_nearest, filter_events_based_on_epochs
from cicada_analysis.cicada_tools.imaging import get_avg_frames_by_epoch


class CicadaWidefieldMovieAverage(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        long_description = '<p align="center"><b>Widefield Movie Average</b></p>'
        long_description = long_description + 'Main parameters:<br>'
        long_description = long_description + (' - Box "Analysis type": Choose the type of analysis you want to perform'
                                               ' (Widefield movie average or save f0).<br>')
        long_description = long_description + (' - Box "events": Choose the type of trial on which you want to center '
                                               'the analysis (auditory hit, whisker miss, ...).<br>')
        long_description = long_description + (' - Box" main epochs": You can filter the trials chosen based on the '
                                               'epoch and you can use epoch transitions as events.<br><br>')
        long_description = long_description + "Files saved:<br>"
        long_description = long_description + (" - Widefield movie average: Average movies centered on the events "
                                               "selected.<br>")
        long_description = long_description + " - Save f0: Average image of fluorescence (baseline)<br>"
        CicadaAnalysis.__init__(self, name="Widefield Movie Average", family_id="Widefield",
                                short_description="Averaged widefield movie centered on selected events",
                                long_description=long_description,
                                config_handler=config_handler, accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaWidefieldMovieAverage(config_handler=self.config_handler)
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

        analysis_list = ['wf_movie_avg', 'save_f0']
        self.add_choices_arg_for_gui(arg_name="analysis_to_do", choices=analysis_list,
                                     default_value="wf_movie_avg", short_description="Analysis to do",
                                     multiple_choices=True,
                                     family_widget="Analysis type")

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

        self.add_int_values_arg_for_gui(arg_name="widefield_start_in_ms", min_value=50, max_value=20000,
                                        short_description="Window before event (ms)",
                                        default_value=100, family_widget="Movie average config")
        self.add_int_values_arg_for_gui(arg_name="widefield_stop_in_ms", min_value=50, max_value=20000,
                                        short_description="Window after event (ms)",
                                        default_value=200, family_widget="Movie average config")
        self.add_bool_option_for_gui(arg_name="subtract_baseline", true_by_default=True,
                                     short_description="Subtract baseline",
                                     long_description=None, family_widget='Movie average config')

        self.add_bool_option_for_gui(arg_name="verbose", true_by_default=True,
                                     short_description="Verbose",
                                     long_description=None, family_widget='Verbose')

    def update_original_data(self):
        """
        To be called if the data to analyse should be updated after the analysis has been run.
        :return: boolean: return True if the data has been modified
        """
        pass

    def run_analysis(self, **kwargs):
        """Averaged widefield movie centered on selected events."""
        CicadaAnalysis.run_analysis(self, **kwargs)

        widefield_acquisition_dict = kwargs["widefield_acquisition"]

        verbose = kwargs.get("verbose", True)

        epochs = kwargs.get("epochs_to_do")
        events_names = kwargs.get("trials_list")

        widefield_start_in_ms = kwargs.get("widefield_start_in_ms")
        widefield_start_in_sec = widefield_start_in_ms / 1000
        widefield_stop_in_ms = kwargs.get("widefield_stop_in_ms")
        widefield_stop_in_sec = widefield_stop_in_ms / 1000

        center_on_epochs = kwargs.get('center_on_epochs')

        analysis_to_do = kwargs.get('analysis_to_do')

        subtract_baseline = kwargs.get('subtract_baseline')

        results_path = self.get_results_path()

        n_sessions = len(self._data_to_analyse)

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

            # Save f0 analysis
            if 'save_f0' in analysis_to_do:
                raw_f_file = session_data.widefield.get_widefield_raw_acquisition_path(acquisition_name='F')[0]
                print(f"Find F file : {raw_f_file}")
                print("Open F file to compute F0 on full recording ... ")
                f_file = h5py.File(raw_f_file, 'r')
                f = f_file['F'][:]
                print("Compute F0")
                winsize = f.shape[0]
                f0 = np.nanpercentile(f[:winsize], 5, axis=0)
                print(f"Save F0 image in {os.path.dirname(raw_f_file)}")
                iio.imwrite(os.path.join(os.path.dirname(raw_f_file), 'F0.tiff'), f0)
                f_file.close()
                del f
                gc.collect()

            # Movie average analysis
            if 'wf_movie_avg' in analysis_to_do:
                if not events_names:
                    print("no events, no analysis")
                    return

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

                if epochs:
                    for epoch in epochs:
                        epoch_times = session_data.behavior.get_behavioral_epochs_times(epoch_name=epoch)

                        # data centered on trials filtered by epoch (epochs and trials from GUI)
                        for events_name in events_names:
                            trials = session_data.behavior.get_behavioral_events_times(event_name=events_name)
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
                                wf_data, epoch_frames, subtract_baseline=subtract_baseline,
                                baseline_end_frame=center_frame_pre)
                            save_path = os.path.join(results_path, f"{mouse_id}", f"{session_id}")
                            os.makedirs(save_path, exist_ok=True)
                            tiff.imwrite(os.path.join(save_path, f'{events_name}_{epoch}.tiff'), avg_data)

                        if center_on_epochs:
                            # data centered on epoch transitions
                            epoch_frames = [
                                (find_nearest(wf_timestamps, t - widefield_start_in_sec),
                                 find_nearest(wf_timestamps, t + widefield_stop_in_sec))
                                for t in epoch_times[0] if t >= widefield_start_in_sec
                            ]
                            avg_data, center_frame, n_frames_post_stim = get_avg_frames_by_epoch(
                                wf_data, epoch_frames, subtract_baseline=subtract_baseline,
                                baseline_end_frame=center_frame_pre)
                            save_path = os.path.join(results_path, f"{mouse_id}", f"{session_id}")
                            os.makedirs(save_path, exist_ok=True)
                            tiff.imwrite(os.path.join(save_path, f'to_{epoch}.tiff'), avg_data)

                else:
                    # data centered on trials
                    for events_name in events_names:
                        trials = session_data.behavior.get_behavioral_events_times(event_name=events_name)
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
                            wf_data, epoch_frames, subtract_baseline=subtract_baseline,
                            baseline_end_frame=center_frame_pre)
                        save_path = os.path.join(results_path, f"{mouse_id}", f"{session_id}")
                        os.makedirs(save_path, exist_ok=True)
                        tiff.imwrite(os.path.join(save_path, f'{session_id}_{events_name}.tiff'), avg_data)

            self.update_progressbar(time_started=self.analysis_start_time, increment_value=100 / n_sessions)

        print(f"Widefield movie average run in {time() - self.analysis_start_time} sec")
