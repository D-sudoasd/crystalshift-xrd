# ruff: noqa: E501

from __future__ import annotations

import base64
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

import numpy as np
from streamlit.components.v2 import component

from orthoxrd.live import LivePreviewResult
from orthoxrd.ui_plot_state import PlotState

_COMPONENT_DIR: Final = Path(__file__).with_name("_live_component")
_COMPONENT_JS: Final = "/* orthoxrd live component */\n" + (
    _COMPONENT_DIR / "live-component.js"
).read_text(encoding="utf-8")
_COMPONENT_HTML: Final = """
<div class="live-shell">
  <div class="live-toolbar">
    <strong data-live-value>live parameter</strong>
    <label>Intensity
      <select data-live-normalisation>
        <option value="global">Global relative</option>
        <option value="local">Local relative</option>
        <option value="model">Model</option>
      </select>
    </label>
    <label class="live-check"><input type="checkbox" data-live-difference> Difference</label>
  </div>
  <canvas data-live-canvas aria-label="Live theoretical XRD pattern"></canvas>
  <input data-live-slider type="range" aria-label="Live parameter frame">
  <div class="live-legend"><span class="baseline">baseline</span><span class="current">current</span><span class="difference">difference</span></div>
</div>
"""
_COMPONENT_CSS: Final = """
:host { display:block; color:#f3f6fa; font-family:system-ui,sans-serif; }
.live-shell { border:1px solid #2a3441; border-radius:8px; background:#121821; padding:12px; }
.live-toolbar { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; font-size:13px; }
.live-toolbar strong { color:#22c7d6; font-family:"Cascadia Mono",Consolas,monospace; }
.live-toolbar label { display:flex; align-items:center; gap:7px; color:#aeb8c5; }
.live-toolbar select { min-height:32px; color:#f3f6fa; background:#18202b; border:1px solid #2a3441; border-radius:5px; }
.live-check input { accent-color:#22c7d6; }
canvas { display:block; width:100%; height:420px; margin-top:8px; }
input[type=range] { width:100%; accent-color:#22c7d6; }
input:disabled, select:disabled { cursor:not-allowed; opacity:.45; }
.live-legend { display:flex; gap:16px; justify-content:flex-end; color:#aeb8c5; font-size:12px; }
.live-legend span::before { content:""; display:inline-block; width:18px; height:2px; margin-right:6px; vertical-align:middle; }
.baseline::before { background:#8a96a6; }.current::before { background:#22c7d6; }.difference::before { background:#f2b84b; }
@media (max-width:520px) { canvas { height:340px; } .live-toolbar { align-items:flex-start; flex-direction:column; } }
"""
_LIVE_COMPONENT: Final = component(
    "orthoxrd_live_pattern",
    html=_COMPONENT_HTML,
    css=_COMPONENT_CSS,
    js=_COMPONENT_JS,
    isolate_styles=True,
)


class MarkerPayload(TypedDict):
    hkl: str
    twoTheta: float
    intensity: float


class LivePayload(TypedDict):
    axisLabel: str
    axisUnit: str
    axisValues: list[float]
    baselineIndex: int
    currentIndex: int
    columns: int
    matrixF32: str
    twoThetaF32: str
    wavelengths: list[float]
    localMaxima: list[float]
    globalMaximum: float
    xAxis: str
    xMinimum: float
    xMaximum: float
    yAuto: bool
    yMinimum: float
    yMaximum: float
    markers: list[list[MarkerPayload]]
    disabled: bool


@dataclass(frozen=True, slots=True)
class LiveSelection:
    frame_index: int
    axis_value: float
    baseline_index: int


def render_live_component(
    result: LivePreviewResult,
    plot_state: PlotState,
    *,
    current_index: int,
    baseline_index: int,
    component_key: str,
    on_selected_index_change: Callable[[], None],
    disabled: bool = False,
) -> LiveSelection:
    payload = _payload(result, plot_state, current_index, baseline_index, disabled)
    component_result = _LIVE_COMPONENT(
        key=component_key,
        data=payload,
        default={"selected_index": current_index},
        on_selected_index_change=on_selected_index_change,
    )
    raw_index = component_result.get("selected_index", current_index)
    selected_index = raw_index if isinstance(raw_index, int) else current_index
    selected_index = max(0, min(selected_index, len(result.axis_values) - 1))
    return LiveSelection(
        frame_index=selected_index,
        axis_value=float(result.axis_values[selected_index]),
        baseline_index=baseline_index,
    )


def _payload(
    result: LivePreviewResult,
    plot_state: PlotState,
    current_index: int,
    baseline_index: int,
    disabled: bool,
) -> LivePayload:
    matrix = np.asarray(result.intensity_model, dtype="<f4")
    two_theta = np.asarray(result.two_theta_deg, dtype="<f4")
    markers: list[list[MarkerPayload]] = [
        [
            {
                "hkl": marker.hkl,
                "twoTheta": marker.two_theta_deg,
                "intensity": marker.intensity_rel_local,
            }
            for marker in frame
        ]
        for frame in result.markers
    ]
    return {
        "axisLabel": result.config.axis,
        "axisUnit": _axis_unit(result.config.axis),
        "axisValues": result.axis_values.tolist(),
        "baselineIndex": baseline_index,
        "currentIndex": current_index,
        "columns": matrix.shape[1],
        "matrixF32": base64.b64encode(matrix.tobytes(order="C")).decode("ascii"),
        "twoThetaF32": base64.b64encode(two_theta.tobytes(order="C")).decode("ascii"),
        "wavelengths": result.wavelengths_a.tolist(),
        "localMaxima": result.local_maxima.tolist(),
        "globalMaximum": result.global_maximum,
        "xAxis": plot_state.x_axis,
        "xMinimum": plot_state.x_minimum,
        "xMaximum": plot_state.x_maximum,
        "yAuto": plot_state.y_auto,
        "yMinimum": plot_state.y_minimum,
        "yMaximum": plot_state.y_maximum,
        "markers": markers,
        "disabled": disabled,
    }


def _axis_unit(axis: str) -> str:
    if axis in {"a_A", "b_A", "c_A", "wavelength_A"}:
        return "A"
    if axis == "energy_keV":
        return "keV"
    return ""
