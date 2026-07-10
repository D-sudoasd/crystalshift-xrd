from __future__ import annotations

import math
from dataclasses import replace

import numpy as np

from orthoxrd.batch_models import (
    BatchPeak,
    ShuffleBranch,
    StepResult,
    SweepAxis,
    SweepConfig,
    SweepResult,
    SweepStep,
    TrajectoryConfig,
    TrajectoryIssue,
    TrajectoryValidationError,
)
from orthoxrd.config import SimulationConfig
from orthoxrd.models import LatticeParameters, RadiationLine, Reflection
from orthoxrd.powder import (
    calculate_reflections,
    energy_kev_to_wavelength_a,
)
from orthoxrd.profiles import calculate_spectrum_arrays
from orthoxrd.structure_factor import signed_shuffle_from_y, y_from_shuffle_magnitude
from orthoxrd.sweep_limits import MAX_PEAK_ROWS, validate_sweep_preflight
from orthoxrd.trajectory import parse_trajectory_csv

_AXIS_LIMITS: dict[SweepAxis, tuple[float, float]] = {
    "y": (0.0, 0.5),
    "shuffle": (0.0, 0.5),
    "shuffle_magnitude": (0.0, 0.5),
    "a_A": (1.0, 20.0),
    "b_A": (1.0, 20.0),
    "c_A": (1.0, 20.0),
    "energy_keV": (1.0, 200.0),
    "wavelength_A": (0.05, 5.0),
}


def generate_sweep(config: SweepConfig | TrajectoryConfig) -> SweepResult:
    match config:
        case SweepConfig():
            steps = _build_range_steps(config)
            base = config.base_config()
        case TrajectoryConfig():
            steps = config.steps
            base = config.base
        case unreachable:
            raise AssertionError(f"unreachable sweep config: {unreachable}")
    validate_sweep_preflight(steps, base)
    step_results = tuple(_calculate_step(base, step) for step in steps)
    peak_count = sum(len(step.peaks) for step in step_results)
    if peak_count > MAX_PEAK_ROWS:
        raise ValueError("sweep exceeds the 1,000,000 peak-row limit")
    peak_max = max(
        (peak.reflection.intensity_model for result in step_results for peak in result.peaks),
        default=0.0,
    )
    spectrum_max = max(
        (float(np.max(result.intensity_model, initial=0.0)) for result in step_results),
        default=0.0,
    )
    return SweepResult(
        config=config,
        steps=step_results,
        peak_global_max=peak_max,
        spectrum_global_max=spectrum_max,
    )


def _build_range_steps(config: SweepConfig) -> tuple[SweepStep, ...]:
    _validate_range(config)
    if config.sweep_step <= 0:
        raise ValueError("sweep step must be positive")
    if config.sweep_stop < config.sweep_start:
        raise ValueError("sweep stop must be greater than or equal to start")
    values: list[float] = []
    current = config.sweep_start
    tolerance = config.sweep_step * 1e-9
    while current <= config.sweep_stop + tolerance:
        values.append(round(current, 12))
        if len(values) > config.max_steps:
            raise ValueError("sweep has too many steps")
        current += config.sweep_step
    return tuple(_range_step(config, index, value) for index, value in enumerate(values))


def _validate_range(config: SweepConfig) -> None:
    values = (config.sweep_start, config.sweep_stop, config.sweep_step)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("sweep start, stop, and step must be finite")
    minimum, maximum = _AXIS_LIMITS[config.sweep_axis]
    if not minimum <= config.sweep_start <= maximum:
        raise ValueError(f"sweep start for {config.sweep_axis} must be within {minimum}-{maximum}")
    if not minimum <= config.sweep_stop <= maximum:
        raise ValueError(f"sweep stop for {config.sweep_axis} must be within {minimum}-{maximum}")


