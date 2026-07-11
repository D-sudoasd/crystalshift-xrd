from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
import plotly.graph_objects as go

from orthoxrd.batch_models import SweepResult
from orthoxrd.i18n import t
from orthoxrd.ui_plot_theme import HEATMAP_SCALE, SERIES, TEXT, plot_layout
from orthoxrd.ui_sweep_range import SweepDisplayRange

SpectrumNormalization = Literal["model", "global", "local"]
PeakMetric = Literal["F2", "I_model", "I_rel_global"]


def plot_sweep_heatmap(
    result: SweepResult,
    normalization: SpectrumNormalization = "global",
    display_range: SweepDisplayRange | None = None,
) -> go.Figure:
    matrix = result.spectrum_matrix(normalization)
    point_indices = _sample_indices(matrix.shape[1], 800)
    step_indices = _sample_indices(matrix.shape[0], 300)
    z_values = matrix[np.ix_(step_indices, point_indices)]
    x_values = result.steps[0].two_theta_deg[point_indices]
    y_values = [result.steps[index].step.axis_value for index in step_indices]
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
            y_title=t("sweep.plot.step"),
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
) -> go.Figure:
    matrix = result.spectrum_matrix(normalization)
    point_indices = _sample_indices(matrix.shape[1], 550)
    step_indices = _sample_indices(matrix.shape[0], 36)
    figure = go.Figure()
    for color_index, step_index in enumerate(step_indices):
        step_result = result.steps[step_index]
        figure.add_scatter3d(
            x=step_result.two_theta_deg[point_indices],
            y=np.full(len(point_indices), step_result.step.axis_value),
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
            "yaxis": {"title": result.steps[0].step.axis, "gridcolor": "#2a3441"},
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
) -> go.Figure:
    figure = go.Figure()
    x_values = [step.step.axis_value for step in result.steps]
    for index, series_id in enumerate(series_ids):
        values: list[float] = []
        hkl_label = series_id
        for step_result in result.steps:
            peak = next((item for item in step_result.peaks if item.series_id == series_id), None)
            if peak is None:
                values.append(0.0)
                continue
            hkl_label = f"{peak.line_label} {peak.reflection.hkl_label}"
            if metric == "F2":
                values.append(peak.reflection.structure_factor_squared)
            elif metric == "I_model":
                values.append(peak.reflection.intensity_model)
            else:
                maximum = result.peak_global_max
                values.append(
                    peak.reflection.intensity_model / maximum * 100.0 if maximum > 0 else 0.0
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
    axis = result.steps[0].step.axis
    figure.update_layout(
        **plot_layout(
            height=490,
            x_title=axis,
            y_title=t(f"sweep.metric.{metric}"),
        ),
        hovermode="x unified",
    )
    return figure


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
