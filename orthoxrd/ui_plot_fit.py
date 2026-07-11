from __future__ import annotations

import plotly.graph_objects as go

from orthoxrd.fit_models import FitResult
from orthoxrd.i18n import t
from orthoxrd.ui_plot_theme import ACCENT, SERIES, plot_layout
from orthoxrd.ui_style import AMBER


def plot_chi2_curve(result: FitResult) -> go.Figure:
    """Plot χ²(y) from the grid scan with best y* and local-minimum markers."""
    ys = [point.y for point in result.grid_scan]
    chi2 = [point.chi2 for point in result.grid_scan]
    figure = go.Figure()
    figure.add_scatter(
        x=ys,
        y=chi2,
        mode="lines",
        name=t("fit.plot.chi2"),
        line={"width": 2.2, "color": SERIES[0]},
        hovertemplate="y=%{x:.7g}<br>χ²=%{y:.7g}<extra></extra>",
    )
    if result.local_minima:
        figure.add_scatter(
            x=[item.y for item in result.local_minima],
            y=[item.chi2 for item in result.local_minima],
            mode="markers",
            name=t("fit.plot.local_minima"),
            marker={
                "size": 9,
                "symbol": "diamond",
                "color": AMBER,
                "line": {"width": 1, "color": "#0b0f14"},
            },
            hovertemplate="candidate y=%{x:.7g}<br>χ²=%{y:.7g}<extra></extra>",
        )
    figure.add_vline(
        x=result.best.y,
        line_dash="dash",
        line_color=ACCENT,
        opacity=0.9,
        annotation_text=f"y*={result.best.y:.6g}",
        annotation_position="top right",
        annotation_font={"color": ACCENT, "size": 11},
    )
    figure.update_layout(
        **plot_layout(
            height=420,
            x_title=t("fit.plot.x_y"),
            y_title=t("fit.plot.y_chi2"),
        ),
        hovermode="x unified",
    )
    return figure
