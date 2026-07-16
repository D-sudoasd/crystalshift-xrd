from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise
from typing import Literal

import numpy as np
import plotly.graph_objects as go

from orthoxrd.batch_models import SweepResult
from orthoxrd.i18n import t
from orthoxrd.peak_metrics import PeakMetric, peak_metric_value
from orthoxrd.structure_coordinates import (
    StructureAxis,
    structure_coordinate_from_y,
)
from orthoxrd.ui_plot_theme import HEATMAP_SCALE, SERIES, TEXT, plot_layout
from orthoxrd.ui_sweep_range import SweepDisplayRange

SpectrumNormalization = Literal["model", "global", "local"]


def plot_sweep_heatmap(
    result: SweepResult,
    normalization: SpectrumNormalization = "global",
    display_range: SweepDisplayRange | None = None,
    *,
    display_axis: StructureAxis | None = None,
) -> go.Figure:
    matrix = result.spectrum_matrix(normalization)
    point_indices = _sample_indices(matrix.shape[1], 800)
    step_indices = _sample_indices(matrix.shape[0], 300)
    z_values = matrix[np.ix_(step_indices, point_indices)]
    x_values = result.steps[0].two_theta_deg[point_indices]
    all_axis_values, axis_title = _display_axis(result, display_axis)
    y_values = [all_axis_values[index] for index in step_indices]
    step_labels = [result.steps[index].step.label for index in step_indices]
    title = {
        "model": t("sweep.plot.i_model"),
        "global": t("sweep.plot.i_global"),
        "local": t("sweep.plot.i_local"),
    }[normalization]
    figure = go.Figure(
        go.Heatmap(
            x=x_values,
            y=y_values,
            z=z_values,
            customdata=np.asarray(step_labels)[:, None],
            colorscale=HEATMAP_SCALE,
            colorbar={"title": title, "tickfont": {"color": TEXT}},
            hovertemplate=(
                "2theta=%{x:.6g}<br>axis=%{y:.7g}<br>"
                "step=%{customdata}<br>I=%{z:.6g}<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        **plot_layout(
            height=max(430, min(720, 300 + len(step_indices) * 3)),
            x_title=t("sweep.plot.two_theta"),
            y_title=axis_title,
            show_legend=False,
        )
    )
    if display_range is not None:
        figure.update_xaxes(
            range=[display_range.two_theta_minimum, display_range.two_theta_maximum]
        )
        figure.update_yaxes(
            range=[display_range.axis_minimum, display_range.axis_maximum]
        )
    return figure


def plot_sweep_waterfall(
    result: SweepResult,
    normalization: SpectrumNormalization = "global",
    display_range: SweepDisplayRange | None = None,
    *,
    display_axis: StructureAxis | None = None,
) -> go.Figure:
    matrix = result.spectrum_matrix(normalization)
    point_indices = _sample_indices(matrix.shape[1], 550)
    step_indices = _sample_indices(matrix.shape[0], 36)
    axis_values, axis_title = _display_axis(result, display_axis)
    figure = go.Figure()
    for color_index, step_index in enumerate(step_indices):
        step_result = result.steps[step_index]
        figure.add_scatter3d(
            x=step_result.two_theta_deg[point_indices],
            y=np.full(len(point_indices), axis_values[step_index]),
            z=matrix[step_index, point_indices],
            mode="lines",
            name=step_result.step.label,
            line={"width": 3, "color": SERIES[color_index % len(SERIES)]},
            hovertemplate=(
                f"{step_result.step.label}<br>2theta=%{{x:.6g}}<br>I=%{{z:.6g}}<extra></extra>"
            ),
        )
    figure.update_layout(
        height=590,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        paper_bgcolor="#0b0f14",
        font={"color": TEXT},
        showlegend=False,
        scene={
            "bgcolor": "#121821",
            "xaxis": {"title": t("sweep.plot.two_theta"), "gridcolor": "#2a3441"},
            "yaxis": {"title": axis_title, "gridcolor": "#2a3441"},
            "zaxis": {"title": t("sweep.plot.intensity"), "gridcolor": "#2a3441"},
            "camera": {"eye": {"x": 1.5, "y": -1.8, "z": 1.1}},
        },
    )
    if display_range is not None:
        figure.update_layout(
            scene_xaxis_range=[
                display_range.two_theta_minimum,
                display_range.two_theta_maximum,
            ],
            scene_yaxis_range=[
                display_range.axis_minimum,
                display_range.axis_maximum,
            ],
        )
    return figure


def plot_peak_evolution(
    result: SweepResult,
    series_ids: Sequence[str],
    metric: PeakMetric,
    *,
    display_axis: StructureAxis | None = None,
) -> go.Figure:
    figure = go.Figure()
    x_values, axis_title = _display_axis(result, display_axis)
    for index, series_id in enumerate(series_ids):
        values: list[float] = []
        hkl_label = series_id
        for step_result in result.steps:
            peak = next((item for item in step_result.peaks if item.series_id == series_id), None)
            if peak is None:
                values.append(0.0)
                continue
            hkl_label = f"{peak.line_label} {peak.reflection.hkl_label}"
            values.append(
                peak_metric_value(
                    peak.reflection,
                    metric,
                    peak_global_max=result.peak_global_max,
                )
            )
        figure.add_scatter(
            x=x_values,
            y=values,
            mode="lines+markers",
            name=hkl_label,
            line={"width": 2, "color": SERIES[index % len(SERIES)]},
            marker={"size": 4},
            hovertemplate="%{x:.7g}<br>%{y:.7g}<extra></extra>",
        )
    figure.update_layout(
        **plot_layout(
            height=490,
            x_title=axis_title,
            y_title=t(f"sweep.metric.{metric}"),
        ),
        hovermode="x unified",
    )
    return figure


def sweep_display_axis_options(result: SweepResult) -> tuple[StructureAxis, ...]:
    """Safe post-calculation structure coordinates for a structure sweep.

    Signed shuffle is a one-to-one linear projection of canonical ``y``.  Shuffle
    magnitude folds both branches onto the same coordinate, so it is intentionally
    withheld when a y sweep crosses the zero-shuffle point at ``y=0.25``.  A CSV
    trajectory is projectable only when its canonical y values are strictly
    monotonic; otherwise its row-order coordinate remains the only safe axis.
    """
    native_axis = result.steps[0].step.axis
    y_values = [step.step.y for step in result.steps]
    if native_axis == "trajectory" and not _is_strictly_monotonic(y_values):
        return ()
    if native_axis not in {"y", "shuffle_magnitude", "trajectory"}:
        return ()
    options: list[StructureAxis] = ["y", "signed_shuffle"]
    if not (min(y_values) < 0.25 < max(y_values)):
        options.append("shuffle_magnitude")
    return tuple(options)


def _is_strictly_monotonic(values: Sequence[float]) -> bool:
    if len(values) < 2:
        return False
    return all(left < right for left, right in pairwise(values)) or all(
        left > right for left, right in pairwise(values)
    )


def _display_axis(
    result: SweepResult,
    display_axis: StructureAxis | None,
) -> tuple[list[float], str]:
    if display_axis is None:
        native_axis = result.steps[0].step.axis
        return (
            [step.step.axis_value for step in result.steps],
            t(f"axis.{native_axis}"),
        )
    options = sweep_display_axis_options(result)
    if display_axis not in options:
        if display_axis == "shuffle_magnitude" and {
            "y",
            "signed_shuffle",
        } <= set(options):
            raise ValueError(
                "shuffle magnitude display is ambiguous because the sweep crosses y=0.25"
            )
        raise ValueError(
            f"{display_axis} is not a safe display coordinate for this sweep"
        )
    return (
        [
            structure_coordinate_from_y(step.step.y, display_axis)
            for step in result.steps
        ],
        t(f"axis.{display_axis}"),
    )


def available_series(result: SweepResult) -> tuple[tuple[str, str], ...]:
    found: dict[str, str] = {}
    for step_result in result.steps:
        for peak in step_result.peaks:
            found.setdefault(
                peak.series_id,
                f"{peak.line_label} {peak.reflection.hkl_label}",
            )
    return tuple(found.items())


def _sample_indices(length: int, maximum: int) -> np.ndarray:
    if length <= maximum:
        return np.arange(length)
    return np.linspace(0, length - 1, maximum, dtype=int)
