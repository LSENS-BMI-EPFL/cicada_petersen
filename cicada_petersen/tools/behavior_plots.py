"""
Petersen lab behavior task plots (whisker / auditory detection, context blocks, time to switch, reaction times).
Moved from cicada_analysis.cicada_tools.behavior.behavior_analysis_plots (revision B4).
"""


import os.path
import itertools
import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator
from scipy.stats._common import ConfidenceInterval
from scipy.stats import bootstrap
import scipy.stats as st
from cicada_petersen.tools.behavior_utils import (
    process_data,
    get_standard_single_session_table,
    get_single_mouse_table,
    get_single_session_time_to_switch,
)
from cicada_analysis.cicada_tools.display.core_plots import save_figure, style_axes


from cicada_analysis.cicada_tools.behavior.behavior_analysis_plots import plot_with_point_and_strip


def set_seaborn_context(sns_context, page_color, lw):
    # sns.set_context(sns_context)
    # sns.set(style=page_color, rc={"lines.linewidth": lw})
    plt.rcParams['pdf.fonttype'] = 42
    plt.rcParams['ps.fonttype'] = 42
    plt.rcParams['svg.fonttype'] = 'none'


def categorical_context_lineplot(data, hue, style, palette, mouse_id, save_formats, figure_size, dpi, markers,
                                 bkgrd_col, label_col, saving_path, figname):
    figure, ax0 = plt.subplots(1, 1, figsize=figure_size, dpi=dpi)

    for element in (('outcome_n', 'catch_palette'), ('outcome_a', 'aud_palette'), ('outcome_w', 'wh_palette')):
        sns.lineplot(x='day', y=element[0], hue=hue, style=style, data=data, palette=palette[element[1]],
                     ax=ax0, markers=markers, marker="o")

    ax0.set_title(f"Mouse {figname[0: 6]} across context days")
    ax0.get_legend().set_visible(False)
    style_axes(ax0, ylim=[-0.1, 1.05], xlabel='Day', ylabel='Lick probability', despine=True,
               background_color=bkgrd_col, color_ticks=label_col, axes_label_color=label_col,
               axes_border_color=label_col)

    results_path = os.path.join(saving_path, f'{mouse_id}')
    save_figure(figure, results_path, figname, save_formats=save_formats)


def categorical_context_days_avg(data, x_name, hue, palette, mouse_id, save_formats, figure_size, dpi,
                                 saving_path, figname):
    figure, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=figure_size, dpi=dpi)

    for element in (('outcome_n', ax0, 'catch_palette'), ('outcome_a', ax1, 'aud_palette'),
                    ('outcome_w', ax2, 'wh_palette')):
        plot_with_point_and_strip(data=data, x_name=x_name, y_name=element[0], hue=hue, legend=False,
                                  palette=palette, ax=element[1], palette_key=element[2], link_mice=False)
    n_days = len(np.unique(data.day.values[:]))
    subtitles = ['catch trials', 'auditory trials', 'whisker trials']
    for ind, ax in enumerate([ax0, ax1, ax2]):
        ax.set_title(f"{subtitles[ind]}")
        style_axes(ax, ylim=[0, 1.05], xlabel='Context', ylabel='Lick probability', despine=True)

    figure.suptitle(f"Average performance across {n_days} days for mouse {mouse_id}")
    results_path = os.path.join(saving_path, f'{mouse_id}')
    save_figure(figure, results_path, figname, save_formats=save_formats)


def categorical_context_boxplot(data, hue, palette, mouse_id, save_formats, figsize, dpi, saving_path, figname):
    figure, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=figsize, dpi=dpi)

    for element in (('hr_n', 'catch_palette', ax0), ('hr_a', 'aud_palette', ax1), ('hr_w', 'wh_palette', ax2)):
        sns.boxenplot(x='day', y=element[0], hue=hue, data=data, palette=palette[element[1]], ax=element[2])

    for ax in [ax0, ax1, ax2]:
        style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True)

    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)

    results_path = os.path.join(saving_path, f'{mouse_id}')
    save_figure(figure, results_path, figname, save_formats=save_formats)


def categorical_context_stripplot(data, hue, palette, mouse_id, save_formats, figsize, dpi, saving_path, figname):
    figure, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=figsize, dpi=dpi)

    for element in (('hr_n', 'catch_palette', ax0), ('hr_a', 'aud_palette', ax1), ('hr_w', 'wh_palette', ax2)):
        sns.stripplot(x='day', y=element[0], hue=hue, data=data, palette=palette[element[1]], dodge=True,
                      jitter=0.2, ax=element[2])

    for ax in [ax0, ax1, ax2]:
        style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True)

    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)

    results_path = os.path.join(saving_path, f'{mouse_id}')
    save_figure(figure, results_path, figname, save_formats=save_formats)


def categorical_context_pointplot(data, hue, palette, mouse_id, save_formats, figsize, dpi, saving_path, figname,
                                  show_single_bloc):
    figure, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=figsize, dpi=dpi)

    for element in (('hr_n', data.hr_n.values, 'catch_palette', ax0), ('hr_a', data.hr_a.values, 'aud_palette', ax1),
                    ('hr_w', data.hr_w.values, 'wh_palette', ax2)):
        if element[0] in list(data.columns) and (not np.isnan(element[1][:]).all()):
            sns.pointplot(x='day', y=element[0], hue=hue, data=data, palette=palette[element[2]], dodge=True,
                          estimator=np.mean, errorbar=('ci', 95), n_boot=1000, ax=element[3])
        if show_single_bloc:
            if element[0] in list(data.columns) and (not np.isnan(element[1][:]).all()):
                sns.stripplot(x='day', y=element[0], hue=hue, data=data, palette=palette[element[2]], dodge=False,
                              marker='o', alpha=.5, ax=element[3])

    subtitles = ['catch trials', 'auditory trials', 'whisker trials']
    for ind, ax in enumerate([ax0, ax1, ax2]):
        ax.set_title(f"{subtitles[ind]}")
        style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True)
        ax.get_legend().set_visible(False)

    figure.suptitle(f"Mouse {mouse_id} across context days")
    results_path = os.path.join(saving_path, f'{mouse_id}')
    save_figure(figure, results_path, figname, save_formats=save_formats)


def categorical_context_opto_pointplot(data, hue, palette, mouse_id, save_formats, figsize, dpi, saving_path, figname):
    figure, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=figsize, dpi=dpi)

    for element in (('hr_n', 'catch_palette', ax0), ('hr_a', 'aud_palette', ax1), ('hr_w', 'wh_palette', ax2)):
        sns.pointplot(x='day', y=element[0], hue=hue, data=data.loc[data['opto_stim'] == 0],
                      palette=palette[element[1]], dodge=True, estimator=np.mean,
                      errorbar=('ci', 95), n_boot=1000, ax=element[2])
        sns.pointplot(x='day', y=element[0], hue=hue, data=data.loc[data['opto_stim'] == 1],
                      palette=palette[element[1]], dodge=True, estimator=np.mean, errorbar=('ci', 95),
                      n_boot=1000, ax=element[2], markers='*', linestyles='dashed')

    for ax in [ax0, ax1, ax2]:
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(title=f'{mouse_id}', handles=handles,
                  labels=['Non Rewarded', 'Rewarded', 'Non Rewarded opto', 'Rewarded opto'])
        style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True)
        plt.legend(loc='lower left', borderaxespad=0)

    results_path = os.path.join(saving_path, f'{mouse_id}')
    save_figure(figure, results_path, figname, save_formats=save_formats)


def plot_difference_between_context(data, palette, mouse_id, save_formats, saving_path, figure_size):
    figure, ax0 = plt.subplots(1, 1, figsize=figure_size)

    for elem in (('hr_n_diff', 5), ('hr_a_diff', 0), ('hr_w_diff', 2)):
        sns.pointplot(x='day', y=elem[0], data=data, color=palette[elem[1]], ax=ax0, markers='o')

    ax0.set_title(f"{mouse_id}")
    style_axes(ax0, ylim=[-0.2, 1.05], xlabel='Day', ylabel='Lick probability', despine=True)

    figname = f"{mouse_id}_context_difference"
    results_path = os.path.join(saving_path, f'{mouse_id}')
    save_figure(figure, results_path, figname, save_formats=save_formats)


