from __future__ import annotations

import math
from collections.abc import Iterator, Mapping

from orthoxrd.export_schema import CsvValue
from orthoxrd.simulation import SimulationResult


def current_spectrum_rows(result: SimulationResult) -> Iterator[Mapping[str, CsvValue]]:
    wavelength = result.config.lines[0].wavelength_a
    for index, (two_theta, model, local) in enumerate(
        zip(
            result.spectrum.two_theta_deg,
            result.spectrum.intensity_model,
            result.spectrum.intensity_rel_local,
            strict=True,
        )
    ):
        q_value, d_value = q_d(float(two_theta), wavelength)
        yield {
            "point_index": index,
            "two_theta_deg": float(two_theta),
            "q_primary_A_inv": q_value,
            "d_primary_A": d_value,
            "intensity_model": float(model),
            "intensity_rel_local": float(local),
        }


def current_peak_rows(result: SimulationResult) -> Iterator[Mapping[str, CsvValue]]:
    volume = result.config.lattice.volume_a3
    for peak in result.peaks:
        reflection = peak.reflection
        yield {
            "line_id": peak.line_id,
            "line": peak.line_label,
            "series_id": peak.series_id,
            "h": reflection.h,
            "k": reflection.k,
            "l": reflection.l,
            "hkl": reflection.hkl_label,
            "hkl_id": reflection.hkl_id,
            "wavelength_A": peak.wavelength_a,
            "line_weight": peak.line_weight,
            "two_theta_deg": reflection.two_theta_deg,
            "d_A": reflection.d_spacing_a,
            "q_A_inv": reflection.q_a_inv,
            "s_A_inv": reflection.scattering_vector_s_a_inv,
            "form_factor_effective": reflection.form_factor_effective,
            "F_real": reflection.structure_factor_real,
            "F_imag": reflection.structure_factor_imag,
            "F2": reflection.structure_factor_squared,
            "multiplicity": reflection.multiplicity,
            "LP": reflection.lorentz_polarization,
            "volume_A3": volume,
            "applied_multiplicity": reflection.applied_multiplicity,
            "applied_LP": reflection.applied_lorentz_polarization,
            "applied_volume_factor": reflection.applied_volume_factor,
            "I_model_peak": reflection.intensity_model,
            "I_rel_local": reflection.intensity_scaled,
        }


def q_d(two_theta_deg: float, wavelength_a: float) -> tuple[float | str, float | str]:
    sine = math.sin(math.radians(two_theta_deg / 2.0))
    if sine <= 0:
        return "", ""
    return 4.0 * math.pi * sine / wavelength_a, wavelength_a / (2.0 * sine)
