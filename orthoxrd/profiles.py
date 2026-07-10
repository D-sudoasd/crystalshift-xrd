from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from orthoxrd.models import ProfileKind, Reflection, SpectrumPoint


@dataclass(frozen=True, slots=True)
class SpectrumArrays:
    two_theta_deg: NDArray[np.float64]
    intensity_model: NDArray[np.float64]
    intensity_rel_local: NDArray[np.float64]


def profile_value(
    x_value: float,
    center: float,
    fwhm: float,
    kind: ProfileKind,
    pseudo_voigt_eta: float,
) -> float:
    if fwhm <= 0:
        raise ValueError("FWHM must be positive")
    delta = x_value - center
    if kind == "gaussian":
        sigma = fwhm / (2.0 * math.sqrt(2.0 * math.log(2.0)))
        return math.exp(-0.5 * (delta / sigma) ** 2)
    if kind == "lorentzian":
        gamma = fwhm / 2.0
        return 1.0 / (1.0 + (delta / gamma) ** 2)
    if pseudo_voigt_eta < 0 or pseudo_voigt_eta > 1:
        raise ValueError("pseudo-Voigt eta must be between 0 and 1")
    gaussian = profile_value(x_value, center, fwhm, "gaussian", pseudo_voigt_eta)
    lorentzian = profile_value(x_value, center, fwhm, "lorentzian", pseudo_voigt_eta)
    return pseudo_voigt_eta * lorentzian + (1.0 - pseudo_voigt_eta) * gaussian


def calculate_spectrum(
    reflections: Sequence[Reflection],
    *,
    two_theta_min: float,
    two_theta_max: float,
    points: int,
    fwhm_deg: float,
    profile_kind: ProfileKind,
    pseudo_voigt_eta: float,
    normalize: bool = True,
) -> tuple[SpectrumPoint, ...]:
    arrays = calculate_spectrum_arrays(
        reflections,
        two_theta_min=two_theta_min,
        two_theta_max=two_theta_max,
        points=points,
        fwhm_deg=fwhm_deg,
        profile_kind=profile_kind,
        pseudo_voigt_eta=pseudo_voigt_eta,
    )
    intensities = arrays.intensity_rel_local if normalize else arrays.intensity_model
    return tuple(
        SpectrumPoint(two_theta_deg=float(x_value), intensity=float(intensity))
        for x_value, intensity in zip(arrays.two_theta_deg, intensities, strict=True)
    )


def calculate_spectrum_arrays(
    reflections: Sequence[Reflection],
    *,
    two_theta_min: float,
    two_theta_max: float,
    points: int,
    fwhm_deg: float,
    profile_kind: ProfileKind,
    pseudo_voigt_eta: float,
) -> SpectrumArrays:
    if points < 2:
        raise ValueError("points must be at least 2")
    if two_theta_max <= two_theta_min:
        raise ValueError("two-theta range is invalid")
    x_values = np.linspace(two_theta_min, two_theta_max, points, dtype=np.float64)
    intensity_model = np.zeros(points, dtype=np.float64)
    for reflection in reflections:
        delta = x_values - reflection.two_theta_deg
        active = np.abs(delta) <= 20.0 * fwhm_deg
        if not np.any(active):
            continue
        match profile_kind:
            case "gaussian":
                sigma = fwhm_deg / (2.0 * math.sqrt(2.0 * math.log(2.0)))
                profile = np.exp(-0.5 * (delta[active] / sigma) ** 2)
            case "lorentzian":
                gamma = fwhm_deg / 2.0
                profile = 1.0 / (1.0 + (delta[active] / gamma) ** 2)
            case "pseudo_voigt":
                if pseudo_voigt_eta < 0 or pseudo_voigt_eta > 1:
                    raise ValueError("pseudo-Voigt eta must be between 0 and 1")
                sigma = fwhm_deg / (2.0 * math.sqrt(2.0 * math.log(2.0)))
                gaussian = np.exp(-0.5 * (delta[active] / sigma) ** 2)
                gamma = fwhm_deg / 2.0
                lorentzian = 1.0 / (1.0 + (delta[active] / gamma) ** 2)
                profile = pseudo_voigt_eta * lorentzian + (1.0 - pseudo_voigt_eta) * gaussian
            case unreachable:
                raise AssertionError(f"unreachable profile kind: {unreachable}")
        intensity_model[active] += reflection.intensity_scaled * profile
    maximum = float(np.max(intensity_model, initial=0.0))
    intensity_rel_local = (
        intensity_model / maximum * 100.0 if maximum > 0 else intensity_model.copy()
    )
    return SpectrumArrays(
        two_theta_deg=x_values,
        intensity_model=intensity_model,
        intensity_rel_local=intensity_rel_local,
    )
