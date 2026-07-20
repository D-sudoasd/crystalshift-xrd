from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from orthoxrd.batch_models import SweepResult
from orthoxrd.config import SimulationConfig
from orthoxrd.export_current_rows import current_peak_rows, current_spectrum_rows
from orthoxrd.export_excel import (
    ExcelColumnSpec,
    ExcelParameterSpec,
    ExcelSheetSpec,
    build_excel_workbook,
)
from orthoxrd.export_fit_rows import (
    BEST_POINT_FIELDS,
    GRID_SCAN_FIELDS,
    LOCAL_MINIMA_FIELDS,
    OBSERVATION_EXPORT_FIELDS,
    REFINE_TRACE_FIELDS,
    RESIDUAL_AT_BEST_FIELDS,
    best_point_rows,
    grid_scan_rows,
    local_minima_rows,
    observation_export_rows,
    refine_trace_rows,
    residual_at_best_rows,
)
from orthoxrd.export_schema import (
    CURRENT_PEAK_FIELDS,
    CURRENT_SPECTRUM_FIELDS,
    F2_EVOLUTION_FIELDS,
    PEAK_EVOLUTION_V2_FIELDS,
    SERIES_MAP_FIELDS,
    SPECTRA_LONG_V2_FIELDS,
    SWEEP_STEPS_FIELDS,
    CsvValue,
)
from orthoxrd.export_sweep_rows import (
    peak_evolution_rows,
    peak_matrix_fields,
    peak_matrix_rows,
    series_map_rows,
    spectra_long_rows,
    spectrum_matrix_fields,
    spectrum_matrix_rows,
    sweep_step_rows,
)
from orthoxrd.fit_models import FitResult
from orthoxrd.live import LivePreviewResult
from orthoxrd.simulation import SimulationResult
from orthoxrd.structure_coordinates import (
    StructureAxis,
    StructureBranch,
    structure_branch_from_y,
)
from orthoxrd.structure_factor import normalized_shuffle_from_y, signed_shuffle_from_y

_TEXT_COLUMNS = frozenset(
    {
        "axis_code",
        "branch",
        "exclude_reason",
        "line",
        "line_label",
        "notes",
        "source",
        "sweep_axis",
        "refine_status",
    }
)

