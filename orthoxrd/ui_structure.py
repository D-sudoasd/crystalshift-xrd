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
from orthoxrd.i18n import t, th
from orthoxrd.models import LatticeParameters
from orthoxrd.presets import LATTICE_PRESETS
from orthoxrd.structure_coordinates import StructureBranch, structure_branch_from_y
from orthoxrd.structure_factor import (
    normalized_shuffle_from_y,
    signed_shuffle_from_y,
    y_from_shuffle_magnitude,
)
from orthoxrd.structure_state import StructureState

PRESET_KEY = "structure_preset"
A_KEY = "structure_a"
B_KEY = "structure_b"
C_KEY = "structure_c"
Y_KEY = "structure_y"
SHUFFLE_KEY = "structure_shuffle"
BRANCH_KEY = "structure_shuffle_branch"


def render_structure_panel() -> StructureState:
    _ensure_structure_defaults()
    st.markdown(f"#### {t('structure.title')}")
    preset_name = st.selectbox(
        t("structure.preset"),
        list(LATTICE_PRESETS),
        key=PRESET_KEY,
        on_change=_apply_selected_preset,
        help=th("structure.preset"),
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
    if BRANCH_KEY not in st.session_state:
        current_y = float(st.session_state[Y_KEY])
        st.session_state[BRANCH_KEY] = "upper" if current_y > 0.25 else "lower"


def _set_structure_values(preset_name: str) -> None:
    preset = LATTICE_PRESETS[preset_name]
    st.session_state[A_KEY] = preset.lattice.a
    st.session_state[B_KEY] = preset.lattice.b
    st.session_state[C_KEY] = preset.lattice.c
    set_structure_y_state(preset.y)


def _apply_selected_preset() -> None:
    _set_structure_values(str(st.session_state[PRESET_KEY]))


def _sync_shuffle_from_y() -> None:
    set_structure_y_state(float(st.session_state[Y_KEY]))


def _sync_y_from_shuffle() -> None:
    shuffle_magnitude = float(st.session_state[SHUFFLE_KEY])
    branch: StructureBranch = (
        "upper" if st.session_state[BRANCH_KEY] == "upper" else "lower"
    )
    set_structure_shuffle_state(shuffle_magnitude, branch)


def set_structure_y_state(
    y_value: float,
    *,
    reference_branch: StructureBranch | None = None,
) -> None:
    """Synchronise canonical y, shuffle magnitude, and the editable magnitude branch."""
    st.session_state[Y_KEY] = y_value
    st.session_state[SHUFFLE_KEY] = abs(signed_shuffle_from_y(y_value))
    branch = structure_branch_from_y(y_value)
    if branch is not None:
        st.session_state[BRANCH_KEY] = branch
    elif reference_branch is not None:
        st.session_state[BRANCH_KEY] = reference_branch
    elif BRANCH_KEY not in st.session_state:
        st.session_state[BRANCH_KEY] = "lower"


def set_structure_shuffle_state(
    shuffle_magnitude: float,
    branch: StructureBranch,
) -> None:
    """Resolve an explicitly branched magnitude and synchronise all structure widgets."""
    y_value = y_from_shuffle_magnitude(
        shuffle_magnitude,
        upper_branch=branch == "upper",
    )
    set_structure_y_state(y_value, reference_branch=branch)


def _render_lattice_inputs() -> LatticeParameters:
    a_col, b_col, c_col = st.columns(3)
    with a_col:
        a_value = st.number_input(
            t("structure.a"),
            1.0,
            20.0,
            step=0.001,
            format="%.4f",
            key=A_KEY,
            help=th("structure.a"),
        )
    with b_col:
        b_value = st.number_input(
            t("structure.b"),
            1.0,
            20.0,
            step=0.001,
            format="%.4f",
            key=B_KEY,
            help=th("structure.b"),
        )
    with c_col:
        c_value = st.number_input(
            t("structure.c"),
            1.0,
            20.0,
            step=0.001,
            format="%.4f",
            key=C_KEY,
            help=th("structure.c"),
        )
    return LatticeParameters(float(a_value), float(b_value), float(c_value))


def _render_shuffle_inputs() -> float:
    y_col, shuffle_col, signed_col = st.columns(3)
    with y_col:
        y_value = st.number_input(
            t("structure.y", ymin=WYCKOFF_Y_MIN, ymax=WYCKOFF_Y_MAX),
            WYCKOFF_Y_MIN,
            WYCKOFF_Y_MAX,
            step=0.001,
            format="%.4f",
            key=Y_KEY,
            on_change=_sync_shuffle_from_y,
            help=th("structure.y"),
        )
    with shuffle_col:
        st.number_input(
            t(
                "structure.shuffle",
                smin=SHUFFLE_MAGNITUDE_MIN,
                smax=SHUFFLE_MAGNITUDE_MAX,
            ),
            SHUFFLE_MAGNITUDE_MIN,
            SHUFFLE_MAGNITUDE_MAX,
            step=0.001,
            format="%.4f",
            key=SHUFFLE_KEY,
            on_change=_sync_y_from_shuffle,
            help=th("structure.shuffle"),
        )
        st.segmented_control(
            t("structure.branch"),
            ["lower", "upper"],
            format_func=lambda value: t(f"structure.branch.{value}"),
            key=BRANCH_KEY,
            on_change=_sync_y_from_shuffle,
            help=th("structure.branch"),
        )
    with signed_col:
        signed_shuffle = signed_shuffle_from_y(float(y_value))
        normalized = normalized_shuffle_from_y(float(y_value))
        branch = structure_branch_from_y(float(y_value))
        branch_label = (
            t("structure.branch.reference")
            if branch is None
            else t(f"structure.branch.{branch}")
        )
        st.markdown(
            """
            <div class="xrd-readout-card">
                <div class="xrd-readout-label">{label}</div>
                <div class="xrd-readout-value">{value}</div>
                <div class="xrd-readout-meta">{meta}</div>
            </div>
            <div class="xrd-readout-card" style="margin-top:0.5rem;">
                <div class="xrd-readout-label">{norm_label}</div>
                <div class="xrd-readout-value">{norm_value}</div>
                <div class="xrd-readout-meta">{norm_meta}</div>
            </div>
            """.format(
                label=t("structure.signed_label"),
                value=f"{signed_shuffle:+.4f}",
                meta=t(
                    "structure.signed_meta",
                    branch=branch_label,
                ),
                norm_label=t("structure.normalized_label"),
                norm_value=f"{normalized:.4f}",
                norm_meta=t("structure.normalized_meta"),
            ),
            unsafe_allow_html=True,
        )
    return float(y_value)


def _render_range_note() -> None:
    signed_min = signed_shuffle_from_y(WYCKOFF_Y_MIN)
    signed_max = signed_shuffle_from_y(WYCKOFF_Y_MAX)
    st.markdown(
        t(
            "structure.relation_note",
            y_min=TI_NB_Y_MIN,
            y_max=TI_NB_Y_MAX,
            s_max=TI_NB_SHUFFLE_MAGNITUDE_MAX,
        ),
        unsafe_allow_html=True,
    )
    with st.expander(t("structure.expander")):
        st.caption(
            t("structure.range_y", ymin=WYCKOFF_Y_MIN, ymax=WYCKOFF_Y_MAX)
        )
        st.caption(
            t("structure.range_signed", smin=signed_min, smax=signed_max)
        )
        st.caption(
            t(
                "structure.range_mag",
                smin=SHUFFLE_MAGNITUDE_MIN,
                smax=SHUFFLE_MAGNITUDE_MAX,
            )
        )
        st.caption(t("structure.range_normalized"))
        st.caption(
            t(
                "structure.range_tinb",
                ymin=TI_NB_Y_MIN,
                ymax=TI_NB_Y_MAX,
                smin=SHUFFLE_MAGNITUDE_MIN,
                smax=TI_NB_SHUFFLE_MAGNITUDE_MAX,
            )
        )
        st.caption(t("structure.branch_detail"))
