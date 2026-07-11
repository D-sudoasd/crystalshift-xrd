from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import cast

import streamlit as st

import orthoxrd.batch as batch_engine
from orthoxrd.batch_models import SweepResult, TrajectoryValidationError
from orthoxrd.export_origin import SweepExportPlotState
from orthoxrd.export_rows import peak_evolution_rows, sweep_step_rows
from orthoxrd.export_writer import PreparedExport
from orthoxrd.export_zip import prepare_sweep_export
from orthoxrd.i18n import t, th
from orthoxrd.simulation import SimulationResult
from orthoxrd.ui_export import discard_prepared
from orthoxrd.ui_plot_sweep import (
    PeakMetric,
    SpectrumNormalization,
    available_series,
    plot_peak_evolution,
    plot_sweep_heatmap,
    plot_sweep_waterfall,
)
from orthoxrd.ui_style import kpi_grid
from orthoxrd.ui_sweep_controls import SweepFormState, render_sweep_form
from orthoxrd.ui_sweep_range import SweepDisplayRange, render_sweep_display_range

RESULT_KEY = "sweep_result"
SIGNATURE_KEY = "sweep_result_signature"
EXPORT_KEY = "sweep_prepared_export"
EXPORT_SIGNATURE_KEY = "sweep_export_signature"


def render_sweep_view(current: SimulationResult) -> None:
    st.subheader(t("sweep.title"))
    form = render_sweep_form(current.config, len(current.peaks))
    _run_if_submitted(form, current)
    result = st.session_state.get(RESULT_KEY)
    if not isinstance(result, SweepResult):
        st.info(t("sweep.empty"))
        return
    stale = st.session_state.get(SIGNATURE_KEY) != form.signature
    if stale:
        st.markdown(t("sweep.stale"), unsafe_allow_html=True)
        discard_prepared(EXPORT_KEY)
        st.session_state.pop(EXPORT_SIGNATURE_KEY, None)
    else:
        st.markdown(t("sweep.valid"), unsafe_allow_html=True)
    _summary(result)
    normalization = cast(SpectrumNormalization, form.normalization)
    display_range = render_sweep_display_range(result)
    view = st.segmented_control(
        t("sweep.result_view"),
        ["heatmap", "waterfall", "peak_evolution", "data_preview"],
        format_func=lambda code: t(f"sweep.view.{code}"),
        default="heatmap",
        key="sweep_result_view",
        help=th("sweep.result_view"),
    )
    if view == "waterfall":
        st.plotly_chart(
            plot_sweep_waterfall(result, normalization, display_range),
            width="stretch",
            config={"displaylogo": False},
        )
    elif view == "peak_evolution":
        _render_peak_evolution(result)
    elif view == "data_preview":
        _render_data_preview(result)
    else:
        st.plotly_chart(
            plot_sweep_heatmap(result, normalization, display_range),
            width="stretch",
            config={"displaylogo": False, "scrollZoom": True},
        )
    _render_export(result, form.signature, stale, display_range)


def _run_if_submitted(form: SweepFormState, current: SimulationResult) -> None:
    if not form.submitted:
        return
    try:
        if form.mode == "trajectory":
            if not form.trajectory_text:
                raise ValueError(t("sweep.err.no_trajectory"))
            config = batch_engine.parse_trajectory_csv(form.trajectory_text, form.base_config)
        else:
            if form.range_config is None:
                raise ValueError(t("sweep.err.incomplete_range"))
            config = form.range_config
        with st.spinner(t("sweep.calc_spinner")):
            result = batch_engine.generate_sweep(config)
    except TrajectoryValidationError as exc:
        st.error(str(exc))
        st.dataframe(
            [asdict(issue) for issue in exc.issues],
            width="stretch",
            hide_index=True,
        )
        return
    except ValueError as exc:
        st.error(str(exc))
        return
    discard_prepared(EXPORT_KEY)
    st.session_state.pop(EXPORT_SIGNATURE_KEY, None)
    st.session_state[RESULT_KEY] = result
    st.session_state[SIGNATURE_KEY] = form.signature


