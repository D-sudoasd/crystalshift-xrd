from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Final, assert_never

import numpy as np
from numpy.typing import NDArray

from orthoxrd.batch_models import ShuffleBranch, SweepAxis
from orthoxrd.config import SimulationConfig, config_hash
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.powder import energy_kev_to_wavelength_a, wavelength_a_to_energy_kev
from orthoxrd.simulation import SimulationResult, calculate_simulation
from orthoxrd.structure_factor import y_from_shuffle_magnitude

MAX_LIVE_FRAMES: Final = 401
MAX_LIVE_POINTS: Final = 2_000
MAX_LIVE_CELLS: Final = 800_000
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


class LivePreviewError(ValueError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class LivePreviewConfig:
    base: SimulationConfig
    axis: SweepAxis
    start: float
    stop: float
    step: float
    preview_points: int = 1_600
    shuffle_branch: ShuffleBranch = "lower"


@dataclass(frozen=True, slots=True)
class LivePeakMarker:
    hkl: str
    two_theta_deg: float
    intensity_rel_local: float


@dataclass(frozen=True, slots=True)
class LivePreviewResult:
    config: LivePreviewConfig
    axis_values: NDArray[np.float64]
    two_theta_deg: NDArray[np.float64]
    wavelengths_a: NDArray[np.float64]
    intensity_model: NDArray[np.float64]
    local_maxima: NDArray[np.float64]
    global_maximum: float
    baseline_index: int
    markers: tuple[tuple[LivePeakMarker, ...], ...]
    signature: str


def generate_live_preview(config: LivePreviewConfig) -> LivePreviewResult:
    values, baseline_index = _axis_values(config)
    _validate_size(config, len(values))
    rows: list[NDArray[np.float64]] = []
    wavelengths: list[float] = []
    markers: list[tuple[LivePeakMarker, ...]] = []
    grid: NDArray[np.float64] | None = None
    for value in values:
        frame = calculate_simulation(config_for_live_value(config, value))
        if grid is None:
            grid = frame.spectrum.two_theta_deg.copy()
        elif not np.array_equal(grid, frame.spectrum.two_theta_deg):
            raise LivePreviewError("live frames must share one two-theta grid")
        rows.append(frame.spectrum.intensity_model.copy())
        wavelengths.append(frame.config.lines[0].wavelength_a)
        markers.append(_markers(frame))
    if grid is None:
        raise LivePreviewError("live preview requires at least one frame")
    matrix = np.vstack(rows, dtype=np.float64)
    local_maxima = np.max(matrix, axis=1, initial=0.0)
    return LivePreviewResult(
        config=config,
        axis_values=_readonly_array(values),
        two_theta_deg=_readonly_array(grid),
        wavelengths_a=_readonly_array(wavelengths),
        intensity_model=_readonly_array(matrix),
        local_maxima=_readonly_array(local_maxima),
        global_maximum=float(np.max(matrix, initial=0.0)),
        baseline_index=baseline_index,
        markers=tuple(markers),
        signature=live_signature(config),
    )


def config_for_live_value(config: LivePreviewConfig, value: float) -> SimulationConfig:
    base = replace(config.base, spectrum_points=config.preview_points)
    match config.axis:
        case "y":
            return replace(base, y=value)
        case "shuffle" | "shuffle_magnitude":
            return replace(
                base,
                y=y_from_shuffle_magnitude(
                    value,
                    upper_branch=config.shuffle_branch == "upper",
                ),
            )
        case "a_A":
            lattice = LatticeParameters(value, base.lattice.b, base.lattice.c)
            return replace(base, lattice=lattice)
        case "b_A":
            lattice = LatticeParameters(base.lattice.a, value, base.lattice.c)
            return replace(base, lattice=lattice)
        case "c_A":
            lattice = LatticeParameters(base.lattice.a, base.lattice.b, value)
            return replace(base, lattice=lattice)
        case "energy_keV":
            wavelength = energy_kev_to_wavelength_a(value)
            return replace(base, lines=_scaled_radiation_lines(base.lines, wavelength))
        case "wavelength_A":
            return replace(base, lines=_scaled_radiation_lines(base.lines, value))
        case unreachable:
            assert_never(unreachable)


def current_axis_value(config: SimulationConfig, axis: SweepAxis) -> float:
    match axis:
        case "y":
            return config.y
        case "shuffle" | "shuffle_magnitude":
            return abs(2.0 * (config.y - 0.25))
        case "a_A":
            return config.lattice.a
        case "b_A":
            return config.lattice.b
        case "c_A":
            return config.lattice.c
        case "energy_keV":
            return wavelength_a_to_energy_kev(config.lines[0].wavelength_a)
        case "wavelength_A":
            return config.lines[0].wavelength_a
        case unreachable:
            assert_never(unreachable)


def live_signature(config: LivePreviewConfig) -> str:
    anchor = _signature_anchor(config)
    payload = {
        "base": config_hash(anchor),
        "axis": config.axis,
        "start": config.start,
        "stop": config.stop,
        "step": config.step,
        "preview_points": config.preview_points,
        "shuffle_branch": config.shuffle_branch,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _axis_values(config: LivePreviewConfig) -> tuple[tuple[float, ...], int]:
    _validate_range(config)
    values: list[float] = []
    current = config.start
    tolerance = config.step * 1e-9
    while current <= config.stop + tolerance:
        values.append(round(current, 12))
        if len(values) > MAX_LIVE_FRAMES:
            raise LivePreviewError("live preview exceeds the 401-frame limit")
        current += config.step
    baseline = current_axis_value(config.base, config.axis)
    if not config.start <= baseline <= config.stop:
        raise LivePreviewError("current baseline must fall inside the live preview range")
    if not any(math.isclose(value, baseline, rel_tol=0.0, abs_tol=1e-12) for value in values):
        values.append(baseline)
        values.sort()
    if len(values) > MAX_LIVE_FRAMES:
        raise LivePreviewError("live preview exceeds the 401-frame limit")
    baseline_index = min(range(len(values)), key=lambda index: abs(values[index] - baseline))
    return tuple(values), baseline_index


def _validate_range(config: LivePreviewConfig) -> None:
    if not all(math.isfinite(value) for value in (config.start, config.stop, config.step)):
        raise LivePreviewError("live start, stop, and step must be finite")
    if config.step <= 0:
        raise LivePreviewError("live step must be positive")
    if config.stop < config.start:
        raise LivePreviewError("live stop must be greater than or equal to start")
    minimum, maximum = _AXIS_LIMITS[config.axis]
    if not minimum <= config.start <= maximum or not minimum <= config.stop <= maximum:
        raise LivePreviewError(
            f"live range for {config.axis} must stay within {minimum:g}-{maximum:g}"
        )


def _validate_size(config: LivePreviewConfig, frames: int) -> None:
    if not 2 <= config.preview_points <= MAX_LIVE_POINTS:
        raise LivePreviewError("live preview points must be within 2-2000")
    if frames * config.preview_points > MAX_LIVE_CELLS:
        raise LivePreviewError("live preview exceeds the 800,000-cell limit")


def _signature_anchor(config: LivePreviewConfig) -> SimulationConfig:
    base = replace(config.base, spectrum_points=config.preview_points)
    match config.axis:
        case "y" | "shuffle" | "shuffle_magnitude":
            return replace(base, y=0.25)
        case "a_A":
            return replace(base, lattice=LatticeParameters(1.0, base.lattice.b, base.lattice.c))
        case "b_A":
            return replace(base, lattice=LatticeParameters(base.lattice.a, 1.0, base.lattice.c))
        case "c_A":
            return replace(base, lattice=LatticeParameters(base.lattice.a, base.lattice.b, 1.0))
        case "energy_keV" | "wavelength_A":
            primary = base.lines[0].wavelength_a
            normalized = tuple(
                RadiationLine(
                    f"line_{index:02d}",
                    line.wavelength_a / primary,
                    line.weight,
                )
                for index, line in enumerate(base.lines)
            )
            return replace(base, lines=normalized)
        case unreachable:
            assert_never(unreachable)


def _scaled_radiation_lines(
    lines: tuple[RadiationLine, ...],
    primary_wavelength_a: float,
) -> tuple[RadiationLine, ...]:
    scale = primary_wavelength_a / lines[0].wavelength_a
    return tuple(
        RadiationLine(line.label, line.wavelength_a * scale, line.weight)
        for line in lines
    )


def _markers(frame: SimulationResult) -> tuple[LivePeakMarker, ...]:
    strongest = sorted(
        frame.peaks,
        key=lambda peak: peak.reflection.intensity_scaled,
        reverse=True,
    )[:8]
    return tuple(
        LivePeakMarker(
            hkl=peak.reflection.hkl_label,
            two_theta_deg=peak.reflection.two_theta_deg,
            intensity_rel_local=peak.reflection.intensity_scaled,
        )
        for peak in strongest
        if peak.reflection.intensity_scaled > 0
    )


def _readonly_array(
    values: Sequence[float] | NDArray[np.float64],
) -> NDArray[np.float64]:
    array = np.asarray(values, dtype=np.float64)
    array.setflags(write=False)
    return array