def plot_single_session(combine_bhv_data, sessions_list, block_size_sessions, color_palette, context_colors, figure_size, dpi,
                        background_color, labels_color, saving_path, save_formats, verbose=False):
    expert_context_sessions_table = []
    for session_id in sessions_list:
        session_table, switches, block_size = get_standard_single_session_table(combine_bhv_data, session=session_id, block_sizes=block_size_sessions)
        if session_table['behavior'].values[0] == 'free_licking':
            continue

        if verbose:
            print(f"Do plot for mouse: {session_table.mouse_id.values[0]}, session : {session_id}, "
                  f"behavior : {session_table['behavior'].values[0]},"
                  f"day : {session_table['day'].values[0]}")

        # Get the data table with one point per bloc
        d = session_table.loc[session_table.early_lick == 0][int(block_size / 2)::block_size]

        # Set plot parameters.
        raster_marker = 2
        marker_width = 2
        marker = itertools.cycle(["o", "s"])
        markers = [next(marker) for i in d["opto_stim"].unique()]

        # Remove legend if not necessary and adjust palette
        # Todo : no need to adjust size of palette to size of category in new seaborn package
        if (d['opto_stim'] == 0).all():
            plot_legend = False
            catch_palette = [color_palette[5]]
            auditory_palette = [color_palette[0]]
            whisker_palette = [color_palette[2]]
        else:
            plot_legend = 'brief'
            catch_palette = [color_palette[5], color_palette[5]]
            auditory_palette = [color_palette[0], color_palette[0]]
            whisker_palette = [color_palette[2], color_palette[2]]

        # Plot the lines :
        if session_table['behavior'].values[0] in ['context', 'whisker_context']:
            # Plot the global perf
            figure, (ax1, ax2) = plt.subplots(2, 1, figsize=figure_size, dpi=dpi,
                                              gridspec_kw={'height_ratios': [2, 3]}, sharex=True)

            # Plot the contrast perf (difference between one block and the 2 surrounding blocks)
            for outcome, contrast, palette in zip(['hr_w', 'hr_a', 'hr_n'],
                                                  ['contrast_w', 'contrast_a', 'contrast_n'],
                                                  [whisker_palette, auditory_palette, catch_palette]):
                contrast_values = [(np.abs(d[outcome].values[i] - d[outcome].values[i - 1]) +
                                    np.abs(d[outcome].values[i] - d[outcome].values[i + 1])) / 2 for
                                   i in np.arange(1, d[outcome].size - 1)]
                contrast_values.insert(0, np.nan)
                contrast_values.insert(len(contrast_values), np.nan)

                d[contrast] = contrast_values
                if contrast in d.columns and (not np.isnan(d[contrast].values[:]).all()):
                    sns.lineplot(data=d, x='trial', y=contrast, hue="opto_stim", style="opto_stim",
                                 palette=palette, ax=ax1, markers=markers, legend=plot_legend)
            ax1.set_ylim([-0.05, 1.05])
            ax1.set_ylabel('Contrast Lick Probability')
            ax1.axhline(y=0.375, xmin=0, xmax=1, color=color_palette[2], linewidth=2, linestyle='--')
            y_err = np.zeros((2, 1))

            # remove nan values
            clean_data = d.contrast_w.dropna().values
            # managing unique value case
            if len(np.unique(clean_data)) == 1:
                mean_value = clean_data[0]
                confidence_interval = ConfidenceInterval(low=mean_value, high=mean_value)

                class BootstrapResult:
                    def __init__(self, confidence_interval):
                        self.confidence_interval = confidence_interval

                bootstrap_res = BootstrapResult(confidence_interval)
            else:
                bootstrap_res = bootstrap(data=(clean_data,), statistic=np.nanmean, n_resamples=10000)

            y_err[0, 0] = np.nanmean(d.contrast_w) - bootstrap_res.confidence_interval.low
            y_err[1, 0] = bootstrap_res.confidence_interval.high - np.nanmean(d.contrast_w)
            ax1.errorbar(max(d.trial) + 10, np.nanmean(d.contrast_w.dropna()), yerr=y_err,
                         xerr=None, fmt='o', color=color_palette[2], ecolor=color_palette[2], elinewidth=2)
            rwd_hr_w = d.loc[d.context == 1].hr_w
            non_rwd_hr_w = d.loc[d.context == 0].hr_w
            d_prime = (np.nanmean(rwd_hr_w) - np.nanmean(non_rwd_hr_w)) / np.sqrt(
                0.5 * (np.var(rwd_hr_w) + np.var(non_rwd_hr_w)))
            d_prime_lsens = st.norm.ppf(min(np.nanmean(rwd_hr_w), 0.999)) - st.norm.ppf(
                max(np.nanmean(non_rwd_hr_w), 0.001))
            perf_dict = {'mouse_id': [session_id[0:5]], 'session_id': [session_id], 'w_contrast_thresh': [0.375],
                         'w_contrast_mean': [np.nanmean(d.contrast_w.dropna())],
                         'w_contrast_ci_low': [bootstrap_res.confidence_interval.low],
                         'w_contrast_ci_high': [bootstrap_res.confidence_interval.high],
                         'w_context_expert': [bootstrap_res.confidence_interval.low > 0.375],
                         'd_prime': [d_prime],
                         'lsens_d_prime': [d_prime_lsens]
                         }
            expert_context_sessions_table.append(pd.DataFrame.from_dict(perf_dict))
            if bootstrap_res.confidence_interval.low > 0.375:
                ax1.plot(max(d.trial) + 10, 0.9, marker='*', color=color_palette[2])
        else:
            figure, ax2 = plt.subplots(1, 1, figsize=figure_size, dpi=dpi)

        # Plot the lick probability
        # Plot the trials over blocs if there are
        for outcome, palette in [('hr_n', catch_palette), ('hr_a', auditory_palette), ('hr_w', whisker_palette)]:
            if outcome in d.columns and (not np.isnan(d[outcome].values[:]).all()):
                sns.lineplot(data=d, x='trial', y=outcome, hue="opto_stim", style="opto_stim",
                             palette=palette, ax=ax2, markers=markers, legend=plot_legend)

        # Display colored bands to distinguish rewarded and non-rewarded context if context task
        if session_table['behavior'].values[0] in ['context', 'whisker_context']:
            rewarded_bloc_bool = list(d.context.values[:])
            bloc_limites = np.arange(start=0, stop=len(session_table.index), step=block_size)
            bloc_area_color = [context_colors[0] if i == 1 else context_colors[1] for i in rewarded_bloc_bool]
            if bloc_limites[-1] < len(session_table.index):
                bloc_area = [(bloc_limites[i], bloc_limites[i + 1]) for i in range(len(bloc_limites) - 1)]
                bloc_area.append((bloc_limites[-1], len(session_table.index)))
                if len(bloc_area) > len(bloc_area_color):
                    bloc_area = bloc_area[0: len(bloc_area_color)]
                for index, coords in enumerate(bloc_area):
                    bloc_color = bloc_area_color[index]
                    ax2.axvspan(coords[0], coords[1], facecolor=bloc_color, zorder=1)

        # Plot the single trials :
        for outcome, color_offset, palette_index in [('outcome_n', 0.1, [4, 5]), ('outcome_a', 0.15, [1, 0]),
                                                     ('outcome_w', 0.2, [3, 2])]:
            if outcome in d.columns and (not np.isnan(d[outcome]).all()):
                for lick_flag, color_index in zip([0, 1], palette_index):
                    lick_subset = session_table.loc[session_table.lick_flag == lick_flag]
                    ax2.scatter(x=lick_subset['trial'], y=lick_subset[outcome] - lick_flag - color_offset,
                                color=color_palette[color_index], marker=raster_marker, linewidths=marker_width)
        figure_title = f"{session_table.mouse_id.values[0]}, {session_id[0:14]}, {session_table.behavior.values[0]} " \
                       f"{session_table.day.values[0]}"
        plt.suptitle(figure_title, color=labels_color)
        style_axes(ax2, ylim=[-0.25, 1.05], xlabel='Trial number', ylabel='Lick probability', despine=True,
                   background_color=background_color, color_ticks=labels_color, axes_label_color=labels_color,
                   axes_border_color=labels_color)

        figure_name = f"{session_table.mouse_id.values[0]}_{session_table.behavior.values[0]}_" \
                      f"{session_table.day.values[0]}"
        session_saving_path = os.path.join(saving_path, f"{session_table.mouse_id.values[0]}",
                                           f'{session_id[0:14]}_{session_table.behavior.values[0]}_'
                                           f'{session_table.day.values[0]}')
        save_figure(figure, session_saving_path, figure_name, save_formats=save_formats)

    if expert_context_sessions_table:
        expert_context_sessions_table = pd.concat(expert_context_sessions_table)
        session_index = []
        for mouse in expert_context_sessions_table['mouse_id'].unique():
            session_index.extend(
                np.arange(0, len(expert_context_sessions_table.loc[expert_context_sessions_table.mouse_id == mouse])))
        expert_context_sessions_table['session_index'] = session_index
        expert_context_sessions_table.to_excel(os.path.join(saving_path, 'context_expert_sessions.xlsx'))
        fig = sns.relplot(data=expert_context_sessions_table, x='session_index', y="w_contrast_mean", col="mouse_id",
                          hue='w_context_expert', height=1.5, aspect=1, col_wrap=4, legend='full')
        fig.set_ylabels('Whisker contrast')
        fig.set(ylim=(0, None))
        fig.figure.suptitle('Global whisker context performance')
        save_figure(fig.figure, saving_path, 'whisker_context_perf', save_formats, dpi="figure", tight_layout=False,
                    bbox_inches='tight')


