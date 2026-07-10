from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

ProfileKind = Literal["gaussian", "lorentzian", "pseudo_voigt"]
ScatteringMode = Literal["unit", "composition"]


def _require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive")


@dataclass(frozen=True, slots=True)
class LatticeParameters:
    a: float
    b: float
    c: float

    def __post_init__(self) -> None:
        _require_positive("a", self.a)
        _require_positive("b", self.b)
        _require_positive("c", self.c)

    @property
    def volume_a3(self) -> float:
        return self.a * self.b * self.c


@dataclass(frozen=True, slots=True)
class ElementFraction:
    symbol: str
    fraction: float

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol[0].isalpha():
            raise ValueError("element symbol is invalid")
        _require_positive(f"fraction for {self.symbol}", self.fraction)


@dataclass(frozen=True, slots=True)
class RadiationLine:
    label: str
    wavelength_a: float
    weight: float

    def __post_init__(self) -> None:
        _require_positive("wavelength", self.wavelength_a)
        _require_positive("line weight", self.weight)


@dataclass(frozen=True, slots=True)
class Reflection:
    h: int
    k: int
    l: int
    d_spacing_a: float
    two_theta_deg: float
    q_a_inv: float
    multiplicity: int
    structure_factor_squared: float
    lorentz_polarization: float
    intensity_raw: float
    intensity_scaled: float
    form_factor_effective: float = 1.0
    structure_factor_real: float = 0.0
    structure_factor_imag: float = 0.0
    applied_multiplicity: float = 1.0
    applied_lorentz_polarization: float = 1.0
    applied_volume_factor: float = 1.0

    @property
    def hkl_label(self) -> str:
        return f"{self.h}{self.k}{self.l}"

    @property
    def hkl_id(self) -> str:
        return f"h{self.h}k{self.k}l{self.l}"

    @property
    def scattering_vector_s_a_inv(self) -> float:
        return 1.0 / (2.0 * self.d_spacing_a)

    @property
    def intensity_model(self) -> float:
        return self.intensity_raw


@dataclass(frozen=True, slots=True)
class SpectrumPoint:
    two_theta_deg: float
    intensity: float
