"""
Petersen lab behavior task tables (trial table columns of the Petersen pipeline: trial_type, context,
lick_flag, abort_window_start_time, mouse_id...).
Moved from cicada_analysis.cicada_tools.behavior.behavior_analysis_utils (revision B4).
"""


import pandas as pd
import numpy as np
import os
import yaml
from cicada_analysis.cicada_tools.core import find_nearest


from cicada_analysis.cicada_tools.behavior.behavior_analysis_utils import get_epoch_frames


def process_data(data, behavior_list, cols, groupby_cols, context_replace_dict=None, reset_idx=False, is_opto=False):
    """
    Process the data based on specified behaviors and columns.

    Parameters:
    action (string):
    data (pd.DataFrame): The input DataFrame containing mouse behavior data.
    behavior_list (list): List of behaviors to filter.
    cols (list): Columns to select for processing.
    groupby_cols (list): Columns to group by for aggregation.
    context_replace_dict (dict): Dictionary for replacing context values.
    reset_idx (bool): Flag to reset the index.

    Returns:
    pd.DataFrame: Processed DataFrame.
    """
    # Keep only specified behaviors
    data = data[data.behavior.isin(behavior_list)]

    if reset_idx:
        data = data.reset_index(drop=True)

    # Add context string column if required
    if context_replace_dict:
        data['context_rwd_str'] = data['context']
        data = data.replace({'context_rwd_str': context_replace_dict})

    # Remove early licks and select columns
    df = data.loc[data.early_lick == 0, cols]

    # Handle NaN values for opto_stim if the column is present
    if 'opto_stim' in df.columns:
        df.fillna({'opto_stim': 0}, inplace=True)
        is_opto = any(df.opto_stim)

    # Average by specified groupby columns
    df_by_day = df.groupby(groupby_cols, as_index=False).agg('mean')

    return df_by_day, is_opto


def cut_session_from_auditory(table, min_miss=3, max_hit=2):
    # If a session does not contain auditory trials, keep whole session.
    # This happens for some test sessions of the GF mice.
    if table.auditory_stim.sum() == 0:
        stop = table.index.max()
    # Get index after which no more than two hits until session end.
    two_hits_left = table.loc[table.auditory_stim == 1, 'lick_flag']
    two_hits_left = (two_hits_left.cumsum() >= (two_hits_left.sum() - max_hit)).idxmax()
    # Find three auditory misses in a row.
    three_aud_misses = table.loc[table.auditory_stim == 1, 'lick_flag']
    three_aud_misses = three_aud_misses.rolling(window=min_miss).sum() == 0
    # Stop flag is the first occurrence of three auditory misses in a row
    # followed by no more than three hits in the rest of the session.
    # In case no three auditory misses keep the whole session.
    if three_aud_misses.sum() == 0:
        stop = table.loc[table.auditory_stim==1, 'trial_id'].idxmax()
    else:
        stop = three_aud_misses.loc[three_aud_misses.index>two_hits_left].idxmax()
        # Stop three trials before the three auditory misses.
        position = three_aud_misses.index.get_loc(stop)
        stop = three_aud_misses.index[position - 3]

    return stop


def add_correct_choice_to_table(table, colname='correct_choice'):
    correct_choice = []
    for i in range(len(table)):
        if table.loc[i].trial_type == 'auditory_trial':
            if table.loc[i].lick_flag == 1:
                correct_choice.append(1)
            else:
                correct_choice.append(0)
        elif table.loc[i].trial_type == 'no_stim_trial':
            if table.loc[i].lick_flag == 0:
                correct_choice.append(1)
            else:
                correct_choice.append(0)
        elif table.loc[i].trial_type == 'whisker_trial':
            if table.loc[i].context == 1:
                if table.loc[i].lick_flag == 1:
                    correct_choice.append(1)
                else:
                    correct_choice.append(0)
            else:
                if table.loc[i].lick_flag == 1:
                    correct_choice.append(0)
                else:
                    correct_choice.append(1)
        else:
            correct_choice.append(0)
    table.insert(loc=len(table.columns), column=colname, value=np.array(correct_choice).astype(bool),
                 allow_duplicates=False)

    return table