def plot_single_mouse_across_days(combine_bhv_data, color_palette, figure_size, dpi, background_color, labels_color,
                                  save_formats, saving_path, verbose=False):
    mice_list = np.unique(combine_bhv_data['mouse_id'].values[:])
    for mouse_id in mice_list:
        if verbose:
            print(f"Plot performance across days for mouse : {mouse_id}")
        mouse_table = get_single_mouse_table(combine_bhv_data, mouse=mouse_id)

        behavior_list = ['auditory', 'whisker', 'whisker_psy']
        df_by_day, is_opto = process_data(mouse_table, behavior_list,
                                          ['outcome_a', 'outcome_w', 'outcome_n', 'day'], ['day'])
        if df_by_day.empty:
            if verbose:
                print(f"No {behavior_list} days in the selected sessions")
            continue

        # Do the plot
        figure, ax = plt.subplots(1, 1, figsize=figure_size, dpi=dpi)
        sns.lineplot(data=df_by_day, x='day', y='outcome_n', color=color_palette[5], ax=ax, marker='o')
        sns.lineplot(data=df_by_day, x='day', y='outcome_a', color=color_palette[0], ax=ax, marker='o')
        if max(df_by_day['day'].values) >= 0:  # This means there's one whisker training day at least
            sns.lineplot(data=df_by_day, x='day', y='outcome_w', color=color_palette[2], ax=ax, marker='o')

        ax.set_title(f"{mouse_id}")
        style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True,
                   background_color=background_color, color_ticks=labels_color, axes_label_color=labels_color,
                   axes_border_color=labels_color)

        results_path = os.path.join(saving_path, f'{mouse_id}')
        save_figure(figure, results_path, f'{mouse_id}_fast_learning', save_formats=save_formats)


def reindex_days(data_to_plot, aligning_value, mode='single'):
    """
    Re-index days based on the number of sessions selected for each mouse.

    Args:
        data_to_plot: DataFrame containing the data to plot.
        aligning_value: String indicating how to align the days ('day' or 'first_session').
        mode: String indicating the mode of re-indexing ('single' or 'double').

    Returns:
        Modified DataFrame with re-indexed days and the x_axis variable.
    """
    artificial_day = []
    for mouse in np.unique(data_to_plot['mouse_id'].values[:]):
        artificial_day.extend(
            np.arange(0, len(np.unique(data_to_plot.loc[(data_to_plot['mouse_id'] == mouse)]['day']))))
    if mode == 'double':
        artificial_day = np.ravel(np.column_stack((artificial_day, artificial_day)))
    data_to_plot['artificial_day'] = artificial_day

    x_axis = 'artificial_day' if aligning_value == 'first_session' else 'day'

    return data_to_plot, x_axis


def plot_mice_average_across_days(combine_bhv_data, aligning_value, color_palette, figure_size, dpi, background_color,
                                  labels_color, link_mice, save_formats, saving_path, verbose=False):
    mice_list = np.unique(combine_bhv_data['mouse_id'].values[:])
    n_mice = len(mice_list)
    if verbose:
        print(f"Plot average across {n_mice} mice : {mice_list}")
    behavior_list = ['auditory', 'whisker']
    cols = ['mouse_id', 'session_id', 'day', 'outcome_w', 'outcome_a', 'outcome_n']
    data_to_plot, is_opto = process_data(combine_bhv_data, behavior_list, cols,
                                         ['mouse_id', 'session_id', 'day'])
    if data_to_plot.empty:
        if verbose:
            print(f"No {behavior_list} days in the selected sessions")
        return

    # Re-index days based on the number of session selected for each mouse
    data_to_plot, x_axis = reindex_days(data_to_plot, aligning_value, mode='single')

    # Save the table used to generate the figure:
    data_to_plot.to_csv(os.path.join(saving_path, 'fast_learning_table.csv'))

    # Do the plots
    figure, ax = plt.subplots(1, 1, figsize=(int(figure_size * 9), int(figure_size * 6)), dpi=dpi)
    outcomes = [('outcome_n', color_palette[5]), ('outcome_a', color_palette[0])]
    if max(data_to_plot['day']) >= 0:  # This means there's one whisker training day at least
        outcomes.append(('outcome_w', color_palette[2]))
    for outcome, color in outcomes:
        sns.pointplot(x=x_axis, y=outcome, data=data_to_plot, color=color, marker='o',
                      estimator=np.nanmean, errorbar=('ci', 95), n_boot=1000, ax=ax, zorder=2)
        # Link mice across days.
        if link_mice:
            mice = data_to_plot.mouse_id.unique()
            for mouse_id in mice:
                data = data_to_plot.loc[data_to_plot.mouse_id == mouse_id]
                sns.pointplot(x=x_axis, y=outcome, data=data,
                              color=color, marker=None, estimator=np.nanmean, ax=ax, zorder=1, lw=2)
        else:
            sns.stripplot(x=x_axis, y=outcome, data=data_to_plot, color=color, dodge=True,
                          marker='o', alpha=.5, ax=ax, zorder=1)

    ax.set_title(f"Average across mice {mice_list}")
    style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True,
               background_color=background_color, color_ticks=labels_color, axes_label_color=labels_color,
               axes_border_color=labels_color)

    results_path = os.path.join(saving_path)
    save_figure(figure, results_path, f'Average_fast_learning', save_formats=save_formats)


def plot_average_mice_over_session(combine_bhv_data, block_size, results_path, save_formats):
    col_to_keep = ['mouse_id', 'session_id', 'day', 'trial_id', 'outcome_w', 'outcome_a', 'outcome_n']
    sub_table = combine_bhv_data[col_to_keep]
    sub_table = sub_table.loc[sub_table.day >= 0]
    sub_table['block_index'] = sub_table.groupby('session_id').cumcount() // block_size
    for outcome, new_col in zip(['outcome_w', 'outcome_a', 'outcome_n'], ['hr_w', 'hr_a', 'hr_n']):
        sub_table[new_col] = sub_table.groupby(['mouse_id', 'session_id', 'day', 'block_index'],
                                               as_index=False)[outcome].transform('mean')

    kept_columns = ['session_id', 'day', 'block_index', 'hr_w', 'hr_a', 'hr_n']
    averaged_table = sub_table[kept_columns]
    averaged_table = averaged_table.groupby(['session_id', 'day', 'block_index'], as_index=False).agg('mean')

    fig = sns.relplot(data=averaged_table, col='day', x='block_index', y='hr_w', kind='line')

    save_figure(fig, results_path, 'performance_over_session', save_formats=save_formats)


