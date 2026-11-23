# Allen brain masks for the widefield figures

Used by `cicada_petersen.tools.widefield_utils.get_allen_ccf`, which overlays the Allen brain outline on widefield
images (plugins Compare baseline, Widefield baseline diff post transition). Shipped as package data
(`pyproject.toml`, `[tool.setuptools.package-data]`), so they work without access to the lab server.

Source: generated from the Allen Mouse Brain Common Coordinate Framework with the AllenSDK, tilted to match the
Petersen lab widefield images (500 x 640 frame). Copied from the lab server
(`Petersen-Lab/analysis/Robin_Dard/Parameters/Widefield/allen_brain`) on 2026-11-23, unchanged.

| File | Content | Shape, dtype | SHA-256 |
|---|---|---|---|
| `allen_isocortex_tilted_500x640.npy` | isocortex mask | (648, 504) float64 | `f5ef83975fcebb2be4c426685a85024494f59567bcc460b57a6f32507bbf4b08` |
| `allen_brain_tilted_500x640.npy` | brain mask (area outlines, NaN outside) | (648, 504) float64 | `15da0994845bef02e9d6fae7f2c7a52bfdf821f96d9bdb96359c2c0824cbba99` |
| `allen_bregma_tilted_500x640.npy` | bregma (x, y) in the masks | (2,) float64 | `3f41a2114a7909ab52410985036963261e8d337b756adc3981197e64d316ea8c` |

Allen Mouse Brain Common Coordinate Framework: © 2015 Allen Institute for Brain Science, Allen Brain Atlas,
available from https://atlas.brain-map.org/.
