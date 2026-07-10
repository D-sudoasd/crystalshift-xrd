from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import streamlit as st

from orthoxrd.batch_models import SweepResult
from orthoxrd.config import config_hash


@dataclass(frozen=True, slots=True)
class SweepDisplayRange:
    two_theta_minimum: float
    two_theta_maximum: float
    axis_minimum: float
    axis_maximum: float


def sweep_display_key(result: SweepResult) -> str:
    first = result.steps[0]
    payload = {
        "config_hash": config_hash(result.base_config),
        "axis": first.step.axis,
        "axis_values": [step.step.axis_value for step in result.steps],
        "two_theta_start": float(first.two_theta_deg[0]),
        "two_theta_stop": float(first.two_theta_deg[-1]),
        "spectrum_points": len(first.two_theta_deg),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]

def render_sweep_display_range(result: SweepResult) -> SweepDisplayRange:
    theta_defaults = (
        float(result.steps[0].two_theta_deg[0]),
        float(result.steps[0].two_theta_deg[-1]),
    )
    axis_values = [step.step.axis_value for step in result.steps]
    axis_defaults = (min(axis_values), max(axis_values))
    if axis_defaults[0] == axis_defaults[1]:
        axis_defaults = (axis_defaults[0] - 0.5, axis_defaults[1] + 0.5)
    namespace = sweep_display_key(result)
    keys = {
        "theta_min": f"sweep_display_theta_min_{namespace}",
        "theta_max": f"sweep_display_theta_max_{namespace}",
        "axis_min": f"sweep_display_axis_min_{namespace}",
        "axis_max": f"sweep_display_axis_max_{namespace}",
    }
    st.session_state.setdefault(keys["theta_min"], theta_defaults[0])
    st.session_state.setdefault(keys["theta_max"], theta_defaults[1])
    st.session_state.setdefault(keys["axis_min"], axis_defaults[0])
    st.session_state.setdefault(keys["axis_max"], axis_defaults[1])
    with st.popover("Sweep display range", use_container_width=True):
        st.caption("Display-only crop. The ZIP always contains the complete simulation window.")
        theta_left, theta_right = st.columns(2)
        with theta_left:
            theta_minimum = float(
                st.number_input(
                    "Sweep 2theta minimum",
                    format="%.7g",
                    key=keys["theta_min"],
                )
            )
        with theta_right:
            theta_maximum = float(
                st.number_input(
                    "Sweep 2theta maximum",
                    format="%.7g",
                    key=keys["theta_max"],
                )
            )
        axis_left, axis_right = st.columns(2)
        with axis_left:
            axis_minimum = float(
                st.number_input(
                    "Sweep axis minimum",
                    format="%.7g",
                    key=keys["axis_min"],
                )
            )
        with axis_right:
            axis_maximum = float(
                st.number_input(
                    "Sweep axis maximum",
                    format="%.7g",
                    key=keys["axis_max"],
                )
            )
        st.button(
            "Reset sweep display range",
            use_container_width=True,
            on_click=_reset,
            args=(keys, theta_defaults, axis_defaults),
        )
    if theta_maximum <= theta_minimum:
        st.error("Sweep 2theta maximum must be greater than the minimum.")
        theta_minimum, theta_maximum = theta_defaults
    if axis_maximum <= axis_minimum:
        st.error("Sweep axis maximum must be greater than the minimum.")
        axis_minimum, axis_maximum = axis_defaults
    return SweepDisplayRange(
        theta_minimum,
        theta_maximum,
        axis_minimum,
        axis_maximum,
    )


def _reset(
    keys: dict[str, str],
    theta_bounds: tuple[float, float],
    axis_bounds: tuple[float, float],
) -> None:
    st.session_state[keys["theta_min"]] = theta_bounds[0]
    st.session_state[keys["theta_max"]] = theta_bounds[1]
    st.session_state[keys["axis_min"]] = axis_bounds[0]
    st.session_state[keys["axis_max"]] = axis_bounds[1]