def plot_single_mouse_across_context_days(combine_bhv_data, block_size_sessions, color_palette, figure_size, dpi, context_hue,
                                          distribution_plot_type, show_single_bloc, background_color, labels_color,
                                          save_formats, saving_path, verbose=False):
    mice_list = np.unique(combine_bhv_data['mouse_id'].values[:])
    for mouse_id in mice_list:
        if verbose:
            print(f"Plot performance across context days for mouse : {mouse_id}")
        mouse_table = get_single_mouse_table(combine_bhv_data, mouse=mouse_id)

        behavior_list = ['context', 'whisker_context']
        cols = ['outcome_a', 'outcome_w', 'outcome_n', 'day', 'context', 'context_background', 'context_rwd_str',
                'opto_stim']
        groupby_cols = ['day', 'context', 'context_rwd_str', 'context_background', 'opto_stim']
        df_by_day, is_opto = process_data(mouse_table, behavior_list, cols, groupby_cols,
                                          {1: 'Rewarded', 0: 'Non-Rewarded'}, reset_idx=True)
        if df_by_day.empty:
            if verbose:
                print(f"No {behavior_list} days in the selected sessions")
            return

        # Look at the mean difference in Lick probability between rewarded and non-rewarded context
        df_by_day_diff = df_by_day.sort_values(by=['day', 'context_rwd_str'], ascending=True)
        for hr, outcome in zip(['hr_w_diff', 'hr_a_diff', 'hr_n_diff'], ['outcome_w', 'outcome_a', 'outcome_n']):
            df_by_day_diff[hr] = df_by_day_diff.loc[df_by_day_diff['opto_stim'] == 0].groupby('day')[outcome].diff()
            df_by_day_diff[f'{hr}_opto'] = df_by_day_diff.groupby(['day', 'context'])[outcome].diff()

        # Plot the delta lick probability between context
        plot_difference_between_context(data=df_by_day_diff, palette=color_palette, mouse_id=mouse_id,
                                        save_formats=save_formats, saving_path=saving_path, figure_size=figure_size)

        # Get each session with one value per block to look at distribution for each session
        mouse_session_list = list(np.unique(mouse_table['session_id'].values[:]))
        by_block_data = []
        for mouse_session in mouse_session_list:
            session_table, switches, block_size = get_standard_single_session_table(mouse_table, session=mouse_session, block_sizes=block_size_sessions)
            session_table = session_table.loc[session_table.early_lick == 0][int(block_size / 2)::block_size]
            by_block_data.append(session_table)
        by_block_data = pd.concat(by_block_data, ignore_index=True)
        by_block_data['context_rwd_str'] = by_block_data['context']
        by_block_data = by_block_data.replace({'context_rwd_str': {1: 'Rewarded', 0: 'Non-Rewarded'}})

        # Define the two color palettes
        if 'background' in context_hue:
            hue_name = ['brown', 'pink']
        else:
            hue_name = ['Rewarded', 'Non-Rewarded']
        context_palette = {
            'catch_palette': {hue_name[0]: 'darkgray', hue_name[1]: 'lightgrey'},
            'wh_palette': {hue_name[0]: 'green', hue_name[1]: 'firebrick'},
            'aud_palette': {hue_name[0]: 'mediumblue', hue_name[1]: 'cornflowerblue'}
        }
        context_opto_palette = {
            'catch_palette': {0: 'darkgray', 1: 'lightgrey'},
            'wh_palette': {0: 'green', 1: 'firebrick'},
            'aud_palette': {0: 'mediumblue', 1: 'cornflowerblue'}
        }

        # Do the plots : one point per day per context (average across blocs) all in one plot
        if is_opto:
            style, markers, suffix = "opto_stim", ["o", "s"], '_opto'
        else:
            style, markers, suffix = None, "o", ""
        categorical_context_lineplot(data=df_by_day, hue=context_hue, style=style, palette=context_palette,
                                     mouse_id=mouse_id, save_formats=save_formats, figure_size=figure_size, dpi=dpi,
                                     markers=markers, bkgrd_col=background_color, label_col=labels_color,
                                     saving_path=saving_path,
                                     figname=f"{mouse_id}_context_reward{suffix}")

        # Do the plots : average over context day between context for each trial type
        if is_opto:
            hue, suffix, plot_palette = "opto_stim", '_opto', context_opto_palette
        else:
            hue, suffix, plot_palette = None, "", context_palette
        categorical_context_days_avg(data=df_by_day, x_name=context_hue, hue=hue, palette=plot_palette,
                                     mouse_id=mouse_id, save_formats=save_formats, figure_size=figure_size, dpi=dpi,
                                     saving_path=saving_path,
                                     figname=f"{mouse_id}_avg_context_days{suffix}")

        # Do the plots : with context and block distribution for each day one subplot per trial type
        common_params = {'data': by_block_data, 'hue': context_hue, 'palette': context_palette, 'mouse_id': mouse_id,
                         'figsize': figure_size, 'dpi': dpi, 'save_formats': save_formats, 'saving_path': saving_path}

        if distribution_plot_type == 'box-plot':
            categorical_context_boxplot(figname=f"{mouse_id}_box_context_reward", **common_params)

        if distribution_plot_type == 'strip-plot':
            categorical_context_stripplot(figname=f"{mouse_id}_strip_context_reward", **common_params)

        if distribution_plot_type == 'point-plot':
            if not is_opto:
                categorical_context_pointplot(figname=f"{mouse_id}_point_context_reward",
                                              show_single_bloc=show_single_bloc, **common_params)
            else:
                categorical_context_opto_pointplot(figname=f"{mouse_id}_point_context_reward_opto", **common_params)


def plot_average_mice_across_context_days(combine_bhv_data, aligning_value, figure_size, dpi, context_hue, link_mice,
                                          save_formats, saving_path, verbose=False, show_legend=False):
    mice_list = np.unique(combine_bhv_data['mouse_id'].values[:])
    n_mice = len(mice_list)
    if verbose:
        print(f"Plot average across {n_mice} mice : {mice_list}")

    behavior_list = ['context', 'whisker_context']
    cols = ['mouse_id', 'session_id', 'outcome_a', 'outcome_w', 'outcome_n', 'day', 'context', 'context_background',
            'context_rwd_str']
    groupby_cols = ['mouse_id', 'session_id', 'day', 'context', 'context_rwd_str', 'context_background']
    data_to_plot, is_opto = process_data(combine_bhv_data, behavior_list, cols, groupby_cols,
                                         {1: 'Rewarded', 0: 'Non-Rewarded'}, reset_idx=True)

    if data_to_plot.empty:
        if verbose:
            print(f"No {behavior_list} days in the selected sessions")
        return

    # Re-index days based on the number of session selected for each mouse
    data_to_plot, x_axis = reindex_days(data_to_plot, aligning_value, mode='double')

    # Save full data table
    data_to_plot.to_csv(os.path.join(saving_path, 'context_days_full_table.csv'))

    # Define the two colort palette
    if 'background' in context_hue:
        hue_name = ['brown', 'pink']
        context_palette = {
            'catch_palette': {hue_name[0]: 'sienna', hue_name[1]: 'pink'},
            'wh_palette': {hue_name[0]: 'sienna', hue_name[1]: 'pink'},
            'aud_palette': {hue_name[0]: 'sienna', hue_name[1]: 'pink'}
        }
    else:
        hue_name = ['Rewarded', 'Non-Rewarded']
        context_palette = {
            'catch_palette': {hue_name[0]: 'darkgray', hue_name[1]: 'lightgrey'},
            'wh_palette': {hue_name[0]: 'green', hue_name[1]: 'darkmagenta'},
            'aud_palette': {hue_name[0]: 'mediumblue', hue_name[1]: 'cornflowerblue'}
        }

    # FIGURES ACROSS DAYS #
    # Figure 1 : Do the plot all in one
    figure, ax = plt.subplots(1, 1, figsize=(int(figure_size * 8), int(figure_size * 5)), dpi=dpi)

    for outcome, palette_key in zip(['outcome_n', 'outcome_a', 'outcome_w'],
                                    ['catch_palette', 'aud_palette', 'wh_palette']):
        plot_with_point_and_strip(data=data_to_plot, x_name=x_axis, y_name=outcome,
                                  hue=context_hue, legend=show_legend, palette=context_palette, ax=ax,
                                  palette_key=palette_key,
                                  link_mice=link_mice)

    ax.set_title(f"Average across mice {mice_list}")
    style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True)
    figure.tight_layout()

    results_path = os.path.join(saving_path)
    save_figure(figure, results_path, f'Average_context_days', save_formats=save_formats)

    # Figure 2 : Do subplots for each trial type
    figure, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(int(figure_size * 8), int(figure_size * 5)), dpi=dpi,
                                           sharey=True)

    for outcome, palette_key, ax in zip(['outcome_n', 'outcome_a', 'outcome_w'],
                                        ['catch_palette', 'aud_palette', 'wh_palette'], [ax0, ax1, ax2]):
        plot_with_point_and_strip(data=data_to_plot, x_name=x_axis, y_name=outcome, hue=context_hue, legend=show_legend,
                                  palette=context_palette, ax=ax, palette_key=palette_key,
                                  link_mice=link_mice)

    subtitles = ['catch trials', 'auditory trials', 'whisker trials']
    for ind, ax in enumerate([ax0, ax1, ax2]):
        ax.set_title(f"{subtitles[ind]}")
        style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel='Lick probability', despine=True)
    figure.tight_layout()

    save_figure(figure, results_path, f'Average_context_days_split', save_formats=save_formats)

    # FIGURES GENERAL AVERAGE #
    # Average the data
    average_data_to_plot = data_to_plot.drop(['session_id', 'day', 'artificial_day'], axis=1)
    general_average_table = average_data_to_plot.groupby(
        ['mouse_id', 'context', 'context_rwd_str', 'context_background'],
        as_index=False).agg('mean')

    # Save averaged data table
    general_average_table.to_csv(os.path.join(saving_path, 'context_days_averaged_table.csv'))

    # Make the figure
    figure, (ax0, ax1, ax2) = plt.subplots(1, 3, figsize=(int(figure_size * 5), int(figure_size * 5)), dpi=dpi,
                                           sharey=True)

    for outcome, palette_key, ax in zip(['outcome_n', 'outcome_a', 'outcome_w'],
                                        ['catch_palette', 'aud_palette', 'wh_palette'], [ax0, ax1, ax2]):
        plot_with_point_and_strip(data=general_average_table, x_name=context_hue, y_name=outcome,
                                  hue=context_hue, legend=show_legend, palette=context_palette, ax=ax,
                                  palette_key=palette_key, link_mice=link_mice)

    subtitles = ['catch trials', 'auditory trials', 'whisker trials']

    for ind, ax in enumerate([ax0, ax1, ax2]):
        ax.set_title(f"{subtitles[ind]}")
        style_axes(ax, ylim=[0, 1.05], xlabel='Context', ylabel='Lick probability', despine=True)

    figure.suptitle(f"Average performance across {n_mice} mice")
    figure.tight_layout()

    results_path = os.path.join(saving_path)
    save_figure(figure, results_path, f'Average_context_days_general', save_formats=save_formats)