def build_standard_behavior_table(nwb_list, cut_session, session_cutoffs, yaml_file_path, result_path):
    """
    Build a behavior table from a list of NWB files containing standardized trial tables.
    :param nwb_list:
    :return:
    """
    bhv_data = []
    session_stop_dict = {}
    for session_index, session_data in enumerate(nwb_list):
        data_frame = session_data.behavior.get_trial_table()
        mouse_id = session_data.subject_id
        behavior_type, day = session_data.petersen.get_bhv_type_and_training_day_index()
        session_id = session_data.session_id
        data_frame['mouse_id'] = [mouse_id for trial in range(len(data_frame.index))]
        data_frame['session_id'] = [session_id for trial in range(len(data_frame.index))]
        data_frame['behavior'] = [behavior_type for trial in range(len(data_frame.index))]
        data_frame['day'] = [day for trial in range(len(data_frame.index))]
        
        # For NWB files without column.
        data_frame['trial_id'] = data_frame.index

        if cut_session == 'manual_cutting':
            data_frame = data_frame.loc[(data_frame.trial_id <= session_cutoffs[1]) &
                                        (data_frame.trial_id >= session_cutoffs[0])]

        elif cut_session == 'adaptive_cutting':
            stop = cut_session_from_auditory(data_frame)
            session_stop_dict[session_id] = (int(0), int(stop))
            data_frame = data_frame.loc[(data_frame.trial_id <= stop)]

        elif cut_session == 'from_yaml':
            # Read the existing data from the YAML file
            if os.path.exists(yaml_file_path['YAML']):
                with open(yaml_file_path['YAML'], 'r') as yaml_file:
                    yaml_data = yaml.safe_load(yaml_file)
                if session_id in yaml_data.keys():
                    data_frame = data_frame.loc[(data_frame.trial_id <= yaml_data[session_id][1]) &
                                                (data_frame.trial_id >= yaml_data[session_id][0])]

        bhv_data.append(data_frame)

    bhv_data = pd.concat(bhv_data, ignore_index=True)

    # Add performance outcome column for each stimulus.
    bhv_data['outcome_w'] = bhv_data.loc[(bhv_data.trial_type == 'whisker_trial')]['lick_flag']
    bhv_data['outcome_a'] = bhv_data.loc[(bhv_data.trial_type == 'auditory_trial')]['lick_flag']
    bhv_data['outcome_n'] = bhv_data.loc[(bhv_data.trial_type == 'no_stim_trial')]['lick_flag']
    # TODO : when reward available is correct
    # bhv_data['correct_choice'] = bhv_data.reward_available == bhv_data.lick_flag
    bhv_data = add_correct_choice_to_table(bhv_data, colname='correct_choice')

    # save adaptive cutting in yaml
    with open(os.path.join(result_path, f"config_session_cutoff.yaml"), 'w') as stream:
        yaml.safe_dump(session_stop_dict, stream, default_flow_style=False, explicit_start=True)

    return bhv_data


