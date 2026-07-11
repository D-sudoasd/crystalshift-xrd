from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

from orthoxrd.i18n import radiation_mode_label, t, th
from orthoxrd.models import RadiationLine
from orthoxrd.powder import energy_kev_to_wavelength_a, wavelength_a_to_energy_kev
from orthoxrd.presets import RADIATION_PRESETS

MODE_KEY = "radiation_mode"
ENERGY_KEY = "radiation_energy"
WAVELENGTH_KEY = "radiation_wavelength"
DOUBLET_KEY = "radiation_include_k_alpha2"
CUSTOM_TEMPLATE_KEY = "radiation_custom_template"
CUSTOM_TEMPLATE_MODE_KEY = "radiation_custom_template_mode"


@dataclass(frozen=True, slots=True)
class RadiationState:
    mode: str
    lines: tuple[RadiationLine, ...]
    primary_wavelength_a: float
    primary_energy_kev: float


def render_radiation_panel() -> RadiationState:
    _ensure_defaults()
    st.markdown(f"#### {t('radiation.title')}")
    mode = st.selectbox(
        t("radiation.source"),
        ["Custom energy", "Custom wavelength", *RADIATION_PRESETS.keys()],
        key=MODE_KEY,
        format_func=radiation_mode_label,
        help=th("radiation.source"),
    )
    lines = _lines_from_mode(mode)
    primary_line = lines[0]
    primary_energy = wavelength_a_to_energy_kev(primary_line.wavelength_a)
    _render_radiation_note(mode, lines, primary_energy)
    return RadiationState(
        mode=mode,
        lines=lines,
        primary_wavelength_a=primary_line.wavelength_a,
        primary_energy_kev=primary_energy,
    )


def _ensure_defaults() -> None:
    st.session_state.setdefault(MODE_KEY, "Custom energy")
    st.session_state.setdefault(ENERGY_KEY, 30.0)
    st.session_state.setdefault(WAVELENGTH_KEY, 1.540593)
    st.session_state.setdefault(DOUBLET_KEY, True)


def _lines_from_mode(mode: str) -> tuple[RadiationLine, ...]:
    template = _custom_template(mode)
    if mode == "Custom energy":
        energy = float(
            st.number_input(
                t("radiation.energy"),
                min_value=1.0,
                max_value=200.0,
                step=0.5,
                format="%.4f",
                key=ENERGY_KEY,
                help=th("radiation.energy"),
            )
        )
        wavelength = energy_kev_to_wavelength_a(energy)
        return _scale_custom_template(template, wavelength, f"{energy:g} keV")
    if mode == "Custom wavelength":
        wavelength = float(
            st.number_input(
                t("radiation.wavelength"),
                min_value=0.05,
                max_value=5.0,
                step=0.001,
                format="%.6f",
                key=WAVELENGTH_KEY,
                help=th("radiation.wavelength"),
            )
        )
        return _scale_custom_template(template, wavelength, f"{wavelength:g} A")
    preset_lines = RADIATION_PRESETS[mode]
    if len(preset_lines) == 1:
        return preset_lines
    include_doublet = st.checkbox(
        t("radiation.include_k_alpha2"),
        key=DOUBLET_KEY,
        help=th("radiation.include_k_alpha2"),
    )
    return preset_lines if include_doublet else (preset_lines[0],)


def install_custom_radiation_template(
    mode: str,
    lines: tuple[RadiationLine, ...],
) -> None:
    if mode not in {"Custom energy", "Custom wavelength"}:
        raise ValueError("custom radiation template requires a custom source mode")
    st.session_state[CUSTOM_TEMPLATE_MODE_KEY] = mode
    st.session_state[CUSTOM_TEMPLATE_KEY] = lines


def _custom_template(mode: str) -> tuple[RadiationLine, ...]:
    if st.session_state.get(CUSTOM_TEMPLATE_MODE_KEY) != mode:
        st.session_state.pop(CUSTOM_TEMPLATE_KEY, None)
        st.session_state.pop(CUSTOM_TEMPLATE_MODE_KEY, None)
        return ()
    value = st.session_state.get(CUSTOM_TEMPLATE_KEY)
    if isinstance(value, tuple) and value and all(
        isinstance(line, RadiationLine) for line in value
    ):
        return value
    st.session_state.pop(CUSTOM_TEMPLATE_KEY, None)
    st.session_state.pop(CUSTOM_TEMPLATE_MODE_KEY, None)
    return ()


def _scale_custom_template(
    template: tuple[RadiationLine, ...],
    primary_wavelength_a: float,
    fallback_label: str,
) -> tuple[RadiationLine, ...]:
    if not template:
        return (RadiationLine(fallback_label, primary_wavelength_a, 1.0),)
    scale = primary_wavelength_a / template[0].wavelength_a
    return tuple(
        RadiationLine(line.label, line.wavelength_a * scale, line.weight)
        for line in template
    )


def _render_radiation_note(
    mode: str,
    lines: tuple[RadiationLine, ...],
    primary_energy_kev: float,
) -> None:
    primary_line = lines[0]
    if mode == "Custom energy":
        suffix = _custom_line_note(lines)
        st.caption(
            t(
                "radiation.primary_wavelength",
                wavelength=primary_line.wavelength_a,
                suffix=suffix,
            )
        )
        return
    if mode == "Custom wavelength":
        suffix = _custom_line_note(lines)
        st.caption(
            t(
                "radiation.primary_energy",
                energy=primary_energy_kev,
                suffix=suffix,
            )
        )
        return
    if len(lines) == 1:
        st.caption(
            t(
                "radiation.primary_line_single",
                label=primary_line.label,
                wavelength=primary_line.wavelength_a,
                energy=primary_energy_kev,
            )
        )
        return
    secondary_line = lines[1]
    st.caption(
        t(
            "radiation.primary_line_doublet",
            primary=primary_line.label,
            w1=primary_line.weight,
            secondary=secondary_line.label,
            w2=secondary_line.weight,
        )
    )


def _custom_line_note(lines: tuple[RadiationLine, ...]) -> str:
    if len(lines) == 1:
        return ""
    return t("radiation.scaled_suffix", count=len(lines))
