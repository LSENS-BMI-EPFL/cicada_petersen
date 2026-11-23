"""The Allen brain masks ship with the package: get_allen_ccf loads them without the lab server."""
import hashlib
import os

import numpy as np

from cicada_petersen.tools.widefield_utils import ALLEN_CCF_DIR, get_allen_ccf

SHA256 = {
    "allen_isocortex_tilted_500x640.npy": "f5ef83975fcebb2be4c426685a85024494f59567bcc460b57a6f32507bbf4b08",
    "allen_brain_tilted_500x640.npy": "15da0994845bef02e9d6fae7f2c7a52bfdf821f96d9bdb96359c2c0824cbba99",
    "allen_bregma_tilted_500x640.npy": "3f41a2114a7909ab52410985036963261e8d337b756adc3981197e64d316ea8c",
}


def test_allen_ccf_files_shipped_unchanged():
    for name, digest in SHA256.items():
        with open(os.path.join(ALLEN_CCF_DIR, name), "rb") as f:
            assert hashlib.sha256(f.read()).hexdigest() == digest, name


def test_get_allen_ccf_loads_packaged_masks():
    iso_mask, atlas_mask, bregma_coords = get_allen_ccf((488, 290))
    assert iso_mask.shape == atlas_mask.shape == (648, 504)
    assert bregma_coords.shape == (2,)
    assert np.nanmax(iso_mask) > 0
