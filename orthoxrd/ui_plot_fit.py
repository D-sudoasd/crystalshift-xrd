from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

import plotly.graph_objects as go

from orthoxrd.fit_models import FitResult
from orthoxrd.i18n import t
from orthoxrd.structure_coordinates import (
    StructureAxis,
    structure_coordinate_from_y,
)
from orthoxrd.ui_plot_theme import ACCENT, SERIES, plot_layout
from orthoxrd.ui_style import AMBER


class _FitCurvePoint(Protocol):
    @property
    def y(self) -> float: ...

    @property
    def scale_s(self) -> float: ...

    @property
    def chi2(self) -> float: ...


def plot_chi2_curve(
    result: FitResult,
    display_axis: StructureAxis = "y",
) -> go.Figure:
    """Plot the grid, refine trace and best point for the fitted objective.

    ``result`` remains canonical in Wyckoff ``y``.  ``display_axis`` is a
    presentation-only projection.  Shuffle magnitude is two-to-one, therefore
    lower and upper branches are emitted as separate traces and never joined.
    """
    figure = go.Figure()
    _add_projected_curve(
        figure,
        result.grid_scan,
        display_axis,
        value=lambda point: point.chi2,
        role="grid",
        name=t("fit.plot.chi2"),
        color=SERIES[0],
        mode="lines",
    )
    _add_projected_curve(
        figure,
        result.refine_trace,
        display_axis,
        value=lambda point: point.chi2,
        role="refine",
        name=t("fit.plot.refine_trace"),
        color=SERIES[1],
        mode="lines+markers",
    )
    _add_projected_markers(
        figure,
        result.local_minima,
        display_axis,
        value=lambda point: point.chi2,
        role="local_minima",
        name=t("fit.plot.local_minima"),
        color=AMBER,
        symbol="diamond",
    )
    _add_best_marker(
        figure,
        result,
        display_axis,
        result.best.chi2,
    )
    figure.update_layout(
        **plot_layout(
            height=420,
            x_title=t(f"axis.{display_axis}"),
            y_title=t("fit.plot.y_chi2"),
        ),
        hovermode="closest" if display_axis == "shuffle_magnitude" else "x unified",
    )
    return figure


def plot_scale_curve(
    result: FitResult,
    display_axis: StructureAxis = "y",
) -> go.Figure:
    """Plot the closed-form optimal scale ``S`` across the scan and refinement."""
    figure = go.Figure()
    _add_projected_curve(
        figure,
        result.grid_scan,
        display_axis,
        value=lambda point: point.scale_s,
        role="grid",
        name=t("fit.plot.scale"),
        color=SERIES[0],
        mode="lines",
    )
    _add_projected_curve(
        figure,
        result.refine_trace,
        display_axis,
        value=lambda point: point.scale_s,
        role="refine",
        name=t("fit.plot.refine_trace"),
        color=SERIES[1],
        mode="lines+markers",
    )
    _add_best_marker(
        figure,
        result,
        display_axis,
        result.best.scale_s,
    )
    figure.update_layout(
        **plot_layout(
            height=420,
            x_title=t(f"axis.{display_axis}"),
            y_title=t("fit.plot.y_scale"),
        ),
        hovermode="closest" if display_axis == "shuffle_magnitude" else "x unified",
    )
    return figure


def plot_observed_vs_fitted(result: FitResult) -> go.Figure:
    """Plot observed peak strength against the best-fit scaled model strength."""
    residuals = result.residuals_at_best
    observed = [item.I_obs for item in residuals]
    fitted = [item.S_I_model for item in residuals]
    labels = [_hkl_label(item.h, item.k, item.l) for item in residuals]
    figure = go.Figure()
    if residuals:
        lower = min(observed + fitted)
        upper = max(observed + fitted)
        if lower == upper:
            padding = abs(lower) * 0.05 or 1.0
            lower -= padding
            upper += padding
        figure.add_scatter(
            x=[lower, upper],
            y=[lower, upper],
            mode="lines",
            name=t("fit.plot.parity_line"),
            line={"width": 1.5, "dash": "dash", "color": SERIES[2]},
            hoverinfo="skip",
            meta={"role": "parity_line"},
        )
    figure.add_scatter(
        x=observed,
        y=fitted,
        text=labels,
        customdata=[
            [item.line_label, item.residual, item.weight, item.included]
            for item in residuals
        ],
        mode="markers+text",
        textposition="top center",
        name=t("fit.plot.observations"),
        marker={
            "size": 9,
            "color": [SERIES[0] if item.included else AMBER for item in residuals],
            "line": {"width": 1, "color": "#0b0f14"},
        },
        hovertemplate=(
            "HKL=%{text}<br>line=%{customdata[0]}<br>"
            "I_obs=%{x:.7g}<br>S*I_model=%{y:.7g}<br>"
            "residual=%{customdata[1]:.7g}<br>weight=%{customdata[2]:.7g}"
            "<extra></extra>"
        ),
        meta={"role": "observations"},
    )
    figure.update_layout(
        **plot_layout(
            height=430,
            x_title=t("fit.plot.x_observed"),
            y_title=t("fit.plot.y_fitted"),
        ),
    )
    figure.update_yaxes(scaleanchor="x", scaleratio=1)
    return figure