_COLUMN_DESCRIPTIONS = {
    "point_index": "Zero-based point index on the exported profile grid.",
    "sweep_index": "Zero-based sweep frame index.",
    "step_id": "Stable sweep-step identifier; preserve as text.",
    "step_label": "Human-readable sweep-step label; preserve as text.",
    "sweep_axis": "Canonical parameter varied by the sweep.",
    "axis_value": (
        "Numeric value on this row's exported axis; interpret it with sweep_axis "
        "or axis_code."
    ),
    "axis_code": "Coordinate represented by axis_value: y or a shuffle coordinate.",
    "row": "Source observation row number.",
    "evaluation": "Local-refinement evaluation sequence number.",
    "grid_index": "Zero-based index of the candidate on the fit grid.",
    "h": "Miller index h.",
    "k": "Miller index k.",
    "l": "Miller index l.",
    "hkl": "Reflection label with all leading zeroes preserved as text.",
    "hkl_id": "Stable reflection identifier; preserve as text.",
    "line": "Radiation-line selector supplied with the observation.",
    "line_id": "Stable radiation-line identifier; preserve as text.",
    "line_label": "Human-readable radiation-line label; preserve as text.",
    "series_id": "Stable radiation-line and HKL series identifier; preserve as text.",
    "two_theta_deg": "Diffraction angle 2theta.",
    "theta_deg": "Bragg angle theta.",
    "q_A-1": "Scattering-vector magnitude q.",
    "q_A_inv": "Scattering-vector magnitude q.",
    "q_primary_A_inv": "q calculated with the primary radiation wavelength.",
    "d_A": "Interplanar spacing d.",
    "d_primary_A": "d calculated with the primary radiation wavelength.",
    "s_A_inv": "sin(theta) divided by wavelength.",
    "g_A_inv": "Reciprocal-lattice magnitude 1/d.",
    "y": "Canonical Cmcm 4c Wyckoff fractional coordinate.",
    "shuffle_signed": "Signed basal shuffle, 2*(y-0.25).",
    "shuffle_magnitude": "Basal-shuffle magnitude, abs(shuffle_signed).",
    "normalized_shuffle": "Normalized basal-shuffle magnitude |s|/0.5, range [0,1].",
    "branch": "Shuffle-magnitude branch: lower, upper, or zero-shuffle reference.",
    "a_A": "Orthorhombic lattice parameter a.",
    "b_A": "Orthorhombic lattice parameter b.",
    "c_A": "Orthorhombic lattice parameter c.",
    "wavelength_A": "Radiation wavelength.",
    "primary_wavelength_A": "Primary radiation-line wavelength.",
    "energy_keV": "Photon energy for this radiation line.",
    "primary_energy_keV": "Photon energy for the primary radiation line.",
    "radiation_line_count": "Number of radiation lines used in this frame.",
    "line_weight": "Relative radiation-line weight used by the forward model.",
    "form_factor_effective": "Effective atomic scattering factor at this q.",
    "F_real": "Real component of the structure factor.",
    "F_imag": "Imaginary component of the structure factor.",
    "F_abs": "Absolute magnitude of the structure factor.",
    "F2": "Squared structure-factor magnitude.",
    "multiplicity": "Crystallographic reflection multiplicity.",
    "LP": "Raw Lorentz-polarisation factor.",
    "volume_A3": "Unit-cell volume used for this sweep row.",
    "cell_volume_A3": "Calculated orthorhombic unit-cell volume.",
    "applied_multiplicity": "Multiplicity factor actually applied to model intensity.",
    "applied_LP": "Lorentz-polarisation factor actually applied to model intensity.",
    "applied_volume_factor": "Cell-volume factor actually applied to model intensity.",
    "I_raw": "Legacy alias for calculated model peak intensity; not measured raw data.",
    "I_model_peak": "Calculated model peak intensity for one radiation line and HKL.",
    "I_model": "Calculated model peak intensity before fit scale S.",
    "intensity_model": "Unnormalised calculated profile intensity.",
    "I_rel_local": "Peak intensity normalised to the maximum within one frame.",
    "I_rel_global": "Peak intensity normalised to the maximum across the sweep.",
    "intensity_rel_local": "Profile intensity normalised within one frame.",
    "intensity_rel_global": "Profile intensity normalised across the sweep.",
    "multiplicity_structure_factor_sq": "Reference factor N*F2.",
    "theoretical_intensity_unscaled": "Reference factor N*F2*LP.",
    "material_scattering_factor_R_hkl": "Reference factor N*F2*LP/V_cell^2.",
    "material_scattering_factor_R_hkl_no_lp": "Reference factor N*F2/V_cell^2.",
    "inverse_material_scattering_factor_1_over_R_hkl": "Reciprocal of R_hkl when defined.",
    "inverse_material_scattering_factor_1_over_R_hkl_no_lp": (
        "Reciprocal of the no-LP R_hkl when defined."
    ),
    "phase_relative_R_hkl_pct": (
        "R_hkl normalised to the maximum within the same radiation line."
    ),
    "phase_relative_R_hkl_no_lp_pct": (
        "No-LP R_hkl normalised to the maximum within the same radiation line."
    ),
    "sin_theta": "Sine of the Bragg angle.",
    "cos_theta": "Cosine of the Bragg angle.",
    "sin_theta_over_lambda_1_over_A": "sin(theta)/wavelength.",
    "sin2_theta_over_lambda2_1_over_A2": "sin(theta)^2/wavelength^2.",
    "I_obs": "User-supplied observed peak area or height, according to observable_mode.",
    "input_weight": "Optional per-observation weight supplied by the user.",
    "sigma": "Optional per-observation standard uncertainty supplied by the user.",
    "resolved_weight": "Weight actually used in the chi-squared objective.",
    "weight": "Resolved weight used in the chi-squared contribution.",
    "included": "One when the observation contributes to the fit; zero otherwise.",
    "exclude_reason": "Reason an observation was excluded from the fit.",
    "notes": "Literal user annotation; never interpreted as an Excel formula.",
    "scale_s": "Closed-form non-negative scale factor S at this y.",
    "chi2": "Weighted residual sum of squares at this y and scale S.",
    "refined_y": "Locally refined candidate y; blank when refinement was not requested or failed.",
    "refined_scale_s": "Scale S at the locally refined candidate; blank when unavailable.",
    "refined_chi2": "Chi-squared at the locally refined candidate; blank when unavailable.",
    "delta_chi2": "Candidate chi-squared minus the selected best chi-squared.",
    "refine_status": "Candidate refinement status: not_requested, refined, or failed.",
    "S_I_model": "Fitted intensity S*I_model at the selected best point.",
    "residual": "Observed minus fitted peak intensity.",
    "source": "Whether the selected point came from the grid or local refinement.",
    "baseline_axis_value": "Canonical axis value for the baseline live frame.",
    "current_axis_value": "Canonical axis value for the selected live frame.",
    "baseline_q_A_inv": "Baseline-frame q value at this profile point.",
    "current_q_A_inv": "Selected-frame q value at this profile point.",
    "baseline_d_A": "Baseline-frame d spacing at this profile point.",
    "current_d_A": "Selected-frame d spacing at this profile point.",
    "baseline_intensity_model": "Unnormalised model intensity in the baseline frame.",
    "current_intensity_model": "Unnormalised model intensity in the selected frame.",
    "difference_intensity_model": "Selected minus baseline unnormalised model intensity.",
    "baseline_intensity_rel_global": "Baseline intensity on the live global scale.",
    "current_intensity_rel_global": "Selected intensity on the live global scale.",
    "difference_intensity_rel_global": "Selected minus baseline global relative intensity.",
}

