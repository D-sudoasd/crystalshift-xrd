"""Bilingual UI text helpers for CrystalShift XRD.

Stable option codes stay language-independent. Display strings come from locales.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Final, Literal

import streamlit as st

from orthoxrd.locales import HELP, TEXT

Lang = Literal["zh", "en"]

LANG_KEY: Final = "current_language"
DEFAULT_LANG: Final[Lang] = "zh"
_MIGRATED_KEY: Final = "_i18n_session_migrated_v1"

# Map legacy English widget values to stable codes.
_SESSION_MIGRATIONS: Final[Mapping[str, Mapping[str, str]]] = {
    "result_view": {
        "Pattern": "pattern",
        "Peaks": "peaks",
        "F2 evolution": "f2",
        "Sweep": "sweep",
        "Method": "method",
    },
    "pattern_mode": {
        "Static": "static",
        "Live evolution": "live",
    },
    "pattern_intensity": {
        "Relative": "relative",
        "Model": "model",
    },
    "pattern_display": {
        "Combined": "combined",
        "Line": "line",
        "Sticks": "sticks",
    },
    "f2_axis": {
        "Wyckoff y": "y",
        "Signed shuffle": "signed_shuffle",
        "Shuffle magnitude": "shuffle_magnitude",
    },
    "f2_branch": {
        "Lower": "lower",
        "Upper": "upper",
    },
    "live_shuffle_branch": {
        "Lower": "lower",
        "Upper": "upper",
    },
    "sweep_input_mode": {
        "Range sweep": "range",
        "CSV trajectory": "trajectory",
    },
    "sweep_normalization": {
        "Global across sweep": "global",
        "Local per step": "local",
        "Model intensity": "model",
    },
    "sweep_result_view": {
        "Heatmap": "heatmap",
        "Waterfall": "waterfall",
        "Peak evolution": "peak_evolution",
        "Data preview": "data_preview",
    },
    "sweep_peak_metric": {
        "F2": "F2",
        "Model peak intensity": "I_model",
        "Global relative peak intensity": "I_rel_global",
    },
    "sweep_axis": {
        "Wyckoff y": "y",
        "Shuffle magnitude": "shuffle_magnitude",
        "Lattice a": "a_A",
        "Lattice b": "b_A",
        "Lattice c": "c_A",
        "Energy": "energy_keV",
        "Wavelength": "wavelength_A",
    },
    "live_axis": {
        "Shuffle magnitude": "shuffle_magnitude",
        "Wyckoff y": "y",
        "Lattice a": "a_A",
        "Lattice b": "b_A",
        "Lattice c": "c_A",
        "Energy": "energy_keV",
        "Wavelength": "wavelength_A",
    },
    "sweep_shuffle_branch": {
        "Lower": "lower",
        "Upper": "upper",
    },
    "advanced_scattering": {
        "Composition form factor": "composition",
        "Unit scatterer F2": "unit",
    },
}


def ensure_language_state() -> None:
    """Initialize language and migrate legacy English option values once."""
    if LANG_KEY not in st.session_state:
        st.session_state[LANG_KEY] = DEFAULT_LANG
    raw = st.session_state[LANG_KEY]
    if raw not in {"zh", "en"}:
        st.session_state[LANG_KEY] = DEFAULT_LANG
    if st.session_state.get(_MIGRATED_KEY):
        return
    for key, mapping in _SESSION_MIGRATIONS.items():
        value = st.session_state.get(key)
        if isinstance(value, str) and value in mapping:
            st.session_state[key] = mapping[value]
    st.session_state[_MIGRATED_KEY] = True


def get_lang() -> Lang:
    ensure_language_state()
    value = st.session_state.get(LANG_KEY, DEFAULT_LANG)
    return "en" if value == "en" else "zh"


def t(key: str, **kwargs: object) -> str:
    """Return a UI label/message for the active language."""
    lang = get_lang()
    catalog = TEXT[lang]
    fallback = TEXT["en"]
    template = catalog.get(key, fallback.get(key, key))
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template
    return template


def th(key: str, **kwargs: object) -> str:
    """Return help/tooltip text for the active language."""
    lang = get_lang()
    catalog = HELP[lang]
    fallback = HELP["en"]
    template = catalog.get(key, fallback.get(key, ""))
    if kwargs and template:
        try:
            return template.format(**kwargs)
        except (KeyError, ValueError):
            return template
    return template


def tf(prefix: str) -> Callable[[str], str]:
    """Build a format_func that maps stable codes to translated labels."""

    def _format(code: str) -> str:
        return t(f"{prefix}.{code}")

    return _format


def axis_label(code: str) -> str:
    return t(f"axis.{code}")


def radiation_mode_label(mode: str) -> str:
    key = f"radiation.mode.{mode}"
    translated = t(key)
    return mode if translated == key else translated


def render_language_toggle() -> None:
    """Render the language segmented control in the title bar."""
    ensure_language_state()
    st.segmented_control(
        t("lang.label"),
        options=["zh", "en"],
        format_func=lambda code: t(f"lang.{code}"),
        key=LANG_KEY,
        label_visibility="collapsed",
        help=th("lang.label"),
    )
