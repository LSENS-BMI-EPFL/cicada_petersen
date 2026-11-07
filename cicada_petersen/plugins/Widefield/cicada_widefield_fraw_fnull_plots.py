import h5py
import numpy as np
import matplotlib.pyplot as plt

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.core import print_info_dict
from cicada_analysis.cicada_tools.display.core_plots import save_figure, BREWER_COLORS


class CicadaWidefieldFrawFnullPlots(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        long_description = '<p align="center"><b>Plots Fraw & F0</b></p>'
        long_description = 'Plot F raw and F0 for WF data'
        CicadaAnalysis.__init__(self, name="Plots Fraw & F0", family_id="Widefield",
                                short_description="Plots raw fluorescence and F0 for specific regions",
                                long_description=long_description,
                                config_handler=config_handler,
                                accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaWidefieldFrawFnullPlots(config_handler=self.config_handler)
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

        self.add_segmentation_arg_for_gui()

        self.add_roi_response_series_arg_for_gui(short_description=" ", long_description=None,
                                                 family_widget="Neural activity to use")

        self.add_int_values_arg_for_gui(arg_name="stop_time_s", min_value=60, max_value=36000,
                                        short_description="Display window end (s)",
                                        long_description="End of the display window in seconds from recording start. "
                                                         "Clipped to recording length if larger.",
                                        default_value=7200, family_widget="Display config")

        self.add_image_format_package_for_gui()

        self.add_verbose_arg_for_gui()

    def update_original_data(self):
        """
        To be called if the data to analyse should be updated after the analysis has been run.
        :return: boolean: return True if the data has been modified
        """
        pass

    def run_analysis(self, **kwargs):
        """Plots raw fluorescence and F0 for specific regions."""
        CicadaAnalysis.run_analysis(self, **kwargs)

        segmentation_dict = kwargs['segmentation']

        roi_response_series_dict = kwargs["roi_response_series"]

        save_formats = kwargs["save_formats"]
        if save_formats is None:
            save_formats = ["pdf"]

        stop_time_s = kwargs.get("stop_time_s", 7200)
        verbose = kwargs.get("verbose", True)

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

            # Get WF raw data path
            wf_raw_f_path = session_data.widefield.get_widefield_raw_acquisition_path(acquisition_name='F')[0]

            # Get info for segmentation and ROIs
            if isinstance(segmentation_dict, dict):
                segmentation_info = segmentation_dict[session_identifier]
            else:
                segmentation_info = segmentation_dict
            if isinstance(roi_response_series_dict, dict):
                roi_response_serie_info = roi_response_series_dict[session_identifier]
            else:
                roi_response_serie_info = roi_response_series_dict

            # Get WF timestamps
            wf_ts = session_data.calcium_imaging.get_roi_response_serie_timestamps(roi_response_serie_info)
            if wf_ts is None or len(wf_ts) == 0:
                print(f'Session {session_identifier} has no activity_ts - skipping.')
                continue

            # Get context timestamps
            rewarded_epochs = session_data.behavior.get_behavioral_epochs_times(epoch_name='rewarded')
            non_rewarded_epochs = session_data.behavior.get_behavioral_epochs_times(epoch_name='non-rewarded')

            # Get contours
            pixels_masks = session_data.calcium_imaging.get_pixel_mask(segmentation_info=segmentation_info)
            pixel_mask_list = [pixels_masks[cell] for cell in range(len(pixels_masks))]
            image_masks = session_data.calcium_imaging.get_image_mask(segmentation_info=segmentation_info)

            # Extract area names
            area_dict = session_data.calcium_imaging.get_cell_indices_by_cell_type(roi_serie_keys=roi_response_serie_info)
            sorted_areas = sorted(area_dict, key=area_dict.get)

            # Extract F raw as a dataset
            F_dset = h5py.File(wf_raw_f_path, 'r')
            data = F_dset['F']

            # Get RAM size (cross-platform)
            try:
                import psutil
                ram_size = psutil.virtual_memory().total / (1024 ** 3)
            except ImportError:
                ram_size = 0  # conservative fallback: use per-pixel loading
            print(f"Total RAM: {np.round(ram_size, 2)} GB")

            # Build raw traces from pixels within ROIs.
            # If RAM < 150 GB load pixel by pixel to avoid OOM; otherwise load full movie at once.
            raw_traces = np.zeros((len(sorted_areas), data.shape[0]))
            if ram_size < 150:
                for roi_idx, roi_name in enumerate(sorted_areas):
                    pix_mask = pixel_mask_list[roi_idx]
                    roi_data = np.zeros((len(pix_mask), data.shape[0]))
                    for index, pixel in enumerate(pix_mask):
                        roi_data[index, :] = data[:, pixel[0], pixel[1]]
                    raw_traces[roi_idx, :] = np.nanmean(roi_data, axis=0)
            else:
                movie_data = data[:]
                for roi_idx, roi_name in enumerate(sorted_areas):
                    mask = image_masks[roi_idx]
                    raw_traces[roi_idx, :] = np.nanmean(movie_data[:, mask.astype(bool)], axis=1)
                del movie_data
            if verbose:
                print('Raw traces obtained')

            # Get f0 image and f0 average for each ROI
            f0_img = session_data.widefield.get_widefield_f0(acquisition_names=["F0 image", "F0"])
            f0_traces = np.zeros((len(sorted_areas), 1))
            for roi_idx, roi_name in enumerate(sorted_areas):
                img_mask = image_masks[roi_idx]
                f0_traces[roi_idx, 0] = np.nanmean(f0_img[img_mask.astype(bool)])
            if verbose:
                print('F0 values obtained')

            # Make figure
            fig, ax = plt.subplots(1, 1, figsize=(20, 10))
            wf_sampling_rate = 1 / np.median(np.diff(wf_ts))
            start = 0
            stop = min(int(stop_time_s * wf_sampling_rate), raw_traces.shape[1] - 1)
            for area_idx, area in enumerate(sorted_areas):
                color = BREWER_COLORS[area_idx % len(BREWER_COLORS)]
                ax.plot(wf_ts[start: stop], raw_traces[area_idx, start: stop], c=color, label=area)
                ax.axhline(y=f0_traces[area_idx], xmin=0, xmax=1, c=color, linestyle='--', linewidth=0.8)
            for i in range(rewarded_epochs.shape[1]):
                if (rewarded_epochs[0, i] > wf_ts[start]) and (rewarded_epochs[1, i] < wf_ts[stop]):
                    ax.axvspan(rewarded_epochs[0, i], rewarded_epochs[1, i], alpha=0.5, color='green')
                else:
                    if rewarded_epochs[0, i] < wf_ts[start]:
                        ax.axvspan(0, rewarded_epochs[1, i], alpha=0.5, color='green')
                    elif rewarded_epochs[1, i] > wf_ts[stop]:
                        ax.axvspan(rewarded_epochs[0, i], wf_ts[stop], alpha=0.5, color='green')
                    else:
                        continue
            for i in range(non_rewarded_epochs.shape[1]):
                if (non_rewarded_epochs[0, i] > wf_ts[start]) and (non_rewarded_epochs[1, i] < wf_ts[stop]):
                    ax.axvspan(non_rewarded_epochs[0, i], non_rewarded_epochs[1, i], alpha=0.5, color='darkmagenta')
                else:
                    if non_rewarded_epochs[0, i] < wf_ts[start]:
                        ax.axvspan(0, non_rewarded_epochs[1, i], alpha=0.5, color='darkmagenta')
                    elif non_rewarded_epochs[1, i] > wf_ts[stop]:
                        ax.axvspan(non_rewarded_epochs[0, i], wf_ts[stop], alpha=0.5, color='darkmagenta')
                    else:
                        continue
            ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
            ax.spines[['right', 'top']].set_visible(False)
            ax.set_title(f'F raw {session_identifier}')
            ax.set_ylabel('F')
            ax.set_xlabel('Time (seconds)')
            save_figure(results_path=self.get_results_path(), save_formats=save_formats,
                               figure=fig, figname=f'{session_identifier}_Fraw')

            self.update_progressbar(time_started=self.analysis_start_time,
                                    increment_value=100 / len(self._data_to_analyse))