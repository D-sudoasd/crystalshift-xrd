from __future__ import annotations

import streamlit as st

from orthoxrd.config import config_hash
from orthoxrd.export_writer import PreparedExport
from orthoxrd.export_zip import prepare_current_export
from orthoxrd.simulation import SimulationResult
from orthoxrd.structure_factor import signed_shuffle_from_y
from orthoxrd.ui_config import build_simulation_config, calculate_cached
from orthoxrd.ui_export import render_current_export
from orthoxrd.ui_f2 import render_f2_view
from orthoxrd.ui_method import render_method_view
from orthoxrd.ui_pattern import render_pattern_view
from orthoxrd.ui_peaks import render_peaks_view
from orthoxrd.ui_plot_state import plot_state_from_session
from orthoxrd.ui_radiation import render_radiation_panel
from orthoxrd.ui_sidebar import render_advanced_settings
from orthoxrd.ui_structure import render_structure_panel
from orthoxrd.ui_style import apply_style, summary_grid
from orthoxrd.ui_sweep import render_sweep_view

VIEWS = ["Pattern", "Peaks", "F2 evolution", "Sweep", "Method"]


def main() -> None:
    st.set_page_config(
        page_title="Orthorhombic XRD Simulator",
        page_icon=":material/science:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    apply_style()
    try:
        advanced = _render_title_and_advanced()
        radiation, structure = _render_core_parameters()
        config = build_simulation_config(structure, radiation, advanced)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
        raise RuntimeError("Streamlit stop did not interrupt execution") from exc
    with st.spinner("Calculating active model..."):
        result = calculate_cached(config)
    digest = config_hash(config)
    _render_active_configuration(structure, radiation, digest, result)
    navigation = st.segmented_control(
        "Result view",
        VIEWS,
        default="Pattern",
        key="result_view",
        label_visibility="collapsed",
    )
    match navigation:
        case "Peaks":
            render_peaks_view(result)
        case "F2 evolution":
            render_f2_view(result)
        case "Sweep":
            render_sweep_view(result)
        case "Method":
            render_method_view()
        case _:
            render_pattern_view(result)


def _render_title_and_advanced():
    title_col, settings_col = st.columns((5.5, 1.35), vertical_alignment="center")
    with title_col:
        st.markdown(
            """
<div class="xrd-titlebar">
  <h1>Orthorhombic XRD Simulator</h1>
  <span class="xrd-model-tag">Cmcm 4c | schema 2.1</span>
</div>
<div class="xrd-subtitle">
  Kinematic powder model for lattice, Wyckoff-y, shuffle, and incident-radiation studies.
</div>
""",
            unsafe_allow_html=True,
        )
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


def _prepare_current_export(result: SimulationResult) -> PreparedExport:
    return prepare_current_export(result, plot_state_from_session(result))

def _render_active_configuration(structure, radiation, digest: str, result) -> None:
    lattice = structure.lattice
    signed = signed_shuffle_from_y(structure.y)
    summary_col, export_col = st.columns((6.0, 1.45), vertical_alignment="center")
    with summary_col:
        summary_grid(
            [
                ("a (A)", f"{lattice.a:.5f}"),
                ("b (A)", f"{lattice.b:.5f}"),
                ("c (A)", f"{lattice.c:.5f}"),
                ("Wyckoff y", f"{structure.y:.6f}"),
                ("shuffle |s|", f"{abs(signed):.6f}"),
                ("energy (keV)", f"{radiation.primary_energy_kev:.6g}"),
                ("lambda (A)", f"{radiation.primary_wavelength_a:.7g}"),
                ("config hash", digest[:12]),
            ]
        )
    with export_col:
        state = plot_state_from_session(result)
        render_current_export(
            result,
            digest,
            _prepare_current_export,
            state_signature=repr(state),
        )
    st.divider()
