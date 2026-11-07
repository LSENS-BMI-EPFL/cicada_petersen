"""
Petersen-lab-specific NWB submodule.

Contains methods that interpret NWB fields according to Petersen lab conventions:
  - experiment_description stored as a Python dict string
  - session_description encoded as underscore-delimited behavior type + day index
  - whisker reward metadata
"""

import ast
import numpy as np
from cicada_nwb.lab_submodules.base import NWBLabSubmodule


class NWBPetersenLab(NWBLabSubmodule):

    name = "petersen"

    @classmethod
    def grouping_factors(cls):
        return {
            "Behavior type":  "petersen.behavior_session_type",
            "Whisker rewarded": "petersen.whisker_rewarded",
            "Session type":   "petersen.session_type",
            "Session description":    "metadata.session_description",
            "Experiment description": "metadata.experiment_description",
        }

    # ----------------------------------------------------------------
    # Session metadata (experiment_description parsed as dict)
    # ----------------------------------------------------------------

    def get_session_metadata(self):
        """
        Parse experiment_description as a Python dict (Petersen lab convention).
        Returns the parsed dict, the raw string if parsing fails, or None.
        """
        desc = self._nwb.experiment_description
        if desc is None:
            return None
        try:
            return ast.literal_eval(desc.replace("nan", "None"))
        except (SyntaxError, ValueError):
            return desc

    def get_experimental_block_size(self):
        """
        Get experimental block size from metadata.
        """
        session_metadata = self.get_session_metadata()
        if not isinstance(session_metadata, dict):
            return None

        block_size = sum([v for k, v in session_metadata.items() if (('weight' in k) and ('reference' not in k))])

        return block_size

    def get_session_type(self):
        """Return the session type from parsed metadata, or None."""
        meta = self.get_session_metadata()
        if isinstance(meta, dict):
            return meta.get('session_type', None)
        return None

    def session_type(self):
        """Return session type string for GUI grouping, or 'NS'."""
        result = self.get_session_type()
        return result if result is not None else 'NS'

    # ----------------------------------------------------------------
    # Behavior type and training day (session_description convention)
    # ----------------------------------------------------------------

    def get_bhv_type_and_training_day_index(self):
        """
        Parse behavior type and training day from session_description.
        Petersen lab convention: underscore-delimited fields.
        Returns (behavior_type, day) or (None, None).
        """
        desc = self._nwb.session_description
        if desc is None:
            return None, None
        try:
            parts = desc.split('_')
            if parts[0] == 'free':
                return parts[0] + '_' + parts[1], int(parts[2])
            if parts[1] == 'psy':
                return parts[0] + '_' + parts[1], int(parts[2])
            if parts[1] == 'on':
                return parts[0] + '_' + parts[1] + '_' + parts[2], int(parts[2])
            if parts[1] == 'off':
                return parts[0] + '_' + parts[1], 1
            if parts[1] == 'context':
                return parts[0] + '_' + parts[1], int(parts[2])
            return parts[0], int(parts[1])
        except (IndexError, ValueError):
            return None, None

    def behavior_session_type(self):
        """Return behavior type string for GUI grouping, or 'NS'."""
        bhv_type, _ = self.get_bhv_type_and_training_day_index()
        return bhv_type if bhv_type is not None else 'NS'

    # ----------------------------------------------------------------
    # Whisker reward
    # ----------------------------------------------------------------

    def get_whisker_rewarded_sessions(self):
        """Return 'whisker rewarded' or 'whisker not rewarded', or None."""
        meta = self.get_session_metadata()
        if not isinstance(meta, dict):
            return None
        wh = meta.get('wh_reward', None)
        if wh is None:
            return None
        return 'whisker rewarded' if wh == 1 else 'whisker not rewarded'

    def whisker_rewarded(self):
        """Return whisker reward status for GUI grouping, or 'NS'."""
        result = self.get_whisker_rewarded_sessions()
        return result if result is not None else 'NS'

    # ----------------------------------------------------------------
    # Facemap (Petersen pipeline: series 'motion_energy' / 'motion_svd', SVD images in acquisition)
    # ----------------------------------------------------------------

    def get_facemap_data(self, image_acquisition_name):
        """
        Return facemap data dict from the BehavioralTimeSeries of the behavior module and an Images acquisition.
        Keys: 'motion_energy', 'motion_svd', 'timestamps', 'svd_images'.
        Returns None if no behavior module or no BehavioralTimeSeries.
        """
        processing = self._nwb.processing
        bhv = next((processing[name] for name in ('behavior', 'Behavior') if name in processing), None)
        if bhv is None:
            return None
        try:
            bts = bhv.get(name='BehavioralTimeSeries')
        except KeyError:
            return None

        result = {}
        ts = bts.time_series
        if 'motion_energy' in ts:
            result['motion_energy'] = np.array(ts['motion_energy'].data[:])
        if 'motion_svd' in ts:
            result['motion_svd'] = np.array(ts['motion_svd'].data[:])
            result['timestamps'] = np.array(ts['motion_svd'].timestamps[:])

        images_list = getattr(self._nwb.acquisition.get(image_acquisition_name), 'images', None)     # None if not Images
        if images_list is None:
            result['svd_images'] = []
        else:
            svd_images = [images_list[f'SVD_im_{i}'].data[:] for i in range(len(images_list))]
            result['svd_images'] = np.stack(svd_images)

        return result