def plot_single_session_time_to_switch(combine_bhv_data, block_size_sessions, n_wh_trials, figsize,
                                       saving_path, save_formats, verbose=False):
    to_rewarded_transitions_prob_dict, to_non_rewarded_transitions_prob_dict, trials_around_dict, mouse_id_dict, \
        day_index_dict = get_single_session_time_to_switch(combine_bhv_data, n_wh_trials, block_size_sessions)

    for session_id in to_rewarded_transitions_prob_dict.keys():
        rewarded_transition_prob = to_rewarded_transitions_prob_dict[session_id]
        non_rewarded_transition_prob = to_non_rewarded_transitions_prob_dict[session_id]
        n_trials_around = trials_around_dict[session_id]
        mouse_id = mouse_id_dict[session_id]
        day_index = day_index_dict[session_id]

        if verbose:
            print(f"Do plot for mouse: {mouse_id}, session : {session_id}, behavior : context, day : {day_index}")

        figure, ax = plt.subplots(1, 1, figsize=figsize)
        scale = np.arange(-n_trials_around, n_trials_around + 1)
        scale = np.delete(scale, n_trials_around)
        before_switch = scale[np.where(scale < 0)[0]]
        after_switch = scale[np.where(scale > 0)[0]]

        ax.plot(before_switch, rewarded_transition_prob[0: len(before_switch)], '--ro')
        ax.plot(before_switch, non_rewarded_transition_prob[0: len(before_switch)], '--go')
        ax.plot(after_switch, rewarded_transition_prob[len(before_switch):], '--go')
        ax.plot(after_switch, non_rewarded_transition_prob[len(before_switch):], '--ro')
        figure_title = f"{mouse_id}, context day {day_index}"
        ax.set_title(figure_title)
        style_axes(ax, ylim=[0, 1.05], xlabel='Trial number', ylabel='Lick probability', despine=True)
        plt.xticks(scale)

        results_path = os.path.join(saving_path, f'{mouse_id}', f'context_{day_index}')
        save_figure(figure, results_path, f'{mouse_id}_context_day_{day_index}_switch', save_formats=save_formats)


def plot_single_mouse_time_to_switch(combine_bhv_data, block_size_sessions, n_wh_trials, figsize,
                                     saving_path, save_formats, verbose, average_mice=False):
    to_rewarded_transitions_prob_dict, to_non_rewarded_transitions_prob_dict, trials_around_dict, mouse_id_dict, day_index_dict = get_single_session_time_to_switch(combine_bhv_data, n_wh_trials, block_size_sessions)

    if to_rewarded_transitions_prob_dict == {}:
        print("No context switch")  # TODO: changer string
    else:
        # Find n trials and do scale
        n_trials = len(to_rewarded_transitions_prob_dict[list(trials_around_dict.keys())[0]])
        n_trials_around = int(n_trials / 2)
        scale = np.arange(-n_trials_around, n_trials_around + 1)
        scale = np.delete(scale, n_trials_around)

        # Prepare values for table
        sessions = np.repeat(list(to_rewarded_transitions_prob_dict.keys()), len(scale))
        mice = [session[0:5] for session in sessions]
        full_scale = np.tile(scale, len(list(to_rewarded_transitions_prob_dict.keys())))
        rwd_values = np.concatenate(list(to_rewarded_transitions_prob_dict.values()), axis=0)
        nn_rwd_values = np.concatenate(list(to_non_rewarded_transitions_prob_dict.values()), axis=0)
        rwd_transitions = ['to_rewarded' for i in range(len(rwd_values))]
        nn_rwd_transitions = ['to_non_rewarded' for i in range(len(nn_rwd_values))]

        # To rewarded df
        to_rwd_data_frame = pd.DataFrame({'Mouse_ID': mice, 'Session_ID': sessions, 'Whisker_trial': full_scale,
                                          'WHR': rwd_values, 'Transition': rwd_transitions})

        # To non-rewarded df
        to_nn_rwd_data_frame = pd.DataFrame({'Mouse_ID': mice, 'Session_ID': sessions, 'Whisker_trial': full_scale,
                                             'WHR': nn_rwd_values, 'Transition': nn_rwd_transitions})

        # Concat
        data_frame = pd.concat((to_rwd_data_frame, to_nn_rwd_data_frame), ignore_index=True)

        # Do single mouse plot (average sessions)
        if not average_mice:
            for mouse in combine_bhv_data.mouse_id.unique():
                print(f"Average session from mouse : {mouse}")
                figure, ax = plt.subplots(1, 1, figsize=figsize)
                data_to_plot = data_frame.loc[data_frame.Mouse_ID == mouse]
                sns.pointplot(x='Whisker_trial', y='WHR', hue='Transition', data=data_to_plot, estimator=np.mean,
                              errorbar=('ci', 95), linestyle=None, hue_order=['to_rewarded', 'to_non_rewarded'],
                              palette=['green', 'red'], ax=ax)
                figure_title = f"{mouse}, average context switch (n= {len(data_to_plot.Session_ID.unique())} sessions) "
                ax.set_title(figure_title)
                style_axes(ax, ylim=[0, 1.05], xlabel='Trial number', ylabel='Lick probability', despine=True)

                results_path = os.path.join(saving_path, f'{mouse}')
                save_figure(figure, results_path, f'{mouse}_average_context_switch', save_formats=save_formats)
        # Return table
        else:
            return data_frame