_MATRIX_VALUE_SPECS: dict[str, tuple[str, str]] = {
    "SpectrumLocal": (
        "Local-relative profile intensity for stable sweep step {identifier}.",
        "percent",
    ),
    "SpectrumGlobal": (
        "Global-relative profile intensity for stable sweep step {identifier}.",
        "percent",
    ),
    "SpectrumModel": (
        "Unnormalised calculated profile intensity for stable sweep step {identifier}.",
        "a.u.",
    ),
    "PeakF2": (
        "Squared structure-factor magnitude F2 for stable series {identifier}.",
        "a.u.",
    ),
    "PeakNF2": (
        "Reference factor N*F2 for stable series {identifier}.",
        "a.u.",
    ),
    "PeakRwithLP": (
        "Reference factor N*F2*LP/V_cell^2 for stable series {identifier}.",
        "model structure-factor units * angstrom^-6",
    ),
    "PeakRnoLP": (
        "Reference factor N*F2/V_cell^2 for stable series {identifier}.",
        "model structure-factor units * angstrom^-6",
    ),
    "PeakModel": (
        "Calculated model peak intensity for stable series {identifier}.",
        "a.u.",
    ),
    "PeakGlobal": (
        "Global-relative peak intensity for stable series {identifier}.",
        "percent",
    ),
}


def build_current_excel_workbook(result: SimulationResult) -> bytes:
    return build_excel_workbook(
        title="CrystalShift XRD current simulation",
        readme=_readme_notes("current simulation"),
        parameters=_simulation_parameters(result.config),
        sheets=(
            _sheet(
                "Spectrum",
                CURRENT_SPECTRUM_FIELDS,
                current_spectrum_rows(result),
            ),
            _sheet("Peaks", CURRENT_PEAK_FIELDS, current_peak_rows(result)),
        ),
    )


