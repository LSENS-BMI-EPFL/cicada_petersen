"""
3D plots of units in Allen CCF coordinates (Petersen lab: bregma-relative coordinates, iblatlas brain surface).
Moved from cicada_analysis.cicada_tools.ephys.ccf_plot_utils (revision B4).
"""


import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage import measure
from cicada_analysis.cicada_tools.ephys.anatomy_utils import AREA_GROUP_COLORS


BREGMA_ML_UM = 5739.0
BREGMA_AP_UM = 5400.0
BREGMA_DV_UM = 332.0
_AMBIGUOUS = {'root', 'fiber tracts', 'cc', 'fxs', 'lfbst', 'mfbc', 'Unassigned', 'unknown', 'Other'}
_COORD_SFX = ('_ap', '_ml', '_dv')
_LABEL_KW  = ('ccf', 'location', 'atlas', 'region')


def collect_coordinates(units_tables: dict, quality_labels: list) -> pd.DataFrame:
    """Extract bregma-relative CCF coordinates from a dict of units DataFrames.

    Args:
        units_tables:   ``{session_id: units_df}`` mapping.
        quality_labels: list of ``bc_label`` values to keep (e.g. ``['good', 'mua']``).

    Returns:
        DataFrame with columns: session, ap_um, ml_um, dv_um, plus any
        ccf/location/atlas/region label columns found in the units table.
        Coordinates are in µm relative to bregma.  ML is mirrored to the left
        hemisphere when the session median falls on the right side.
    """
    rows = []
    for session_id, units_df in units_tables.items():
        if units_df is None or units_df.empty:
            continue
        if 'bc_label' in units_df.columns:
            units_df = units_df[units_df['bc_label'].isin(quality_labels)]
        if units_df.empty:
            continue

        ap = BREGMA_AP_UM - units_df['ccf_atlas_ap'].values
        ml = units_df['ccf_atlas_ml'].values - BREGMA_ML_UM
        dv = BREGMA_DV_UM - units_df['ccf_atlas_dv'].values
        if len(ml) and float(np.median(ml)) > 0:
            ml = -ml

        label_cols = {
            c: units_df[c].fillna('unknown').values
            for c in units_df.columns
            if any(kw in c for kw in _LABEL_KW) and not c.endswith(_COORD_SFX)
        }
        for j in range(len(units_df)):
            row = {'session': session_id, 'ap_um': ap[j], 'ml_um': ml[j], 'dv_um': dv[j]}
            for c, vals in label_cols.items():
                row[c] = vals[j]
            rows.append(row)

    return pd.DataFrame(rows)


def build_color_scheme(df: pd.DataFrame, color_by: str) -> tuple:
    """Build a colour mapping for a categorical column in *df*.

    Args:
        df:       DataFrame produced by :func:`collect_coordinates`.
        color_by: column name present in *df*, or ``'area_group'`` to use the
                  canonical Allen-atlas-inspired palette from :data:`AREA_GROUP_COLORS`.

    Returns:
        ``(col, ordered_labels, color_dict)`` where *ordered_labels* lists
        non-ambiguous labels first (sorted by frequency) followed by ambiguous
        ones, and *color_dict* maps each label to a hex colour string.
    """
    if color_by not in df.columns:
        raise ValueError(f'color_by column {color_by!r} not found in DataFrame')

    col = color_by
    all_labels = df[col].dropna().unique()

    if color_by == 'area_group':
        named = sorted(lbl for lbl in all_labels if lbl not in _AMBIGUOUS)
        last  = sorted(lbl for lbl in all_labels if lbl in _AMBIGUOUS)
        ordered = named + last
        colors = {lbl: AREA_GROUP_COLORS.get(lbl, '#CCCCCC') for lbl in ordered}
    else:
        named = sorted(lbl for lbl in all_labels if lbl not in _AMBIGUOUS)
        last  = sorted(lbl for lbl in all_labels if lbl in _AMBIGUOUS)
        ordered = named + last
        palette = sns.color_palette('tab20', n_colors=max(len(named), 1))
        colors = {lbl: f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
                  for lbl, (r, g, b) in zip(named, palette)}
        for lbl in last:
            colors[lbl] = '#CCCCCC'

    return col, ordered, colors


def build_brain_surface(ba, decimate: int = 3) -> tuple:
    """Build a left-hemisphere brain surface mesh via marching cubes.

    Args:
        ba:       ``iblatlas.atlas.AllenAtlas`` instance (caller's responsibility
                  to import and construct).
        decimate: stride applied to the label volume before marching cubes —
                  higher values are faster but produce a coarser mesh.

    Returns:
        ``(ap_um, ml_um, dv_um, faces)`` — vertex coordinates in µm relative to
        bregma and a face index array suitable for Plotly ``Mesh3d`` or
        ``mpl_toolkits.mplot3d.art3d.Poly3DCollection``.
    """
    print('Computing brain surface mesh …')
    label = ba.label[::decimate, ::decimate, ::decimate]
    brain_mask = label != 0

    verts, faces, _, _ = measure.marching_cubes(
        brain_mask.astype(np.float32), level=0.5, step_size=1,
    )
    res = ba.res_um * decimate
    ap_um = (ba.bc.y0 * 1e6) + verts[:, 0] * res * np.sign(ba.bc.dy)
    ml_um = (ba.bc.x0 * 1e6) + verts[:, 1] * res * np.sign(ba.bc.dx)
    dv_um = (ba.bc.z0 * 1e6) + verts[:, 2] * res * np.sign(ba.bc.dz)

    keep = ml_um <= 200
    vert_map = np.full(len(verts), -1, dtype=int)
    vert_map[keep] = np.arange(keep.sum())
    ap_um = ap_um[keep]
    ml_um = ml_um[keep]
    dv_um = dv_um[keep]
    faces = vert_map[faces[keep[faces].all(axis=1)]]

    print(f'  mesh: {len(ap_um):,} vertices, {len(faces):,} faces')
    return ap_um, ml_um, dv_um, faces