def plot_residual_contributions(result: FitResult) -> go.Figure:
    """Plot each included peak's ``weight * residual**2`` contribution to χ²."""
    included = [item for item in result.residuals_at_best if item.included]
    labels = [
        f"{_hkl_label(item.h, item.k, item.l)} · {item.line_id}" for item in included
    ]
    contributions = [item.weight * item.residual**2 for item in included]
    figure = go.Figure()
    figure.add_bar(
        x=labels,
        y=contributions,
        customdata=[
            [item.line_label, item.residual, item.weight, item.I_obs, item.S_I_model]
            for item in included
        ],
        name=t("fit.plot.chi2_contribution"),
        marker={"color": SERIES[0]},
        hovertemplate=(
            "peak=%{x}<br>line=%{customdata[0]}<br>"
            "residual=%{customdata[1]:.7g}<br>weight=%{customdata[2]:.7g}<br>"
            "I_obs=%{customdata[3]:.7g}<br>S*I_model=%{customdata[4]:.7g}<br>"
            "w*residual^2=%{y:.7g}<extra></extra>"
        ),
        meta={"role": "chi2_contribution"},
    )
    figure.update_layout(
        **plot_layout(
            height=430,
            x_title=t("fit.plot.x_hkl"),
            y_title=t("fit.plot.y_chi2_contribution"),
            show_legend=False,
        ),
    )
    return figure


def _add_projected_curve(
    figure: go.Figure,
    points: Sequence[_FitCurvePoint],
    display_axis: StructureAxis,
    *,
    value: Callable[[_FitCurvePoint], float],
    role: str,
    name: str,
    color: str,
    mode: str,
) -> None:
    for branch, branch_points in _projected_branches(points, display_axis):
        if not branch_points:
            continue
        x_values = [structure_coordinate_from_y(point.y, display_axis) for point in branch_points]
        y_values = [value(point) for point in branch_points]
        branch_suffix = f" ({t(f'branch.{branch}')})" if branch is not None else ""
        figure.add_scatter(
            x=x_values,
            y=y_values,
            customdata=[point.y for point in branch_points],
            mode=mode,
            name=f"{name}{branch_suffix}",
            legendgroup=f"{role}:{branch or 'single'}",
            line={"width": 2.2, "color": color},
            marker={"size": 6, "color": color},
            hovertemplate=(
                "%{x:.7g}<br>y=%{customdata:.7g}<br>%{y:.7g}<extra></extra>"
            ),
            meta={"role": role, **({"branch": branch} if branch is not None else {})},
        )


def _add_projected_markers(
    figure: go.Figure,
    points: Sequence[_FitCurvePoint],
    display_axis: StructureAxis,
    *,
    value: Callable[[_FitCurvePoint], float],
    role: str,
    name: str,
    color: str,
    symbol: str,
) -> None:
    if not points:
        return
    figure.add_scatter(
        x=[structure_coordinate_from_y(point.y, display_axis) for point in points],
        y=[value(point) for point in points],
        customdata=[point.y for point in points],
        mode="markers",
        name=name,
        marker={
            "size": 9,
            "symbol": symbol,
            "color": color,
            "line": {"width": 1, "color": "#0b0f14"},
        },
        hovertemplate="%{x:.7g}<br>y=%{customdata:.7g}<br>%{y:.7g}<extra></extra>",
        meta={"role": role},
    )


def _add_best_marker(
    figure: go.Figure,
    result: FitResult,
    display_axis: StructureAxis,
    value: float,
) -> None:
    figure.add_scatter(
        x=[structure_coordinate_from_y(result.best.y, display_axis)],
        y=[value],
        customdata=[result.best.y],
        mode="markers",
        name=t("fit.plot.best"),
        marker={
            "size": 11,
            "symbol": "star",
            "color": ACCENT,
            "line": {"width": 1, "color": "#0b0f14"},
        },
        hovertemplate="%{x:.7g}<br>y=%{customdata:.7g}<br>%{y:.7g}<extra></extra>",
        meta={"role": "best"},
    )


def _projected_branches(
    points: Sequence[_FitCurvePoint],
    display_axis: StructureAxis,
) -> tuple[tuple[str | None, tuple[_FitCurvePoint, ...]], ...]:
    if display_axis != "shuffle_magnitude":
        return ((None, tuple(points)),)
    zero_shuffle = tuple(point for point in points if point.y == 0.25)
    lower = tuple(point for point in points if point.y < 0.25)
    upper = tuple(point for point in points if point.y > 0.25)
    if lower and upper:
        return (("lower", lower + zero_shuffle), ("upper", zero_shuffle + upper))
    if lower:
        return (("lower", lower + zero_shuffle),)
    if upper:
        return (("upper", zero_shuffle + upper),)
    return ((None, zero_shuffle),)


def _hkl_label(h: int, k: int, l: int) -> str:
    return f"{h}{k}{l}"


__all__ = [
    "plot_chi2_curve",
    "plot_observed_vs_fitted",
    "plot_residual_contributions",
    "plot_scale_curve",
]