def build_f2_excel_workbook(
    rows: Sequence[Mapping[str, CsvValue]],
    *,
    axis: StructureAxis,
    branch: StructureBranch,
    start: float,
    stop: float,
    points: int,
    active_y: float,
) -> bytes:
    active_signed = signed_shuffle_from_y(active_y)
    active_branch = structure_branch_from_y(active_y) or "reference"
    selected_hkls = ", ".join(dict.fromkeys(str(row["hkl"]) for row in rows))
    return build_excel_workbook(
        title="CrystalShift XRD analytical F2 evolution",
        readme=(
            "This standalone workbook mirrors the on-screen analytical F2 evolution table.",
            "The companion CSV remains the canonical machine-readable export.",
            "HKL labels are written as text so leading zeroes such as 021 are preserved.",
            "The Parameters sheet records the model and selected path; "
            "Columns explains every field.",
            "For the unit-scatterer Cmcm 4c model, F2 is zero when h+k is odd; "
            "otherwise F2 = 16*cos(2*pi*k*y - pi*l/2)^2.",
            "Peak profile, LP, multiplicity, composition, and volume factors are excluded.",
        ),
        parameters=(
            _parameter(
                "Model",
                "structure_factor_model",
                "analytic_unit_scatterer_cmcm_4c",
                "Analytical Cmcm 4c unit-scatterer F2 model.",
            ),
            _parameter("Evolution", "axis_code", axis, "Coordinate represented by axis_value."),
            _parameter(
                "Evolution",
                "shuffle_branch",
                branch if axis == "shuffle_magnitude" else "not_applicable",
                "Branch used only to map shuffle magnitude back to canonical y.",
            ),
            _parameter("Evolution", "start", start, "Inclusive axis start.", "fractional"),
            _parameter("Evolution", "stop", stop, "Inclusive axis stop.", "fractional"),
            _parameter("Evolution", "points", points, "Number of samples per HKL series."),
            _parameter(
                "Evolution",
                "selected_hkls",
                selected_hkls,
                "HKL series included in F2Evolution; preserve leading zeroes.",
            ),
            _parameter(
                "Active structure",
                "active_y",
                active_y,
                "Canonical Cmcm 4c y used for the on-screen active marker.",
                "fractional",
            ),
            _parameter(
                "Active structure",
                "active_shuffle_signed",
                active_signed,
                "Derived signed shuffle, 2*(active_y-0.25).",
                "fractional",
                "derived",
            ),
            _parameter(
                "Active structure",
                "active_shuffle_magnitude",
                abs(active_signed),
                "Derived absolute shuffle magnitude.",
                "fractional",
                "derived",
            ),
            _parameter(
                "Active structure",
                "active_normalized_shuffle",
                normalized_shuffle_from_y(active_y),
                "Normalized basal-shuffle magnitude |s|/0.5, range [0,1].",
                "1",
                "derived",
            ),
            _parameter(
                "Active structure",
                "active_branch",
                active_branch,
                "Branch of active_y relative to the zero-shuffle y=0.25 reference.",
                role="derived",
            ),
        ),
        sheets=(_sheet("F2Evolution", F2_EVOLUTION_FIELDS, rows),),
    )


def build_sweep_excel_workbook(result: SweepResult) -> bytes:
    return build_excel_workbook(
        title="CrystalShift XRD sweep analysis",
        readme=_readme_notes("sweep"),
        parameters=(*_simulation_parameters(result.base_config), *_sweep_parameters(result)),
        sheets=_sweep_sheets(result),
    )


def build_live_excel_workbook(
    result: LivePreviewResult,
    sweep: SweepResult,
    current_index: int,
    baseline_index: int,
    comparison_fields: Sequence[str],
    comparison_data: Iterable[Mapping[str, CsvValue]],
) -> bytes:
    return build_excel_workbook(
        title="CrystalShift XRD live evolution analysis",
        readme=_readme_notes("live evolution"),
        parameters=(
            *_simulation_parameters(sweep.base_config),
            *_sweep_parameters(sweep),
            *_live_parameters(result, current_index, baseline_index),
        ),
        sheets=(
            *_sweep_sheets(sweep),
            _sheet("FrameComparison", comparison_fields, comparison_data),
        ),
    )


def build_fit_excel_workbook(result: FitResult) -> bytes:
    return build_excel_workbook(
        title="CrystalShift XRD discrete peak intensity fit",
        readme=(
            *_readme_notes("discrete peak intensity fit"),
            "This is a discrete peak-intensity fit, not a Rietveld or full-pattern refinement.",
        ),
        parameters=(*_simulation_parameters(result.config), *_fit_parameters(result)),
        sheets=(
            _sheet(
                "Observations",
                OBSERVATION_EXPORT_FIELDS,
                observation_export_rows(result),
            ),
            _sheet("GridScan", GRID_SCAN_FIELDS, grid_scan_rows(result)),
            _sheet("RefineTrace", REFINE_TRACE_FIELDS, refine_trace_rows(result)),
            _sheet("BestPoint", BEST_POINT_FIELDS, best_point_rows(result)),
            _sheet(
                "Residuals",
                RESIDUAL_AT_BEST_FIELDS,
                residual_at_best_rows(result),
            ),
            _sheet("LocalMinima", LOCAL_MINIMA_FIELDS, local_minima_rows(result)),
        ),
    )


