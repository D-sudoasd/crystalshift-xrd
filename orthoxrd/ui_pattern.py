from __future__ import annotations

from typing import cast

import streamlit as st

from orthoxrd.export_rows import current_peak_rows, current_spectrum_rows
from orthoxrd.export_schema import CURRENT_PEAK_FIELDS, CURRENT_SPECTRUM_FIELDS
from orthoxrd.i18n import t, th
from orthoxrd.simulation import SimulationResult
from orthoxrd.ui_live import render_live_view
from orthoxrd.ui_plot_pattern import (
    DisplayKind,
    IntensityKind,
    XAxisKind,
    plot_pattern,
)
from orthoxrd.ui_plot_state import render_plot_state
from orthoxrd.ui_structure_context import structure_context_caption
from orthoxrd.ui_tables import rows_to_csv


def render_pattern_view(result: SimulationResult) -> None:
    st.subheader(t("pattern.title"))
    st.caption(structure_context_caption(result.config.y))
    mode = st.segmented_control(
        t("pattern.mode"),
        ["static", "live"],
        format_func=lambda code: t(f"pattern.mode.{code}"),
        default="static",
        key="pattern_mode",
        help=th("pattern.mode"),
    )
    left, middle, right, label_col = st.columns((1.2, 1.0, 1.0, 0.75))
    with left:
        axis_label = st.segmented_control(
            t("pattern.axis"),
            ["2theta", "q_primary", "d_primary"],
            default="2theta",
            key="pattern_axis",
            help=th("pattern.axis"),
        )
    with middle:
        intensity_label = st.segmented_control(
            t("pattern.intensity"),
            ["relative", "model"],
            format_func=lambda code: t(f"pattern.intensity.{code}"),
            default="relative",
            key="pattern_intensity",
            help=th("pattern.intensity"),
        )
    with right:
        display_label = st.segmented_control(
            t("pattern.display"),
            ["combined", "line", "sticks"],
            format_func=lambda code: t(f"pattern.display.{code}"),
            default="combined",
            key="pattern_display",
            help=th("pattern.display"),
        )
    with label_col:
        show_hkl = st.toggle(
            t("pattern.hkl_labels"),
            value=True,
            key="pattern_hkl_labels",
            help=th("pattern.hkl_labels"),
        )
    axis = cast(XAxisKind, axis_label or "2theta")
    plot_state = render_plot_state(result, axis)
    if mode == "live":
        render_live_view(result, plot_state)
        st.caption(t("pattern.live_caption"))
        return
    intensity: IntensityKind = "model" if intensity_label == "model" else "relative"
    display = cast(DisplayKind, display_label or "combined")
    selected = st.session_state.get("selected_peak_series")
    st.plotly_chart(
        plot_pattern(
            result,
            x_axis=axis,
            intensity=intensity,
            display=display,
            show_hkl=show_hkl,
            selected_series=selected if isinstance(selected, str) else None,
            plot_state=plot_state,
        ),
        width="stretch",
        config={"displaylogo": False, "scrollZoom": True},
    )
    st.caption(t("pattern.static_caption"))
    _downloads(result)


def _downloads(result: SimulationResult) -> None:
    spectrum_rows = list(current_spectrum_rows(result))
    peak_rows = list(current_peak_rows(result))
    left, right = st.columns(2)
    with left:
        st.download_button(
            t("pattern.download_spectrum"),
            rows_to_csv(spectrum_rows, CURRENT_SPECTRUM_FIELDS),
            "spectrum.csv",
            "text/csv",
            key="pattern_spectrum_csv",
            use_container_width=True,
            help=th("pattern.download_spectrum"),
        )
    with right:
        st.download_button(
            t("pattern.download_peaks"),
            rows_to_csv(peak_rows, CURRENT_PEAK_FIELDS),
            "peaks.csv",
            "text/csv",
            key="pattern_peaks_csv",
            use_container_width=True,
            help=th("pattern.download_peaks"),
        )
    st.caption(t("export.csv_excel_hint.current"))
