from __future__ import annotations

import streamlit as st

from orthoxrd.constants import (
    SHUFFLE_MAGNITUDE_MAX,
    SHUFFLE_MAGNITUDE_MIN,
    TI_NB_SHUFFLE_MAGNITUDE_MAX,
    TI_NB_Y_MAX,
    TI_NB_Y_MIN,
    WYCKOFF_Y_MAX,
    WYCKOFF_Y_MIN,
)
from orthoxrd.models import LatticeParameters
from orthoxrd.presets import LATTICE_PRESETS
from orthoxrd.structure_factor import signed_shuffle_from_y, y_from_shuffle_magnitude
from orthoxrd.structure_state import StructureState

PRESET_KEY = "structure_preset"
A_KEY = "structure_a"
B_KEY = "structure_b"
C_KEY = "structure_c"
Y_KEY = "structure_y"
SHUFFLE_KEY = "structure_shuffle"


def render_structure_panel() -> StructureState:
    _ensure_structure_defaults()
    st.markdown("#### Structure")
    preset_name = st.selectbox(
        "Lattice preset",
        list(LATTICE_PRESETS),
        key=PRESET_KEY,
        on_change=_apply_selected_preset,
    )
    st.caption(LATTICE_PRESETS[preset_name].note)
    lattice = _render_lattice_inputs()
    y_value = _render_shuffle_inputs()
    _render_range_note()
    return StructureState.from_y(lattice=lattice, y_value=y_value)


def _ensure_structure_defaults() -> None:
    first_preset = next(iter(LATTICE_PRESETS))
    if PRESET_KEY not in st.session_state:
        st.session_state[PRESET_KEY] = first_preset
        _set_structure_values(first_preset)
    if A_KEY not in st.session_state:
        _set_structure_values(str(st.session_state[PRESET_KEY]))


def _set_structure_values(preset_name: str) -> None:
    preset = LATTICE_PRESETS[preset_name]
    st.session_state[A_KEY] = preset.lattice.a
    st.session_state[B_KEY] = preset.lattice.b
    st.session_state[C_KEY] = preset.lattice.c
    st.session_state[Y_KEY] = preset.y
    st.session_state[SHUFFLE_KEY] = abs(signed_shuffle_from_y(preset.y))


def _apply_selected_preset() -> None:
    _set_structure_values(str(st.session_state[PRESET_KEY]))


def _sync_shuffle_from_y() -> None:
    y_value = float(st.session_state[Y_KEY])
    st.session_state[SHUFFLE_KEY] = abs(signed_shuffle_from_y(y_value))


def _sync_y_from_shuffle() -> None:
    shuffle_magnitude = float(st.session_state[SHUFFLE_KEY])
    current_y = float(st.session_state[Y_KEY])
    st.session_state[Y_KEY] = y_from_shuffle_magnitude(
        shuffle_magnitude,
        upper_branch=current_y > 0.25,
    )


def _render_lattice_inputs() -> LatticeParameters:
    a_col, b_col, c_col = st.columns(3)
    with a_col:
        a_value = st.number_input("a (A)", 1.0, 20.0, step=0.001, format="%.4f", key=A_KEY)
    with b_col:
        b_value = st.number_input("b (A)", 1.0, 20.0, step=0.001, format="%.4f", key=B_KEY)
    with c_col:
        c_value = st.number_input("c (A)", 1.0, 20.0, step=0.001, format="%.4f", key=C_KEY)
    return LatticeParameters(float(a_value), float(b_value), float(c_value))


def _render_shuffle_inputs() -> float:
    y_col, shuffle_col, signed_col = st.columns(3)
    with y_col:
        y_value = st.number_input(
            f"Wyckoff y ({WYCKOFF_Y_MIN:.3f}-{WYCKOFF_Y_MAX:.3f})",
            WYCKOFF_Y_MIN,
            WYCKOFF_Y_MAX,
            step=0.001,
            format="%.4f",
            key=Y_KEY,
            on_change=_sync_shuffle_from_y,
        )
    with shuffle_col:
        st.number_input(
            (f"Basal shuffle magnitude ({SHUFFLE_MAGNITUDE_MIN:.3f}-{SHUFFLE_MAGNITUDE_MAX:.3f})"),
            SHUFFLE_MAGNITUDE_MIN,
            SHUFFLE_MAGNITUDE_MAX,
            step=0.001,
            format="%.4f",
            key=SHUFFLE_KEY,
            on_change=_sync_y_from_shuffle,
        )
    with signed_col:
        signed_shuffle = signed_shuffle_from_y(float(y_value))
        st.markdown(
            """
            <div class="xrd-readout-card">
                <div class="xrd-readout-label">signed shuffle</div>
                <div class="xrd-readout-value">{value}</div>
                <div class="xrd-readout-meta">2(y - 0.25)</div>
            </div>
            """.format(value=f"{signed_shuffle:+.4f}"),
            unsafe_allow_html=True,
        )
    return float(y_value)


def _render_range_note() -> None:
    signed_min = signed_shuffle_from_y(WYCKOFF_Y_MIN)
    signed_max = signed_shuffle_from_y(WYCKOFF_Y_MAX)
    st.markdown(
        '<div class="xrd-note"><strong>y / shuffle relation</strong> '
        'signed = 2(y - 0.25); magnitude = abs(signed). '
        f'Ti-Nb lower branch: y={TI_NB_Y_MIN:.3f}..{TI_NB_Y_MAX:.3f}, '
        f'magnitude=0..{TI_NB_SHUFFLE_MAGNITUDE_MAX:.3f}.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("Valid ranges and branch details"):
        st.caption(
            f"Wyckoff y valid range: {WYCKOFF_Y_MIN:.3f} to {WYCKOFF_Y_MAX:.3f}"
        )
        st.caption(
            "shuffle_signed = 2(y - 0.25), range: "
            f"{signed_min:.3f} to {signed_max:+.3f}"
        )
        st.caption(
            "shuffle_magnitude = abs(shuffle_signed), range: "
            f"{SHUFFLE_MAGNITUDE_MIN:.3f} to {SHUFFLE_MAGNITUDE_MAX:.3f}"
        )
        st.caption(
            "Default Ti-Nb lower-branch sweep: "
            f"y={TI_NB_Y_MIN:.3f}..{TI_NB_Y_MAX:.3f}, "
            f"shuffle_magnitude={SHUFFLE_MAGNITUDE_MIN:.3f}.."
            f"{TI_NB_SHUFFLE_MAGNITUDE_MAX:.3f}"
        )
        st.caption(
            "Lower branch: y = 0.25 - shuffle_magnitude / 2; "
            "upper branch: y = 0.25 + shuffle_magnitude / 2."
        )
