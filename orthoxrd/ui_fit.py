from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import cast

import streamlit as st

from orthoxrd.config import SimulationConfig
from orthoxrd.export_writer import PreparedExport
from orthoxrd.export_zip import prepare_fit_export
from orthoxrd.fit import (
    run_discrete_peak_fit,
    validate_discrete_peak_fit_observations,
)
from orthoxrd.fit_models import (
    FitError,
    FitOptions,
    FitResult,
    LocalMinimumCandidate,
    ObservableMode,
)
from orthoxrd.fit_observations import (
    observation_csv_editor_template,
    observation_csv_template,
    parse_observation_csv,
)
from orthoxrd.i18n import t, th
from orthoxrd.scattering import composition_to_text
from orthoxrd.structure_coordinates import StructureAxis
from orthoxrd.ui_export import discard_prepared
from orthoxrd.ui_plot_fit import (
    plot_chi2_curve,
    plot_observed_vs_fitted,
    plot_residual_contributions,
    plot_scale_curve,
)
from orthoxrd.ui_structure import set_structure_y_state
from orthoxrd.ui_style import kpi_grid

RESULT_KEY = "fit_result"
SIGNATURE_KEY = "fit_result_signature"
EXPORT_KEY = "fit_prepared_export"
EXPORT_SIGNATURE_KEY = "fit_export_signature"
OBS_TEXT_KEY = "fit_observations_text"
OBS_UPLOAD_TOKEN_KEY = "fit_observations_upload_token"
APPLY_FLASH_KEY = "fit_apply_flash"
APPLY_FLASH_KIND_KEY = "fit_apply_flash_kind"
APPLY_PENDING_Y_KEY = "fit_apply_pending_y"
SELECTED_CANDIDATE_KEY = "fit_selected_candidate"
# Resource bounds for observation CSV upload (bytes / data rows excluding header).
MAX_OBS_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_OBS_UPLOAD_ROWS = 500


def consume_pending_structure_apply() -> None:
    """Commit deferred Apply y* before structure widgets are instantiated.

    Streamlit forbids mutating structure widgets after they exist in the same run,
    so Apply only queues the value.
    Call this once near the top of ``main`` before ``render_structure_panel``.
    """
    if APPLY_PENDING_Y_KEY not in st.session_state:
        return
    y_star = float(st.session_state.pop(APPLY_PENDING_Y_KEY))
    set_structure_y_state(y_star)


def render_fit_view(config: SimulationConfig) -> None:
    st.subheader(t("fit.title"))
    st.caption(t("fit.subtitle"))

    flash_y = st.session_state.pop(APPLY_FLASH_KEY, None)
    if flash_y is not None:
        flash_kind = st.session_state.pop(APPLY_FLASH_KIND_KEY, "best")
        flash_key = (
            "fit.apply_candidate_success" if flash_kind == "candidate" else "fit.apply_success"
        )
        st.success(t(flash_key, y=float(flash_y)))

    _render_fixed_model_context(config)
    observable_mode = _render_observable_mode()
    observations_text = _render_observation_inputs(config)
    options = _render_fit_options(observable_mode)
    options_valid = options is not None
    observation_count, observation_error = _validate_observation_input(
        observations_text,
        config=config,
        options=options,
    )
    observations_ready = observation_error is None and observation_count >= 2
    if observation_error is not None:
        st.warning(t("fit.obs.invalid", error=observation_error))
    elif not observations_ready:
        st.info(t("fit.obs.need_two", count=observation_count))

    signature = (
        _fit_signature(config, options, observations_text) if options is not None else ""
    )

    run_clicked = st.button(
        t("fit.run"),
        type="primary",
        key="run_fit",
        use_container_width=True,
        disabled=not options_valid or not observations_ready,
        help=th("fit.run"),
    )
    if run_clicked and options is not None:
        _run_fit(config, observations_text, options, signature)

    result = st.session_state.get(RESULT_KEY)
    if not isinstance(result, FitResult):
        st.info(t("fit.empty"))
        return

    stale = st.session_state.get(SIGNATURE_KEY) != signature
    if stale:
        st.markdown(t("fit.stale"), unsafe_allow_html=True)
        discard_prepared(EXPORT_KEY)
        st.session_state.pop(EXPORT_SIGNATURE_KEY, None)
    else:
        st.markdown(t("fit.valid"), unsafe_allow_html=True)

    _render_summary(result)
    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)

    _render_diagnostics(result)
    _render_identifiability(result)
    _render_local_minima(result, stale)
    _render_residuals(result)
    _render_apply(result, stale)
    _render_export(result, signature, stale)


