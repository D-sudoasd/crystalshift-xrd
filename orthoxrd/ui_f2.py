from __future__ import annotations

from typing import cast

import streamlit as st

from orthoxrd.export_excel_packages import build_f2_excel_workbook
from orthoxrd.export_schema import F2_EVOLUTION_FIELDS, CsvValue
from orthoxrd.i18n import t, th
from orthoxrd.simulation import SimulationResult
from orthoxrd.structure_coordinates import (
    structure_branch_from_y,
    structure_coordinate_from_y,
    y_from_structure_coordinate,
)
from orthoxrd.structure_factor import normalized_shuffle_from_y
from orthoxrd.structure_geometry import build_cmcm_shuffle_geometry
from orthoxrd.ui_plot_f2 import F2Axis, F2Branch, plot_f2_evolution
from orthoxrd.ui_plot_structure import StructurePlotLabels, plot_cmcm_shuffle_structure
from orthoxrd.ui_tables import rows_to_csv

DEFAULT_HKLS = ("110", "020", "021", "131")
F2_EXPORT_FIELDS = F2_EVOLUTION_FIELDS


def render_f2_view(result: SimulationResult) -> None:
    st.subheader(t("f2.title"))
    st.caption(t("f2.caption"))
    hkl_options = _hkl_options(result)
    selected = st.multiselect(
        t("f2.hkls"),
        hkl_options,
        default=[value for value in DEFAULT_HKLS if value in hkl_options],
        max_selections=12,
        key="f2_hkls",
        help=th("f2.hkls"),
    )
    axis_code = st.segmented_control(
        t("f2.axis"),
        ["y", "signed_shuffle", "shuffle_magnitude"],
        format_func=lambda code: t(f"axis.{code}"),
        default="shuffle_magnitude",
        key="f2_axis",
        help=th("f2.axis"),
    )
    axis = cast(F2Axis, axis_code or "shuffle_magnitude")
    branch: F2Branch = "lower"
    if axis == "shuffle_magnitude":
        branch_code = st.segmented_control(
            t("f2.branch"),
            ["lower", "upper"],
            format_func=lambda code: t(f"branch.{code}"),
            default="lower",
            key="f2_branch",
            help=th("f2.branch"),
        )
        branch = "upper" if branch_code == "upper" else "lower"
    start, stop, points = _range_controls(axis)
    if not selected:
        st.info(t("f2.empty"))
    else:
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
        table_rows: list[dict[str, CsvValue]] = [dict(row) for row in rows]
        with st.expander(t("f2.preview")):
            st.dataframe(table_rows[:1000], width="stretch", hide_index=True, height=330)
        st.caption(t("export.csv_excel_hint.f2"))
        csv_column, excel_column = st.columns(2)
        with csv_column:
            st.download_button(
                t("f2.download"),
                rows_to_csv(table_rows, F2_EXPORT_FIELDS),
                "f2_evolution.csv",
                "text/csv",
                key="f2_csv",
                use_container_width=True,
                help=th("f2.download"),
            )
        with excel_column:
            st.download_button(
                t("f2.download_excel"),
                build_f2_excel_workbook(
                    table_rows,
                    axis=axis,
                    branch=branch,
                    start=start,
                    stop=stop,
                    points=points,
                    active_y=result.config.y,
                ),
                "f2_evolution.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="f2_xlsx",
                use_container_width=True,
                help=th("f2.download_excel"),
            )
    _render_structure_preview(
        result,
        axis=axis,
        start=start,
        stop=stop,
        points=points,
        branch=branch,
    )


def _render_structure_preview(
    result: SimulationResult,
    *,
    axis: F2Axis,
    start: float,
    stop: float,
    points: int,
    branch: F2Branch,
) -> None:
    st.markdown(t("f2.structure_preview.title"))
    st.caption(t("f2.structure_preview.help"))
    active_value = structure_coordinate_from_y(result.config.y, axis)
    default_value = min(max(active_value, start), stop)
    widget_key = f"f2_structure_preview_{axis}_{branch}"
    stored_value = st.session_state.get(widget_key)
    if not isinstance(stored_value, (int, float)) or not start <= stored_value <= stop:
        st.session_state.pop(widget_key, None)
    preview_value = float(
        st.slider(
            f"{t('f2.structure_preview.slider')} · {t(f'axis.{axis}')}",
            min_value=start,
            max_value=stop,
            value=default_value,
            step=(stop - start) / (points - 1),
            format="%.4f",
            key=widget_key,
            help=th("f2.structure_preview.slider"),
        )
    )
    preview_y = y_from_structure_coordinate(
        preview_value,
        axis,
        branch=branch if axis == "shuffle_magnitude" else None,
    )
    signed = structure_coordinate_from_y(preview_y, "signed_shuffle")
    magnitude = abs(signed)
    normalized = normalized_shuffle_from_y(preview_y)
    preview_branch = structure_branch_from_y(preview_y)
    branch_label = (
        t(f"branch.{preview_branch}") if preview_branch is not None else "y=0.25"
    )
    displacement_a = result.config.lattice.b * abs(preview_y - 0.25)
    st.caption(
        f"y=0.25 → {t('live.ui.current')} y={preview_y:.6f} · "
        f"{t('axis.signed_shuffle')}={signed:+.6f} · "
        f"{t('axis.shuffle_magnitude')}={magnitude:.6f} · "
        f"{t('app.summary.normalized_shuffle')}={normalized:.4f} · {branch_label} | "
        f"|Δb|=b·|y−0.25|={displacement_a:.6f} Å"
    )
    st.plotly_chart(
        plot_cmcm_shuffle_structure(
            build_cmcm_shuffle_geometry(result.config.lattice, preview_y),
            labels=StructurePlotLabels(
                cell=t("structure.plot.cell"),
                reference=t("structure.plot.reference"),
                current=t("structure.plot.current"),
                shuffle_path=t("structure.plot.shuffle_path"),
                shuffle_arrow=t("structure.plot.shuffle_arrow"),
            ),
        ),
        width="stretch",
        config={"displaylogo": False, "scrollZoom": True},
    )
    st.caption(t("f2.structure_preview.caption"))


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
                t("f2.start"),
                min_value=defaults[2],
                max_value=defaults[3],
                value=defaults[0],
                step=0.001,
                format="%.4f",
                key=f"f2_start_{axis}",
                help=th("f2.start"),
            )
        )
    with middle:
        stop = float(
            st.number_input(
                t("f2.stop"),
                min_value=defaults[2],
                max_value=defaults[3],
                value=defaults[1],
                step=0.001,
                format="%.4f",
                key=f"f2_stop_{axis}",
                help=th("f2.stop"),
            )
        )
    with right:
        points = int(
            st.number_input(
                t("f2.points"),
                min_value=10,
                max_value=2000,
                value=301,
                step=10,
                key="f2_points",
                help=th("f2.points"),
            )
        )
    if stop <= start:
        st.error(t("f2.stop_error"))
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
