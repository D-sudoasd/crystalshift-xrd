from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
import plotly.graph_objects as go

from orthoxrd.i18n import t
from orthoxrd.structure_factor import analytic_unit_structure_factor_squared
from orthoxrd.ui_plot_theme import SERIES, plot_layout

F2Axis = Literal["y", "signed_shuffle", "shuffle_magnitude"]
F2Branch = Literal["lower", "upper"]


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
    y_values = _y_values(x_values, axis, branch)
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
        rows.extend(
            {"axis_value": float(x_value), "hkl": label, "F2": float(f2_value)}
            for x_value, f2_value in zip(x_values, f2_values, strict=True)
        )
    figure.add_vline(
        x=_x_from_y(active_y, axis),
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


def _y_values(values: np.ndarray, axis: F2Axis, branch: F2Branch) -> np.ndarray:
    if axis == "y":
        return values
    if axis == "signed_shuffle":
        return 0.25 + values / 2.0
    sign = -1.0 if branch == "lower" else 1.0
    return 0.25 + sign * values / 2.0


def _x_from_y(y_value: float, axis: F2Axis) -> float:
    signed = 2.0 * (y_value - 0.25)
    if axis == "y":
        return y_value
    if axis == "signed_shuffle":
        return signed
    return abs(signed)
