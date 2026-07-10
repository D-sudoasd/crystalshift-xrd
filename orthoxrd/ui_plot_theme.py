from __future__ import annotations

from typing import Any

from orthoxrd.ui_style import ACCENT, BORDER, CANVAS, GRID, MUTED, SURFACE, TEXT

SERIES = (
    "#22c7d6",
    "#f2b84b",
    "#ff7b86",
    "#8ea6ff",
    "#48c78e",
    "#d58cff",
    "#ff9f58",
    "#70b7ff",
)
HEATMAP_SCALE = [
    [0.0, "#0b0f14"],
    [0.18, "#152634"],
    [0.42, "#176579"],
    [0.68, "#22c7d6"],
    [1.0, "#f2d06b"],
]


def plot_layout(
    *,
    height: int,
    x_title: str,
    y_title: str,
    show_legend: bool = True,
) -> dict[str, Any]:
    axis = {
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": BORDER,
        "zeroline": False,
        "ticks": "outside",
        "tickfont": {"color": MUTED},
        "title": {"font": {"color": TEXT}},
        "automargin": True,
    }
    return {
        "height": height,
        "margin": {"l": 58, "r": 24, "t": 28, "b": 54},
        "paper_bgcolor": CANVAS,
        "plot_bgcolor": SURFACE,
        "font": {"color": TEXT, "size": 12},
        "hoverlabel": {"bgcolor": SURFACE, "bordercolor": BORDER, "font_color": TEXT},
        "xaxis": {**axis, "title": x_title},
        "yaxis": {**axis, "title": y_title},
        "showlegend": show_legend,
        "legend": {
            "orientation": "h",
            "y": 1.04,
            "x": 0,
            "font": {"color": TEXT},
            "bgcolor": "rgba(0,0,0,0)",
        },
        "colorway": list(SERIES),
    }


__all__ = [
    "ACCENT",
    "HEATMAP_SCALE",
    "MUTED",
    "SERIES",
    "TEXT",
    "plot_layout",
]
