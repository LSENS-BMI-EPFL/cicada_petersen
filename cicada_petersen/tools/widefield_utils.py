"""
Petersen lab widefield utilities.

All functions here are specific to the Petersen lab NWB format
(session.widefield, session.petersen.*) or to EPFL NAS file paths.
Generic imaging utilities live in cicada_analysis.cicada_tools.imaging.

Moved from cicada_analysis.cicada_tools.widefield.widefield_petersen_lab_utils (revision B4).
"""
import os
import warnings

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.colors as colors
from matplotlib.colors import TwoSlopeNorm
from skimage.transform import rescale

from cicada_analysis.cicada_tools.display.core_plots import save_figure, get_colormap
from cicada_analysis.cicada_tools.core import find_nearest


def get_wf_scalebar(scale: float = 1) -> int:
    x = [62 * scale, 167 * scale]
    y = [162 * scale, 152 * scale]
    c = np.sqrt((x[1] - x[0]) ** 2 + (y[0] - y[1]) ** 2)
    return round(c / 6)


def get_allen_ccf(bregma: tuple = (528, 315),
                  root: str = r"\\sv-nas1.rcp.epfl.ch\Petersen-Lab\analysis\Robin_Dard\Parameters\Widefield\allen_brain",
                  ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Lab specific :
    Find on lab server the AllenSDK file to generate the npy files used to overlay widefield images and Allen brain
    """

    ## all images aligned to 240,175 at widefield video alignment, after expanding image, goes to this. Set manually.
    iso_mask = np.load(root + r"\allen_isocortex_tilted_500x640.npy")
    atlas_mask = np.load(root + r"\allen_brain_tilted_500x640.npy")
    bregma_coords = np.load(root + r"\allen_bregma_tilted_500x640.npy")

    displacement_x = int(bregma[0] - np.round(bregma_coords[0] + 20))
    displacement_y = int(bregma[1] - np.round(bregma_coords[1]))

    margin_y = atlas_mask.shape[0] - np.abs(displacement_y)
    margin_x = atlas_mask.shape[1] - np.abs(displacement_x)

    if displacement_y >= 0 and displacement_x >= 0:
        atlas_mask[displacement_y:, displacement_x:] = atlas_mask[:margin_y, :margin_x]
        atlas_mask[:displacement_y, :] *= 0
        atlas_mask[:, :displacement_x] *= 0

        iso_mask[displacement_y:, displacement_x:] = iso_mask[:margin_y, :margin_x]
        iso_mask[:displacement_y, :] *= 0
        iso_mask[:, :displacement_x] *= 0

    elif displacement_y < 0 <= displacement_x:
        atlas_mask[:displacement_y, displacement_x:] = atlas_mask[-margin_y:, :margin_x]
        atlas_mask[displacement_y:, :] *= 0
        atlas_mask[:, :displacement_x] *= 0

        iso_mask[:displacement_y, displacement_x:] = iso_mask[-margin_y:, :margin_x]
        iso_mask[displacement_y:, :] *= 0
        iso_mask[:, :displacement_x] *= 0

    elif displacement_y >= 0 > displacement_x:
        atlas_mask[displacement_y:, :displacement_x] = atlas_mask[:margin_y, -margin_x:]
        atlas_mask[:displacement_y, :] *= 0
        atlas_mask[:, displacement_x:] *= 0

        iso_mask[displacement_y:, :displacement_x] = iso_mask[:margin_y, -margin_x:]
        iso_mask[:displacement_y, :] *= 0
        iso_mask[:, displacement_x:] *= 0

    else:
        atlas_mask[:displacement_y, :displacement_x] = atlas_mask[-margin_y:, -margin_x:]
        atlas_mask[displacement_y:, :] *= 0
        atlas_mask[:, displacement_x:] *= 0

        iso_mask[:displacement_y, :displacement_x] = iso_mask[-margin_y:, -margin_x:]
        iso_mask[displacement_y:, :] *= 0
        iso_mask[:, displacement_x:] *= 0

    return iso_mask, atlas_mask, bregma_coords


def plot_wf_single_frame(frame: np.ndarray, title: str, figure, ax_to_plot, suptitle: str,
                         saving_path: str, save_formats, colormap: str = 'hotcold',
                         vmin: float = -0.005, vmax: float = 0.02, halfrange: float = 0.04,
                         cbar_shrink: float = 1.0, separated_plots: bool = True, dpi=300) -> None:
    """

    :param frame: 2d array of shape (px x px)
    :param title: (str) title for the image
    :param figure: (fig) already defined figure onto which add the image
    :param ax_to_plot: (ax) already defined ax of the figure onto which add the image
    :param suptitle: (str) only used if separated_plots is True, main title of each single frame
    :param saving_path: (str) path to save the image series
    :param save_formats: (list of str) formats to use in the saving
    :param colormap: matplotlib colormap to use
    :param vmin: (float) minimal value use in the colormap
    :param vmax: (float) maximal value use in the colormap
    :param halfrange: (float) center value for the seismic colormap used for the image
    :param cbar_shrink: (float) scaler for the colorbar size alongside the image
    :param separated_plots: (bool) use to generate one figure per image in addition to filling predefined figure
    :return: fill the predefined figure and return single image
    """
    subfig, ax = plt.subplots(1, 1, figsize=(4, 4), frameon=False)

    bregma = (488, 290)
    scale = 4
    scalebar = get_wf_scalebar(scale=scale)
    iso_mask, atlas_mask, allen_bregma = get_allen_ccf(bregma)
    cmap = get_colormap(colormap)
    cmap.set_bad(color="white")

    single_frame = np.rot90(rescale(frame, scale, anti_aliasing=False))
    single_frame = np.pad(single_frame, [(0, 650 - single_frame.shape[0]), (0, 510 - single_frame.shape[1])],
                          mode='constant', constant_values=np.nan)

    mask = np.pad(iso_mask, [(0, 650 - iso_mask.shape[0]), (0, 510 - iso_mask.shape[1])], mode='constant',
                  constant_values=np.nan)
    single_frame = np.where(mask > 0, single_frame, np.nan)

    if colormap == 'hotcold':
        cmap = get_colormap('hotcold')
        norm = TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        im = ax_to_plot.imshow(single_frame, norm=norm, cmap=cmap)
        im_2 = ax.imshow(single_frame, norm=norm, cmap=cmap)
        cmap.set_bad(color="white")
    else:
        norm = colors.CenteredNorm(halfrange=halfrange)
        im = ax_to_plot.imshow(single_frame, cmap="seismic", norm=norm)
        im_2 = ax.imshow(single_frame, cmap="seismic", norm=norm)

    ax_to_plot.contour(atlas_mask, levels=np.unique(atlas_mask), colors='gray', linewidths=1)
    ax_to_plot.contour(iso_mask, levels=np.unique(np.round(iso_mask)), colors='black', linewidths=2, zorder=2)
    ax_to_plot.scatter(bregma[0], bregma[1], marker='+', c='k', s=100, linewidths=2, zorder=3)
    ax_to_plot.hlines(25, 25, 25 + scalebar * 3, linewidth=2, colors='k')
    ax_to_plot.text(50, 100, "3 mm", size=10)
    ax_to_plot.set_axis_off()
    ax_to_plot.set_title(title)
    figure.colorbar(im, ax=ax_to_plot, location='right', shrink=cbar_shrink)

    if separated_plots:
        subfig.suptitle(suptitle)
        ax.set_title(title)
        ax.contour(atlas_mask, levels=np.unique(atlas_mask), colors='gray', linewidths=1)
        ax.contour(iso_mask, levels=np.unique(np.round(iso_mask)), colors='black', linewidths=2, zorder=2)
        ax.scatter(bregma[0], bregma[1], marker='+', c='k', s=100, linewidths=2, zorder=3)
        ax.hlines(25, 25, 25 + scalebar * 3, linewidth=2, colors='k')
        ax.text(50, 100, "3 mm", size=10)
        ax.set_axis_off()
        subfig.colorbar(im_2, ax=ax, location='right', shrink=cbar_shrink)
        save_figure(results_path=saving_path, save_formats=save_formats, figure=subfig,
                    figname=f'{suptitle}_{title}' if suptitle != ' ' else f'{title}', dpi=dpi)

    plt.close()


def plot_wf_avg(avg_data: np.ndarray, output_path: str, n_frames_post_stim: int, n_frames_averaged: int,
                key: str, center_frame: int, figname: str, save_formats, subdir: str, do_single_plots=False,
                c_scale: tuple = (-0.005, 0.02), halfrange: float = 0.04, colormap: str = 'hotcold',
                img_size=5, dpi=300) -> None:
    """

    :param avg_data: 3d array of shape (frames x px x px) of a widefield image series
    :param output_path: (str) root path for image series saving
    :param n_frames_post_stim: (int) the number of frames to plot after the center frame
    :param n_frames_averaged: (int) the numer of successive frames to average from the image series
    :param key: (str) use for figure main title
    :param center_frame: (int) the index in the stack of the frame at the 'center' relative to an event, first frame of the series
    :param figname: (str) the name of the figure
    :param save_formats: (list of str) formats to save the image series
    :param subdir: (str) directory to create in the output_path to save the results
    :param do_single_plots: (bool) whether or not to save the single frame plot
    :param c_scale: (tuple) minimal and maximal values for the colorbar
    :param halfrange: (float) central value for diverging colormap
    :param colormap: (str) use to retrieve a matplotlib colormap
    :param img_size: (int) the size of each image of the series
    :param dpi: (int) resolution of the image
    :return: an image series of (n_frames_post_stim / n_frames_averaged) images
    """
    path = os.path.join(output_path, f"{subdir}")
    if not os.path.exists(path):
        os.makedirs(path)

    cutlet_idx = 0
    n_cols = int(np.ceil(n_frames_post_stim / n_frames_averaged))
    fig, axes = plt.subplots(1, n_cols, figsize=(int(img_size * n_cols), int(img_size)), frameon=False)
    fig.suptitle(f'{key}')
    for start in range(center_frame, center_frame + n_frames_post_stim, n_frames_averaged):
        if start + n_frames_averaged > center_frame + n_frames_post_stim:
            break
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            frame_mean = np.nanmean(avg_data[start:start + n_frames_averaged], axis=0)
        plot_wf_single_frame(frame_mean,
                             title=f'Frames #{start - center_frame}-{start - center_frame + n_frames_averaged}',
                             figure=fig, ax_to_plot=axes[cutlet_idx], suptitle=key,
                             colormap=colormap, vmin=c_scale[0], vmax=c_scale[1],
                             halfrange=halfrange, cbar_shrink=0.75,
                             saving_path=path, save_formats=save_formats, separated_plots=do_single_plots, dpi=dpi)
        cutlet_idx += 1
    fig.tight_layout()
    save_figure(results_path=path, save_formats=save_formats, figure=fig, figname=f'{figname}_wf_avg', dpi=dpi)


def trial_type_interpreter(trial_type: str) -> tuple[int, str]:
    """

    :param trial_type: (str) describing the trial type (e.g. whisker_hit_trial)
    :return: (tuple) categorization of the trial type (e.g. (1, whisker_stim))
    """
    lick_flag = 1 if 'hit' in trial_type or 'false_alarm' in trial_type else 0
    if 'whisker' in trial_type:
        stim_type_string = 'whisker_stim'
    elif 'auditory' in trial_type:
        stim_type_string = 'auditory_stim'
    else:
        stim_type_string = 'no_stim'
    return lick_flag, stim_type_string


def trial_type_baseline(trial_type: str, trial_table: pd.DataFrame, rrs_ts: np.ndarray,
                        quiet_window_mode: str, general_img_dict_without_trial_type: dict,
                        general_img_dict: dict, general_img_transition_time_no_type_dict: dict,
                        general_img_transition_time_dict: dict,
                        session_data, mouse_id: str, session_id: str, epoch: str,
                        epoch_starts: list, shape_x: int, shape_y: int) -> None:
    """

    :param trial_type: (str) describing the trial type (e.g. whisker_hit_trial)
    :param trial_table: (table) behavior table of the session
    :param rrs_ts: (1d array) timestamps of the session data should be same length as session data dim 0
    :param quiet_window_mode: (str) how is defined the quiet window
    :param general_img_dict_without_trial_type: (dict) dictionary to extend
    :param general_img_dict: (dict) dictionary to extend
    :param general_img_transition_time_no_type_dict: (dict) dictionary to extend
    :param general_img_transition_time_dict: (dict) dictionary to extend
    :param session_data: (3d array) session data of shape (n frames x px x px)
    :param mouse_id: (str) ID of the mouse
    :param session_id: (str) ID of the session
    :param epoch: (str) ID of the epoch
    :param epoch_starts: (list) timestamps of the epoch start
    :param shape_x: (int) image width
    :param shape_y: (int) image height
    :return: extended dictionary
    """
    context_replace_dict = {'Rewarded': 'rewarded', 'Non-Rewarded': 'non-rewarded'}
    trial_table = trial_table.replace({'context': context_replace_dict})
    lick_flag, stim_type_string = trial_type_interpreter(trial_type)
    trial_type_table = trial_table.loc[(trial_table[stim_type_string] == 1) & (trial_table.lick_flag == lick_flag) &
                                       (trial_table.context == epoch)]
    avg_data_list = []
    time_in_context_list = []
    for trial in range(len(trial_type_table)):
        quiet_start = trial_type_table.iloc[trial].abort_window_start_time
        stim_time = trial_type_table.iloc[trial].start_time
        if quiet_window_mode == 'last 2s':
            start_frame = find_nearest(rrs_ts, stim_time - 2)
        elif quiet_window_mode == 'last 0.5s':
            start_frame = find_nearest(rrs_ts, stim_time - 0.5)
        else:
            start_frame = find_nearest(rrs_ts, quiet_start)
        end_frame = find_nearest(rrs_ts, stim_time)

        filtered_epoch_ts = [t for t in epoch_starts if t < stim_time]
        closest_below = max(filtered_epoch_ts) if filtered_epoch_ts else np.nan
        time_in_context_list.append(stim_time - closest_below)

        data = session_data[start_frame:end_frame, :, :]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            avg_data = np.nanmean(data, axis=0)
        avg_data_list.append(avg_data)

    if len(avg_data_list) == 0:
        print(f'No data to stack for {trial_type}, continue')
        general_img_dict_without_trial_type[mouse_id][session_id][epoch].append(np.full((1, shape_x, shape_y), np.nan))
        general_img_dict[mouse_id][session_id][epoch][trial_type].append(np.full((1, shape_x, shape_y), np.nan))
        return

    avg_img = np.stack(avg_data_list)
    general_img_dict_without_trial_type[mouse_id][session_id][epoch].append(avg_img)
    general_img_dict[mouse_id][session_id][epoch][trial_type].append(avg_img)
    general_img_transition_time_no_type_dict[mouse_id][session_id][epoch].append(time_in_context_list)
    general_img_transition_time_dict[mouse_id][session_id][epoch][trial_type].append(time_in_context_list)


def get_session_average_wf_baseline_images(trial_table: pd.DataFrame, session_data, wf_ts: np.ndarray,
                                           quiet_window_mode: str) -> np.ndarray:
    """

    :param trial_table: (table) behavior table of the session
    :param session_data: (h5) widefield data for the session
    :param wf_ts: (1d array) timestamps of the widefield data, length should match first dim; of session_data
    :param quiet_window_mode: (str) definition of the quiet window
    :return: (2d array) average of quiet windows by trial first across trials after
    """
    avg_data_list = []
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
        data = session_data[start_frame:end_frame, :, :]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            avg_data = np.nanmean(data, axis=0)
        avg_data_list.append(avg_data)
    avg_data_list = np.stack(avg_data_list)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(avg_data_list, axis=0)


def average_images_from_dict(image_dict: dict) -> np.ndarray:
    """
    Convenient recursive function to return a 2d array averaging images from a nested dictionary
    :param image_dict: (dict) nested dictionary
    :return: 2d array averaging images from a nested dictionary
    """
    images = []
    for key, value in image_dict.items():
        if isinstance(value, dict):
            images.append(average_images_from_dict(value))
        elif isinstance(value, list):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                images.append(np.nanmean(np.stack(value), axis=0))
        else:
            images.append(value)
    images = np.stack(images)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return np.nanmean(images, axis=0)