def plot_average_mice_time_to_switch(combine_bhv_data, block_size_sessions, n_wh_trials, figsize,
                                     saving_path, save_formats, verbose, average_mice):
    # Get table
    data_frame = plot_single_mouse_time_to_switch(combine_bhv_data, block_size_sessions=block_size_sessions,
                                                  n_wh_trials=n_wh_trials, figsize=figsize, saving_path=saving_path,
                                                  save_formats=save_formats, verbose=verbose, average_mice=average_mice)
    # Save a full results table:
    data_frame.to_csv(os.path.join(saving_path, 'context_transitions_full_table.csv'))

    # Average for each mouse
    data_frame = data_frame.drop('Session_ID', axis=1)
    mice_grp_data = data_frame.groupby(['Mouse_ID', 'Transition', 'Whisker_trial']).agg('mean')
    mice_grp_data = mice_grp_data.reset_index()

    # Save a datafame averaged by mouse:
    mice_grp_data.to_csv(os.path.join(saving_path, 'context_transitions_averaged_table.csv'))

    # Plot 1
    if verbose:
        print("Plot average time to switch")
    figure, ax = plt.subplots(1, 1, figsize=(int(figsize * 5), int(figsize * 5)))
    sns.pointplot(x='Whisker_trial', y='WHR', hue='Transition', data=mice_grp_data, estimator=np.mean,
                  errorbar=('ci', 95), linestyle='none', hue_order=['to_rewarded', 'to_non_rewarded'],
                  palette=['green', 'darkmagenta'], legend=False, ax=ax)
    figure_title = f"Averaged switch time (n={len(mice_grp_data.Mouse_ID.unique())} mice)"
    ax.set_title(figure_title)
    style_axes(ax, ylim=[0, 1.05], xlabel='Whisker trial number', ylabel='Lick probability', despine=True)

    results_path = os.path.join(saving_path)
    save_figure(figure, results_path, f'Average_context_switch', save_formats=save_formats)

    # Plot 2
    figure, ax = plt.subplots(1, 1, figsize=(int(figsize * 3), int(figsize * 6)))
    data_to_plot = mice_grp_data.loc[mice_grp_data['Whisker_trial'].isin([-1, 1])]
    for mouse in data_to_plot.Mouse_ID.unique():
        sns.pointplot(x='Whisker_trial', y='WHR', hue='Transition', palette=["green", "darkmagenta"],
                      hue_order=["to_rewarded", "to_non_rewarded"], alpha=0.5, zorder=-1,
                      data=data_to_plot.loc[data_to_plot.Mouse_ID == mouse], legend=False, ax=ax)
    plt.setp(ax.collections, alpha=.3)
    plt.setp(ax.lines, alpha=.3)
    sns.pointplot(x='Whisker_trial', y='WHR', hue='Transition', estimator=np.mean, errorbar=('ci', 95),
                  palette=["green", "darkmagenta"], hue_order=["to_rewarded", "to_non_rewarded"], linestyle='none', dodge=True,
                  data=data_to_plot, legend=False, ax=ax)
    figure_title = f"Averaged switch time (n={len(mice_grp_data.Mouse_ID.unique())} mice)"
    ax.set_title(figure_title)
    style_axes(ax, ylim=[0, 1.05], xlabel='Trial number', ylabel='Lick probability', despine=True)

    # Statistics:
    to_rewarded_pre = data_to_plot.loc[(data_to_plot.Whisker_trial == -1) &
                                       (data_to_plot.Transition == 'to_rewarded')].WHR.values[:]
    to_rewarded_post = data_to_plot.loc[(data_to_plot.Whisker_trial == 1) &
                                        (data_to_plot.Transition == 'to_rewarded')].WHR.values[:]
    to_nn_rewarded_pre = data_to_plot.loc[(data_to_plot.Whisker_trial == -1) &
                                          (data_to_plot.Transition == 'to_non_rewarded')].WHR.values[:]
    to_nn_rewarded_post = data_to_plot.loc[(data_to_plot.Whisker_trial == 1) &
                                           (data_to_plot.Transition == 'to_non_rewarded')].WHR.values[:]

    to_rewarded_p = st.wilcoxon(to_rewarded_post, to_rewarded_pre, alternative='greater')
    to_nn_rewarded_p = st.wilcoxon(to_nn_rewarded_pre, to_nn_rewarded_post, alternative='greater')
    if verbose:
        print(f'To R+ p-val: {to_rewarded_p}')
        print(f'To R- p-val: {to_nn_rewarded_p}')
    if to_rewarded_p[1] < 0.05:
        ax.plot(0.95, 1.03, '*', markersize=3, color='green')
    if to_nn_rewarded_p[1] < 0.05:
        ax.plot(1.05, 1.03, '*', markersize=3, color='darkmagenta')

    results_path = os.path.join(saving_path)
    save_figure(figure, results_path, f'Average_context_switch_single_trial', save_formats=save_formats)


def plot_single_mouse_psychometrics_across_days(combine_bhv_data, saving_path, save_formats, verbose=False):
    for mouse_id in combine_bhv_data['mouse_id'].unique():
        if verbose:
            print(f"Plot Psychometric curves for mouse : {mouse_id}")
        mouse_table = get_single_mouse_table(combine_bhv_data, mouse=mouse_id)

        # Keep only whisker psychophysical days
        mouse_table = mouse_table[mouse_table.behavior.isin(['whisker_psy'])]
        if mouse_table.empty:
            return

        # Remap individual whisker stim amplitude to 5 levels including no_stim_trials (level 0)
        for day_idx in mouse_table['day'].unique():
            if verbose:
                print(f"{mouse_id}, day: {day_idx}")
            mouse_table_day = mouse_table.loc[mouse_table['day'] == day_idx]
            wh_stim_amp_mapper = {k: idx for idx, k in
                                  enumerate(np.unique(mouse_table_day['whisker_stim_amplitude'].values))}

            mouse_table.loc[mouse_table['day'] == day_idx, 'whisker_stim_levels'] = mouse_table.loc[
                mouse_table['day'] == day_idx, 'whisker_stim_amplitude'].map(wh_stim_amp_mapper)

        stim_amplitude_levels = np.unique(mouse_table['whisker_stim_levels'].values)
        if verbose:
            print(f"Stim levels: {stim_amplitude_levels}")

        # Plot psychometric curve
        g = sns.FacetGrid(mouse_table, col='day', col_wrap=4, height=4, aspect=1, sharey=True, sharex=True)

        g.map(sns.pointplot, 'whisker_stim_levels', 'lick_flag', order=sorted(stim_amplitude_levels),
              estimator=np.mean, errorbar=('ci', 95), n_boot=1000, seed=42, color='forestgreen')

        g.set_axis_labels('Stimulus amplitude [mT]', 'P(lick)')
        g.set(xticks=range(5), xticklabels=[0, 10, 20, 25, 30])
        g.set(ylim=(0, 1.1))
        figname = f"{mouse_id}_psychometric_curve"

        # Save figures
        results_path = os.path.join(saving_path, f'{mouse_id}')
        save_figure(g, results_path, figname, save_formats=save_formats)

    return


def plot_reaction_time(df, trial_types, colors, context_reward_palette, mouse_id, saving_path, save_formats, figsize,
                       with_context=False):
    figure, axes = plt.subplots(len(trial_types), 1, figsize=figsize)
    if mouse_id is not None:
        figname = f"{mouse_id}_reaction_time" + ("_context" if with_context else "")
    else:
        figname = "reaction_time" + ("_context" if with_context else "")
    for index, ax in enumerate(axes):
        if with_context:
            sns.boxenplot(df.loc[df.trial_type == trial_types[index]], x='day', y='computed_reaction_time',
                          hue='context', palette=context_reward_palette.get(trial_types[index]), ax=ax)
        else:
            sns.boxenplot(df.loc[df.trial_type == trial_types[index]], x='day', y='computed_reaction_time',
                          color=colors[index], ax=ax)
        if index == 0:
            if mouse_id is not None:
                ax.set_title(f"{mouse_id}")
            else:
                ax.set_title("Reaction time")
        style_axes(ax, ylim=[0, 1.05], xlabel='Day', ylabel=f'{trial_types[index].capitalize()} \n Reaction time (s)',
                   despine=True)

    if mouse_id is not None:
        results_path = os.path.join(saving_path, f'{mouse_id}')
    else:
        results_path = saving_path
    save_figure(figure, results_path, figname, save_formats=save_formats)


def plot_single_mouse_reaction_time_across_days(combine_bhv_data, color_palette, figsize, saving_path,
                                                save_formats, verbose=False):

    for mouse_id in combine_bhv_data.mouse_id.unique():
        if verbose:
            print(f"Mouse : {mouse_id}")
        mouse_table = get_single_mouse_table(combine_bhv_data, mouse=mouse_id)

        # Keep only Auditory and Whisker days
        mouse_table = mouse_table.loc[mouse_table.behavior.isin(('auditory', 'whisker', 'context', 'whisker_context'))]

        # Select columns for plot
        cols = ['start_time', 'stop_time', 'lick_time', 'trial_type', 'lick_flag', 'early_lick', 'context',
                'day', 'response_window_start_time']

        # first df with only rewarded context: compute reaction time
        df = mouse_table.loc[(mouse_table.early_lick == 0) & (mouse_table.lick_flag == 1) &
                             (mouse_table.context != 0) & (mouse_table.context != 'passive'), cols]
        df['computed_reaction_time'] = df['lick_time'] - df['response_window_start_time']
        df = df.replace({'context': {1: 'Rewarded', 0: 'Non-Rewarded', 'active': 'Rewarded', 'nan': 'Rewarded'}})

        # second df with two contexts: compute reaction time
        df_2 = mouse_table.loc[(mouse_table.early_lick == 0) & (mouse_table.lick_flag == 1) & (mouse_table.context != 'passive'), cols]
        df_2['computed_reaction_time'] = df_2['lick_time'] - df_2['response_window_start_time']
        df_2 = df_2.replace({'context': {1: 'Rewarded', 0: 'Non-Rewarded', 'active': 'Rewarded', 'nan': 'Rewarded'}})

        trial_types = np.sort(list(np.unique(mouse_table.trial_type.values[:])))
        colors = [color_palette[0], color_palette[4], color_palette[2]]
        context_reward_palette = {
            'auditory_trial': {'Rewarded': 'mediumblue', 'Non-Rewarded': 'cornflowerblue'},
            'no_stim_trial': {'Rewarded': 'black', 'Non-Rewarded': 'darkgray'},
            'whisker_trial': {'Rewarded': 'green', 'Non-Rewarded': 'firebrick'},
        }

        # Plot without context
        plot_reaction_time(df, trial_types, colors, context_reward_palette, mouse_id, saving_path, save_formats,
                           figsize, with_context=False)

        # Plot with context
        plot_reaction_time(df_2, trial_types, colors, context_reward_palette, mouse_id, saving_path, save_formats,
                           figsize, with_context=True)


