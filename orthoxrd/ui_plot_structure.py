from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go

from orthoxrd.structure_geometry import CmcmShuffleGeometry, ShuffleSiteGeometry, Vector3
from orthoxrd.ui_style import ACCENT, BORDER, CANVAS, GRID, MUTED, SURFACE, TEXT


@dataclass(frozen=True, slots=True)
class StructurePlotLabels:
    cell: str = "cell"
    reference: str = "y=0.25 reference"
    current: str = "current Cmcm 4c"
    shuffle_path: str = "shuffle paths"
    shuffle_arrow: str = "shuffle arrowheads"


def plot_cmcm_shuffle_structure(
    geometry: CmcmShuffleGeometry,
    labels: StructurePlotLabels | None = None,
) -> go.Figure:
    """Render the current Cmcm 4c sites against the zero-shuffle reference."""
    active_labels = labels or StructurePlotLabels()
    figure = go.Figure()
    figure.add_trace(_cell_trace(geometry, name=active_labels.cell))
    figure.add_trace(
        _site_trace(geometry.sites, reference=True, name=active_labels.reference)
    )
    has_displacement = any(
        abs(component) > 1e-12
        for site in geometry.sites
        for component in site.displacement_cartesian_a
    )
    if has_displacement:
        figure.add_trace(
            _shuffle_path_trace(geometry.sites, name=active_labels.shuffle_path)
        )
        figure.add_trace(_shuffle_cone_trace(geometry, name=active_labels.shuffle_arrow))
    figure.add_trace(
        _site_trace(geometry.sites, reference=False, name=active_labels.current)
    )
    axis = {
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": BORDER,
        "zeroline": False,
        "tickfont": {"color": MUTED},
        "title": {"font": {"color": TEXT}},
        "backgroundcolor": SURFACE,
    }
    figure.update_layout(
        height=540,
        margin={"l": 0, "r": 0, "t": 28, "b": 0},
        paper_bgcolor=CANVAS,
        font={"color": TEXT, "size": 12},
        hoverlabel={"bgcolor": SURFACE, "bordercolor": BORDER, "font_color": TEXT},
        legend={
            "orientation": "h",
            "x": 0.0,
            "y": 1.02,
            "bgcolor": "rgba(0,0,0,0)",
        },
        scene={
            "xaxis": {**axis, "title": "a (Å)"},
            "yaxis": {**axis, "title": "b (Å)"},
            "zaxis": {**axis, "title": "c (Å)"},
            "aspectmode": "data",
            "camera": {
                "eye": {"x": 1.45, "y": 1.6, "z": 1.15},
                "projection": {"type": "orthographic"},
            },
        },
    )
    return figure


def _cell_trace(geometry: CmcmShuffleGeometry, *, name: str) -> go.Scatter3d:
    x_values: list[float | None] = []
    y_values: list[float | None] = []
    z_values: list[float | None] = []
    for edge in geometry.cell_edges:
        for point in (edge.start_cartesian_a, edge.end_cartesian_a):
            x_values.append(point[0])
            y_values.append(point[1])
            z_values.append(point[2])
        x_values.append(None)
        y_values.append(None)
        z_values.append(None)
    return go.Scatter3d(
        x=x_values,
        y=y_values,
        z=z_values,
        mode="lines",
        name=name,
        line={"color": MUTED, "width": 3},
        hoverinfo="skip",
    )


def _site_trace(
    sites: tuple[ShuffleSiteGeometry, ...],
    *,
    reference: bool,
    name: str,
) -> go.Scatter3d:
    points = tuple(
        site.reference_cartesian_a if reference else site.current_cartesian_a for site in sites
    )
    fractions = tuple(
        site.reference_fractional if reference else site.current_fractional for site in sites
    )
    x_values, y_values, z_values = _components(points)
    customdata = [
        [site.site_index, *fraction, site.displacement_cartesian_a[1]]
        for site, fraction in zip(sites, fractions, strict=True)
    ]
    return go.Scatter3d(
        x=x_values,
        y=y_values,
        z=z_values,
        mode="markers",
        name=name,
        marker={
            "size": 7 if reference else 10,
            "color": MUTED if reference else ACCENT,
            "opacity": 0.38 if reference else 0.95,
            "line": {"color": TEXT, "width": 1},
        },
        customdata=customdata,
        hovertemplate=(
            "4c site %{customdata[0]}"
            "<br>fractional=(%{customdata[1]:.6g}, %{customdata[2]:.6g}, "
            "%{customdata[3]:.6g})"
            "<br>Δb=%{customdata[4]:+.6g} Å<extra></extra>"
        ),
    )


def _shuffle_path_trace(
    sites: tuple[ShuffleSiteGeometry, ...],
    *,
    name: str,
) -> go.Scatter3d:
    x_values: list[float | None] = []
    y_values: list[float | None] = []
    z_values: list[float | None] = []
    for site in sites:
        for point in (site.reference_cartesian_a, site.current_cartesian_a):
            x_values.append(point[0])
            y_values.append(point[1])
            z_values.append(point[2])
        x_values.append(None)
        y_values.append(None)
        z_values.append(None)
    return go.Scatter3d(
        x=x_values,
        y=y_values,
        z=z_values,
        mode="lines",
        name=name,
        line={"color": "#f2b84b", "width": 6},
        hoverinfo="skip",
        showlegend=False,
    )


def _shuffle_cone_trace(geometry: CmcmShuffleGeometry, *, name: str) -> go.Cone:
    current = tuple(site.current_cartesian_a for site in geometry.sites)
    displacements = tuple(site.displacement_cartesian_a for site in geometry.sites)
    x_values, y_values, z_values = _components(current)
    u_values, v_values, w_values = _components(displacements)
    return go.Cone(
        x=x_values,
        y=y_values,
        z=z_values,
        u=u_values,
        v=v_values,
        w=w_values,
        name=name,
        anchor="tip",
        sizemode="absolute",
        sizeref=min(geometry.lattice.a, geometry.lattice.b, geometry.lattice.c) * 0.055,
        colorscale=[[0.0, "#f2b84b"], [1.0, "#f2b84b"]],
        showscale=False,
        hoverinfo="skip",
    )


def _components(points: tuple[Vector3, ...]) -> tuple[list[float], list[float], list[float]]:
    return (
        [point[0] for point in points],
        [point[1] for point in points],
        [point[2] for point in points],
    )


__all__ = ["StructurePlotLabels", "plot_cmcm_shuffle_structure"]
