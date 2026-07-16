from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Literal

from orthoxrd.batch import SweepResult
from orthoxrd.export_current_rows import q_d
from orthoxrd.export_schema import CsvValue
from orthoxrd.peak_metrics import PeakMetric, peak_metric_value
from orthoxrd.powder import wavelength_a_to_energy_kev

SpectrumKind = Literal["model", "local", "global"]


def sweep_step_rows(result: SweepResult) -> Iterator[Mapping[str, CsvValue]]:
    axis = _axis(result)
    for step_result in result.steps:
        step = step_result.step
        primary = step.lines[0]
        yield {
            "sweep_index": step.index,
            "step_id": step.step_id,
            "step_label": step.label,
            "sweep_axis": axis,
            "axis_value": step.axis_value,
            "y": step.y,
            "shuffle_signed": step.shuffle_signed,
            "shuffle_magnitude": step.shuffle_magnitude,
            "a_A": step.lattice.a,
            "b_A": step.lattice.b,
            "c_A": step.lattice.c,
            "primary_energy_keV": wavelength_a_to_energy_kev(primary.wavelength_a),
            "primary_wavelength_A": primary.wavelength_a,
            "radiation_line_count": len(step.lines),
        }


def series_map_rows(result: SweepResult) -> Iterator[Mapping[str, CsvValue]]:
    seen: set[str] = set()
    for step_result in result.steps:
        for peak in step_result.peaks:
            if peak.series_id in seen:
                continue
            seen.add(peak.series_id)
            reflection = peak.reflection
            yield {
                "series_id": peak.series_id,
                "line_id": peak.line_id,
                "h": reflection.h,
                "k": reflection.k,
                "l": reflection.l,
                "hkl": reflection.hkl_label,
                "hkl_id": reflection.hkl_id,
            }


def peak_evolution_rows(result: SweepResult) -> Iterator[Mapping[str, CsvValue]]:
    axis = _axis(result)
    for step_result in result.steps:
        for peak in step_result.peaks:
            step = peak.step
            reflection = peak.reflection
            yield {
                "sweep_index": step.index,
                "sweep_axis": axis,
                "y": step.y,
                "shuffle_signed": step.shuffle_signed,
                "shuffle_magnitude": step.shuffle_magnitude,
                "a_A": step.lattice.a,
                "b_A": step.lattice.b,
                "c_A": step.lattice.c,
                "line": peak.line_label,
                "h": reflection.h,
                "k": reflection.k,
                "l": reflection.l,
                "hkl": reflection.hkl_label,
                "two_theta_deg": reflection.two_theta_deg,
                "d_A": reflection.d_spacing_a,
                "q_A-1": reflection.q_a_inv,
                "multiplicity": reflection.multiplicity,
                "F2": reflection.structure_factor_squared,
                "LP": reflection.lorentz_polarization,
                "I_raw": reflection.intensity_model,
                "I_rel_local": reflection.intensity_scaled,
                "I_rel_global": _peak_global(result, reflection.intensity_model),
                "step_id": step.step_id,
                "step_label": step.label,
                "axis_value": step.axis_value,
                "line_id": peak.line_id,
                "series_id": peak.series_id,
                "wavelength_A": peak.wavelength_a,
                "line_weight": peak.line_weight,
                "s_A_inv": reflection.scattering_vector_s_a_inv,
                "form_factor_effective": reflection.form_factor_effective,
                "F_real": reflection.structure_factor_real,
                "F_imag": reflection.structure_factor_imag,
                "volume_A3": step.lattice.volume_a3,
                "applied_multiplicity": reflection.applied_multiplicity,
                "applied_LP": reflection.applied_lorentz_polarization,
                "applied_volume_factor": reflection.applied_volume_factor,
                "I_model_peak": reflection.intensity_model,
                "theta_deg": reflection.theta_deg,
                "g_A_inv": reflection.g_a_inv,
                "sin_theta": reflection.sin_theta,
                "cos_theta": reflection.cos_theta,
                "sin_theta_over_lambda_1_over_A": (
                    reflection.sin_theta_over_lambda_a_inv
                ),
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
            }


def spectra_long_rows(result: SweepResult) -> Iterator[Mapping[str, CsvValue]]:
    axis = _axis(result)
    for step_result in result.steps:
        step = step_result.step
        primary = step.lines[0]
        energy = wavelength_a_to_energy_kev(primary.wavelength_a)
        for two_theta, model, local in zip(
            step_result.two_theta_deg,
            step_result.intensity_model,
            step_result.intensity_rel_local,
            strict=True,
        ):
            q_value, d_value = q_d(float(two_theta), primary.wavelength_a)
            yield {
                "sweep_index": step.index,
                "sweep_axis": axis,
                "y": step.y,
                "shuffle_signed": step.shuffle_signed,
                "shuffle_magnitude": step.shuffle_magnitude,
                "two_theta_deg": float(two_theta),
                "intensity_rel_local": float(local),
                "intensity_rel_global": _spectrum_global(result, float(model)),
                "step_id": step.step_id,
                "step_label": step.label,
                "axis_value": step.axis_value,
                "a_A": step.lattice.a,
                "b_A": step.lattice.b,
                "c_A": step.lattice.c,
                "primary_energy_keV": energy,
                "primary_wavelength_A": primary.wavelength_a,
                "q_primary_A_inv": q_value,
                "d_primary_A": d_value,
                "intensity_model": float(model),
            }


def spectrum_matrix_rows(
    result: SweepResult,
    kind: SpectrumKind,
) -> Iterator[Mapping[str, CsvValue]]:
    matrix = result.spectrum_matrix(kind)
    for point_index, two_theta in enumerate(result.steps[0].two_theta_deg):
        row: dict[str, CsvValue] = {"two_theta_deg": float(two_theta)}
        for step_index, step_result in enumerate(result.steps):
            row[step_result.step.step_id] = float(matrix[step_index, point_index])
        yield row


def spectrum_matrix_fields(result: SweepResult) -> tuple[str, ...]:
    return ("two_theta_deg", *(step.step.step_id for step in result.steps))


def peak_matrix_rows(
    result: SweepResult,
    metric: PeakMetric,
) -> Iterator[Mapping[str, CsvValue]]:
    series = _series_ids(result)
    for step_result in result.steps:
        values = {
            peak.series_id: peak_metric_value(
                peak.reflection,
                metric,
                peak_global_max=result.peak_global_max,
            )
            for peak in step_result.peaks
        }
        row: dict[str, CsvValue] = {"step_id": step_result.step.step_id}
        row.update({series_id: values.get(series_id, 0.0) for series_id in series})
        yield row


def peak_matrix_fields(result: SweepResult) -> tuple[str, ...]:
    return ("step_id", *_series_ids(result))


def _series_ids(result: SweepResult) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(peak.series_id for step_result in result.steps for peak in step_result.peaks)
    )


def _axis(result: SweepResult) -> str:
    return result.steps[0].step.axis


def _peak_global(result: SweepResult, value: float) -> float:
    return value / result.peak_global_max * 100.0 if result.peak_global_max > 0 else 0.0


def _spectrum_global(result: SweepResult, value: float) -> float:
    maximum = result.spectrum_global_max
    return value / maximum * 100.0 if maximum > 0 else 0.0


def _csv_optional(value: float | None) -> float | str:
    return "" if value is None else value
