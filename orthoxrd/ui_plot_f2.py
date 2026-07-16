from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go

from orthoxrd.i18n import t
from orthoxrd.structure_coordinates import StructureAxis as F2Axis
from orthoxrd.structure_coordinates import StructureBranch as F2Branch
from orthoxrd.structure_coordinates import (
    structure_branch_from_y,
    structure_coordinate_from_y,
    y_from_structure_coordinate,
)
from orthoxrd.structure_factor import analytic_unit_structure_factor_squared
from orthoxrd.ui_plot_theme import SERIES, plot_layout


def plot_f2_evolution(
    hkls: Sequence[tuple[int, int, int]],
    *,
    axis: F2Axis,
    start: float,
    stop: float,
    points: int,
    branch: F2Branch,
    active_y: float,
) -> tuple[go.Figure, list[dict[str, float | str]]]:
    x_values = np.linspace(start, stop, points, dtype=np.float64)
    y_values = np.asarray(
        [
            y_from_structure_coordinate(
                float(value),
                axis,
                branch=branch if axis == "shuffle_magnitude" else None,
            )
            for value in x_values
        ],
        dtype=np.float64,
    )
    figure = go.Figure()
    rows: list[dict[str, float | str]] = []
    for index, (h_value, k_value, l_value) in enumerate(hkls):
        label = f"{h_value}{k_value}{l_value}"
        f2_values = np.asarray(
            [
                analytic_unit_structure_factor_squared(
                    h_value,
                    k_value,
                    l_value,
                    float(y_value),
                )
                for y_value in y_values
            ],
            dtype=np.float64,
        )
        figure.add_scatter(
            x=x_values,
            y=f2_values,
            mode="lines",
            name=label,
            line={"width": 2, "color": SERIES[index % len(SERIES)]},
            hovertemplate=f"HKL {label}<br>x=%{{x:.7g}}<br>F2=%{{y:.7g}}<extra></extra>",
        )
        for x_value, y_value, f2_value in zip(
            x_values,
            y_values,
            f2_values,
            strict=True,
        ):
            canonical_y = float(y_value)
            signed = structure_coordinate_from_y(canonical_y, "signed_shuffle")
            row_branch = structure_branch_from_y(canonical_y)
            rows.append(
                {
                    "axis_value": float(x_value),
                    "hkl": label,
                    "F2": float(f2_value),
                    "axis_code": axis,
                    "y": canonical_y,
                    "shuffle_signed": signed,
                    "shuffle_magnitude": abs(signed),
                    "branch": row_branch if row_branch is not None else "reference",
                }
            )
    active_branch = structure_branch_from_y(active_y)
    active_x = _x_from_y(active_y, axis)
    if (
        start <= active_x <= stop
        and (
            axis != "shuffle_magnitude"
            or active_branch is None
            or active_branch == branch
        )
    ):
        figure.add_vline(
            x=active_x,
            line_dash="dash",
            line_color="#f3f6fa",
            opacity=0.75,
        )
    figure.update_layout(
        **plot_layout(
            height=480,
            x_title=t(f"f2.x_title.{axis}"),
            y_title=t("f2.y_title"),
        ),
        hovermode="x unified",
    )
    return figure, rows


def _x_from_y(y_value: float, axis: F2Axis) -> float:
    return structure_coordinate_from_y(y_value, axis)