def _render_fixed_model_context(config: SimulationConfig) -> None:
    """Keep the inputs held fixed by the inverse fit visible beside its controls."""
    composition = (
        composition_to_text(config.composition)
        if config.scattering_mode == "composition"
        else t("app.active_model.composition_na")
    )
    radiation = ", ".join(
        f"{line.label}: λ={line.wavelength_a:.7g} Å, w={line.weight:.6g}"
        for line in config.lines
    )
    st.markdown(t("fit.context.header"))
    st.caption(
        t(
            "fit.context.details",
            a=config.lattice.a,
            b=config.lattice.b,
            c=config.lattice.c,
            radiation=radiation,
            scattering=t(f"advanced.scattering.{config.scattering_mode}"),
            composition=composition,
            tth_min=config.two_theta_min,
            tth_max=config.two_theta_max,
            hkl_max=config.hkl_max,
            lp=t("common.on") if config.include_lorentz_polarization else t("common.off"),
            multiplicity=t("common.on") if config.include_multiplicity else t("common.off"),
            volume=t("common.on") if config.include_cell_volume else t("common.off"),
        )
    )
    st.caption(t("fit.context.profile_excluded"))


def _render_observable_mode() -> ObservableMode:
    st.markdown(t("fit.observable.header"))
    value = st.selectbox(
        t("fit.observable_mode"),
        ["peak_area", "peak_height"],
        format_func=lambda code: t(f"fit.mode.{code}"),
        key="fit_observable_mode",
        help=th("fit.observable_mode"),
    )
    observable_mode = cast(ObservableMode, value)
    if observable_mode == "peak_height":
        st.info(t("fit.peak_height_note"))
    return observable_mode


def _render_observation_inputs(config: SimulationConfig) -> str:
    st.markdown(t("fit.obs.header"))
    if len(config.lines) > 1:
        st.warning(
            t(
                "fit.obs.multiline_warning",
                lines=", ".join(
                    f"line_{index:02d}={line.label}" for index, line in enumerate(config.lines)
                ),
            )
        )
    upload = st.file_uploader(
        t("fit.obs.upload"),
        type=["csv", "txt"],
        key="fit_observation_file",
        help=th("fit.obs.upload"),
    )
    if upload is not None:
        raw = upload.getvalue()
        if len(raw) > MAX_OBS_UPLOAD_BYTES:
            st.error(
                t(
                    "fit.err.obs_too_large",
                    max_mib=MAX_OBS_UPLOAD_BYTES / (1024 * 1024),
                    size_kib=len(raw) / 1024,
                )
            )
        else:
            token = hashlib.sha256(raw).hexdigest()
            if st.session_state.get(OBS_UPLOAD_TOKEN_KEY) != token:
                try:
                    decoded = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    st.error(t("fit.err.obs_encoding"))
                else:
                    data_rows = _count_csv_data_rows(decoded)
                    if data_rows > MAX_OBS_UPLOAD_ROWS:
                        st.error(
                            t(
                                "fit.err.obs_too_many_rows",
                                max_rows=MAX_OBS_UPLOAD_ROWS,
                                rows=data_rows,
                            )
                        )
                    else:
                        st.session_state[OBS_UPLOAD_TOKEN_KEY] = token
                        st.session_state[OBS_TEXT_KEY] = decoded
    if OBS_TEXT_KEY not in st.session_state:
        st.session_state[OBS_TEXT_KEY] = observation_csv_editor_template()

    text = st.text_area(
        t("fit.obs.editor"),
        height=180,
        key=OBS_TEXT_KEY,
        help=th("fit.obs.editor"),
    )
    st.download_button(
        t("fit.obs.template"),
        observation_csv_template(),
        file_name="observation_template.csv",
        mime="text/csv",
        key="fit_observation_template",
        help=th("fit.obs.template"),
    )
    st.caption(t("fit.obs.caption", max_rows=MAX_OBS_UPLOAD_ROWS))
    return str(text)