def plot_reaction_time_general_data(combine_bhv_data, figsize, saving_path, save_formats, verbose=False):

    # Keep only Auditory and Whisker days
    table = combine_bhv_data.loc[combine_bhv_data.behavior.isin(('auditory', 'whisker', 'context', 'whisker_context'))]

    # Select columns for plot
    cols = ['trial_id', 'mouse_id', 'session_id', 'start_time', 'stop_time', 'lick_time', 'trial_type', 'lick_flag',
            'early_lick', 'context', 'day', 'response_window_start_time']

    # first df with only rewarded context: compute reaction time
    df = table.loc[(table.early_lick == 0) & (table.lick_flag == 1) & (table.context == 1), cols]
    df['computed_reaction_time'] = df['lick_time'] - df['response_window_start_time']
    df = df.replace({'context': {1: 'Rewarded', 0: 'Non-Rewarded'}})

    # second df with two contexts: compute reaction time
    df_2 = table.loc[(table.early_lick == 0) & (table.lick_flag == 1), cols]
    df_2['computed_reaction_time'] = df_2['lick_time'] - df_2['response_window_start_time']
    df_2 = df_2.replace({'context': {1: 'Rewarded', 0: 'Non-Rewarded'}})

    context_reward_palette = {
        'auditory_trial': {'Rewarded': 'mediumblue', 'Non-Rewarded': 'cornflowerblue'},
        'no_stim_trial': {'Rewarded': 'black', 'Non-Rewarded': 'darkgray'},
        'whisker_trial': {'Rewarded': 'green', 'Non-Rewarded': 'darkmagenta'},
    }

    # Plots
    # Figure 1 : reaction time by trial type
    figure, ax0 = plt.subplots(1, 1, figsize=(int(figsize * 4), int(figsize * 4)))
    figname = "Reaction_time_all_types"
    sns.boxplot(df, x='trial_type', y='computed_reaction_time', ax=ax0)
    style_axes(ax0, ylim=[0, 1.05], xlabel='Trial type', ylabel='Reaction time (s)', despine=True)
    figure.suptitle('Reaction time (in RWD context)')
    figure.tight_layout()
    save_figure(figure, saving_path, figname, save_formats=save_formats)

    # Figure 1bis - group by mouse
    avg_to_keep = ['mouse_id', 'session_id', 'trial_type', 'context', 'computed_reaction_time']
    session_avg_df = df[avg_to_keep]
    session_avg_df = session_avg_df.groupby(['mouse_id', 'session_id', 'trial_type', 'context'],
                                            as_index=False).agg('mean')
    mouse_avg_df = session_avg_df.drop('session_id', axis=1)
    mouse_avg_df = mouse_avg_df.groupby(['mouse_id', 'trial_type', 'context'], as_index=False).agg('mean')

    figure, ax0 = plt.subplots(1, 1, figsize=(int(figsize * 4), int(figsize * 4)))
    figname = "Reaction_time_all_types_mouse_averaged"
    sns.pointplot(mouse_avg_df, x='trial_type', y='computed_reaction_time', ax=ax0)
    sns.stripplot(mouse_avg_df, x='trial_type', y='computed_reaction_time', ax=ax0)
    style_axes(ax0, ylim=[0, 1.05], xlabel='Trial type', ylabel='Reaction time (s)', despine=True)
    figure.suptitle('Reaction time (in RWD context)')
    figure.tight_layout()
    save_figure(figure, saving_path, figname, save_formats=save_formats)

    # Figure 2 : reaction time by trial type and context
    figure, (ax0) = plt.subplots(1, 1, figsize=(int(figsize * 4), int(figsize * 4)))
    figname = "Reaction_time_all_types_context"
    sns.boxplot(df_2, x='trial_type', y='computed_reaction_time', hue='context', legend=False,
                palette=context_reward_palette['whisker_trial'], ax=ax0)
    style_axes(ax0, ylim=[0, 1.05], xlabel='Trial type', ylabel='Reaction time (s)', despine=True)
    figure.tight_layout()
    figure.suptitle('Reaction time')
    figure.tight_layout()
    save_figure(figure, saving_path, figname, save_formats=save_formats)

    # Figure 2bis - group by mouse
    avg_to_keep = ['mouse_id', 'session_id', 'trial_type', 'context', 'computed_reaction_time']
    session_avg_df2 = df_2[avg_to_keep]
    session_avg_df2 = session_avg_df2.groupby(['mouse_id', 'session_id', 'trial_type', 'context'],
                                              as_index=False).agg('mean')
    session_avg_df2 = session_avg_df2.drop('session_id', axis=1)
    mouse_avg_df2 = session_avg_df2.groupby(['mouse_id', 'trial_type', 'context'], as_index=False).agg('mean')
    mouse_avg_df2.to_csv(os.path.join(saving_path, 'mouse_averaged_reaction_time.csv'))

    figure, (ax0) = plt.subplots(1, 1, figsize=(int(figsize * 4), int(figsize * 4)))
    figname = "Reaction_time_all_types_context_mouse_averaged"
    sns.pointplot(mouse_avg_df2, x='trial_type', y='computed_reaction_time', hue='context', legend=False,
                  palette=context_reward_palette['whisker_trial'], dodge=True, ax=ax0)
    sns.stripplot(mouse_avg_df2, x='trial_type', y='computed_reaction_time', hue='context', legend=False,
                  palette=context_reward_palette['whisker_trial'], ax=ax0)
    style_axes(ax0, ylim=[0, 1.05], xlabel='Trial type', ylabel='Reaction time (s)', despine=True)
    figure.tight_layout()
    figure.suptitle('Reaction time')
    figure.tight_layout()
    save_figure(figure, saving_path, figname, save_formats=save_formats)

    # Figure 3 : reaction time at whisker trials in the two contexts
    figure, ax0 = plt.subplots(1, 1, figsize=(int(figsize * 3), int(figsize * 6)))
    figname = "Reaction_time_whisker_context"
    table_to_plot = df_2.loc[df_2.trial_type == 'whisker_trial']
    sns.violinplot(table_to_plot, y='computed_reaction_time', split=True, hue='context', legend=False,
                   palette=context_reward_palette['whisker_trial'])
    ax0.axhline(y=0.25, xmin=0, xmax=1, color='k', linestyle='--')
    style_axes(ax0, ylim=[0, 1.05], xlabel='Whisker trials', ylabel='Reaction time (s)', despine=True)
    figure.tight_layout()
    figure.tight_layout()
    figure.suptitle('Reaction time')
    save_figure(figure, saving_path, figname, save_formats=save_formats)

    # Figure 3bis :
    figure, ax0 = plt.subplots(1, 1, figsize=(int(figsize * 3), int(figsize * 6)))
    figname = "Reaction_time_whisker_context_mouse_averaged"
    table_to_plot = mouse_avg_df2.loc[mouse_avg_df2.trial_type == 'whisker_trial']
    sns.pointplot(table_to_plot, y='computed_reaction_time', hue='context', legend=False,
                  palette=context_reward_palette['whisker_trial'], dodge=True)
    sns.stripplot(table_to_plot, y='computed_reaction_time', hue='context', legend=False,
                  palette=context_reward_palette['whisker_trial'], dodge=True)
    ax0.axhline(y=0.25, xmin=0, xmax=1, color='k', linestyle='--')
    style_axes(ax0, ylim=[0, 1.05], xlabel='Whisker trials', ylabel='Reaction time (s)', despine=True)
    figure.tight_layout()
    figure.tight_layout()
    figure.suptitle('Reaction time')
    save_figure(figure, saving_path, figname, save_formats=save_formats)


