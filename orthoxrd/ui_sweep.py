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
    st.subheader("Sweep and trajectory")
    form = render_sweep_form(current.config, len(current.peaks))
    _run_if_submitted(form, current)
    result = st.session_state.get(RESULT_KEY)
    if not isinstance(result, SweepResult):
        st.info(
            "Configure the sweep and select Run sweep. No batch calculation runs automatically."
        )
        return
    stale = st.session_state.get(SIGNATURE_KEY) != form.signature
    if stale:
        st.markdown(
            '<div class="xrd-state xrd-state--warning">'
            "Result is stale because the active configuration changed. "
            "The preview is retained, but export is disabled until rerun."
            "</div>",
            unsafe_allow_html=True,
        )
        discard_prepared(EXPORT_KEY)
        st.session_state.pop(EXPORT_SIGNATURE_KEY, None)
    else:
        st.markdown(
            '<div class="xrd-state xrd-state--valid">'
            "Sweep result matches the active configuration."
            "</div>",
            unsafe_allow_html=True,
        )
    _summary(result)
    normalization = _normalization(form.normalization)
    display_range = render_sweep_display_range(result)
    view = st.segmented_control(
        "Sweep result view",
        ["Heatmap", "Waterfall", "Peak evolution", "Data preview"],
        default="Heatmap",
        key="sweep_result_view",
    )
    if view == "Waterfall":
        st.plotly_chart(
            plot_sweep_waterfall(result, normalization, display_range),
            width="stretch",
            config={"displaylogo": False},
        )
    elif view == "Peak evolution":
        _render_peak_evolution(result)
    elif view == "Data preview":
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
                raise ValueError("Select a trajectory CSV before running.")
            config = batch_engine.parse_trajectory_csv(form.trajectory_text, form.base_config)
        else:
            if form.range_config is None:
                raise ValueError("Range sweep configuration is incomplete.")
            config = form.range_config
        with st.spinner("Calculating sweep..."):
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
            ("steps", f"{len(result.steps):,}"),
            ("peak rows", f"{peak_rows:,}"),
            ("spectrum cells", f"{spectrum_cells:,}"),
            ("global profile max", f"{result.spectrum_global_max:.6g}"),
        ]
    )


def _render_peak_evolution(result: SweepResult) -> None:
    metric_label = st.selectbox(
        "Peak metric",
        ["F2", "Model peak intensity", "Global relative peak intensity"],
        key="sweep_peak_metric",
    )
    metric = cast(
        PeakMetric,
        {
            "F2": "F2",
            "Model peak intensity": "I_model",
            "Global relative peak intensity": "I_rel_global",
        }[metric_label],
    )
    series = available_series(result)
    labels = [label for _, label in series]
    defaults = [
        label
        for label in labels
        if any(label.endswith(hkl) for hkl in ("110", "020", "021", "131"))
    ][:12]
    selected_labels = st.multiselect(
        "Peak series (maximum 12)",
        labels,
        default=defaults or labels[:4],
        max_selections=12,
        key="sweep_peak_series",
    )
    label_to_id = {label: series_id for series_id, label in series}
    selected_ids = [label_to_id[label] for label in selected_labels]
    st.plotly_chart(
        plot_peak_evolution(result, selected_ids, metric),
        width="stretch",
        config={"displaylogo": False},
    )


def _render_data_preview(result: SweepResult) -> None:
    st.markdown("##### Sweep steps")
    st.dataframe(
        list(sweep_step_rows(result)),
        width="stretch",
        hide_index=True,
        height=250,
    )
    st.markdown("##### Peak evolution sample")
    rows = []
    for index, row in enumerate(peak_evolution_rows(result)):
        if index >= 500:
            break
        rows.append(row)
    st.dataframe(rows, width="stretch", hide_index=True, height=360)
    st.caption("Preview is limited to 500 peak rows. The ZIP contains the complete tables.")


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
        "Prepare sweep ZIP",
        disabled=stale,
        key="prepare_sweep_zip",
        use_container_width=True,
    ):
        discard_prepared(EXPORT_KEY)
        with st.spinner("Streaming schema 2.1 files into ZIP..."):
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
        st.caption("Run the active configuration, then prepare the schema 2.1 ZIP.")
        return
    export_matches = (
        st.session_state.get(EXPORT_SIGNATURE_KEY) == active_export_signature
    )
    path = Path(prepared.path)
    if stale or not export_matches or not path.exists():
        st.caption("Run the active configuration, then prepare the schema 2.1 ZIP.")
        return
    with path.open("rb") as handle:
        st.download_button(
            "Download sweep ZIP",
            data=handle,
            file_name="orthorhombic_xrd_sweep.zip",
            mime="application/zip",
            key="download_sweep_zip",
            use_container_width=True,
        )
    st.caption(f"{prepared.size_bytes / 1024:.1f} KiB | SHA-256 {prepared.sha256[:12]}...")


def _normalization(label: str) -> SpectrumNormalization:
    return cast(
        SpectrumNormalization,
        {
            "Global across sweep": "global",
            "Local per step": "local",
            "Model intensity": "model",
        }[label],
    )