def _count_csv_data_rows(text: str) -> int:
    """Count non-empty data rows (excludes header and blank lines)."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return 0
    return max(0, len(lines) - 1)


def _validate_observation_input(
    text: str,
    *,
    config: SimulationConfig,
    options: FitOptions | None,
) -> tuple[int, str | None]:
    """Return the valid observation count and a concise eager-validation error."""
    if _count_csv_data_rows(text) == 0:
        return 0, None
    try:
        observations = parse_observation_csv(text)
    except (FitError, ValueError) as exc:
        return 0, str(exc)
    if len(observations) >= 2 and options is not None:
        try:
            matched = validate_discrete_peak_fit_observations(
                config,
                observations,
                options,
            )
        except (FitError, ValueError) as exc:
            return 0, str(exc)
        return sum(1 for item in matched if item.included), None
    return len(observations), None


def _render_fit_options(observable_mode: ObservableMode) -> FitOptions | None:
    st.markdown(t("fit.options.header"))
    weight_col, note_col = st.columns(2)
    with weight_col:
        weight_mode = st.selectbox(
            t("fit.weight_mode"),
            ["poisson", "equal"],
            format_func=lambda code: t(f"fit.weight.{code}"),
            key="fit_weight_mode",
            help=th("fit.weight_mode"),
        )
    with note_col:
        st.caption(t("fit.options.scan_note"))
    y_start_col, y_stop_col, grid_col = st.columns(3)
    with y_start_col:
        y_start = float(
            st.number_input(
                t("fit.y_start"),
                min_value=0.0,
                max_value=0.5,
                value=0.0,
                step=0.01,
                format="%.4f",
                key="fit_y_start",
                help=th("fit.y_start"),
            )
        )
    with y_stop_col:
        y_stop = float(
            st.number_input(
                t("fit.y_stop"),
                min_value=0.0,
                max_value=0.5,
                value=0.5,
                step=0.01,
                format="%.4f",
                key="fit_y_stop",
                help=th("fit.y_stop"),
            )
        )
    with grid_col:
        grid_points = int(
            st.number_input(
                t("fit.grid_points"),
                min_value=2,
                max_value=1001,
                value=201,
                step=10,
                key="fit_grid_points",
                help=th("fit.grid_points"),
            )
        )
    if y_stop < y_start:
        st.error(t("fit.err.y_range"))
        return None
    return FitOptions(
        observable_mode=observable_mode,
        weight_mode=weight_mode,  # type: ignore[arg-type]
        y_start=y_start,
        y_stop=y_stop,
        grid_points=grid_points,
    )


def _run_fit(
    config: SimulationConfig,
    observations_text: str,
    options: FitOptions,
    signature: str,
) -> None:
    try:
        observations = parse_observation_csv(observations_text)
        with st.spinner(t("fit.calc_spinner")):
            result = run_discrete_peak_fit(config, observations, options)
    except FitError as exc:
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
    st.session_state[SIGNATURE_KEY] = signature


def _render_summary(result: FitResult) -> None:
    best = result.best
    included = sum(1 for item in result.matched if item.included)
    kpi_grid(
        [
            (t("fit.kpi.y_star"), f"{best.y:.6f}"),
            (t("fit.kpi.s_star"), f"{best.scale_s:.6g}"),
            (t("fit.kpi.chi2_star"), f"{best.chi2:.6g}"),
            (t("fit.kpi.shuffle_signed"), f"{best.shuffle_signed:.6f}"),
            (t("fit.kpi.shuffle_mag"), f"{best.shuffle_magnitude:.6f}"),
            (t("fit.kpi.source"), best.source),
            (t("fit.kpi.peaks"), f"{included}/{len(result.matched)}"),
            (t("fit.kpi.mode"), t(f"fit.mode.{result.options.observable_mode}")),
        ]
    )


def _render_diagnostics(result: FitResult) -> None:
    st.markdown(t("fit.diagnostics.header"))
    raw_axis = st.segmented_control(
        t("fit.display_coordinate"),
        options=["y", "signed_shuffle", "shuffle_magnitude"],
        default="y",
        format_func=lambda code: t(f"axis.{code}"),
        key="fit_display_axis",
        help=th("fit.display_coordinate"),
    )
    display_axis = cast(StructureAxis, raw_axis or "y")
    if display_axis == "shuffle_magnitude":
        st.caption(t("fit.display_coordinate_magnitude_note"))

    objective_col, scale_col = st.columns(2)
    with objective_col:
        st.caption(t("fit.diagnostics.chi2"))
        st.plotly_chart(
            plot_chi2_curve(result, display_axis),
            width="stretch",
            config={"displaylogo": False},
        )
    with scale_col:
        st.caption(t("fit.diagnostics.scale"))
        st.plotly_chart(
            plot_scale_curve(result, display_axis),
            width="stretch",
            config={"displaylogo": False},
        )

    parity_col, contribution_col = st.columns(2)
    with parity_col:
        st.caption(t("fit.diagnostics.parity"))
        st.plotly_chart(
            plot_observed_vs_fitted(result),
            width="stretch",
            config={"displaylogo": False},
        )
    with contribution_col:
        st.caption(t("fit.diagnostics.contributions"))
        st.plotly_chart(
            plot_residual_contributions(result),
            width="stretch",
            config={"displaylogo": False},
        )


def _render_identifiability(result: FitResult) -> None:
    st.markdown(t("fit.identifiability.header"))
    diagnostic = result.identifiability
    if diagnostic is None:
        st.info(t("fit.identifiability.unavailable"))
        return
    status_text = t(f"fit.identifiability.status.{diagnostic.status}")
    interval = (
        f"[{diagnostic.y_lower:.6f}, {diagnostic.y_upper:.6f}]"
        if diagnostic.y_lower is not None and diagnostic.y_upper is not None
        else t("fit.identifiability.no_interval")
    )
    left, right = st.columns(2)
    with left:
        st.metric(t("fit.identifiability.status_label"), status_text)
    with right:
        st.metric(t("fit.identifiability.interval_label"), interval)
    st.caption(
        t(
            "fit.identifiability.note",
            threshold=diagnostic.delta_chi2_threshold,
            reasons="; ".join(diagnostic.reasons) or t("fit.identifiability.no_reason"),
        )
    )
    if diagnostic.status in {"multi_modal", "boundary_limited", "flat"}:
        st.warning(t(f"fit.identifiability.warning.{diagnostic.status}"))
    elif diagnostic.status == "identified":
        st.success(t("fit.identifiability.identified"))
    else:
        st.info(t("fit.identifiability.unavailable"))


def _render_local_minima(result: FitResult, stale: bool) -> None:
    st.markdown(t("fit.local_minima.header"))
    if not result.local_minima:
        st.caption(t("fit.local_minima.empty"))
        return
    rows = [
        {
            "grid_index": item.grid_index,
            "y": item.y,
            "scale_s": item.scale_s,
            "chi2": item.chi2,
            "refined_y": item.refined_y,
            "refined_scale_s": item.refined_scale_s,
            "refined_chi2": item.refined_chi2,
            "delta_chi2": _candidate_delta_chi2(result, item),
            "refine_status": item.refine_status,
        }
        for item in result.local_minima
    ]
    st.dataframe(rows, width="stretch", hide_index=True, height=220)
    candidate_indices = [item.grid_index for item in result.local_minima]
    selected_index = st.selectbox(
        t("fit.local_minima.select"),
        options=candidate_indices,
        format_func=lambda index: _candidate_label(result, index),
        key=SELECTED_CANDIDATE_KEY,
        help=t("fit.local_minima.select_help"),
    )
    selected = next(
        item for item in result.local_minima if item.grid_index == selected_index
    )
    if st.button(
        t("fit.apply_candidate"),
        disabled=stale,
        key="apply_selected_fit_candidate",
        use_container_width=True,
        help=t("fit.apply_candidate_help"),
    ):
        _queue_structure_apply(_candidate_y(selected), "candidate")


def _candidate_label(result: FitResult, grid_index: int) -> str:
    candidate = next(item for item in result.local_minima if item.grid_index == grid_index)
    return (
        f"grid {candidate.grid_index}: y={_candidate_y(candidate):.6f}, "
        f"Δχ²={_candidate_delta_chi2(result, candidate):.6g}"
    )


def _candidate_delta_chi2(
    result: FitResult,
    candidate: LocalMinimumCandidate,
) -> float:
    chi2 = candidate.refined_chi2 if candidate.refined_chi2 is not None else candidate.chi2
    return chi2 - result.best.chi2


def _candidate_y(candidate: LocalMinimumCandidate) -> float:
    return candidate.refined_y if candidate.refined_y is not None else candidate.y


def _render_residuals(result: FitResult) -> None:
    st.markdown(t("fit.residuals.header"))
    rows = [
        {
            "h": residual.h,
            "k": residual.k,
            "l": residual.l,
            "line_id": residual.line_id,
            "line_label": residual.line_label,
            "series_id": residual.series_id,
            "I_obs": residual.I_obs,
            "I_model": residual.I_model,
            "S_I_model": residual.S_I_model,
            "residual": residual.residual,
            "weight": residual.weight,
            "included": residual.included,
        }
        for residual in result.residuals_at_best
    ]
    st.dataframe(rows, width="stretch", hide_index=True, height=320)


def _render_apply(result: FitResult, stale: bool) -> None:
    st.divider()
    if st.button(
        t("fit.apply"),
        disabled=stale,
        key="apply_fit_y_star",
        use_container_width=True,
        help=th("fit.apply"),
    ):
        _queue_structure_apply(float(result.best.y), "best")
    st.caption(t("fit.apply_caption"))


def _queue_structure_apply(y_value: float, kind: str) -> None:
    """Defer structure widget writes to the next Streamlit run."""
    st.session_state[APPLY_PENDING_Y_KEY] = float(y_value)
    st.session_state[APPLY_FLASH_KEY] = float(y_value)
    st.session_state[APPLY_FLASH_KIND_KEY] = kind
    st.rerun()


def _render_export(result: FitResult, signature: str, stale: bool) -> None:
    st.divider()
    if st.button(
        t("fit.prepare"),
        disabled=stale,
        key="prepare_fit_zip",
        use_container_width=True,
        help=th("fit.prepare"),
    ):
        discard_prepared(EXPORT_KEY)
        with st.spinner(t("fit.spinner")):
            prepared = prepare_fit_export(result)
        st.session_state[EXPORT_KEY] = prepared
        st.session_state[EXPORT_SIGNATURE_KEY] = signature
    prepared = st.session_state.get(EXPORT_KEY)
    if not isinstance(prepared, PreparedExport):
        st.caption(t("fit.prepare_caption"))
        return
    export_matches = st.session_state.get(EXPORT_SIGNATURE_KEY) == signature
    path = Path(prepared.path)
    if not path.exists():
        discard_prepared(EXPORT_KEY)
        st.session_state.pop(EXPORT_SIGNATURE_KEY, None)
        st.warning(t("export.expired"))
        return
    if stale or not export_matches:
        st.caption(t("fit.prepare_caption"))
        return
    with path.open("rb") as handle:
        st.download_button(
            t("fit.download"),
            data=handle,
            file_name="discrete_peak_fit.zip",
            mime="application/zip",
            key="download_fit_zip",
            use_container_width=True,
            help=th("fit.download"),
        )
    st.caption(
        t("fit.export_size", kib=prepared.size_bytes / 1024, sha=prepared.sha256[:12])
    )


def _fit_relevant_config_payload(config: SimulationConfig) -> dict[str, object]:
    """Simulation fields that affect discrete-peak fit results.

    Excludes panel Wyckoff y (engine scans its own y grid; catalog positions are
    y-independent) and profile-only knobs unused by ``run_discrete_peak_fit``.
    """
    return {
        "composition": [
            {"symbol": item.symbol, "fraction": item.fraction} for item in config.composition
        ],
        "corrections": {
            "cell_volume_1_over_V": config.include_cell_volume,
            "lorentz_polarization": config.include_lorentz_polarization,
            "multiplicity": config.include_multiplicity,
        },
        "hkl_max": config.hkl_max,
        "lattice": {
            "a_A": config.lattice.a,
            "b_A": config.lattice.b,
            "c_A": config.lattice.c,
        },
        "radiation": [
            {
                "label": line.label,
                "wavelength_A": line.wavelength_a,
                "weight": line.weight,
            }
            for line in config.lines
        ],
        "scattering_mode": config.scattering_mode,
        "two_theta_deg": {"min": config.two_theta_min, "max": config.two_theta_max},
    }


def _fit_signature(
    config: SimulationConfig,
    options: FitOptions,
    observations_text: str,
) -> str:
    payload = {
        "config": _fit_relevant_config_payload(config),
        "observable_mode": options.observable_mode,
        "weight_mode": options.weight_mode,
        "y_start": options.y_start,
        "y_stop": options.y_stop,
        "grid_points": options.grid_points,
        "profile_delta_chi2": options.profile_delta_chi2,
        "observations_sha256": hashlib.sha256(
            observations_text.encode("utf-8")
        ).hexdigest(),
    }
    material = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