def get_standard_single_session_table(combine_bhv_data, session, block_sizes=None, block_size=20):
    """
    Get a single session trial table from the combined behavior table.
    :param combine_bhv_data: combined behavior table from multiple sessions.
    :param session: the session ID to extract.
    :param block_sizes: optional dictionary mapping session IDs to their block size
        (typically derived from the NWB metadata). Used for non-context sessions.
    :param block_size: hard-coded fallback block size, used when neither the context
        switches nor the metadata provide a block size.
    :return:
    """
    session_table = combine_bhv_data.loc[(combine_bhv_data['session_id'] == session)]
    session_table = session_table.loc[session_table.early_lick == 0]
    session_table = session_table.reset_index(drop=True)

    # Find the block length if context
    if session_table['behavior'].values[0] in ["context", 'whisker_context']:
        switches = np.where(np.diff(session_table.context.values[:]))[0]
        if len(switches) <= 1:
            block_length = switches[0] + 1
        else:
            block_length = min(np.diff(switches))
    else:
        switches = None
        # Prefer the block size coming from the session metadata, fall back on the
        # hard-coded default when it is missing or invalid (None / 0).
        metadata_block_size = block_sizes.get(session) if block_sizes else None
        block_length = int(metadata_block_size) if metadata_block_size else block_size

    # Add  trial info
    session_table['trial'] = session_table.index

    # Add block info
    session_table['block'] = session_table['trial'].transform(lambda x: x // block_length)

    # Fix for 'old' NWB : set opto_stim values to 0 and not NaN Todo: remove this condition with new NWBs
    session_table.fillna({'opto_stim': 0}, inplace=True)

    # Compute hit rates. Use transform to propagate hit rate to all entries.
    for outcome, new_col in zip(['outcome_w', 'outcome_a', 'outcome_n', 'correct_choice'],
                                ['hr_w', 'hr_a', 'hr_n', 'correct']):
        session_table[new_col] = session_table.groupby(['block', 'opto_stim'], as_index=False)[outcome].transform(
            'mean')

    return session_table, switches, block_length


def get_single_mouse_table(combine_bhv_data, mouse):
    mouse_table = combine_bhv_data.loc[(combine_bhv_data['mouse_id'] == mouse)]
    mouse_table = mouse_table.reset_index(drop=True)

    return mouse_table


def get_single_session_time_to_switch(combine_bhv_data, n_wh_trials, block_size_sessions=None):
    sessions_list = np.unique(combine_bhv_data['session_id'].values[:])
    to_rewarded_transitions_prob = dict()
    to_non_rewarded_transitions_prob = dict()
    n_trials_around_dict = dict()
    mouse_id_dict = dict()
    day_index_dict = dict()
    for session_id in sessions_list:
        session_table, switches, block_size = get_standard_single_session_table(combine_bhv_data, session=session_id, block_sizes=block_size_sessions)

        # Keep only the session with context
        if session_table['behavior'].values[0] not in ['context', 'whisker_context']:
            continue

        mouse_id_dict[session_id] = session_table.mouse_id.values[0]
        day_index_dict[session_id] = session_table.day.values[0]

        # Keep only the whisker trials
        whisker_session_table = session_table.loc[session_table.trial_type == 'whisker_trial']
        whisker_session_table = whisker_session_table.reset_index(drop=True)

        # extract licks array
        licks = whisker_session_table.outcome_w.values[:]

        # Extract transitions rwd to non rwd and opposite
        rewarded_transitions = np.where(np.diff(whisker_session_table.context.values[:]) == 1)[0]
        non_rewarded_transitions = np.where(np.diff(whisker_session_table.context.values[:]) == -1)[0]

        # Build rewarded transitions matrix from trial -3 to trial +3
        wh_switches = np.where(np.diff(whisker_session_table.context.values[:]))[0]
        if n_wh_trials is None:
            n_trials_around = min(np.diff(wh_switches))
        else:
            n_trials_around = n_wh_trials
        n_trials_around_dict[session_id] = n_trials_around
        trials_above = n_trials_around + 1
        trials_below = n_trials_around - 1

        # Build rewarded transition matrix
        rewarded_transitions_mat = np.zeros((len(rewarded_transitions), 2 * n_trials_around))
        for index, transition in enumerate(list(rewarded_transitions)):
            if transition + trials_above > len(licks):
                rewarded_transitions_mat = rewarded_transitions_mat[0: len(rewarded_transitions) - 1, :]
                continue
            else:
                rewarded_transitions_mat[index, :] = licks[
                    np.arange(transition - trials_below, transition + trials_above)]
        rewarded_transition_prob = np.mean(rewarded_transitions_mat, axis=0)
        to_rewarded_transitions_prob[session_id] = rewarded_transition_prob

        # Build non_rewarded transitions matrix
        non_rewarded_transitions_mat = np.zeros((len(non_rewarded_transitions), 2 * n_trials_around))
        for index, transition in enumerate(list(non_rewarded_transitions)):
            if transition + trials_above > len(licks):
                non_rewarded_transitions_mat = non_rewarded_transitions_mat[0: len(non_rewarded_transitions) - 1, :]
                continue
            else:
                non_rewarded_transitions_mat[index, :] = licks[
                    np.arange(transition - trials_below, transition + trials_above)]
        non_rewarded_transition_prob = np.mean(non_rewarded_transitions_mat, axis=0)
        to_non_rewarded_transitions_prob[session_id] = non_rewarded_transition_prob

    return to_rewarded_transitions_prob, to_non_rewarded_transitions_prob, n_trials_around_dict, mouse_id_dict, \
        day_index_dict


def get_all_quiet_windows(table, reference_ts, quiet_window_mode):
    quiet_window_frames = []
    for trial in range(len(table)):
        quiet_start = table.iloc[trial].abort_window_start_time
        stim_time = table.iloc[trial].start_time
        if quiet_window_mode == 'last 2s':
            start_frame = find_nearest(reference_ts, stim_time - 2)
        elif quiet_window_mode == 'last 0.5s':
            start_frame = find_nearest(reference_ts, stim_time - 0.5)
        else:
            start_frame = find_nearest(reference_ts, quiet_start)
        end_frame = find_nearest(reference_ts, stim_time)
        quiet_window_frames.append(np.arange(start_frame, end_frame))

    return quiet_window_frames


def get_frames_in_stim(trial_table, stim_names, trial_duration, reference_ts):
    stim_table = trial_table.loc[trial_table.trial_type.isin(stim_names)]
    stim_table = stim_table.reset_index(drop=True)
    stim_frames = []
    for trial in range(len(stim_table)):
        stim_time = stim_table.iloc[trial].start_time
        start_frame = int(find_nearest(reference_ts, stim_time))
        end_frame = int(find_nearest(reference_ts, stim_time + trial_duration))
        stim_frames.extend(np.arange(start_frame, end_frame))
    stim_frames = np.array(stim_frames)

    return stim_frames


def get_iti_frames(reference_ts, trial_table=None, epoch_times=None,
                   stim_names=('whisker_trial', 'auditory_trial'), trial_duration=5):
    """
    Return a boolean array marking inter-trial interval (ITI) frames.

    Args:
        reference_ts: 1D array of timestamps matching the signal to analyse (e.g. facemap_timestamps).
        trial_table: DataFrame with trial information used to exclude stimulus-locked frames.
                     If None, stim filtering is skipped.
        epoch_times: (2, n_epochs) array — if provided, only frames within these epochs are kept.
                     Useful to restrict the ITI to a specific behavioural context (e.g. rewarded).
        stim_names: trial_type values treated as stimuli.
        trial_duration: seconds after each stimulus onset to exclude.

    Returns:
        Boolean numpy array of shape (len(reference_ts),) — True for ITI frames.
    """
    iti_frames = np.ones(len(reference_ts), dtype=bool)

    if epoch_times is not None:
        epoch_frame_indices = get_epoch_frames(epoch_times=epoch_times,
                                               reference_ts=reference_ts,
                                               max_idx=len(reference_ts))
        epoch_mask = np.zeros(len(reference_ts), dtype=bool)
        epoch_mask[epoch_frame_indices] = True
        iti_frames &= epoch_mask

    if trial_table is not None and stim_names:
        stim_frame_indices = get_frames_in_stim(trial_table=trial_table,
                                                stim_names=list(stim_names),
                                                trial_duration=trial_duration,
                                                reference_ts=reference_ts)
        iti_frames[stim_frame_indices] = False

    return iti_frames


def get_block_size_from_table(trial_table, fallback=20):
    """
    Compute the number of trials per context block from the trial table.

    Finds the index of the first context transition, which equals the number of
    trials in the first block. Used to build per-trial epoch labels without
    hardcoding the block size.

    Args:
        trial_table (pd.DataFrame): Trial table with a 'context' column.
        fallback (int): Value returned when block size cannot be determined.

    Returns:
        int: Number of trials per context block.
    """
    try:
        transitions = list(np.diff(trial_table['context'].values))
        transitions.insert(0, 0)
        switch_indices = np.where(transitions)[0]
        if len(switch_indices) == 0:
            return fallback
        return int(switch_indices[0])
    except Exception:
        return fallback


def get_n_trials_per_block_from_table(trial_table, trial_type='whisker_trial', fallback=8):
    """
    Compute the number of trials of a given type per context block.

    Filters the table to rows matching `trial_type`, then counts rows before
    the first context transition — i.e. the number of occurrences of that trial
    type in the first complete block. Works for any trial type (whisker, auditory,
    catch, etc.).

    Args:
        trial_table (pd.DataFrame): Full trial table with 'trial_type' and 'context' columns.
        trial_type (str): Trial type to count (default: 'whisker_trial').
        fallback (int): Value returned when the count cannot be determined.

    Returns:
        int: Number of trials of the specified type per context block.
    """
    try:
        filtered = trial_table.loc[trial_table['trial_type'] == trial_type].reset_index(drop=True)
        if len(filtered) == 0:
            return fallback
        transitions = np.diff(filtered['context'].values)
        switch_indices = np.where(transitions != 0)[0]
        if len(switch_indices) == 0:
            return fallback
        return int(switch_indices[0] + 1)
    except Exception:
        return fallback