def make_plotly_figure(df: pd.DataFrame, mesh, color_by: str = 'region',
                       title_tag: str = ''):
    """Build an interactive Plotly 3D scatter of unit CCF coordinates.

    Args:
        df:        DataFrame from :func:`collect_coordinates`.
        mesh:      ``(ap_um, ml_um, dv_um, faces)`` from :func:`build_brain_surface`,
                   or ``None`` to omit the surface.
        color_by:  ``'region'`` or ``'ccf_acronym'``.
        title_tag: string appended to the figure title.

    Returns:
        ``plotly.graph_objects.Figure``  (caller must have plotly installed).
    """
    import plotly.graph_objects as go

    col, ordered, colors = build_color_scheme(df, color_by)

    traces = []
    if mesh is not None:
        ap_m, ml_m, dv_m, faces = mesh
        traces.append(go.Mesh3d(
            x=ml_m, y=ap_m, z=dv_m,
            i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
            color='lightgrey', opacity=0.12,
            flatshading=False, lighting=dict(ambient=0.8, diffuse=0.5),
            showscale=False, name='Brain surface', hoverinfo='skip',
        ))

    for label in ordered:
        sub = df[df[col] == label]
        if sub.empty:
            continue
        is_bg = label in _AMBIGUOUS
        color = colors.get(label, '#888888')
        traces.append(go.Scatter3d(
            x=sub['ml_um'], y=sub['ap_um'], z=sub['dv_um'],
            mode='markers',
            marker=dict(size=2 if is_bg else 3, color=color,
                        opacity=0.15 if is_bg else 0.7, line=dict(width=0)),
            name=label,
            text=sub['session'] + '<br>' + sub[col],
            hovertemplate='<b>%{text}</b><br>ML=%{x:.0f} AP=%{y:.0f} DV=%{z:.0f}<extra></extra>',
        ))

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=f'Unit CCF coordinates [{color_by}] — {title_tag}', font_size=13),
        scene=dict(
            xaxis=dict(title='ML (µm)', backgroundcolor='white', gridcolor='#ddd'),
            yaxis=dict(title='AP (µm)', backgroundcolor='white', gridcolor='#ddd'),
            zaxis=dict(title='DV (µm)', backgroundcolor='white', gridcolor='#ddd'),
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=-1.5, z=0.8)),
        ),
        legend=dict(itemsizing='constant', font_size=11),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='white',
    )
    return fig


def make_rotation_animation(df: pd.DataFrame, mesh, color_by: str = 'region',
                             title_tag: str = '', n_frames: int = 120,
                             fps: int = 30) -> tuple:
    """Build a rotating matplotlib 3D animation of unit CCF coordinates.

    Args:
        df:        DataFrame from :func:`collect_coordinates`.
        mesh:      ``(ap_um, ml_um, dv_um, faces)`` or ``None``.
        color_by:  ``'region'`` or ``'ccf_acronym'``.
        title_tag: string appended to the axes title.
        n_frames:  total number of animation frames (one full rotation).
        fps:       frames per second used when saving.

    Returns:
        ``(fig, anim)`` — matplotlib Figure and FuncAnimation.
    """
    col, ordered, colors = build_color_scheme(df, color_by)

    fig = plt.figure(figsize=(8, 7), dpi=150)
    ax = fig.add_subplot(111, projection='3d')

    poly = None
    if mesh is not None:
        ap_m, ml_m, dv_m, faces = mesh
        verts = np.column_stack([ml_m, ap_m, dv_m])
        stride = max(1, len(faces) // 8000)
        face_verts = verts[faces[::stride]]
        poly = Poly3DCollection(face_verts, alpha=0.06, facecolor='lightgrey',
                                edgecolor='none', zorder=0)
        ax.add_collection3d(poly)

    for label in ordered:
        sub = df[df[col] == label]
        if sub.empty:
            continue
        is_bg = label in _AMBIGUOUS
        ax.scatter(sub['ml_um'], sub['ap_um'], sub['dv_um'],
                   c=colors.get(label, '#888888'),
                   s=0.5 if is_bg else 2.0,
                   alpha=0.15 if is_bg else 0.6,
                   linewidths=0,
                   label=label if not is_bg else '_nolegend_',
                   rasterized=True)

    ax.set_xlabel('ML (µm)', fontsize=7, labelpad=2)
    ax.set_ylabel('AP (µm)', fontsize=7, labelpad=2)
    ax.set_zlabel('DV (µm)', fontsize=7, labelpad=2)
    ax.tick_params(labelsize=6)
    ax.set_title(f'Unit CCF [{color_by}] — {title_tag}', fontsize=8, pad=4)
    ax.legend(loc='upper left', fontsize=6, frameon=False,
              markerscale=3, bbox_to_anchor=(-0.05, 1.05))

    def update(frame):
        ax.view_init(elev=20, azim=frame * 360 / n_frames)
        return (poly,) if poly is not None else ()

    anim = animation.FuncAnimation(fig, update, frames=n_frames,
                                   interval=1000 / fps, blit=False)
    return fig, anim