def _range_step(config: SweepConfig, index: int, value: float) -> SweepStep:
    lattice = config.lattice
    y_value = config.base_y
    lines = config.lines
    match config.sweep_axis:
        case "y":
            y_value = value
        case "shuffle" | "shuffle_magnitude":
            y_value = y_from_shuffle_magnitude(
                value,
                upper_branch=config.shuffle_branch == "upper",
            )
        case "a_A":
            lattice = LatticeParameters(value, lattice.b, lattice.c)
        case "b_A":
            lattice = LatticeParameters(lattice.a, value, lattice.c)
        case "c_A":
            lattice = LatticeParameters(lattice.a, lattice.b, value)
        case "energy_keV":
            lines = (RadiationLine(f"{value:g} keV", energy_kev_to_wavelength_a(value), 1.0),)
        case "wavelength_A":
            lines = (RadiationLine(f"{value:g} A", value, 1.0),)
        case unreachable:
            raise AssertionError(f"unreachable sweep axis: {unreachable}")
    shuffle_signed = signed_shuffle_from_y(y_value)
    return SweepStep(
        index=index,
        step_id=f"step_{index:04d}",
        label=f"{config.sweep_axis}={value:.8g}",
        axis=config.sweep_axis,
        axis_value=value,
        lattice=lattice,
        y=y_value,
        shuffle_signed=shuffle_signed,
        shuffle_magnitude=abs(shuffle_signed),
        lines=lines,
    )


def _calculate_step(base: SimulationConfig, step: SweepStep) -> StepResult:
    peaks = _calculate_peaks(base, step)
    model_reflections = tuple(
        replace(peak.reflection, intensity_scaled=peak.reflection.intensity_model) for peak in peaks
    )
    arrays = calculate_spectrum_arrays(
        model_reflections,
        two_theta_min=base.two_theta_min,
        two_theta_max=base.two_theta_max,
        points=base.spectrum_points,
        fwhm_deg=base.fwhm_deg,
        profile_kind=base.profile_kind,
        pseudo_voigt_eta=base.pseudo_voigt_eta,
    )
    return StepResult(
        step=step,
        peaks=peaks,
        two_theta_deg=arrays.two_theta_deg,
        intensity_model=arrays.intensity_model,
        intensity_rel_local=arrays.intensity_rel_local,
    )


def _calculate_peaks(
    base: SimulationConfig,
    step: SweepStep,
) -> tuple[BatchPeak, ...]:
    weighted: list[tuple[int, RadiationLine, Reflection, float]] = []
    for line_index, line in enumerate(step.lines):
        reflections = calculate_reflections(
            lattice=step.lattice,
            y=step.y,
            wavelength_a=line.wavelength_a,
            two_theta_min=base.two_theta_min,
            two_theta_max=base.two_theta_max,
            hkl_max=base.hkl_max,
            scattering_mode=base.scattering_mode,
            composition=base.composition,
            include_lorentz_polarization=base.include_lorentz_polarization,
            include_multiplicity=base.include_multiplicity,
            include_cell_volume=base.include_cell_volume,
        )
        for reflection in reflections:
            weighted.append(
                (line_index, line, reflection, reflection.intensity_model * line.weight)
            )
    maximum = max((item[3] for item in weighted), default=0.0)
    peaks = tuple(
        BatchPeak(
            step=step,
            line_id=f"line_{line_index:02d}",
            line_label=line.label,
            wavelength_a=line.wavelength_a,
            line_weight=line.weight,
            reflection=_weighted_reflection(reflection, intensity, maximum),
        )
        for line_index, line, reflection, intensity in weighted
    )
    return tuple(sorted(peaks, key=lambda peak: peak.reflection.two_theta_deg))


def _weighted_reflection(
    reflection: Reflection,
    intensity: float,
    maximum: float,
) -> Reflection:
    scaled = intensity / maximum * 100.0 if maximum > 0 else 0.0
    return replace(
        reflection,
        intensity_raw=intensity,
        intensity_scaled=scaled,
    )


__all__ = [
    "BatchPeak",
    "ShuffleBranch",
    "StepResult",
    "SweepAxis",
    "SweepConfig",
    "SweepResult",
    "SweepStep",
    "TrajectoryConfig",
    "TrajectoryIssue",
    "TrajectoryValidationError",
    "generate_sweep",
    "parse_trajectory_csv",
]
