from __future__ import annotations

from typing import cast

import streamlit as st

from orthoxrd.export_schema import CsvValue
from orthoxrd.simulation import SimulationResult
from orthoxrd.ui_plot_f2 import F2Axis, F2Branch, plot_f2_evolution
from orthoxrd.ui_tables import rows_to_csv

DEFAULT_HKLS = ("110", "020", "021", "131")


def render_f2_view(result: SimulationResult) -> None:
    st.subheader("Structure-factor evolution")
    st.caption(
        "Analytical unit-scatterer Cmcm 4c F2. Peak-profile, LP, multiplicity, "
        "composition, and volume factors are intentionally excluded."
    )
    hkl_options = _hkl_options(result)
    selected = st.multiselect(
        "HKL series (maximum 12)",
        hkl_options,
        default=[value for value in DEFAULT_HKLS if value in hkl_options],
        max_selections=12,
        key="f2_hkls",
    )
    axis_label = st.segmented_control(
        "Evolution axis",
        ["Wyckoff y", "Signed shuffle", "Shuffle magnitude"],
        default="Shuffle magnitude",
        key="f2_axis",
    )
    axis = cast(
        F2Axis,
        {
            "Wyckoff y": "y",
            "Signed shuffle": "signed_shuffle",
            "Shuffle magnitude": "shuffle_magnitude",
        }[axis_label or "Shuffle magnitude"],
    )
    branch: F2Branch = "lower"
    if axis == "shuffle_magnitude":
        branch_label = st.segmented_control(
            "Shuffle branch",
            ["Lower", "Upper"],
            default="Lower",
            key="f2_branch",
        )
        branch = "upper" if branch_label == "Upper" else "lower"
    start, stop, points = _range_controls(axis)
    if not selected:
        st.info("Select at least one HKL series.")
        return
    hkls = tuple(_parse_hkl(value) for value in selected)
    figure, rows = plot_f2_evolution(
        hkls,
        axis=axis,
        start=start,
        stop=stop,
        points=points,
        branch=branch,
        active_y=result.config.y,
    )
    st.plotly_chart(
        figure,
        width="stretch",
        config={"displaylogo": False, "scrollZoom": True},
    )
    table_rows: list[dict[str, CsvValue]] = [
        {"axis_value": row["axis_value"], "hkl": row["hkl"], "F2": row["F2"]} for row in rows
    ]
    with st.expander("Data preview"):
        st.dataframe(table_rows[:1000], width="stretch", hide_index=True, height=330)
    st.download_button(
        "F2 evolution CSV",
        rows_to_csv(table_rows, ("axis_value", "hkl", "F2")),
        "f2_evolution.csv",
        "text/csv",
        key="f2_csv",
    )


def _range_controls(axis: F2Axis) -> tuple[float, float, int]:
    defaults = {
        "y": (0.167, 0.25, 0.0, 0.5),
        "signed_shuffle": (-0.166, 0.0, -0.5, 0.5),
        "shuffle_magnitude": (0.0, 0.166, 0.0, 0.5),
    }[axis]
    left, middle, right = st.columns(3)
    with left:
        start = float(
            st.number_input(
                "Evolution start",
                min_value=defaults[2],
                max_value=defaults[3],
                value=defaults[0],
                step=0.001,
                format="%.4f",
                key=f"f2_start_{axis}",
            )
        )
    with middle:
        stop = float(
            st.number_input(
                "Evolution stop",
                min_value=defaults[2],
                max_value=defaults[3],
                value=defaults[1],
                step=0.001,
                format="%.4f",
                key=f"f2_stop_{axis}",
            )
        )
    with right:
        points = int(
            st.number_input(
                "Evolution points",
                min_value=10,
                max_value=2000,
                value=301,
                step=10,
                key="f2_points",
            )
        )
    if stop <= start:
        st.error("Evolution stop must be greater than start.")
        st.stop()
    return start, stop, points


def _hkl_options(result: SimulationResult) -> list[str]:
    values: list[str] = list(DEFAULT_HKLS)
    for peak in result.peaks:
        reflection = peak.reflection
        label = (
            reflection.hkl_label
            if max(reflection.h, reflection.k, reflection.l) < 10
            else f"{reflection.h},{reflection.k},{reflection.l}"
        )
        if label not in values:
            values.append(label)
    return values


def _parse_hkl(label: str) -> tuple[int, int, int]:
    if "," in label:
        parts = label.split(",")
        if len(parts) == 3 and all(part.isdigit() for part in parts):
            return int(parts[0]), int(parts[1]), int(parts[2])
    if len(label) == 3 and label.isdigit():
        return int(label[0]), int(label[1]), int(label[2])
    raise ValueError(f"unsupported HKL label: {label}")
