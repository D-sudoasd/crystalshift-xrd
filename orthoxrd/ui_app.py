from __future__ import annotations

import streamlit as st

from orthoxrd.config import config_hash
from orthoxrd.export_writer import PreparedExport
from orthoxrd.export_zip import prepare_current_export
from orthoxrd.i18n import ensure_language_state, render_language_toggle, t, th
from orthoxrd.scattering import composition_to_text
from orthoxrd.simulation import SimulationResult
from orthoxrd.structure_factor import signed_shuffle_from_y
from orthoxrd.ui_config import build_simulation_config, calculate_cached
from orthoxrd.ui_export import render_current_export
from orthoxrd.ui_f2 import render_f2_view
from orthoxrd.ui_fit import consume_pending_structure_apply, render_fit_view
from orthoxrd.ui_method import render_method_view
from orthoxrd.ui_pattern import render_pattern_view
from orthoxrd.ui_peaks import render_peaks_view
from orthoxrd.ui_plot_state import plot_state_from_session
from orthoxrd.ui_radiation import render_radiation_panel
from orthoxrd.ui_sidebar import render_advanced_settings
from orthoxrd.ui_structure import render_structure_panel
from orthoxrd.ui_style import apply_style, summary_grid
from orthoxrd.ui_sweep import render_sweep_view

VIEW_CODES = ("pattern", "peaks", "f2", "sweep", "fit", "method")


def main() -> None:
    ensure_language_state()
    st.set_page_config(
        page_title=t("app.page_title"),
        page_icon=":material/science:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_style()
    # Apply y* must land before structure number_inputs are created this run.
    consume_pending_structure_apply()
    try:
        advanced = _render_title_and_advanced()
        radiation, structure = _render_core_parameters()
        _render_required_input_review()
        config = build_simulation_config(structure, radiation, advanced)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
        raise RuntimeError("Streamlit stop did not interrupt execution") from exc
    with st.spinner(t("app.spinner")):
        result = calculate_cached(config)
    digest = config_hash(config)
    _render_active_configuration(structure, radiation, digest, result)
    navigation = st.segmented_control(
        t("nav.label"),
        VIEW_CODES,
        format_func=lambda code: t(f"nav.{code}"),
        default="pattern",
        key="result_view",
        label_visibility="collapsed",
        help=th("nav.label"),
    )
    match navigation:
        case "peaks":
            render_peaks_view(result)
        case "f2":
            render_f2_view(result)
        case "sweep":
            render_sweep_view(result)
        case "fit":
            render_fit_view(result.config)
        case "method":
            render_method_view()
        case _:
            render_pattern_view(result)


def _render_title_and_advanced():
    title_col, lang_col, settings_col = st.columns(
        (5.0, 0.9, 1.2),
        vertical_alignment="center",
    )
    with title_col:
        st.markdown(
            f"""
<div class="xrd-titlebar">
  <h1>{t("app.page_title")}</h1>
  <span class="xrd-model-tag">{t("app.model_tag")}</span>
</div>
<div class="xrd-subtitle">
  {t("app.subtitle")}
</div>
""",
            unsafe_allow_html=True,
        )
    with lang_col:
        render_language_toggle()
    with settings_col:
        return render_advanced_settings()


def _render_core_parameters():
    st.divider()
    radiation_col, structure_col = st.columns((1.0, 1.8), gap="large")
    with radiation_col:
        radiation = render_radiation_panel()
    with structure_col:
        structure = render_structure_panel()
    return radiation, structure


def _render_required_input_review() -> None:
    st.markdown(t("inputs.required_review"), unsafe_allow_html=True)


def _prepare_current_export(result: SimulationResult) -> PreparedExport:
    return prepare_current_export(result, plot_state_from_session(result))


def _render_active_configuration(
    structure,
    radiation,
    digest: str,
    result: SimulationResult,
) -> None:
    lattice = structure.lattice
    signed = signed_shuffle_from_y(structure.y)
    summary_col, export_col = st.columns((6.0, 1.45), vertical_alignment="center")
    with summary_col:
        summary_grid(
            [
                (t("app.summary.a"), f"{lattice.a:.5f}"),
                (t("app.summary.b"), f"{lattice.b:.5f}"),
                (t("app.summary.c"), f"{lattice.c:.5f}"),
                (t("app.summary.y"), f"{structure.y:.6f}"),
                (t("app.summary.shuffle"), f"{abs(signed):.6f}"),
                (t("app.summary.energy"), f"{radiation.primary_energy_kev:.6g}"),
                (t("app.summary.lambda"), f"{radiation.primary_wavelength_a:.7g}"),
                (t("app.summary.hash"), digest[:12]),
            ]
        )
    with export_col:
        state = plot_state_from_session(result)
        render_current_export(
            result,
            digest,
            _prepare_current_export,
            state_signature=(
                f"{digest}:{state.x_axis}:{state.x_minimum:.12g}:{state.x_maximum:.12g}:"
                f"{int(state.y_auto)}:{state.y_minimum:.12g}:{state.y_maximum:.12g}"
            ),
        )
    config = result.config
    composition = (
        composition_to_text(config.composition)
        if config.scattering_mode == "composition"
        else t("app.active_model.composition_na")
    )
    st.caption(
        t(
            "app.active_model_details",
            scattering=t(f"advanced.scattering.{config.scattering_mode}"),
            composition=composition,
            tth_min=config.two_theta_min,
            tth_max=config.two_theta_max,
            profile=t(f"advanced.profile.{config.profile_kind}"),
            fwhm=config.fwhm_deg,
            lp=t("common.on") if config.include_lorentz_polarization else t("common.off"),
            multiplicity=t("common.on") if config.include_multiplicity else t("common.off"),
            volume=t("common.on") if config.include_cell_volume else t("common.off"),
        )
    )
    st.divider()
