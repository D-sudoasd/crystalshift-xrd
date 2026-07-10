from __future__ import annotations

from typing import Any

import streamlit as st

from orthoxrd.export_rows import current_peak_rows
from orthoxrd.export_schema import CURRENT_PEAK_FIELDS, CsvValue
from orthoxrd.simulation import SimulationResult
from orthoxrd.ui_plot_pattern import plot_pattern
from orthoxrd.ui_tables import rows_to_csv


def render_peaks_view(result: SimulationResult) -> None:
    st.subheader("Bragg peaks")
    all_rows = [dict(row) for row in current_peak_rows(result)]
    filtered = _filter_rows(all_rows, result)
    st.caption(
        f"Showing {len(filtered):,} of {len(all_rows):,} calculated peak rows. "
        "Scroll the table horizontally for all fields; CSV exports include every column."
    )
    event = st.dataframe(
        filtered,
        width="stretch",
        height=470,
        hide_index=True,
        key="peaks_table",
        on_select="rerun",
        selection_mode="single-row",
        column_order=list(CURRENT_PEAK_FIELDS),
    )
    selected_index = _selected_index(event)
    if selected_index is not None and selected_index < len(filtered):
        selected = filtered[selected_index]
        series_id = str(selected["series_id"])
        st.session_state["selected_peak_series"] = series_id
        st.caption(
            f"Selected {selected['line']} {selected['hkl']} | "
            f"2theta={float(selected['two_theta_deg']):.6f} deg | {series_id}"
        )
        st.plotly_chart(
            plot_pattern(
                result,
                x_axis="2theta",
                intensity="relative",
                display="combined",
                show_hkl=False,
                selected_series=series_id,
            ),
            width="stretch",
            config={"displaylogo": False},
        )
    _downloads(all_rows, filtered)


def _filter_rows(
    rows: list[dict[str, CsvValue]],
    result: SimulationResult,
) -> list[dict[str, CsvValue]]:
    col_hkl, col_line, col_intensity = st.columns((1.0, 1.25, 1.0))
    with col_hkl:
        hkl_query = st.text_input(
            "HKL filter",
            placeholder="e.g. 110 or 02",
            key="peaks_hkl_filter",
        ).strip()
    line_options = list(dict.fromkeys(str(row["line"]) for row in rows))
    with col_line:
        selected_lines = st.multiselect(
            "Radiation line",
            line_options,
            default=line_options,
            key="peaks_line_filter",
        )
    with col_intensity:
        minimum_intensity = float(
            st.number_input(
                "Minimum I_rel (%)",
                min_value=0.0,
                max_value=100.0,
                value=result.config.min_peak,
                step=0.1,
                key="peaks_intensity_filter",
            )
        )
    angle_range = st.slider(
        "2theta filter (deg)",
        min_value=float(result.config.two_theta_min),
        max_value=float(result.config.two_theta_max),
        value=(float(result.config.two_theta_min), float(result.config.two_theta_max)),
        step=0.05,
        key="peaks_angle_filter",
    )
    return [
        row
        for row in rows
        if (not hkl_query or hkl_query in str(row["hkl"]))
        and str(row["line"]) in selected_lines
        and float(row["I_rel_local"]) >= minimum_intensity
        and angle_range[0] <= float(row["two_theta_deg"]) <= angle_range[1]
    ]


def _downloads(
    all_rows: list[dict[str, CsvValue]],
    filtered: list[dict[str, CsvValue]],
) -> None:
    left, right = st.columns(2)
    with left:
        st.download_button(
            "All peaks CSV",
            rows_to_csv(all_rows, CURRENT_PEAK_FIELDS),
            "peaks_all.csv",
            "text/csv",
            key="peaks_all_csv",
            use_container_width=True,
        )
    with right:
        st.download_button(
            "Filtered peaks CSV",
            rows_to_csv(filtered, CURRENT_PEAK_FIELDS),
            "peaks_filtered.csv",
            "text/csv",
            key="peaks_filtered_csv",
            use_container_width=True,
        )


def _selected_index(event: Any) -> int | None:
    selection = getattr(event, "selection", None)
    rows = getattr(selection, "rows", ())
    return int(rows[0]) if rows else None
