"""Behavior table helpers on tables cut as the trimmed demo files are (index not from 0, partial blocks)."""
import numpy as np
import pandas as pd

from cicada_petersen.tools.behavior_utils import add_correct_choice_to_table, get_context_start_per_trial


def test_add_correct_choice_to_table_index_not_from_zero():
    table = pd.DataFrame({'trial_type': ['auditory_trial', 'no_stim_trial', 'whisker_trial', 'whisker_trial'],
                          'lick_flag': [1, 1, 1, 0], 'context': [1, 1, 0, 0]}, index=[135, 136, 137, 138])
    out = add_correct_choice_to_table(table, colname='correct_trial')
    assert out['correct_trial'].tolist() == [True, False, False, True]
    assert list(out.index) == [135, 136, 137, 138]


def test_context_start_per_trial_partial_first_block():
    trial_t = np.array([1313.2, 1319.9, 1352.8, 1362.8, 1429.3])
    starts = get_context_start_per_trial(trial_t, [1359.16, 1310.6])
    assert starts.tolist() == [1310.6, 1310.6, 1310.6, 1359.16, 1359.16]


def test_context_start_per_trial_before_first_epoch_and_on_start():
    starts = get_context_start_per_trial([5.0, 10.0, 25.0], [10.0, 20.0])
    assert starts.tolist() == [10.0, 10.0, 20.0]
