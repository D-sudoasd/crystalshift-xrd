from __future__ import annotations

import math
from typing import Literal

import numpy as np
import plotly.graph_objects as go

from orthoxrd.i18n import t
from orthoxrd.simulation import CalculatedPeak, SimulationResult
from orthoxrd.ui_plot_state import PlotState
from orthoxrd.ui_plot_theme import ACCENT, SERIES, plot_layout

XAxisKind = Literal["2theta", "q_primary", "d_primary"]
IntensityKind = Literal["model", "relative"]
DisplayKind = Literal["line", "sticks", "combined"]


def plot_pattern(
    result: SimulationResult,
    *,
    x_axis: XAxisKind,
    intensity: IntensityKind,
    display: DisplayKind,
    show_hkl: bool,
    selected_series: str | None = None,
    plot_state: PlotState | None = None,
) -> go.Figure:
    wavelength = result.config.lines[0].wavelength_a
    x_values = _transform(result.spectrum.two_theta_deg, wavelength, x_axis)
    y_values = (
        result.spectrum.intensity_model
        if intensity == "model"
        else result.spectrum.intensity_rel_local
    )
    peaks = tuple(
        peak for peak in result.peaks if peak.reflection.intensity_scaled >= result.config.min_peak
    )
    figure = go.Figure()
    if display in {"line", "combined"}:
        figure.add_scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            name=t("plot.trace.model") if intensity == "model" else t("plot.trace.relative"),
            line={"color": ACCENT, "width": 1.8},
            hovertemplate="%{x:.7g}<br>I=%{y:.7g}<extra></extra>",
        )
    if display in {"sticks", "combined"}:
        _add_sticks(figure, peaks, wavelength, x_axis, intensity, selected_series)
    if show_hkl:
        _add_labels(figure, peaks, wavelength, x_axis, intensity)
    x_title = t(f"plot.x_title.{x_axis}")
    y_title = t("plot.y_title.model") if intensity == "model" else t("plot.y_title.relative")
    figure.update_layout(
        **plot_layout(height=510, x_title=x_title, y_title=y_title),
        hovermode="x unified",
        barmode="overlay",
    )
    if plot_state is None and x_axis == "d_primary":
        figure.update_xaxes(autorange="reversed")
    elif plot_state is not None:
        x_range = (
            [plot_state.x_maximum, plot_state.x_minimum]
            if x_axis == "d_primary"
            else [plot_state.x_minimum, plot_state.x_maximum]
        )
        figure.update_xaxes(range=x_range)
        if not plot_state.y_auto:
            figure.update_yaxes(range=[plot_state.y_minimum, plot_state.y_maximum])
        figure.update_layout(
            uirevision=f"{x_axis}:{plot_state.x_minimum:.12g}:{plot_state.x_maximum:.12g}"
        )
    return figure


def _add_sticks(
    figure: go.Figure,
    peaks: tuple[CalculatedPeak, ...],
    wavelength: float,
    x_axis: XAxisKind,
    intensity: IntensityKind,
    selected_series: str | None,
) -> None:
    regular = tuple(peak for peak in peaks if peak.series_id != selected_series)
    selected = tuple(peak for peak in peaks if peak.series_id == selected_series)
    for name, values, color, width in (
        (t("plot.trace.bragg"), regular, "rgba(242,184,75,.45)", 0.02),
        (t("plot.trace.selected"), selected, SERIES[2], 0.035),
    ):
        if not values:
            continue
        x_values = _transform(
            np.asarray([peak.reflection.two_theta_deg for peak in values]),
            wavelength,
            x_axis,
        )
        heights = [
            peak.reflection.intensity_model
            if intensity == "model"
            else peak.reflection.intensity_scaled
            for peak in values
        ]
        figure.add_bar(
            x=x_values,
            y=heights,
            width=width,
            name=name,
            marker={"color": color},
            customdata=[
                [peak.line_label, peak.reflection.hkl_label, peak.series_id] for peak in values
            ],
            hovertemplate=(
                "%{customdata[0]} %{customdata[1]}"
                "<br>x=%{x:.7g}<br>I=%{y:.7g}<br>%{customdata[2]}<extra></extra>"
            ),
        )


def _add_labels(
    figure: go.Figure,
    peaks: tuple[CalculatedPeak, ...],
    wavelength: float,
    x_axis: XAxisKind,
    intensity: IntensityKind,
) -> None:
    strongest = sorted(peaks, key=lambda peak: peak.reflection.intensity_scaled, reverse=True)[:12]
    if not strongest:
        return
    x_values = _transform(
        np.asarray([peak.reflection.two_theta_deg for peak in strongest]),
        wavelength,
        x_axis,
    )
    heights = [
        peak.reflection.intensity_model
        if intensity == "model"
        else peak.reflection.intensity_scaled
        for peak in strongest
    ]
    figure.add_scatter(
        x=x_values,
        y=heights,
        mode="text",
        text=[peak.reflection.hkl_label for peak in strongest],
        textposition="top center",
        textfont={"size": 10, "color": "#d9e0e8"},
        showlegend=False,
        hoverinfo="skip",
    )


def _transform(
    two_theta_deg: np.ndarray,
    wavelength_a: float,
    kind: XAxisKind,
) -> np.ndarray:
    values = np.asarray(two_theta_deg, dtype=np.float64)
    if kind == "2theta":
        return values
    theta = np.deg2rad(values / 2.0)
    q_values = 4.0 * math.pi * np.sin(theta) / wavelength_a
    if kind == "q_primary":
        return q_values
    return np.divide(
        2.0 * math.pi,
        q_values,
        out=np.full_like(q_values, np.nan),
        where=q_values > 0,
    )
