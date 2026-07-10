from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Final, assert_never

import numpy as np
import streamlit as st

from orthoxrd.batch_models import ShuffleBranch, SweepAxis
from orthoxrd.live import (
    LivePreviewConfig,
    LivePreviewError,
    LivePreviewResult,
    config_for_live_value,
    current_axis_value,
    generate_live_preview,
    live_signature,
)
from orthoxrd.live_component import render_live_component
from orthoxrd.models import RadiationLine
from orthoxrd.simulation import SimulationResult
from orthoxrd.structure_factor import signed_shuffle_from_y, y_from_shuffle_magnitude
from orthoxrd.ui_live_controls import render_live_controls
from orthoxrd.ui_live_export import (
    invalidate_live_export,
    render_live_export,
)
from orthoxrd.ui_plot_state import PlotState, transform_axis
from orthoxrd.ui_radiation import (
    ENERGY_KEY,
    MODE_KEY,
    WAVELENGTH_KEY,
    install_custom_radiation_template,
)
from orthoxrd.ui_structure import A_KEY, B_KEY, C_KEY, SHUFFLE_KEY, Y_KEY

LIVE_RESULT_KEY: Final = "live_preview_result"
LIVE_BASELINE_KEY: Final = "live_baseline_index"


def render_live_view(current: SimulationResult, plot_state: PlotState) -> None:
    config = render_live_controls(current)
    desired_signature = live_signature(config)
    stored = st.session_state.get(LIVE_RESULT_KEY)
    result = stored if isinstance(stored, LivePreviewResult) else None
    if result is None or result.config.axis != config.axis:
        result = _generate(config)
    stale = result.signature != desired_signature
    if stale:
        st.markdown(
            '<div class="xrd-state xrd-state--warning">Live preview is stale. '
            "Rebuild after changing non-active physics or range settings.</div>",
            unsafe_allow_html=True,
        )
        if st.button("Rebuild live preview", type="primary", use_container_width=True):
            result = _generate(config)
            stale = False
    else:
        st.markdown(
            '<div class="xrd-state xrd-state--valid">Live preview matches the '
            "active scientific configuration.</div>",
            unsafe_allow_html=True,
        )
    current_index = _current_index(current, result)
    baseline_index = _baseline_index(result)
    if not stale:
        baseline_index = _render_baseline_action(result, current_index, baseline_index)
    _render_component(result, plot_state, current_index, baseline_index, stale)
    if stale:
        invalidate_live_export()
        st.caption("The previous preview is retained, but interaction and export are disabled.")
        return
    render_live_export(result, plot_state, current_index, baseline_index)


def _render_component(
    result: LivePreviewResult,
    plot_state: PlotState,
    current_index: int,
    baseline_index: int,
    disabled: bool,
) -> None:
    plot_state = _resolved_live_plot_state(result, plot_state)
    st.caption(
        f"{len(result.axis_values)} exact frames | {result.config.preview_points} points/frame | "
        f"{result.intensity_model.size:,} browser preview cells"
    )
    component_key = (
        f"live_pattern_{result.signature[:12]}_{baseline_index}_{int(disabled)}"
    )
    render_live_component(
        result,
        plot_state,
        current_index=current_index,
        baseline_index=baseline_index,
        component_key=component_key,
        on_selected_index_change=lambda: _commit_component(
            component_key,
            result,
            result.config.axis,
            result.config.shuffle_branch,
        ),
        disabled=disabled,
    )


def _render_baseline_action(
    result: LivePreviewResult,
    current_index: int,
    baseline_index: int,
) -> int:
    left, right = st.columns((2.2, 1))
    with left:
        st.caption(
            f"Baseline {result.axis_values[baseline_index]:.7g} | "
            f"Current {result.axis_values[current_index]:.7g}"
        )
    with right:
        if st.button("Set current as baseline", use_container_width=True):
            baseline_index = current_index
            st.session_state[LIVE_BASELINE_KEY] = current_index
            invalidate_live_export()
    return baseline_index


