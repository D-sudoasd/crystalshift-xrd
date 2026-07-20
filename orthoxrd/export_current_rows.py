from __future__ import annotations

import math
from collections.abc import Iterator, Mapping

from orthoxrd.export_schema import CsvValue
from orthoxrd.powder import wavelength_a_to_energy_kev
from orthoxrd.simulation import SimulationResult
from orthoxrd.structure_factor import normalized_shuffle_from_y, signed_shuffle_from_y


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
    shuffle_signed = signed_shuffle_from_y(result.config.y)
    maximum_r_by_line: dict[str, float] = {}
    maximum_r_no_lp_by_line: dict[str, float] = {}
    for peak in result.peaks:
        maximum_r_by_line[peak.line_id] = max(
            maximum_r_by_line.get(peak.line_id, 0.0),
            peak.reflection.reference_r_hkl_with_lp,
        )
        maximum_r_no_lp_by_line[peak.line_id] = max(
            maximum_r_no_lp_by_line.get(peak.line_id, 0.0),
            peak.reflection.reference_r_hkl_no_lp,
        )
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
            "y": result.config.y,
            "shuffle_signed": shuffle_signed,
            "shuffle_magnitude": abs(shuffle_signed),
            "normalized_shuffle": normalized_shuffle_from_y(result.config.y),
            "a_A": result.config.lattice.a,
            "b_A": result.config.lattice.b,
            "c_A": result.config.lattice.c,
            "energy_keV": wavelength_a_to_energy_kev(peak.wavelength_a),
            "theta_deg": reflection.theta_deg,
            "g_A_inv": reflection.g_a_inv,
            "sin_theta": reflection.sin_theta,
            "cos_theta": reflection.cos_theta,
            "sin_theta_over_lambda_1_over_A": reflection.sin_theta_over_lambda_a_inv,
            "sin2_theta_over_lambda2_1_over_A2": (
                reflection.sin2_theta_over_lambda2_a_inv2
            ),
            "F_abs": reflection.structure_factor_abs,
            "cell_volume_A3": reflection.cell_volume_a3,
            "multiplicity_structure_factor_sq": reflection.n_f2,
            "theoretical_intensity_unscaled": reflection.n_f2_lp,
            "material_scattering_factor_R_hkl": reflection.reference_r_hkl_with_lp,
            "material_scattering_factor_R_hkl_no_lp": reflection.reference_r_hkl_no_lp,
            "inverse_material_scattering_factor_1_over_R_hkl": _csv_optional(
                reflection.inverse_reference_r_hkl_with_lp
            ),
            "inverse_material_scattering_factor_1_over_R_hkl_no_lp": _csv_optional(
                reflection.inverse_reference_r_hkl_no_lp
            ),
            "phase_relative_R_hkl_pct": _relative(
                reflection.reference_r_hkl_with_lp,
                maximum_r_by_line.get(peak.line_id, 0.0),
            ),
            "phase_relative_R_hkl_no_lp_pct": _relative(
                reflection.reference_r_hkl_no_lp,
                maximum_r_no_lp_by_line.get(peak.line_id, 0.0),
            ),
        }


def q_d(two_theta_deg: float, wavelength_a: float) -> tuple[float | str, float | str]:
    sine = math.sin(math.radians(two_theta_deg / 2.0))
    if sine <= 0:
        return "", ""
    return 4.0 * math.pi * sine / wavelength_a, wavelength_a / (2.0 * sine)


def _relative(value: float, maximum: float) -> float:
    return value / maximum * 100.0 if maximum > 0 else 0.0


def _csv_optional(value: float | None) -> float | str:
    return "" if value is None else value
