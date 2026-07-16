from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace

from orthoxrd.constants import HC_KEV_ANGSTROM
from orthoxrd.models import ElementFraction, LatticeParameters, Reflection, ScatteringMode
from orthoxrd.scattering import effective_form_factor
from orthoxrd.structure_factor import cmcm_4c_structure_factor, validate_y


def energy_kev_to_wavelength_a(energy_kev: float) -> float:
    if not math.isfinite(energy_kev) or energy_kev <= 0:
        raise ValueError("energy must be positive")
    return HC_KEV_ANGSTROM / energy_kev


def wavelength_a_to_energy_kev(wavelength_a: float) -> float:
    if not math.isfinite(wavelength_a) or wavelength_a <= 0:
        raise ValueError("wavelength must be positive")
    return HC_KEV_ANGSTROM / wavelength_a


def d_spacing_orthorhombic(h: int, k: int, l: int, lattice: LatticeParameters) -> float:
    if h == 0 and k == 0 and l == 0:
        raise ValueError("000 is not a valid reflection")
    reciprocal = (h * h) / (lattice.a * lattice.a)
    reciprocal += (k * k) / (lattice.b * lattice.b)
    reciprocal += (l * l) / (lattice.c * lattice.c)
    return 1.0 / math.sqrt(reciprocal)


def bragg_two_theta_deg(d_spacing_a: float, wavelength_a: float) -> float | None:
    if d_spacing_a <= 0 or wavelength_a <= 0:
        raise ValueError("d-spacing and wavelength must be positive")
    argument = wavelength_a / (2.0 * d_spacing_a)
    if argument > 1.0:
        return None
    return math.degrees(2.0 * math.asin(argument))


def multiplicity_orthorhombic(h: int, k: int, l: int) -> int:
    non_zero = sum(1 for value in (h, k, l) if value != 0)
    return 2**non_zero


def lorentz_polarization_factor(two_theta_deg: float) -> float:
    theta = math.radians(two_theta_deg / 2.0)
    denominator = math.sin(theta) ** 2 * math.cos(theta)
    if denominator <= 1e-12:
        return 0.0
    return (1.0 + math.cos(2.0 * theta) ** 2) / denominator


def _form_factor(
    scattering_mode: ScatteringMode,
    composition: Sequence[ElementFraction],
    s_a_inv: float,
) -> float:
    if scattering_mode == "unit":
        return 1.0
    return effective_form_factor(composition, s_a_inv)


def calculate_reflections(
    *,
    lattice: LatticeParameters,
    y: float,
    wavelength_a: float,
    two_theta_min: float,
    two_theta_max: float,
    hkl_max: int,
    scattering_mode: ScatteringMode = "composition",
    composition: Sequence[ElementFraction] = (),
    include_lorentz_polarization: bool = True,
    include_multiplicity: bool = True,
    include_cell_volume: bool = True,
    min_scaled_intensity: float = 0.0,
) -> tuple[Reflection, ...]:
    validate_y(y)
    if wavelength_a <= 0:
        raise ValueError("wavelength must be positive")
    if two_theta_min < 0 or two_theta_max <= two_theta_min:
        raise ValueError("two-theta range is invalid")
    if hkl_max < 1:
        raise ValueError("hkl_max must be at least 1")

    rows: list[Reflection] = []
    for h in range(0, hkl_max + 1):
        for k in range(0, hkl_max + 1):
            for l in range(0, hkl_max + 1):
                if h == 0 and k == 0 and l == 0:
                    continue
                d_spacing = d_spacing_orthorhombic(h, k, l, lattice)
                two_theta = bragg_two_theta_deg(d_spacing, wavelength_a)
                if two_theta is None or two_theta < two_theta_min or two_theta > two_theta_max:
                    continue
                s_value = 1.0 / (2.0 * d_spacing)
                form_factor = _form_factor(scattering_mode, composition, s_value)
                structure_factor = cmcm_4c_structure_factor(h, k, l, y, form_factor)
                structure_factor_squared = float(
                    (structure_factor * structure_factor.conjugate()).real
                )
                if abs(structure_factor_squared) < 1e-12:
                    structure_factor_squared = 0.0
                multiplicity = multiplicity_orthorhombic(h, k, l)
                lp_factor = lorentz_polarization_factor(two_theta)
                applied_multiplicity = float(multiplicity) if include_multiplicity else 1.0
                applied_lp = lp_factor if include_lorentz_polarization else 1.0
                applied_volume = 1.0 / lattice.volume_a3 if include_cell_volume else 1.0
                intensity = max(
                    structure_factor_squared * applied_multiplicity * applied_lp * applied_volume,
                    0.0,
                )
                rows.append(
                    Reflection(
                        h=h,
                        k=k,
                        l=l,
                        d_spacing_a=d_spacing,
                        two_theta_deg=two_theta,
                        q_a_inv=2.0 * math.pi / d_spacing,
                        multiplicity=multiplicity,
                        structure_factor_squared=structure_factor_squared,
                        lorentz_polarization=lp_factor,
                        intensity_raw=intensity,
                        intensity_scaled=0.0,
                        form_factor_effective=form_factor,
                        structure_factor_real=float(structure_factor.real),
                        structure_factor_imag=float(structure_factor.imag),
                        applied_multiplicity=applied_multiplicity,
                        applied_lorentz_polarization=applied_lp,
                        applied_volume_factor=applied_volume,
                        cell_volume_a3=lattice.volume_a3,
                    )
                )

    maximum = max((row.intensity_raw for row in rows), default=0.0)
    reflections: list[Reflection] = []
    for row in sorted(rows, key=lambda item: (item.two_theta_deg, item.h, item.k, item.l)):
        scaled = row.intensity_raw / maximum * 100.0 if maximum > 0 else 0.0
        if scaled < min_scaled_intensity:
            continue
        reflections.append(replace(row, intensity_scaled=scaled))
    return tuple(reflections)
