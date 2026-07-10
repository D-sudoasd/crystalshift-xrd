from __future__ import annotations

from typing import cast

import streamlit as st

from orthoxrd.export_rows import current_peak_rows, current_spectrum_rows
from orthoxrd.export_schema import CURRENT_PEAK_FIELDS, CURRENT_SPECTRUM_FIELDS
from orthoxrd.simulation import SimulationResult
from orthoxrd.ui_live import render_live_view
from orthoxrd.ui_plot_pattern import (
    DisplayKind,
    IntensityKind,
    XAxisKind,
    plot_pattern,
)
from orthoxrd.ui_plot_state import render_plot_state
from orthoxrd.ui_tables import rows_to_csv


def render_pattern_view(result: SimulationResult) -> None:
    st.subheader("Theoretical powder pattern")
    mode = st.segmented_control(
        "Pattern mode",
        ["Static", "Live evolution"],
        default="Static",
        key="pattern_mode",
    )
    left, middle, right, label_col = st.columns((1.2, 1.0, 1.0, 0.75))
    with left:
        axis_label = st.segmented_control(
            "Horizontal axis",
            ["2theta", "q_primary", "d_primary"],
            default="2theta",
            key="pattern_axis",
        )
    with middle:
        intensity_label = st.segmented_control(
            "Intensity",
            ["Relative", "Model"],
            default="Relative",
            key="pattern_intensity",
        )
    with right:
        display_label = st.segmented_control(
            "Display",
            ["Combined", "Line", "Sticks"],
            default="Combined",
            key="pattern_display",
        )
    with label_col:
        show_hkl = st.toggle("HKL labels", value=True, key="pattern_hkl_labels")
    axis = cast(XAxisKind, axis_label or "2theta")
    plot_state = render_plot_state(result, axis)
    if mode == "Live evolution":
        render_live_view(result, plot_state)
        st.caption(
            "Each slider position is an exact backend frame; no frame interpolation is used."
        )
        return
    intensity: IntensityKind = "model" if intensity_label == "Model" else "relative"
    display = cast(
        DisplayKind,
        {
            "Combined": "combined",
            "Line": "line",
            "Sticks": "sticks",
        }.get(display_label or "Combined", "combined"),
    )
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
    st.caption(
        "Model intensity is calculated, uncalibrated intensity. "
        "q_primary and d_primary use the primary wavelength."
    )
    _downloads(result)


def _downloads(result: SimulationResult) -> None:
    spectrum_rows = list(current_spectrum_rows(result))
    peak_rows = list(current_peak_rows(result))
    left, right = st.columns(2)
    with left:
        st.download_button(
            "Spectrum CSV",
            rows_to_csv(spectrum_rows, CURRENT_SPECTRUM_FIELDS),
            "spectrum.csv",
            "text/csv",
            key="pattern_spectrum_csv",
            use_container_width=True,
        )
    with right:
        st.download_button(
            "Peak table CSV",
            rows_to_csv(peak_rows, CURRENT_PEAK_FIELDS),
            "peaks.csv",
            "text/csv",
            key="pattern_peaks_csv",
            use_container_width=True,
        )