def _sweep_sheets(result: SweepResult) -> tuple[ExcelSheetSpec, ...]:
    spectrum_fields = spectrum_matrix_fields(result)
    peak_fields = peak_matrix_fields(result)
    return (
        _sheet("PeakEvolution", PEAK_EVOLUTION_V2_FIELDS, peak_evolution_rows(result)),
        _sheet("SpectraLong", SPECTRA_LONG_V2_FIELDS, spectra_long_rows(result)),
        _sheet(
            "SpectrumLocal",
            spectrum_fields,
            spectrum_matrix_rows(result, "local"),
        ),
        _sheet(
            "SpectrumGlobal",
            spectrum_fields,
            spectrum_matrix_rows(result, "global"),
        ),
        _sheet("SweepSteps", SWEEP_STEPS_FIELDS, sweep_step_rows(result)),
        _sheet("SeriesMap", SERIES_MAP_FIELDS, series_map_rows(result)),
        _sheet(
            "SpectrumModel",
            spectrum_fields,
            spectrum_matrix_rows(result, "model"),
        ),
        _sheet("PeakF2", peak_fields, peak_matrix_rows(result, "F2")),
        _sheet("PeakNF2", peak_fields, peak_matrix_rows(result, "N_F2")),
        _sheet(
            "PeakRwithLP",
            peak_fields,
            peak_matrix_rows(result, "R_hkl_with_LP"),
        ),
        _sheet(
            "PeakRnoLP",
            peak_fields,
            peak_matrix_rows(result, "R_hkl_no_LP"),
        ),
        _sheet("PeakModel", peak_fields, peak_matrix_rows(result, "I_model")),
        _sheet(
            "PeakGlobal",
            peak_fields,
            peak_matrix_rows(result, "I_rel_global"),
        ),
    )


def _sheet(
    name: str,
    fields: Sequence[str],
    rows: Iterable[Mapping[str, CsvValue]],
) -> ExcelSheetSpec:
    field_tuple = tuple(fields)
    text_fields = frozenset(
        field for field in field_tuple if _column_data_type(field) == "text"
    )
    return ExcelSheetSpec(
        name=name,
        fields=field_tuple,
        rows=rows,
        columns={field: _column_spec(name, field) for field in field_tuple},
        text_fields=text_fields,
    )


def _column_spec(sheet_name: str, field: str) -> ExcelColumnSpec:
    matrix_spec = _MATRIX_VALUE_SPECS.get(sheet_name)
    if matrix_spec is not None and _column_data_type(field) == "number" and (
        field.startswith("step_") or field.startswith("line_")
    ):
        description, unit = matrix_spec
        return ExcelColumnSpec(
            description=description.format(identifier=field),
            unit=unit,
            data_type="number",
        )
    return ExcelColumnSpec(
        description=_column_description(field),
        unit=_column_unit(field),
        data_type=_column_data_type(field),
    )


def _column_description(field: str) -> str:
    known = _COLUMN_DESCRIPTIONS.get(field)
    if known is not None:
        return known
    if field.startswith("step_"):
        return "Matrix value for this stable sweep-step identifier."
    if field.startswith("line_"):
        return "Matrix value for this stable radiation-line and HKL series identifier."
    readable = field.replace("_", " ").replace("-", " ")
    return f"Exported {readable} value; governing formulas are recorded in manifest.json."


def _column_unit(field: str) -> str:
    if field in {
        "two_theta_deg",
        "theta_deg",
    }:
        return "degree"
    if field in {
        "a_A",
        "b_A",
        "c_A",
        "d_A",
        "d_primary_A",
        "wavelength_A",
        "primary_wavelength_A",
    }:
        return "angstrom"
    if field in {
        "q_A-1",
        "q_A_inv",
        "q_primary_A_inv",
        "s_A_inv",
        "g_A_inv",
        "sin_theta_over_lambda_1_over_A",
        "baseline_q_A_inv",
        "current_q_A_inv",
    }:
        return "angstrom^-1"
    if field == "sin2_theta_over_lambda2_1_over_A2":
        return "angstrom^-2"
    if field in {"volume_A3", "cell_volume_A3"}:
        return "angstrom^3"
    if field in {
        "material_scattering_factor_R_hkl",
        "material_scattering_factor_R_hkl_no_lp",
    }:
        return "model structure-factor units * angstrom^-6"
    if field in {
        "inverse_material_scattering_factor_1_over_R_hkl",
        "inverse_material_scattering_factor_1_over_R_hkl_no_lp",
    }:
        return "inverse model structure-factor units * angstrom^6"
    if field in {"energy_keV", "primary_energy_keV"}:
        return "keV"
    if field in {
        "baseline_d_A",
        "current_d_A",
    }:
        return "angstrom"
    if field in {"y", "refined_y", "shuffle_signed", "shuffle_magnitude"}:
        return "fractional"
    if field == "normalized_shuffle":
        return "1"
    if "rel_" in field or field.endswith("_pct"):
        return "percent"
    if "intensity" in field.casefold() or field in {"F2", "F_abs", "chi2"}:
        return "a.u."
    return ""


