from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import TypedDict

from orthoxrd.models import (
    ElementFraction,
    LatticeParameters,
    ProfileKind,
    RadiationLine,
    ScatteringMode,
)
from orthoxrd.structure_factor import validate_y


class LatticePayload(TypedDict):
    a_A: float
    b_A: float
    c_A: float


class RadiationPayload(TypedDict):
    label: str
    wavelength_A: float
    weight: float


class CompositionPayload(TypedDict):
    symbol: str
    fraction: float


class SimulationPayload(TypedDict):
    composition: list[CompositionPayload]
    corrections: dict[str, bool]
    hkl_max: int
    lattice: LatticePayload
    min_peak_percent: float
    profile: dict[str, float | str]
    radiation: list[RadiationPayload]
    scattering_mode: ScatteringMode
    spectrum_points: int
    two_theta_deg: dict[str, float]
    wyckoff_y: float


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    lattice: LatticeParameters
    y: float
    lines: tuple[RadiationLine, ...]
    scattering_mode: ScatteringMode
    composition: tuple[ElementFraction, ...]
    two_theta_min: float
    two_theta_max: float
    hkl_max: int
    min_peak: float
    profile_kind: ProfileKind
    fwhm_deg: float
    pseudo_voigt_eta: float
    spectrum_points: int
    include_lorentz_polarization: bool
    include_multiplicity: bool
    include_cell_volume: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("a", self.lattice.a),
            ("b", self.lattice.b),
            ("c", self.lattice.c),
        ):
            if not 1.0 <= value <= 20.0:
                raise ValueError(f"{name} must be within 1-20 A")
        validate_y(self.y)
        if not self.lines:
            raise ValueError("at least one radiation line is required")
        if self.two_theta_min < 0 or self.two_theta_max <= self.two_theta_min:
            raise ValueError("two-theta range is invalid")
        if self.hkl_max < 1:
            raise ValueError("hkl_max must be at least 1")
        if not math.isfinite(self.min_peak) or self.min_peak < 0:
            raise ValueError("minimum peak intensity must be non-negative")
        if not math.isfinite(self.fwhm_deg) or self.fwhm_deg <= 0:
            raise ValueError("FWHM must be positive")
        if not 0 <= self.pseudo_voigt_eta <= 1:
            raise ValueError("pseudo-Voigt eta must be between 0 and 1")
        if self.spectrum_points < 2 or self.spectrum_points > 10_000:
            raise ValueError("spectrum points must be between 2 and 10000")


def config_payload(config: SimulationConfig) -> SimulationPayload:
    return {
        "composition": [
            {"symbol": item.symbol, "fraction": item.fraction} for item in config.composition
        ],
        "corrections": {
            "cell_volume_1_over_V": config.include_cell_volume,
            "lorentz_polarization": config.include_lorentz_polarization,
            "multiplicity": config.include_multiplicity,
        },
        "hkl_max": config.hkl_max,
        "lattice": {
            "a_A": config.lattice.a,
            "b_A": config.lattice.b,
            "c_A": config.lattice.c,
        },
        "min_peak_percent": config.min_peak,
        "profile": {
            "fwhm_deg": config.fwhm_deg,
            "kind": config.profile_kind,
            "pseudo_voigt_eta": config.pseudo_voigt_eta,
        },
        "radiation": [
            {
                "label": line.label,
                "wavelength_A": line.wavelength_a,
                "weight": line.weight,
            }
            for line in config.lines
        ],
        "scattering_mode": config.scattering_mode,
        "spectrum_points": config.spectrum_points,
        "two_theta_deg": {"min": config.two_theta_min, "max": config.two_theta_max},
        "wyckoff_y": config.y,
    }


def config_json(config: SimulationConfig) -> str:
    return json.dumps(
        config_payload(config),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )


def config_hash(config: SimulationConfig) -> str:
    return hashlib.sha256(config_json(config).encode("utf-8")).hexdigest()
