from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass, replace

import streamlit as st

from orthoxrd.batch_models import ShuffleBranch, SweepAxis, SweepConfig
from orthoxrd.config import SimulationConfig, config_hash
from orthoxrd.powder import wavelength_a_to_energy_kev

AXIS_LABELS: dict[str, SweepAxis] = {
    "Wyckoff y": "y",
    "Shuffle magnitude": "shuffle_magnitude",
    "Lattice a": "a_A",
    "Lattice b": "b_A",
    "Lattice c": "c_A",
    "Energy": "energy_keV",
    "Wavelength": "wavelength_A",
}
TRAJECTORY_TEMPLATE = """
step_label,a_A,b_A,c_A,y,shuffle_magnitude,shuffle_branch,energy_keV,wavelength_A
start,,,,0.167,,lower,,
finish,,,,0.250,,lower,,
"""


@dataclass(frozen=True, slots=True)
class SweepFormState:
    submitted: bool
    mode: str
    signature: str
    range_config: SweepConfig | None
    trajectory_text: str | None
    normalization: str
    base_config: SimulationConfig


def render_sweep_form(base: SimulationConfig, peak_count: int) -> SweepFormState:
    spectrum_points = int(
        st.number_input(
            "Sweep spectrum points",
            min_value=200,
            max_value=10_000,
            value=800,
            step=100,
            key="sweep_spectrum_points",
        )
    )
    run_base = replace(base, spectrum_points=spectrum_points)
    mode = st.segmented_control(
        "Sweep input",
        ["Range sweep", "CSV trajectory"],
        default="Range sweep",
        key="sweep_input_mode",
    )
    normalization = st.selectbox(
        "Heatmap normalization",
        ["Global across sweep", "Local per step", "Model intensity"],
        key="sweep_normalization",
        help="Global normalization preserves amplitude evolution between steps.",
    )
    if normalization == "Local per step":
        st.warning(
            "Local normalization rescales every step independently; "
            "you cannot compare amplitude between steps."
        )
    if mode == "CSV trajectory":
        return _trajectory_form(run_base, normalization)
    return _range_form(run_base, peak_count, normalization)


def _range_form(
    base: SimulationConfig,
    peak_count: int,
    normalization: str,
) -> SweepFormState:
    axis_label = st.selectbox("Sweep axis", list(AXIS_LABELS), key="sweep_axis")
    axis = AXIS_LABELS[axis_label]
    branch: ShuffleBranch = "lower"
    if axis == "shuffle_magnitude":
        selected = st.selectbox(
            "Shuffle branch",
            ["Lower", "Upper"],
            key="sweep_shuffle_branch",
        )
        branch = "upper" if selected == "Upper" else "lower"
        relation = (
            "Lower branch: y = 0.25 - shuffle_magnitude / 2"
            if branch == "lower"
            else "Upper branch: y = 0.25 + shuffle_magnitude / 2"
        )
        st.markdown(f'<div class="xrd-note">{relation}</div>', unsafe_allow_html=True)
    default_start, default_stop, default_step, minimum, maximum = _axis_defaults(base, axis)
    with st.form("range_sweep_form", border=True):
        left, middle, right = st.columns(3)
        with left:
            start = float(
                st.number_input(
                    "Sweep start",
                    min_value=minimum,
                    max_value=maximum,
                    value=default_start,
                    step=default_step,
                    format="%.6g",
                    key=f"sweep_start_{axis}",
                )
            )
        with middle:
            stop = float(
                st.number_input(
                    "Sweep stop",
                    min_value=minimum,
                    max_value=maximum,
                    value=default_stop,
                    step=default_step,
                    format="%.6g",
                    key=f"sweep_stop_{axis}",
                )
            )
        with right:
            step = float(
                st.number_input(
                    "Sweep step",
                    min_value=max(default_step / 100.0, 1e-8),
                    max_value=max(maximum - minimum, default_step),
                    value=default_step,
                    step=default_step,
                    format="%.6g",
                    key=f"sweep_step_{axis}",
                )
            )
        submitted = st.form_submit_button(
            "Run sweep",
            type="primary",
            use_container_width=True,
        )
    count = _step_count(start, stop, step)
    st.caption(
        f"Estimate: {count:,} steps | {count * base.spectrum_points:,} spectrum cells | "
        f"up to {count * peak_count:,} peak rows."
    )
    config = SweepConfig.from_simulation(
        base,
        axis=axis,
        start=start,
        stop=stop,
        step=step,
        shuffle_branch=branch,
    )
    payload = {
        "base": config_hash(base),
        "axis": axis,
        "start": start,
        "stop": stop,
        "step": step,
        "branch": branch,
    }
    return SweepFormState(
        submitted=submitted,
        mode="range",
        signature=_signature(payload),
        range_config=config,
        trajectory_text=None,
        normalization=normalization,
        base_config=base,
    )


def _trajectory_form(base: SimulationConfig, normalization: str) -> SweepFormState:
    with st.form("trajectory_sweep_form", border=True):
        upload = st.file_uploader(
            "Trajectory CSV",
            type=["csv"],
            key="sweep_trajectory_file",
            help="Blank cells inherit the active configuration. Rows are never expanded.",
        )
        submitted = st.form_submit_button(
            "Run sweep",
            type="primary",
            use_container_width=True,
        )
    st.download_button(
        "Trajectory template CSV",
        TRAJECTORY_TEMPLATE,
        "trajectory_template.csv",
        "text/csv",
        key="trajectory_template",
    )
    st.caption(
        "Columns: step_label, a_A, b_A, c_A, y, shuffle_magnitude, "
        "shuffle_branch, energy_keV, wavelength_A. Limit: 1-1001 rows."
    )
    raw = upload.getvalue() if upload is not None else b""
    text = raw.decode("utf-8-sig") if raw else None
    payload = {
        "base": config_hash(base),
        "trajectory_sha256": hashlib.sha256(raw).hexdigest() if raw else "",
    }
    return SweepFormState(
        submitted=submitted,
        mode="trajectory",
        signature=_signature(payload),
        range_config=None,
        trajectory_text=text,
        normalization=normalization,
        base_config=base,
    )


def _axis_defaults(
    base: SimulationConfig,
    axis: SweepAxis,
) -> tuple[float, float, float, float, float]:
    if axis == "y":
        return 0.167, 0.25, 0.001, 0.0, 0.5
    if axis in {"shuffle", "shuffle_magnitude"}:
        return 0.0, 0.166, 0.001, 0.0, 0.5
    if axis in {"a_A", "b_A", "c_A"}:
        value = {
            "a_A": base.lattice.a,
            "b_A": base.lattice.b,
            "c_A": base.lattice.c,
        }[axis]
        return max(1.0, value * 0.98), min(20.0, value * 1.02), 0.001, 1.0, 20.0
    if axis == "energy_keV":
        energy = wavelength_a_to_energy_kev(base.lines[0].wavelength_a)
        return max(1.0, energy - 5.0), min(200.0, energy + 5.0), 0.5, 1.0, 200.0
    wavelength = base.lines[0].wavelength_a
    return max(0.05, wavelength - 0.05), min(5.0, wavelength + 0.05), 0.005, 0.05, 5.0


def _step_count(start: float, stop: float, step: float) -> int:
    if step <= 0 or stop < start:
        return 0
    return math.floor((stop - start) / step + 1e-9) + 1


def _signature(payload: Mapping[str, str | float]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