def _column_data_type(field: str) -> str:
    if field in _TEXT_COLUMNS:
        return "text"
    folded = field.casefold()
    if (
        folded == "hkl"
        or folded.startswith("hkl_")
        or folded == "id"
        or folded.endswith("_id")
        or "label" in folded
    ):
        return "text"
    return "number"


def _readme_notes(export_kind: str) -> tuple[str, ...]:
    return (
        f"This workbook mirrors the {export_kind} CSV process tables for Excel viewing.",
        "CSV files remain the canonical machine-readable data and retain their headers.",
        "Exact provenance, formulas, limitations, and checksums remain in manifest.json.",
        "HKL labels and stable identifiers are written as text so leading zeroes are preserved.",
        "Parameters explains inputs and derived state; Columns explains every workbook column.",
    )


def _simulation_parameters(config: SimulationConfig) -> tuple[ExcelParameterSpec, ...]:
    signed = signed_shuffle_from_y(config.y)
    parameters = [
        _parameter("Structure", "a_A", config.lattice.a, "Orthorhombic lattice a.", "angstrom"),
        _parameter("Structure", "b_A", config.lattice.b, "Orthorhombic lattice b.", "angstrom"),
        _parameter("Structure", "c_A", config.lattice.c, "Orthorhombic lattice c.", "angstrom"),
        _parameter(
            "Structure",
            "cell_volume_A3",
            config.lattice.volume_a3,
            "Derived orthorhombic unit-cell volume a*b*c.",
            "angstrom^3",
            "derived",
        ),
        _parameter(
            "Structure",
            "wyckoff_y",
            config.y,
            "Canonical Cmcm 4c fractional coordinate used by the forward model.",
            "fractional",
        ),
        _parameter(
            "Structure",
            "shuffle_signed",
            signed,
            "Derived signed basal shuffle, 2*(y-0.25).",
            "fractional",
            "derived",
        ),
        _parameter(
            "Structure",
            "shuffle_magnitude",
            abs(signed),
            "Derived basal-shuffle magnitude; branch information is not discarded from y.",
            "fractional",
            "derived",
        ),
        _parameter(
            "Structure",
            "normalized_shuffle",
            normalized_shuffle_from_y(config.y),
            "Normalized basal-shuffle magnitude |s|/0.5, range [0,1].",
            "1",
            "derived",
        ),
        _parameter(
            "Scattering",
            "scattering_mode",
            config.scattering_mode,
            "Unit or composition-dependent atomic scattering-factor model.",
        ),
        _parameter(
            "Scattering",
            "composition",
            "; ".join(
                f"{item.symbol}:{item.fraction:.12g}" for item in config.composition
            ),
            "Normalised element fractions used only in composition scattering mode.",
        ),
        _parameter(
            "Range",
            "two_theta_min_deg",
            config.two_theta_min,
            "Lower bound of the calculated 2theta window.",
            "degree",
        ),
        _parameter(
            "Range",
            "two_theta_max_deg",
            config.two_theta_max,
            "Upper bound of the calculated 2theta window.",
            "degree",
        ),
        _parameter("Range", "hkl_max", config.hkl_max, "Maximum absolute Miller index."),
        _parameter(
            "Range",
            "min_peak_percent",
            config.min_peak,
            "Default UI peak-display filter; canonical exports retain the complete peak rows.",
            "percent",
        ),
        _parameter("Profile", "profile_kind", config.profile_kind, "Peak profile function."),
        _parameter(
            "Profile",
            "fwhm_deg",
            config.fwhm_deg,
            "Common full width at half maximum used by the profile model.",
            "degree",
        ),
        _parameter(
            "Profile",
            "pseudo_voigt_eta",
            config.pseudo_voigt_eta,
            "Pseudo-Voigt Lorentzian mixing fraction.",
            "fraction",
        ),
        _parameter(
            "Profile",
            "spectrum_points",
            config.spectrum_points,
            "Number of points on the calculated profile grid.",
        ),
        _parameter(
            "Corrections",
            "lorentz_polarization",
            config.include_lorentz_polarization,
            "Whether the LP factor contributes to I_model_peak.",
        ),
        _parameter(
            "Corrections",
            "multiplicity",
            config.include_multiplicity,
            "Whether crystallographic multiplicity contributes to I_model_peak.",
        ),
        _parameter(
            "Corrections",
            "cell_volume_1_over_V",
            config.include_cell_volume,
            "Whether the 1/V cell-volume factor contributes to I_model_peak.",
        ),
    ]
    for index, line in enumerate(config.lines, start=1):
        section = f"Radiation {index}"
        parameters.extend(
            (
                _parameter(section, "label", line.label, "Radiation-line display label."),
                _parameter(
                    section,
                    "wavelength_A",
                    line.wavelength_a,
                    "Radiation wavelength.",
                    "angstrom",
                ),
                _parameter(
                    section,
                    "weight",
                    line.weight,
                    "Relative line weight used in I_model_peak.",
                ),
            )
        )
    return tuple(parameters)


