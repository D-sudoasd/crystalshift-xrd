from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import streamlit as st

from orthoxrd.models import ElementFraction, ProfileKind, ScatteringMode
from orthoxrd.presets import TI2448_COMPOSITION
from orthoxrd.scattering import composition_to_text, parse_composition


@dataclass(frozen=True, slots=True)
class AdvancedState:
    scattering_mode: ScatteringMode
    composition: tuple[ElementFraction, ...]
    two_theta_min: float
    two_theta_max: float
    hkl_max: int
    min_peak: float
    spectrum_points: int
    profile_kind: ProfileKind
    fwhm: float
    eta: float
    include_lorentz_polarization: bool
    include_multiplicity: bool
    include_cell_volume: bool


def render_advanced_settings() -> AdvancedState:
    with st.popover("Advanced settings", use_container_width=True):
        st.markdown("##### Scattering")
        scattering_mode, composition = _scattering_inputs()
        st.markdown("##### Simulation window")
        pattern = _pattern_inputs()
        st.markdown("##### Peak profile")
        profile_kind, fwhm, eta = _profile_inputs()
        st.markdown("##### Applied factors")
        include_lp = st.checkbox("Lorentz-polarization", value=True, key="advanced_lp")
        include_mult = st.checkbox(
            "Orthorhombic multiplicity", value=True, key="advanced_multiplicity"
        )
        include_volume = st.checkbox(
            "Scale by unit-cell volume (1/V)", value=True, key="advanced_volume"
        )
    return AdvancedState(
        scattering_mode=scattering_mode,
        composition=composition,
        two_theta_min=pattern[0],
        two_theta_max=pattern[1],
        hkl_max=pattern[2],
        min_peak=pattern[3],
        spectrum_points=pattern[4],
        profile_kind=profile_kind,
        fwhm=fwhm,
        eta=eta,
        include_lorentz_polarization=include_lp,
        include_multiplicity=include_mult,
        include_cell_volume=include_volume,
    )


def _scattering_inputs() -> tuple[ScatteringMode, tuple[ElementFraction, ...]]:
    label = st.selectbox(
        "Atomic scattering",
        ["Composition form factor", "Unit scatterer F2"],
        key="advanced_scattering",
        help="Composition mode uses the effective X-ray form factor versus s.",
    )
    if label == "Unit scatterer F2":
        st.caption("All sites use f=1. Best for isolating the analytical F2(y) trend.")
        return "unit", ()
    text = st.text_area(
        "Composition fractions",
        value=composition_to_text(TI2448_COMPOSITION),
        height=88,
        key="advanced_composition",
        help="Comma-separated element fractions, for example Ti=0.24, Nb=0.48, Zr=0.28.",
    )
    return "composition", tuple(parse_composition(text))


def _pattern_inputs() -> tuple[float, float, int, float, int]:
    left, right = st.columns(2)
    with left:
        minimum = float(
            st.number_input(
                "Simulation 2theta min (deg)", 0.0, 170.0, 1.0, 0.5, key="advanced_tth_min"
            )
        )
        hkl_max = int(st.slider("Max h, k, l", 1, 12, 6, key="advanced_hkl_max"))
        points = int(
            st.number_input(
                "Spectrum points",
                min_value=200,
                max_value=10_000,
                value=4000,
                step=200,
                key="advanced_points",
            )
        )
    with right:
        maximum = float(
            st.number_input(
                "Simulation 2theta max (deg)", 1.0, 179.0, 20.0, 0.5, key="advanced_tth_max"
            )
        )
        cutoff = float(
            st.number_input(
                "Table cutoff (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.1,
                step=0.1,
                key="advanced_cutoff",
            )
        )
    if maximum <= minimum:
        raise ValueError("2theta max must be greater than 2theta min")
    return minimum, maximum, hkl_max, cutoff, points


def _profile_inputs() -> tuple[ProfileKind, float, float]:
    selected = st.selectbox(
        "Peak shape",
        ["pseudo_voigt", "gaussian", "lorentzian"],
        key="advanced_profile",
    )
    profile_kind = cast(ProfileKind, selected)
    left, right = st.columns(2)
    with left:
        fwhm = float(
            st.number_input(
                "FWHM (deg 2theta)",
                min_value=0.001,
                max_value=5.0,
                value=0.06,
                step=0.005,
                format="%.4f",
                key="advanced_fwhm",
            )
        )
    with right:
        eta = float(
            st.slider(
                "Pseudo-Voigt eta",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                key="advanced_eta",
                disabled=selected != "pseudo_voigt",
            )
        )
    return profile_kind, fwhm, eta
