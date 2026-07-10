from __future__ import annotations

from typing import Final, assert_never

import streamlit as st

from orthoxrd.batch_models import ShuffleBranch, SweepAxis
from orthoxrd.live import LivePreviewConfig, current_axis_value
from orthoxrd.simulation import SimulationResult

LIVE_AXIS_LABELS: Final[dict[str, SweepAxis]] = {
    "Shuffle magnitude": "shuffle_magnitude",
    "Wyckoff y": "y",
    "Lattice a": "a_A",
    "Lattice b": "b_A",
    "Lattice c": "c_A",
    "Energy": "energy_keV",
    "Wavelength": "wavelength_A",
}
_AXIS_LIMITS: Final[dict[SweepAxis, tuple[float, float]]] = {
    "y": (0.0, 0.5),
    "shuffle": (0.0, 0.5),
    "shuffle_magnitude": (0.0, 0.5),
    "a_A": (1.0, 20.0),
    "b_A": (1.0, 20.0),
    "c_A": (1.0, 20.0),
    "energy_keV": (1.0, 200.0),
    "wavelength_A": (0.05, 5.0),
}


def render_live_controls(current: SimulationResult) -> LivePreviewConfig:
    control, range_col = st.columns((0.9, 2.1), gap="large")
    with control:
        label = st.selectbox("Live parameter", list(LIVE_AXIS_LABELS), key="live_axis")
        axis = LIVE_AXIS_LABELS[label]
        branch: ShuffleBranch = "lower"
        if axis == "shuffle_magnitude":
            selected = st.segmented_control(
                "Shuffle branch",
                ["Lower", "Upper"],
                default="Lower",
                key="live_shuffle_branch",
            )
            branch = "upper" if selected == "Upper" else "lower"
    defaults = _ensure_range(current, axis)
    minimum, maximum = _AXIS_LIMITS[axis]
    with range_col:
        start_col, stop_col, step_col, points_col = st.columns(4)
        with start_col:
            start_raw = st.number_input(
                "Live start",
                min_value=minimum,
                max_value=maximum,
                value=None,
                format="%.7g",
                key=f"live_start_{axis}",
            )
            assert start_raw is not None
            start = float(start_raw)
        with stop_col:
            stop_raw = st.number_input(
                "Live stop",
                min_value=minimum,
                max_value=maximum,
                value=None,
                format="%.7g",
                key=f"live_stop_{axis}",
            )
            assert stop_raw is not None
            stop = float(stop_raw)
        with step_col:
            step_raw = st.number_input(
                "Live step",
                min_value=max(defaults[2] / 100.0, 1e-8),
                max_value=max(maximum - minimum, defaults[2]),
                value=None,
                format="%.7g",
                key=f"live_step_{axis}",
            )
            assert step_raw is not None
            step = float(step_raw)
        with points_col:
            st.session_state.setdefault(
                "live_preview_points", min(current.config.spectrum_points, 1600)
            )
            points_raw = st.number_input(
                "Preview points",
                min_value=400,
                max_value=2000,
                value=None,
                step=200,
                key="live_preview_points",
            )
            assert points_raw is not None
            points = int(points_raw)
    st.caption(
        "The slider switches precomputed exact frames locally. Python receives only "
        "the final frame when the slider is released."
    )
    return LivePreviewConfig(
        base=current.config,
        axis=axis,
        start=start,
        stop=stop,
        step=step,
        preview_points=points,
        shuffle_branch=branch,
    )


def _ensure_range(
    current: SimulationResult,
    axis: SweepAxis,
) -> tuple[float, float, float]:
    value = current_axis_value(current.config, axis)
    defaults = _defaults(value, axis)
    start_key = f"live_start_{axis}"
    stop_key = f"live_stop_{axis}"
    step_key = f"live_step_{axis}"
    st.session_state.setdefault(start_key, defaults[0])
    st.session_state.setdefault(stop_key, defaults[1])
    st.session_state.setdefault(step_key, defaults[2])
    start = float(st.session_state[start_key])
    stop = float(st.session_state[stop_key])
    if not start <= value <= stop:
        st.session_state[start_key] = min(start, value)
        st.session_state[stop_key] = max(stop, value)
    return defaults


def _defaults(value: float, axis: SweepAxis) -> tuple[float, float, float]:
    match axis:
        case "y":
            return min(0.167, value), max(0.25, value), 0.001
        case "shuffle" | "shuffle_magnitude":
            return 0.0, max(0.166, value), 0.001
        case "a_A" | "b_A" | "c_A":
            return max(1.0, value * 0.98), min(20.0, value * 1.02), 0.001
        case "energy_keV":
            return max(1.0, value - 5.0), min(200.0, value + 5.0), 0.1
        case "wavelength_A":
            return max(0.05, value - 0.05), min(5.0, value + 0.05), 0.001
        case unreachable:
            assert_never(unreachable)