def _sweep_parameters(result: SweepResult) -> tuple[ExcelParameterSpec, ...]:
    first = result.steps[0].step
    last = result.steps[-1].step
    return (
        _parameter("Sweep", "axis", first.axis, "Canonical calculation axis."),
        _parameter("Sweep", "step_count", len(result.steps), "Number of calculated frames."),
        _parameter(
            "Sweep",
            "first_axis_value",
            first.axis_value,
            "Canonical axis value of the first frame.",
        ),
        _parameter(
            "Sweep",
            "last_axis_value",
            last.axis_value,
            "Canonical axis value of the last frame.",
        ),
    )


def _live_parameters(
    result: LivePreviewResult,
    current_index: int,
    baseline_index: int,
) -> tuple[ExcelParameterSpec, ...]:
    config = result.config
    return (
        _parameter("Live", "axis", config.axis, "Parameter varied by live evolution."),
        _parameter("Live", "start", config.start, "Requested live range start."),
        _parameter("Live", "stop", config.stop, "Requested live range stop."),
        _parameter("Live", "step", config.step, "Requested live range increment."),
        _parameter(
            "Live",
            "preview_points",
            config.preview_points,
            "Profile points calculated per live frame.",
        ),
        _parameter(
            "Live",
            "shuffle_branch",
            config.shuffle_branch,
            "Branch used when live axis is shuffle magnitude.",
        ),
        _parameter("Live", "baseline_index", baseline_index, "Baseline frame index."),
        _parameter(
            "Live",
            "baseline_axis_value",
            float(result.axis_values[baseline_index]),
            "Canonical axis value of the baseline frame.",
        ),
        _parameter("Live", "current_index", current_index, "Selected frame index."),
        _parameter(
            "Live",
            "current_axis_value",
            float(result.axis_values[current_index]),
            "Canonical axis value of the selected frame.",
        ),
    )


