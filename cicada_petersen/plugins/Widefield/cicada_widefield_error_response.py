import os
import numpy as np
import pandas as pd
import seaborn as sns

from cicada_analysis import CicadaAnalysis
from cicada_analysis.cicada_tools.display.core_plots import save_figure
from cicada_petersen.tools.behavior_utils import (
    get_n_trials_per_block_from_table,
    build_standard_behavior_table,
    get_standard_single_session_table,
)
from cicada_analysis.cicada_tools.core import print_info_dict
from cicada_analysis.cicada_tools.imaging import build_psth_dataframe


class CicadaWidefieldErrorResponse(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        long_description = '<p align="center"><b>Widefield Error Response</b></p>'

        CicadaAnalysis.__init__(self, name="Widefield Error Response", family_id="Widefield",
                                short_description="Response to error at whisker trials",
                                long_description=long_description,
                                config_handler=config_handler, accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaWidefieldErrorResponse(config_handler=self.config_handler)
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

        cuts_list = ['no_cut', 'manual_cutting', 'adaptive_cutting', 'from_yaml']
        self.add_choices_arg_for_gui(arg_name="cut_session", choices=cuts_list,
                                     default_value="no_cut", short_description="Cut(s) to do",
                                     multiple_choices=False,
                                     family_widget="session_len")

        self.add_open_file_dialog_arg_for_gui(arg_name='yaml_path', extensions=['yaml', 'yml'], mandatory=False,
                                              short_description='Select path to yaml file',
                                              long_description='Path to yaml file specifying how to cut each session',
                                              key_names='YAML', family_widget='session_len')

        self.add_int_values_arg_for_gui(arg_name="first_trial", min_value=0, max_value=100,
                                        short_description="Manual: First trail to take",
                                        long_description="",
                                        default_value=0, family_widget="session_len")

        self.add_int_values_arg_for_gui(arg_name="last_trial", min_value=100, max_value=700,
                                        short_description="Manual: Last trial to take",
                                        long_description="",
                                        default_value=500, family_widget="session_len")

        all_cell_types = []
        for data_to_analyse in self._data_to_analyse:
            all_cell_types.extend(data_to_analyse.calcium_imaging.get_all_cell_types())
        all_cell_types = list(set(all_cell_types))
        self.add_choices_arg_for_gui(arg_name="cell_types_to_do", choices=all_cell_types,
                                     default_value=False, short_description="cell_types_to_do",
                                     multiple_choices=True,
                                     family_widget="cell type")

        plots_list = ['wf_psth_session_plot', 'wf_psth_mouse_plot', 'wf_psth_full_plot']
        self.add_choices_arg_for_gui(arg_name="plots_to_do", choices=plots_list,
                                     default_value="wf_psth_full_plot", short_description="Plot(s) to do",
                                     multiple_choices=True,
                                     family_widget="plot type")

        alignment_opt = ['stim. time', 'lick']
        self.add_choices_arg_for_gui(arg_name="alignment", choices=alignment_opt,
                                     default_value="stim. time", short_description="Alignment mode",
                                     multiple_choices=False,
                                     family_widget="psth_config")

        self.add_int_values_arg_for_gui(arg_name="psth_start", min_value=50, max_value=20000,
                                        short_description="Range of psth (ms) before event",
                                        default_value=100, family_widget="psth_config")
        self.add_int_values_arg_for_gui(arg_name="psth_stop", min_value=50, max_value=20000,
                                        short_description="Range of psth (ms) after event",
                                        default_value=200, family_widget="psth_config")

        self.add_bool_option_for_gui(arg_name="subtract_baseline", true_by_default=True,
                                     short_description="Subtract baseline",
                                     long_description=None, family_widget='psth_config')

        self.add_image_format_package_for_gui()

        self.add_verbose_arg_for_gui()

    def update_original_data(self):
        """
        To be called if the data to analyse should be updated after the analysis has been run.
        :return: boolean: return True if the data has been modified
        """
        pass

    def run_analysis(self, **kwargs):
        """Response to error at whisker trials."""
        CicadaAnalysis.run_analysis(self, **kwargs)

        # Get PARAMS from GUI #

        roi_response_series_dict = kwargs["roi_response_series"]

        cell_types_to_do = kwargs["cell_types_to_do"]

        plots = kwargs.get('plots_to_do')

        alignment = kwargs.get('alignment')

        time_range = (kwargs.get("psth_start") / 1000, kwargs.get("psth_stop") / 1000)

        subtract_baseline = kwargs.get("subtract_baseline", False)

        verbose = kwargs.get("verbose", True)

        cut_session = kwargs.get("cut_session")
        yaml_file_path = kwargs.get('yaml_path')
        first_trial = kwargs.get("first_trial")
        last_trial = kwargs.get("last_trial")

        # ----------- END OF PARAMS -------------- #

        behavior_data_table = build_standard_behavior_table(nwb_list=self._data_to_analyse, cut_session=cut_session,
                                                            session_cutoffs=[first_trial, last_trial],
                                                            yaml_file_path=yaml_file_path,
                                                            result_path=self.get_results_path())

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

            if isinstance(roi_response_series_dict, dict):
                roi_response_serie_info = roi_response_series_dict[session_identifier]
            else:
                roi_response_serie_info = roi_response_series_dict

            # get psth timestamps and data
            activity_ts = session_data.calcium_imaging.get_roi_response_serie_timestamps(roi_response_serie_info)
            if activity_ts is None or len(activity_ts) == 0:
                print(f'Session {session_id} has no activity_ts - skipping.')
                continue
            activity = session_data.calcium_imaging.get_roi_response_serie_data(roi_response_serie_info)
            if activity is None or len(activity) == 0:
                print(f'Session {session_id} has no rrs - skipping.')
                continue

            behavior_type, behavior_day = session_data.petersen.get_bhv_type_and_training_day_index()
            cell_type_dict = session_data.calcium_imaging.get_cell_indices_by_cell_type(roi_response_serie_info)
            n_cells = activity.shape[0]
            cell_type_array = np.full(n_cells, 'na', dtype=object)
            if cell_type_dict:
                for ct, rois in cell_type_dict.items():
                    if ct in cell_types_to_do:
                        cell_type_array[rois] = ct

            # Get session table
            session_table, switches, block_size = get_standard_single_session_table(
                behavior_data_table, session=session_id,
                block_sizes={session_id: session_data.petersen.get_experimental_block_size()})
            # Keep only whisker trials and count how many error per block
            whisker_session_table = session_table.loc[session_table.trial_type == 'whisker_trial']
            whisker_session_table = whisker_session_table.reset_index()
            whisker_session_table = whisker_session_table.assign(incorrect_choice=~whisker_session_table.correct_choice)
            # Compute number of whisker trials per block dynamically (fallback = 8)
            n_whisker_per_block = get_n_trials_per_block_from_table(session_table, trial_type='whisker_trial')
            cumsum_error_block = whisker_session_table.groupby(
                whisker_session_table.index // n_whisker_per_block)['incorrect_choice'].cumsum()
            whisker_session_table = whisker_session_table.assign(cumsum_error_block=cumsum_error_block)
            whisker_session_table.loc[whisker_session_table.correct_choice == True, 'cumsum_error_block'] = 0

            contexts = whisker_session_table.context.unique()
            n_errors = np.sort(whisker_session_table.cumsum_error_block.unique())
            for context in contexts:
                if verbose:
                    if context == 1:
                        print('Rewarded context')
                    else:
                        print('Non-rewarded context')
                for n_error in n_errors:
                    if alignment == 'stim. time':
                        time_column = 'whisker_stim_time'
                    else:
                        time_column = 'lick_time'
                    if ((context == 1) and (n_error != 0)) or ((context == 0) and (n_error == 0)):
                        continue
                    trials_kept = whisker_session_table.loc[((whisker_session_table.context == context) &
                                                            (whisker_session_table.cumsum_error_block == n_error)), time_column]
                    if trials_kept.isnull().all():
                        print('No trial kept in this condition')
                        continue
                    tmp_table = build_psth_dataframe(
                        data=activity, event_timestamps=np.array(trials_kept),
                        frame_timestamps=activity_ts, window_s=time_range,
                        subtract_baseline=subtract_baseline,
                        trial_type='whisker_trial', session_id=session_id, mouse_id=mouse_id,
                        extra_metadata={'cell_type': cell_type_array,
                                        'behavior_type': behavior_type,
                                        'behavior_day': behavior_day})
                    if cell_type_dict:
                        tmp_table = tmp_table[tmp_table['cell_type'] != 'na']
                    if context == 0:
                        epoch = 'Non-Rewarded'
                    else:
                        epoch = 'Rewarded'
                    tmp_table['epoch'] = epoch
                    tmp_table['n_errors'] = n_error
                    dfs_list.append(tmp_table)
        dfs_list = pd.concat(dfs_list, ignore_index=True)

        saving_folder = self.get_results_path()

        # Do the plots
        print(' ')
        print('Doing some plots')
        if 'wf_psth_session_plot' in plots:
            print(' ')
            print('Plot single session figures')
            for session_id in dfs_list.session_id.unique():
                session_df = dfs_list.loc[dfs_list.session_id == session_id]
                mouse_id = session_df.mouse_id.unique()[0]
                fig = sns.relplot(data=session_df, x='time', y='activity',
                                  col='epoch', row='cell_type',
                                  hue='n_errors', kind='line')
                save_figure(results_path=os.path.join(saving_folder, str(mouse_id)),
                                   save_formats=['pdf'],
                                   figure=fig, figname=f'{session_id}_whisker_error_trials')

        # by session average
        dfs_list_session = dfs_list.groupby(["mouse_id", "session_id", "trial_type", "epoch", "n_errors",
                                             "behavior_day", "behavior_type", "roi", "cell_type", "time"],
                                            as_index=False).agg('mean')
        # plot for each mouse
        if 'wf_psth_mouse_plot' in plots:
            mouse_list = pd.unique(dfs_list.mouse_id)
            for mouse in mouse_list:
                if verbose:
                    print(' ')
                    print(f'Do the mouse plot: {mouse}')
                mouse_table = dfs_list_session.loc[dfs_list_session['mouse_id'] == mouse]
                fig = sns.relplot(data=mouse_table, x='time', y='activity', col='epoch', row='cell_type',
                                  hue='n_errors', kind='line')
                path = os.path.join(saving_folder, mouse)
                if not os.path.exists(path):
                    os.makedirs(path)
                save_figure(results_path=str(path), save_formats=['pdf'],
                                   figure=fig, figname=f'{mouse}_whisker_error_trials_average')

        # average for each mouse across sessions
        mice_avg_data = dfs_list_session.drop(['session_id', 'behavior_day'], axis=1)
        mice_avg_data = mice_avg_data.groupby(["mouse_id", "trial_type", "epoch", "n_errors",
                                               "behavior_type", "roi", "cell_type", "time"],
                                              as_index=False).agg('mean')
        # plot general average
        if 'wf_psth_full_plot' in plots:
            fig = sns.relplot(data=mice_avg_data, x='time', y='activity', col='epoch', row='cell_type', hue='n_errors',
                              kind='line')
            save_figure(results_path=saving_folder, save_formats=['pdf'],
                               figure=fig, figname='whisker_error_trials')
