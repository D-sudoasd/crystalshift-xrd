from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import streamlit as st

from orthoxrd.i18n import t, th
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
    with st.popover(t("advanced.popover"), use_container_width=True):
        st.markdown(t("advanced.scattering_section"))
        scattering_mode, composition = _scattering_inputs()
        st.markdown(t("advanced.window_section"))
        pattern = _pattern_inputs()
        st.markdown(t("advanced.profile_section"))
        profile_kind, fwhm, eta = _profile_inputs()
        st.markdown(t("advanced.factors_section"))
        include_lp = st.checkbox(
            t("advanced.lp"),
            value=True,
            key="advanced_lp",
            help=th("advanced.lp"),
        )
        include_mult = st.checkbox(
            t("advanced.multiplicity"),
            value=True,
            key="advanced_multiplicity",
            help=th("advanced.multiplicity"),
        )
        include_volume = st.checkbox(
            t("advanced.volume"),
            value=True,
            key="advanced_volume",
            help=th("advanced.volume"),
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
    mode = st.selectbox(
        t("advanced.scattering"),
        ["composition", "unit"],
        format_func=lambda code: t(f"advanced.scattering.{code}"),
        key="advanced_scattering",
        help=th("advanced.scattering"),
    )
    if mode == "unit":
        st.caption(t("advanced.unit_caption"))
        return "unit", ()
    text = st.text_area(
        t("advanced.composition"),
        value=composition_to_text(TI2448_COMPOSITION),
        height=88,
        key="advanced_composition",
        help=th("advanced.composition"),
    )
    return "composition", tuple(parse_composition(text))


def _pattern_inputs() -> tuple[float, float, int, float, int]:
    left, right = st.columns(2)
    with left:
        minimum = float(
            st.number_input(
                t("advanced.tth_min"),
                0.0,
                170.0,
                1.0,
                0.5,
                key="advanced_tth_min",
                help=th("advanced.tth_min"),
            )
        )
        hkl_max = int(
            st.slider(
                t("advanced.hkl_max"),
                1,
                12,
                6,
                key="advanced_hkl_max",
                help=th("advanced.hkl_max"),
            )
        )
        points = int(
            st.number_input(
                t("advanced.points"),
                min_value=200,
                max_value=10_000,
                value=4000,
                step=200,
                key="advanced_points",
                help=th("advanced.points"),
            )
        )
    with right:
        maximum = float(
            st.number_input(
                t("advanced.tth_max"),
                1.0,
                179.0,
                20.0,
                0.5,
                key="advanced_tth_max",
                help=th("advanced.tth_max"),
            )
        )
        cutoff = float(
            st.number_input(
                t("advanced.cutoff"),
                min_value=0.0,
                max_value=100.0,
                value=0.1,
                step=0.1,
                key="advanced_cutoff",
                help=th("advanced.cutoff"),
            )
        )
    if maximum <= minimum:
        raise ValueError("2theta max must be greater than 2theta min")
    return minimum, maximum, hkl_max, cutoff, points


def _profile_inputs() -> tuple[ProfileKind, float, float]:
    selected = st.selectbox(
        t("advanced.profile"),
        ["pseudo_voigt", "gaussian", "lorentzian"],
        key="advanced_profile",
        help=th("advanced.profile"),
    )
    profile_kind = cast(ProfileKind, selected)
    left, right = st.columns(2)
    with left:
        fwhm = float(
            st.number_input(
                t("advanced.fwhm"),
                min_value=0.001,
                max_value=5.0,
                value=0.06,
                step=0.005,
                format="%.4f",
                key="advanced_fwhm",
                help=th("advanced.fwhm"),
            )
        )
    with right:
        eta = float(
            st.slider(
                t("advanced.eta"),
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                key="advanced_eta",
                disabled=selected != "pseudo_voigt",
                help=th("advanced.eta"),
            )
        )
    return profile_kind, fwhm, eta