def _fit_parameters(result: FitResult) -> tuple[ExcelParameterSpec, ...]:
    options = result.options
    best = result.best
    return (
        _parameter(
            "Fit options",
            "observable_mode",
            options.observable_mode,
            "Observed quantity entering the discrete peak-intensity fit.",
        ),
        _parameter(
            "Fit options",
            "weight_mode",
            options.weight_mode,
            "Global weighting rule before per-observation overrides.",
        ),
        _parameter("Fit options", "y_start", options.y_start, "Grid-scan lower y bound."),
        _parameter("Fit options", "y_stop", options.y_stop, "Grid-scan upper y bound."),
        _parameter(
            "Fit options",
            "grid_points",
            options.grid_points,
            "Number of uniform points in the y grid scan.",
        ),
        _parameter(
            "Fit options",
            "poisson_epsilon",
            options.poisson_epsilon,
            "Lower denominator bound for Poisson-like weights.",
        ),
        _parameter(
            "Fit options",
            "model_zero_tol",
            options.model_zero_tol,
            "Model-intensity tolerance used to identify vanishing peaks.",
        ),
        _parameter(
            "Fit options",
            "exclude_vanishing_model",
            options.exclude_vanishing_model,
            "Whether vanishing model peaks are excluded.",
        ),
        _parameter(
            "Fit options",
            "max_local_minima",
            options.max_local_minima,
            "Maximum local-minimum candidates retained for inspection.",
        ),
        _parameter(
            "Fit options",
            "profile_delta_chi2",
            options.profile_delta_chi2,
            "Δχ² threshold for the heuristic profile identifiability interval.",
            "chi2",
        ),
        _parameter(
            "Fit options",
            "refine",
            options.refine,
            "Whether local refinement follows the grid minimum.",
        ),
        _parameter(
            "Fit options",
            "refine_xtol",
            options.refine_xtol,
            "Local-refinement y tolerance.",
        ),
        _parameter(
            "Fit options",
            "refine_max_iter",
            options.refine_max_iter,
            "Maximum local-refinement evaluations.",
        ),
        _parameter("Fit result", "best_y", best.y, "Selected fitted Wyckoff y.", role="result"),
        _parameter(
            "Fit result",
            "best_shuffle_signed",
            best.shuffle_signed,
            "Signed basal shuffle derived from best_y.",
            role="result",
        ),
        _parameter(
            "Fit result",
            "best_shuffle_magnitude",
            best.shuffle_magnitude,
            "Basal-shuffle magnitude derived from best_y.",
            role="result",
        ),
        _parameter(
            "Fit result",
            "best_normalized_shuffle",
            best.normalized_shuffle,
            "Normalized basal-shuffle magnitude |s|/0.5, range [0,1].",
            "1",
            "result",
        ),
        _parameter(
            "Fit result",
            "best_scale_s",
            best.scale_s,
            "Selected non-negative fit scale S.",
            role="result",
        ),
        _parameter(
            "Fit result",
            "best_chi2",
            best.chi2,
            "Weighted residual sum of squares at the selected point.",
            role="result",
        ),
        _parameter(
            "Fit identifiability",
            "profile_method",
            (
                result.identifiability.method
                if result.identifiability is not None
                else "profile_delta_chi2"
            ),
            (
                "Profile method used for the y interval; this is a heuristic, "
                "not a covariance estimate."
            ),
            role="diagnostic",
        ),
        _parameter(
            "Fit identifiability",
            "profile_status",
            (
                result.identifiability.status
                if result.identifiability is not None
                else "not_available"
            ),
            "Identifiability status from the profile Δχ² diagnostic.",
            role="diagnostic",
        ),
        _parameter(
            "Fit identifiability",
            "profile_y_lower",
            result.identifiability.y_lower if result.identifiability is not None else None,
            "Lower profile Δχ² bound for y; heuristic.",
            "fractional",
            "diagnostic",
        ),
        _parameter(
            "Fit identifiability",
            "profile_y_upper",
            result.identifiability.y_upper if result.identifiability is not None else None,
            "Upper profile Δχ² bound for y; heuristic.",
            "fractional",
            "diagnostic",
        ),
        _parameter(
            "Fit identifiability",
            "profile_reasons",
            "; ".join(result.identifiability.reasons)
            if result.identifiability is not None
            else "not_recorded",
            "Reasons attached to the profile identifiability status.",
            role="diagnostic",
        ),
        _parameter(
            "Fit result",
            "included_peak_count",
            sum(1 for item in result.matched if item.included),
            "Observations contributing to the objective.",
            role="result",
        ),
        _parameter(
            "Fit result",
            "matched_peak_count",
            len(result.matched),
            "Observations matched to a model series.",
            role="result",
        ),
        _parameter(
            "Fit result",
            "warnings",
            "; ".join(result.warnings),
            "Fit warnings emitted by the engine.",
            role="result",
        ),
    )


def _parameter(
    section: str,
    name: str,
    value: CsvValue | bool | None,
    description: str,
    unit: str = "",
    role: str = "input",
) -> ExcelParameterSpec:
    return ExcelParameterSpec(
        section=section,
        name=name,
        value=value,
        description=description,
        unit=unit,
        role=role,
    )


__all__ = [
    "build_current_excel_workbook",
    "build_f2_excel_workbook",
    "build_fit_excel_workbook",
    "build_live_excel_workbook",
    "build_sweep_excel_workbook",
]
