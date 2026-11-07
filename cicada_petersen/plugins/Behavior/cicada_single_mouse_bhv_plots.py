import os

from cicada_analysis import CicadaAnalysis
from cicada_petersen.tools.behavior_utils import build_standard_behavior_table
from cicada_petersen.tools.behavior_plots import (
    set_seaborn_context,
    plot_single_session,
    plot_single_mouse_across_days,
    plot_single_mouse_across_context_days,
    plot_single_session_time_to_switch,
    plot_single_mouse_time_to_switch,
    plot_single_mouse_psychometrics_across_days,
    plot_single_mouse_reaction_time_across_days,
)


class CicadaSingleMouseBhvPlots(CicadaAnalysis):
    def __init__(self, config_handler=None):
        """
        """
        long_description = ('<p align="center"><b>Plot mouse behavior</b></p><br>'
                            'Produce behavior plots for single session and single mouse.<br><br>')

        CicadaAnalysis.__init__(self, name="Single mouse behavior", family_id="Behavior",
                                short_description="Plots single mouse and single session behavior",
                                long_description=long_description,
                                config_handler=config_handler,
                                accepted_data_formats=["CI_DATA"])

    def copy(self):
        """
        Make a copy of the analysis
        Returns:

        """
        analysis_copy = CicadaSingleMouseBhvPlots(config_handler=self.config_handler)
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

        for session_data in self._data_to_analyse:
            if not session_data.behavior.has_trial_table():
                self.invalid_data_help = f"No trial table in session {session_data.identifier}"
                return False
            # the plots describe the whisker task: they read its trial columns
            columns = session_data.behavior.get_trial_table().columns
            missing = [c for c in ('trial_type', 'lick_flag') if c not in columns]
            if missing:
                self.invalid_data_help = f"The trial table of {session_data.identifier} has no {missing} " \
                                         f"column (whisker task trials)"
                return False

        return True

    def setup_parameters(self):
        """

        Returns:

        """
        CicadaAnalysis.setup_parameters(self)

        plots_list = ['single_session', 'across_days', 'psycho', 'across_context_days',
                      'context_switch', 'reaction_time']
        self.add_choices_arg_for_gui(arg_name="plots_to_do", choices=plots_list,
                                     default_value="single_session", short_description="Plot(s) to do",
                                     multiple_choices=True,
                                     family_widget="Plot type")

        self.add_color_arg_for_gui(arg_name="auditory_hit_color", default_value=(0.13, 0.37, 0.66, 1.),
                                   short_description="Color of auditory hit trials",
                                   long_description=None, family_widget="Trial colors")
        self.add_color_arg_for_gui(arg_name="auditory_miss_color", default_value=(0, 1, 1, 1.),
                                   short_description="Color of auditory miss trials",
                                   long_description=None, family_widget="Trial colors")
        self.add_color_arg_for_gui(arg_name="whisker_hit_color", default_value=(0.14, 0.52, 0.26, 1.),
                                   short_description="Color of whisker hit trials",
                                   long_description=None, family_widget="Trial colors")
        self.add_color_arg_for_gui(arg_name="whisker_miss_color", default_value=(0.84, 0.1, 0.11, 1.),
                                   short_description="Color of whisker miss trials",
                                   long_description=None, family_widget="Trial colors")
        self.add_color_arg_for_gui(arg_name="nostim_miss_color", default_value=(0.8, 0.8, 0.8, 1.),
                                   short_description="Color of correct rejection trials",
                                   long_description=None, family_widget="Trial colors")
        self.add_color_arg_for_gui(arg_name="nostim_hit_color", default_value=(0, 0, 0, 1.),
                                   short_description="Color of false alarm trials",
                                   long_description=None, family_widget="Trial colors")

        self.add_color_arg_for_gui(arg_name="rewarded_context_color", default_value=(0, 0.5, 0, 0.25),
                                   short_description="Background color for rewarded context",
                                   long_description=None, family_widget="Context color")
        self.add_color_arg_for_gui(arg_name="non_rewarded_context_color", default_value=(0.7, 0.13, 0.13, 0.25),
                                   short_description="Background color for non-rewarded context",
                                   long_description=None, family_widget="Context color")

        self.add_color_arg_for_gui(arg_name="bckgrnd_color", default_value=(1, 1, 1, 1.),
                                   short_description="Background color for figure",
                                   long_description=None, family_widget="Figure colors")
        self.add_color_arg_for_gui(arg_name="axes_color", default_value=(0, 0, 0, 1.),
                                   short_description="Color axe label for figure",
                                   long_description=None, family_widget="Figure colors")

        context_hue_list = ['background noise', 'rewarded or not']
        self.add_choices_arg_for_gui(arg_name="context_hue", choices=context_hue_list,
                                     default_value="rewarded or not", short_description="Group for context plot",
                                     multiple_choices=False,
                                     family_widget="Context")
        context_hue_list = ['strip-plot', 'box-plot', 'point-plot']
        self.add_choices_arg_for_gui(arg_name="context_plot_type", choices=context_hue_list,
                                     default_value='point-plot', short_description="Type of plot for context hit rates "
                                                                                   "across days",
                                     multiple_choices=False,
                                     family_widget="Context")
        self.add_bool_option_for_gui(arg_name="show_single_bloc", true_by_default=False,
                                     short_description="Show each bloc in plot if point-plot is selected",
                                     family_widget="Context")

        whisker_counts = ['full block', 'defined']
        self.add_choices_arg_for_gui(arg_name="whisker_switch", choices=whisker_counts,
                                     default_value='defined', short_description="Counting whisker trials around "
                                                                                "transitions",
                                     multiple_choices=False,
                                     family_widget="Context switch")
        self.add_int_values_arg_for_gui(arg_name="n_whisker_trials", min_value=1, max_value=8,
                                        short_description="Number of whisker trials to plot around context switch",
                                        long_description="",
                                        default_value=4, family_widget="Context switch")

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

        self.add_image_format_package_for_gui()

        sns_contexts = ['paper', 'notebook', 'talk', 'poster']
        self.add_choices_arg_for_gui(arg_name="sns_context", choices=sns_contexts,
                                     default_value="poster", short_description="Seaborn context",
                                     multiple_choices=False,
                                     family_widget="Image Format")

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

        # -----------------TAKE PARAMS FROM GUI----------------------- #

        verbose = kwargs.get("verbose", False)

        plots = kwargs.get('plots_to_do')

        aud_hit_color = kwargs.get("auditory_hit_color")
        aud_miss_color = kwargs.get("auditory_miss_color")
        wh_hit_color = kwargs.get("whisker_hit_color")
        wh_miss_color = kwargs.get("whisker_miss_color")
        cr_color = kwargs.get("nostim_miss_color")
        fa_color = kwargs.get("nostim_hit_color")

        context_hue = kwargs.get("context_hue")
        context_plot_type = kwargs.get("context_plot_type")
        show_single_bloc = kwargs.get("show_single_bloc")

        whisker_switch = kwargs.get("whisker_switch")
        n_whisker_trials = kwargs.get("n_whisker_trials")

        bckgrnd_colour = kwargs.get("bckgrnd_color")
        ax_label_color = kwargs.get("axes_color")

        rwd_bloc_color = kwargs.get("rewarded_context_color")
        non_rwd_bloc_color = kwargs.get("non_rewarded_context_color")

        cut_session = kwargs.get("cut_session")
        yaml_file_path = kwargs.get('yaml_path')
        first_trial = kwargs.get("first_trial")
        last_trial = kwargs.get("last_trial")

        width_fig = kwargs.get("width_fig")
        height_fig = kwargs.get("height_fig")
        sns_context = kwargs.get('sns_context')
        dpi = kwargs.get("dpi", 300)
        save_formats = kwargs.get("save_formats", "png")

        color_palette = [aud_hit_color, aud_miss_color, wh_hit_color, wh_miss_color, cr_color, fa_color]

        # ------------------------------------------------------------ #
        # List of sessions to plot
        sessions_list = [session_data.session_id for session_data in self._data_to_analyse]

        # Concatenate all behavior data tables into one table and save it as a CSV file
        behavior_data_table = build_standard_behavior_table(nwb_list=self._data_to_analyse, cut_session=cut_session,
                                                            session_cutoffs=[first_trial, last_trial],
                                                            yaml_file_path=yaml_file_path,
                                                            result_path=self.get_results_path())
        behavior_data_table.to_csv(os.path.join(self.get_results_path(), 'concatenated_bhv_tables.csv'))

        # Get the block size for each session based on metadata info
        block_size_dict = dict()
        for session_data in self._data_to_analyse:
            block_size_dict[session_data.session_id] = session_data.petersen.get_experimental_block_size()

        # Set the context for all figures
        set_seaborn_context(sns_context=sns_context, page_color='white', lw=2)

        if 'single_session' in plots:
            plot_single_session(combine_bhv_data=behavior_data_table, sessions_list=sessions_list,
                                block_size_sessions=block_size_dict, color_palette=color_palette,
                                context_colors=[rwd_bloc_color, non_rwd_bloc_color],
                                figure_size=(width_fig, height_fig), dpi=dpi, background_color=bckgrnd_colour,
                                labels_color=ax_label_color,
                                saving_path=self.get_results_path(), save_formats=save_formats, verbose=verbose)

        if 'across_days' in plots:
            plot_single_mouse_across_days(combine_bhv_data=behavior_data_table,
                                          color_palette=color_palette,
                                          figure_size=(width_fig, height_fig), dpi=dpi,
                                          background_color=bckgrnd_colour, labels_color=ax_label_color,
                                          save_formats=save_formats, saving_path=self.get_results_path(),
                                          verbose=verbose)

        if 'across_context_days' in plots:
            hue_ctx = "context_background" if context_hue == "background noise" else "context_rwd_str"
            plot_single_mouse_across_context_days(combine_bhv_data=behavior_data_table,
                                                  block_size_sessions=block_size_dict,
                                                  color_palette=color_palette,
                                                  figure_size=(width_fig, height_fig), dpi=dpi,
                                                  context_hue=hue_ctx,
                                                  save_formats=save_formats,
                                                  distribution_plot_type=context_plot_type,
                                                  show_single_bloc=show_single_bloc,
                                                  background_color=bckgrnd_colour, labels_color=ax_label_color,
                                                  saving_path=self.get_results_path(), verbose=verbose)

        if "context_switch" in plots:
            n_wh_trials = None if whisker_switch == "full block" else n_whisker_trials
            plot_single_session_time_to_switch(combine_bhv_data=behavior_data_table,
                                               block_size_sessions=block_size_dict,
                                               figsize=(width_fig, height_fig),
                                               n_wh_trials=n_wh_trials,
                                               saving_path=self.get_results_path(), save_formats=save_formats,
                                               verbose=verbose)
            plot_single_mouse_time_to_switch(combine_bhv_data=behavior_data_table,
                                             block_size_sessions=block_size_dict,
                                             n_wh_trials=n_wh_trials,
                                             figsize=(width_fig, height_fig),
                                             saving_path=self.get_results_path(), save_formats=save_formats,
                                             verbose=verbose, average_mice=False)

        if "psycho" in plots:
            plot_single_mouse_psychometrics_across_days(combine_bhv_data=behavior_data_table,
                                                        saving_path=self.get_results_path(), save_formats=save_formats,
                                                        verbose=verbose)

        if 'reaction_time' in plots:
            plot_single_mouse_reaction_time_across_days(combine_bhv_data=behavior_data_table,
                                                        color_palette=color_palette,
                                                        figsize=(width_fig, height_fig),
                                                        saving_path=self.get_results_path(), save_formats=save_formats,
                                                        verbose=verbose)
