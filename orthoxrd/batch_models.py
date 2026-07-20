from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from orthoxrd.config import SimulationConfig
from orthoxrd.models import (
    ElementFraction,
    LatticeParameters,
    ProfileKind,
    RadiationLine,
    Reflection,
    ScatteringMode,
    SpectrumPoint,
)

SweepAxis = Literal[
    "y",
    "shuffle",
    "shuffle_magnitude",
    "a_A",
    "b_A",
    "c_A",
    "energy_keV",
    "wavelength_A",
]
ShuffleBranch = Literal["lower", "upper"]


@dataclass(frozen=True, slots=True)
class SweepConfig:
    lattice: LatticeParameters
    lines: tuple[RadiationLine, ...]
    scattering_mode: ScatteringMode
    composition: tuple[ElementFraction, ...]
    two_theta_min: float
    two_theta_max: float
    hkl_max: int
    include_lorentz_polarization: bool
    include_multiplicity: bool
    include_cell_volume: bool
    profile_kind: ProfileKind
    fwhm_deg: float
    pseudo_voigt_eta: float
    spectrum_points: int
    sweep_axis: SweepAxis
    sweep_start: float
    sweep_stop: float
    sweep_step: float
    base_y: float = 0.25
    min_peak: float = 0.0
    shuffle_branch: ShuffleBranch = "lower"
    max_steps: int = 1001

    @classmethod
    def from_simulation(
        cls,
        base: SimulationConfig,
        *,
        axis: SweepAxis,
        start: float,
        stop: float,
        step: float,
        shuffle_branch: ShuffleBranch = "lower",
    ) -> SweepConfig:
        return cls(
            lattice=base.lattice,
            lines=base.lines,
            scattering_mode=base.scattering_mode,
            composition=base.composition,
            two_theta_min=base.two_theta_min,
            two_theta_max=base.two_theta_max,
            hkl_max=base.hkl_max,
            include_lorentz_polarization=base.include_lorentz_polarization,
            include_multiplicity=base.include_multiplicity,
            include_cell_volume=base.include_cell_volume,
            profile_kind=base.profile_kind,
            fwhm_deg=base.fwhm_deg,
            pseudo_voigt_eta=base.pseudo_voigt_eta,
            spectrum_points=base.spectrum_points,
            sweep_axis=axis,
            sweep_start=start,
            sweep_stop=stop,
            sweep_step=step,
            base_y=base.y,
            min_peak=base.min_peak,
            shuffle_branch=shuffle_branch,
        )

    def with_sweep(
        self,
        axis: SweepAxis,
        start: float,
        stop: float,
        step: float,
    ) -> SweepConfig:
        return replace(
            self,
            sweep_axis=axis,
            sweep_start=start,
            sweep_stop=stop,
            sweep_step=step,
        )

    def base_config(self) -> SimulationConfig:
        return SimulationConfig(
            lattice=self.lattice,
            y=self.base_y,
            lines=self.lines,
            scattering_mode=self.scattering_mode,
            composition=self.composition,
            two_theta_min=self.two_theta_min,
            two_theta_max=self.two_theta_max,
            hkl_max=self.hkl_max,
            min_peak=self.min_peak,
            profile_kind=self.profile_kind,
            fwhm_deg=self.fwhm_deg,
            pseudo_voigt_eta=self.pseudo_voigt_eta,
            spectrum_points=self.spectrum_points,
            include_lorentz_polarization=self.include_lorentz_polarization,
            include_multiplicity=self.include_multiplicity,
            include_cell_volume=self.include_cell_volume,
        )


@dataclass(frozen=True, slots=True)
class SweepStep:
    index: int
    step_id: str
    label: str
    axis: str
    axis_value: float
    lattice: LatticeParameters
    y: float
    shuffle_signed: float
    shuffle_magnitude: float
    normalized_shuffle: float
    lines: tuple[RadiationLine, ...]

    @property
    def column_label(self) -> str:
        return self.step_id


@dataclass(frozen=True, slots=True)
class BatchPeak:
    step: SweepStep
    line_id: str
    line_label: str
    wavelength_a: float
    line_weight: float
    reflection: Reflection

    @property
    def series_id(self) -> str:
        return f"{self.line_id}__{self.reflection.hkl_id}"


@dataclass(frozen=True, slots=True)
class StepResult:
    step: SweepStep
    peaks: tuple[BatchPeak, ...]
    two_theta_deg: NDArray[np.float64]
    intensity_model: NDArray[np.float64]
    intensity_rel_local: NDArray[np.float64]

    @property
    def local_spectrum(self) -> tuple[SpectrumPoint, ...]:
        return tuple(
            SpectrumPoint(float(x_value), float(intensity))
            for x_value, intensity in zip(
                self.two_theta_deg,
                self.intensity_rel_local,
                strict=True,
            )
        )

    @property
    def raw_spectrum(self) -> tuple[SpectrumPoint, ...]:
        return tuple(
            SpectrumPoint(float(x_value), float(intensity))
            for x_value, intensity in zip(
                self.two_theta_deg,
                self.intensity_model,
                strict=True,
            )
        )


@dataclass(frozen=True, slots=True)
class TrajectoryConfig:
    base: SimulationConfig
    steps: tuple[SweepStep, ...]
    max_steps: int = 1001


@dataclass(frozen=True, slots=True)
class SweepResult:
    config: SweepConfig | TrajectoryConfig
    steps: tuple[StepResult, ...]
    peak_global_max: float
    spectrum_global_max: float

    @property
    def base_config(self) -> SimulationConfig:
        match self.config:
            case SweepConfig():
                return self.config.base_config()
            case TrajectoryConfig():
                return self.config.base
            case unreachable:
                raise AssertionError(f"unreachable sweep config: {unreachable}")

    def spectrum_matrix(self, kind: Literal["model", "local", "global"]) -> NDArray[np.float64]:
        match kind:
            case "model":
                return np.vstack([step.intensity_model for step in self.steps])
            case "local":
                return np.vstack([step.intensity_rel_local for step in self.steps])
            case "global":
                matrix = np.vstack([step.intensity_model for step in self.steps])
                if self.spectrum_global_max <= 0:
                    return np.zeros_like(matrix)
                return matrix / self.spectrum_global_max * 100.0
            case unreachable:
                raise AssertionError(f"unreachable spectrum matrix kind: {unreachable}")


@dataclass(frozen=True, slots=True)
class TrajectoryIssue:
    row: int
    column: str
    value: str
    message: str


class TrajectoryValidationError(ValueError):
    def __init__(self, issues: tuple[TrajectoryIssue, ...]) -> None:
        self.issues = issues
        super().__init__(str(self))

    def __str__(self) -> str:
        first = self.issues[0]
        return f"trajectory row {first.row}, {first.column}: {first.message}"