def _resolved_live_plot_state(
    result: LivePreviewResult,
    state: PlotState,
) -> PlotState:
    if state.x_axis == "2theta":
        return state
    base_values = transform_axis(
        result.two_theta_deg,
        result.config.base.lines[0].wavelength_a,
        state.x_axis,
    )
    finite_base = base_values[np.isfinite(base_values)]
    if not (
        np.isclose(state.x_minimum, np.min(finite_base))
        and np.isclose(state.x_maximum, np.max(finite_base))
    ):
        return state
    all_values = [
        transform_axis(result.two_theta_deg, float(wavelength), state.x_axis)
        for wavelength in result.wavelengths_a
    ]
    finite = np.concatenate([values[np.isfinite(values)] for values in all_values])
    return replace(
        state,
        x_minimum=float(np.min(finite)),
        x_maximum=float(np.max(finite)),
    )

def _current_index(current: SimulationResult, result: LivePreviewResult) -> int:
    value = current_axis_value(current.config, result.config.axis)
    return int(np.argmin(np.abs(result.axis_values - value)))


def _baseline_index(result: LivePreviewResult) -> int:
    value = int(st.session_state.get(LIVE_BASELINE_KEY, result.baseline_index))
    return max(0, min(value, len(result.axis_values) - 1))


@st.cache_data(max_entries=8, show_spinner=False, hash_funcs={LivePreviewConfig: live_signature})
def _generate_cached(config: LivePreviewConfig) -> LivePreviewResult:
    return generate_live_preview(config)


def _generate(config: LivePreviewConfig) -> LivePreviewResult:
    try:
        with st.spinner("Preparing exact live frames..."):
            result = _generate_cached(config)
    except LivePreviewError as exc:
        st.error(str(exc))
        st.stop()
        raise RuntimeError("Streamlit stop did not interrupt execution") from exc
    invalidate_live_export()
    st.session_state[LIVE_RESULT_KEY] = result
    st.session_state[LIVE_BASELINE_KEY] = result.baseline_index
    return result


def _commit_component(
    component_key: str,
    result: LivePreviewResult,
    axis: SweepAxis,
    branch: ShuffleBranch,
) -> None:
    state = st.session_state.get(component_key)
    if not isinstance(state, Mapping):
        return
    raw_index = state.get("selected_index")
    if not isinstance(raw_index, int):
        return
    index = max(0, min(raw_index, len(result.axis_values) - 1))
    value = float(result.axis_values[index])
    frame = config_for_live_value(result.config, value)
    _apply_axis_value(axis, value, branch, frame.lines)


def _apply_axis_value(
    axis: SweepAxis,
    value: float,
    branch: ShuffleBranch,
    radiation_lines: tuple[RadiationLine, ...] = (),
) -> None:
    match axis:
        case "y":
            st.session_state[Y_KEY] = value
            st.session_state[SHUFFLE_KEY] = abs(signed_shuffle_from_y(value))
        case "shuffle" | "shuffle_magnitude":
            st.session_state[SHUFFLE_KEY] = value
            st.session_state[Y_KEY] = y_from_shuffle_magnitude(
                value,
                upper_branch=branch == "upper",
            )
        case "a_A":
            st.session_state[A_KEY] = value
        case "b_A":
            st.session_state[B_KEY] = value
        case "c_A":
            st.session_state[C_KEY] = value
        case "energy_keV":
            st.session_state[MODE_KEY] = "Custom energy"
            st.session_state[ENERGY_KEY] = value
            install_custom_radiation_template("Custom energy", radiation_lines)
        case "wavelength_A":
            st.session_state[MODE_KEY] = "Custom wavelength"
            st.session_state[WAVELENGTH_KEY] = value
            install_custom_radiation_template("Custom wavelength", radiation_lines)
        case unreachable:
            assert_never(unreachable)