def analysis_1st_whisker_against_time(session_data, verbose, rwd_wh_table, nn_rwd_wh_table, last_rwd_wh_table,
                                      last_nn_rwd_wh_table):

    mouse_id = session_data.subject_id
    session_id = session_data.session_id

    # Get trial table
    trial_table = session_data.behavior.get_trial_table()

    rewarded_context_timestamps = session_data.behavior.get_behavioral_epochs_times(epoch_name='rewarded')
    non_rewarded_context_timestamps = session_data.behavior.get_behavioral_epochs_times(epoch_name='non-rewarded')
    if rewarded_context_timestamps is None or non_rewarded_context_timestamps is None:
        print('No timestamps, skip this session.')
        return

    whisker_table = trial_table.loc[trial_table.trial_type == 'whisker_trial']
    whisker_table = whisker_table.reset_index(drop=True)

    transitions = list(np.diff(whisker_table['context']))
    transitions.insert(0, 0)
    whisker_table['transitions'] = transitions
    cols = ['start_time', 'lick_flag', 'context', 'transitions']
    filter_wh_table = whisker_table[cols]

    # Transitions to rewarded
    rwd_filter_wh_table = filter_wh_table.loc[filter_wh_table.transitions == 1]
    rwd_filter_wh_table = process_transitions(rwd_filter_wh_table, rewarded_context_timestamps, session_id,
                                              mouse_id, 'reward_epoch_start', 'time_in_reward')
    rwd_wh_table.append(rwd_filter_wh_table)

    # Transitions to non-rewarded
    nn_rwd_filter_wh_table = filter_wh_table.loc[filter_wh_table.transitions == -1]
    nn_rwd_filter_wh_table = process_transitions(nn_rwd_filter_wh_table, non_rewarded_context_timestamps, session_id,
                                                 mouse_id, 'non_reward_epoch_start',
                                                 'time_in_non_reward')
    nn_rwd_wh_table.append(nn_rwd_filter_wh_table)

    # Last non-rewarded whisker trial
    last_non_rwd_whisker = (np.where(filter_wh_table.transitions == 1)[0] - 1).tolist()
    last_non_rwd_whisker_table = filter_wh_table.loc[last_non_rwd_whisker]
    last_non_rwd_whisker_table = process_transitions(last_non_rwd_whisker_table, rewarded_context_timestamps,
                                                     session_id, mouse_id, 'next_reward_epoch_start',
                                                     'time_to_reward')
    last_nn_rwd_wh_table.append(last_non_rwd_whisker_table)

    # Last rewarded whisker trial
    last_rwd_whisker = (np.where(filter_wh_table.transitions == -1)[0] - 1).tolist()
    last_rwd_whisker_table = filter_wh_table.loc[last_rwd_whisker]
    last_rwd_whisker_table = process_transitions(last_rwd_whisker_table, non_rewarded_context_timestamps, session_id,
                                                 mouse_id, 'next_non_reward_epoch_start',
                                                 'time_to_non_reward')
    last_rwd_wh_table.append(last_rwd_whisker_table)


def process_transitions(filter_table, context_timestamps, session_id, mouse_id, new_col_epoch, time_label):
    if context_timestamps[0][0] == 0:
        if len(context_timestamps[0][1:]) == len(filter_table) + 1:
            filter_table = filter_table.assign(**{new_col_epoch: context_timestamps[0][1:-1]})
        else:
            filter_table = filter_table.assign(**{new_col_epoch: context_timestamps[0][1:]})
    else:
        if len(context_timestamps[0]) == len(filter_table) + 1:
            filter_table = filter_table.assign(**{new_col_epoch: context_timestamps[0][:-1]})
        else:
            filter_table = filter_table.assign(**{new_col_epoch: context_timestamps[0]})

    filter_table[time_label] = filter_table['start_time'] - filter_table[new_col_epoch]
    filter_table['session_id'] = session_id
    filter_table['mouse_id'] = mouse_id
    return filter_table


def plot_1st_whisker_against_time(save_path, save_formats, transition_full_dataset):
    # Add a column for time around transition (all possibilities)
    cols_to_merge = ['time_in_reward', 'time_in_non_reward', 'time_to_non_reward', 'time_to_reward']
    transition_full_dataset['Time around transition'] = transition_full_dataset[cols_to_merge].bfill(axis=1).iloc[:, 0]

    # Add a 10sec bin for each trial
    transition_trial_times = transition_full_dataset['Time around transition'].values[:]
    bins = np.arange(-300, 300, 10)
    digitized = np.digitize(transition_trial_times, bins=bins) - 1
    symmetrical_digitized = np.where(transition_trial_times < 0, -(len(bins) // 2 - digitized), digitized - len(bins) // 2 + 1)
    transition_full_dataset['time_bin'] = symmetrical_digitized

    # Average and count by time bin
    cols = ['time_bin', 'lick_flag',  'context', 'whisker_trial']
    bin_averaged_full_data = transition_full_dataset[cols].groupby(['time_bin', 'context', 'whisker_trial'],
                                                                   as_index=False).mean(numeric_only=True)
    bin_count_full_data = transition_full_dataset[cols].groupby(['time_bin', 'context', 'whisker_trial'],
                                                                as_index=False).count()

    # Add here dict for time bin and actual time interval
    x_label_dict = {-1: '10-0', -2: '20-10', -3: '30-20', -4: '40-30',
                    -5: '50-40', -6: '60-50', -7: '70-60', -8: '80-70', -9: '90-80', -10: '100-90',
                    1: '0-10', 2: '10-20', 3: '20-30', 4: '30-40',
                    5: '40-50', 6: '50-60', 7: '60-70', 8: '70-80', 9: '80-90', 10: '90-100'}

    # Figure 1: Time around transition for 1st & last whisker trial of the block
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    sns.boxplot(data=transition_full_dataset, y='Time around transition', x='whisker_trial', hue='context',
                palette=['darkmagenta', 'green'], showfliers=False, whis=[5, 95],
                notch=True, medianprops={"color": "k", "linewidth": 2}, ax=ax)
    ax.axhline(y=0, xmin=0, xmax=1, color='k', linestyle='--')
    ax.set_ylabel('Time around transition (s)')
    ax.set_xlabel('Whisker trial')
    sns.despine()
    fig.tight_layout()
    save_figure(fig, save_path, f"Whisker_trial_timing_distribution", save_formats=save_formats)

    # Figure 2: same than figure 1 but split lick and no lick
    fig = sns.catplot(kind='box', data=transition_full_dataset, y='Time around transition',
                      col='whisker_trial', x='context', hue='lick_flag',
                      showfliers=False, whis=[5, 95],
                      notch=True, medianprops={"color": "k", "linewidth": 2})
    sns.despine()
    for ax in fig.axes.flatten():
        ax.axhline(y=0, xmin=0, xmax=1, color='k', linestyle='--')
    fig.tight_layout()
    save_figure(fig, save_path, f"Whisker_trial_timing_distribution_outcomes", save_formats=save_formats)

    # Figure 3: lick probability over time at whisker trials around transitions both way
    data_to_plot = bin_averaged_full_data.loc[(bin_averaged_full_data.time_bin < 6) &
                                              (bin_averaged_full_data.time_bin > -6)]
    count_to_plot = bin_count_full_data.loc[(bin_count_full_data.time_bin < 6) &
                                            (bin_count_full_data.time_bin > -6)]

    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    ax1 = ax.twinx()

    sns.pointplot(data=data_to_plot, x='time_bin', y='lick_flag', hue='context', palette=['darkmagenta', 'green'],
                  markers='o', ax=ax)
    sns.barplot(data=count_to_plot, x='time_bin',
                y='lick_flag', hue='context', palette=['darkmagenta', 'green'], legend=False, ax=ax1)

    positions = [tick for tick in ax.get_xticks()]
    new_label = [x_label_dict[int(i.get_text())] for i in ax.get_xticklabels()]
    ax.xaxis.set_major_locator(FixedLocator(positions))
    ax.set_xlabel('Time around transition (s)')
    ax.set_xticklabels(new_label)
    ax.axvline(x=np.median(positions), ymin=0, ymax=1, c='k', linestyle='--')
    ax.set_ylim(0, 1.05)
    ax.set_ylabel('Lick Probability')
    ax1.set_ylim(0, 5000)
    ax1.set_yticks(np.arange(0, 900, 200))
    ax1.set_ylabel('Number of trials')
    sns.despine()
    fig.tight_layout()
    save_figure(fig, save_path, f"Lick_probability_around_transitions", save_formats=save_formats)
