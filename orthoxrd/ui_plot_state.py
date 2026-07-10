from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np
import streamlit as st
from numpy.typing import NDArray

from orthoxrd.simulation import SimulationResult

XAxisKind = Literal["2theta", "q_primary", "d_primary"]


@dataclass(frozen=True, slots=True)
class PlotState:
    x_axis: XAxisKind
    x_minimum: float
    x_maximum: float
    y_auto: bool
    y_minimum: float
    y_maximum: float


def transform_axis(
    two_theta_deg: NDArray[np.float64],
    wavelength_a: float,
    kind: XAxisKind,
) -> NDArray[np.float64]:
    values = np.asarray(two_theta_deg, dtype=np.float64)
    match kind:
        case "2theta":
            return values
        case "q_primary":
            theta = np.deg2rad(values / 2.0)
            return 4.0 * math.pi * np.sin(theta) / wavelength_a
        case "d_primary":
            theta = np.deg2rad(values / 2.0)
            q_values = 4.0 * math.pi * np.sin(theta) / wavelength_a
            return np.divide(
                2.0 * math.pi,
                q_values,
                out=np.full_like(q_values, np.nan),
                where=q_values > 0,
            )


def default_x_bounds(result: SimulationResult, axis: XAxisKind) -> tuple[float, float]:
    values = transform_axis(
        result.spectrum.two_theta_deg,
        result.config.lines[0].wavelength_a,
        axis,
    )
    finite = values[np.isfinite(values)]
    return float(np.min(finite)), float(np.max(finite))


def render_plot_state(result: SimulationResult, axis: XAxisKind) -> PlotState:
    x_default = default_x_bounds(result, axis)
    minimum_key = f"plot_x_min_{axis}"
    maximum_key = f"plot_x_max_{axis}"
    st.session_state.setdefault(minimum_key, x_default[0])
    st.session_state.setdefault(maximum_key, x_default[1])
    with st.popover("Display range", use_container_width=True):
        st.caption("Display-only crop. Simulation and exported rows remain unchanged.")
        left, right = st.columns(2)
        with left:
            x_minimum = float(
                st.number_input(
                    "X minimum",
                    format="%.7g",
                    key=minimum_key,
                )
            )
        with right:
            x_maximum = float(
                st.number_input(
                    "X maximum",
                    format="%.7g",
                    key=maximum_key,
                )
            )
        y_auto = st.toggle("Automatic Y range", value=True, key="plot_y_auto")
        y_minimum = 0.0
        y_maximum = 105.0
        if not y_auto:
            y_left, y_right = st.columns(2)
            with y_left:
                y_minimum = float(
                    st.number_input("Y minimum", value=0.0, format="%.7g", key="plot_y_min")
                )
            with y_right:
                y_maximum = float(
                    st.number_input("Y maximum", value=105.0, format="%.7g", key="plot_y_max")
                )
        st.button(
            "Reset display range",
            key=f"plot_reset_{axis}",
            use_container_width=True,
            on_click=_reset_x_bounds,
            args=(axis, x_default),
        )
    if x_maximum <= x_minimum:
        st.error("X maximum must be greater than X minimum.")
        x_minimum, x_maximum = x_default
    if not y_auto and y_maximum <= y_minimum:
        st.error("Y maximum must be greater than Y minimum.")
        y_minimum, y_maximum = 0.0, 105.0
    return PlotState(axis, x_minimum, x_maximum, y_auto, y_minimum, y_maximum)


def plot_state_from_session(result: SimulationResult) -> PlotState:
    raw_axis = st.session_state.get("pattern_axis", "2theta")
    axis: XAxisKind = (
        raw_axis
        if raw_axis in {"2theta", "q_primary", "d_primary"}
        else "2theta"
    )
    x_default = default_x_bounds(result, axis)
    x_minimum = float(st.session_state.get(f"plot_x_min_{axis}", x_default[0]))
    x_maximum = float(st.session_state.get(f"plot_x_max_{axis}", x_default[1]))
    y_auto = bool(st.session_state.get("plot_y_auto", True))
    y_minimum = float(st.session_state.get("plot_y_min", 0.0))
    y_maximum = float(st.session_state.get("plot_y_max", 105.0))
    if x_maximum <= x_minimum:
        x_minimum, x_maximum = x_default
    if y_maximum <= y_minimum:
        y_minimum, y_maximum = 0.0, 105.0
    return PlotState(axis, x_minimum, x_maximum, y_auto, y_minimum, y_maximum)

def _reset_x_bounds(axis: XAxisKind, bounds: tuple[float, float]) -> None:
    st.session_state[f"plot_x_min_{axis}"] = bounds[0]
    st.session_state[f"plot_x_max_{axis}"] = bounds[1]