def _summary(result: SweepResult) -> None:
    peak_rows = sum(len(step.peaks) for step in result.steps)
    spectrum_cells = len(result.steps) * len(result.steps[0].two_theta_deg)
    kpi_grid(
        [
            (t("sweep.kpi.steps"), f"{len(result.steps):,}"),
            (t("sweep.kpi.peak_rows"), f"{peak_rows:,}"),
            (t("sweep.kpi.spectrum_cells"), f"{spectrum_cells:,}"),
            (t("sweep.kpi.global_max"), f"{result.spectrum_global_max:.6g}"),
        ]
    )


def _render_peak_evolution(result: SweepResult) -> None:
    metric = cast(
        PeakMetric,
        st.selectbox(
            t("sweep.peak_metric"),
            ["F2", "I_model", "I_rel_global"],
            format_func=lambda code: t(f"sweep.metric.{code}"),
            key="sweep_peak_metric",
            help=th("sweep.peak_metric"),
        ),
    )
    series = available_series(result)
    labels = [label for _, label in series]
    defaults = [
        label
        for label in labels
        if any(label.endswith(hkl) for hkl in ("110", "020", "021", "131"))
    ][:12]
    selected_labels = st.multiselect(
        t("sweep.peak_series"),
        labels,
        default=defaults or labels[:4],
        max_selections=12,
        key="sweep_peak_series",
        help=th("sweep.peak_series"),
    )
    label_to_id = {label: series_id for series_id, label in series}
    selected_ids = [label_to_id[label] for label in selected_labels]
    st.plotly_chart(
        plot_peak_evolution(result, selected_ids, metric),
        width="stretch",
        config={"displaylogo": False},
    )


def _render_data_preview(result: SweepResult) -> None:
    st.markdown(t("sweep.steps_header"))
    st.dataframe(
        list(sweep_step_rows(result)),
        width="stretch",
        hide_index=True,
        height=250,
    )
    st.markdown(t("sweep.peak_sample_header"))
    rows = []
    for index, row in enumerate(peak_evolution_rows(result)):
        if index >= 500:
            break
        rows.append(row)
    st.dataframe(rows, width="stretch", hide_index=True, height=360)
    st.caption(t("sweep.preview_caption"))


def _render_export(
    result: SweepResult,
    signature: str,
    stale: bool,
    display_range: SweepDisplayRange,
) -> None:
    active_export_signature = (
        f"{signature}:{display_range.two_theta_minimum}:"
        f"{display_range.two_theta_maximum}:{display_range.axis_minimum}:"
        f"{display_range.axis_maximum}"
    )
    st.divider()
    if st.button(
        t("sweep.prepare"),
        disabled=stale,
        key="prepare_sweep_zip",
        use_container_width=True,
        help=th("sweep.prepare"),
    ):
        discard_prepared(EXPORT_KEY)
        with st.spinner(t("sweep.spinner")):
            prepared = prepare_sweep_export(
                result,
                SweepExportPlotState(
                    display_range.two_theta_minimum,
                    display_range.two_theta_maximum,
                    display_range.axis_minimum,
                    display_range.axis_maximum,
                ),
            )
        st.session_state[EXPORT_KEY] = prepared
        st.session_state[EXPORT_SIGNATURE_KEY] = active_export_signature
    prepared = st.session_state.get(EXPORT_KEY)
    if not isinstance(prepared, PreparedExport):
        st.caption(t("sweep.prepare_caption"))
        return
    export_matches = (
        st.session_state.get(EXPORT_SIGNATURE_KEY) == active_export_signature
    )
    path = Path(prepared.path)
    if stale or not export_matches or not path.exists():
        st.caption(t("sweep.prepare_caption"))
        return
    with path.open("rb") as handle:
        st.download_button(
            t("sweep.download"),
            data=handle,
            file_name="orthorhombic_xrd_sweep.zip",
            mime="application/zip",
            key="download_sweep_zip",
            use_container_width=True,
            help=th("sweep.download"),
        )
    st.caption(
        t("sweep.export_size", kib=prepared.size_bytes / 1024, sha=prepared.sha256[:12])
    )
