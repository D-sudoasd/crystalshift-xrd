from __future__ import annotations

import hashlib
import json

from orthoxrd import __version__
from orthoxrd.batch_models import SweepResult
from orthoxrd.config import SimulationConfig, config_json, config_payload
from orthoxrd.export_rows import sweep_step_rows
from orthoxrd.export_schema import (
    EXPORT_SCHEMA_VERSION,
    PEAK_EVOLUTION_FIELDS,
    SPECTRA_LONG_FIELDS,
)
from orthoxrd.export_writer import ExportFileMeta

_MODEL_PEAK_FORMULA = (
    "F² × applied_multiplicity × applied_LP × "
    "applied_volume_factor × line_weight"
)
_APPLIED_VOLUME_FACTOR_NOTE = (
    "1 / V_cell when the cell-volume correction is enabled; otherwise 1"
)


def manifest_json(
    digest: str,
    files: dict[str, ExportFileMeta],
    config: SimulationConfig,
    export_kind: str,
) -> str:
    files_block = {
        name: {
            "rows": metadata.rows,
            "columns": metadata.columns,
            "sha256": metadata.sha256,
        }
        for name, metadata in files.items()
    }
    units = {
        "lattice_and_d": "angstrom",
        "q_and_s": "angstrom^-1",
        "two_theta": "degree",
        "energy": "keV",
        "relative_intensity": "percent",
        "model_intensity": "arbitrary calculated units",
        "reference_R_hkl": "model structure-factor units * angstrom^-6",
    }
    common = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "app_version": __version__,
        "export_kind": export_kind,
        "generated_at_utc": None,
        "deterministic": True,
        "config_hash": digest,
        "model": "orthorhombic alpha-double-prime Cmcm 4c",
        "corrections": config_payload(config)["corrections"],
        "units": units,
        "files": files_block,
    }
    if export_kind == "fit":
        payload = {
            **common,
            "intensity": {
                "I_model_peak": _MODEL_PEAK_FORMULA,
                "applied_volume_factor": _APPLIED_VOLUME_FACTOR_NOTE,
                "objective": "chi2(y, S) = sum_i w_i (I_obs,i - S * I_model,i(y))^2",
                "scale_S": (
                    "closed-form non-negative least-squares "
                    "S(y) = sum w I_obs I_model / sum w I_model^2"
                ),
            },
            "normalization": {
                "note": (
                    "discrete peak intensity fit; no sweep step local/global "
                    "profile normalization"
                ),
            },
            "compatibility": {
                "legacy_headers_preserved": False,
                "byte_for_byte_compatible": False,
                "numeric_tolerance": 1e-8,
                "method": "discrete_peak_intensity_fit",
            },
            "limits": [
                "kinematic powder calculation",
                "not Rietveld / not full-pattern profile refinement",
                "lattice, radiation, and intensity corrections fixed from simulation config",
                "free parameters: Wyckoff y and scale S only",
                "no texture, absorption, microstrain, domain size, zero shift, or background",
            ],
        }
    else:
        payload = {
            **common,
            "intensity": {
                "I_model_peak": _MODEL_PEAK_FORMULA,
                "applied_volume_factor": _APPLIED_VOLUME_FACTOR_NOTE,
                "I_profile_model": "sum(I_model_peak * profile(two_theta-center))",
                "I_rel_local": "100 * value / maximum within one step",
                "I_rel_global": "100 * value / maximum across the sweep",
                "I_raw": (
                    "legacy alias for calculated model peak intensity; not experimental raw data"
                ),
                "multiplicity_structure_factor_sq": "N * F2",
                "theoretical_intensity_unscaled": "N * F2 * LP",
                "material_scattering_factor_R_hkl": "N * F2 * LP / V_cell^2",
                "material_scattering_factor_R_hkl_no_lp": "N * F2 / V_cell^2",
                "phase_relative_R_hkl_pct": (
                    "100 * R_hkl / max(R_hkl) within the same radiation line"
                ),
                "phase_relative_R_hkl_no_lp_pct": (
                    "100 * R_hkl_no_LP / max(R_hkl_no_LP) within the same radiation line"
                ),
                "reference_R_scope": (
                    "unnormalized theoretical reference factors independent of applied correction "
                    "toggles and radiation line weight; not instrument-calibrated "
                    "absolute intensity"
                ),
            },
            "normalization": {
                "local": "each sweep step scaled to max 100",
                "global": "all sweep steps scaled to the global maximum",
            },
            "compatibility": {
                "legacy_headers_preserved": True,
                "legacy_peak_fields": list(PEAK_EVOLUTION_FIELDS),
                "legacy_spectra_fields": list(SPECTRA_LONG_FIELDS),
                "byte_for_byte_compatible": False,
                "numeric_tolerance": 1e-8,
            },
            "limits": [
                "kinematic powder calculation",
                "no texture or preferred orientation",
                "no absorption or anomalous dispersion",
                "no microstrain, domain size, zero shift, background, or absolute calibration",
            ],
        }
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + chr(10)


def sweep_config_json(result: SweepResult) -> str:
    payload = {
        "simulation": config_payload(result.base_config),
        "steps": list(sweep_step_rows(result)),
    }
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + chr(10)


def sweep_hash(result: SweepResult) -> str:
    payload = config_json(result.base_config) + json.dumps(
        list(sweep_step_rows(result)),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current_readme() -> str:
    return """# Current orthorhombic XRD simulation

Files
- spectrum.csv: profile on the common two-theta grid.
- peaks.csv: Bragg reflections, current y/lattice/radiation, geometry, structure
  factor, model-intensity decomposition, and R_hkl reference factors.
- analysis.xlsx: Excel-oriented mirror with README, Parameters, and Columns sheets.
- config.json: exact simulation inputs.
- manifest.json: schema, formulas, units, limits, and checksums.

Reference R factors
- material_scattering_factor_R_hkl = N * F2 * LP / V_cell^2.
- material_scattering_factor_R_hkl_no_lp = N * F2 / V_cell^2.
- The no-LP convention is for integrated experimental areas that have already
  received the corresponding LP, polarization, or geometry correction.
- Both are unnormalized theoretical model reference factors, not measured or
  instrument-calibrated absolute intensities. They exclude texture, absorption,
  and experimental peak-integration error.

Origin
1. Import spectrum.csv as comma-delimited text with the first row as Long Name.
2. Set two_theta_deg as X and intensity_rel_local or intensity_model as Y.
3. Import peaks.csv separately for labels and reflection filtering.

Python

    import numpy as np
    import matplotlib.pyplot as plt
    data = np.genfromtxt("spectrum.csv", delimiter=",", names=True)
    plt.plot(data["two_theta_deg"], data["intensity_rel_local"])
    plt.xlabel("2theta (deg)")
    plt.ylabel("Relative intensity (%)")
    plt.show()
"""


def sweep_readme() -> str:
    return """# Orthorhombic XRD sweep export

Mapping
- sweep_steps.csv maps stable step IDs to a, b, c, y, shuffle, and radiation.
- series_map.csv maps stable series IDs to radiation line and HKL.
- Long tables support filtering and tidy-data plotting.
- Matrix tables are ready for Origin contour/heatmap workflows.
- analysis.xlsx mirrors the analysis tables for Excel viewing and preserves identifiers as text.

Intensity
- model is unnormalized calculated profile or peak intensity.
- global uses one maximum for the sweep and preserves amplitude evolution.
- local normalizes each step separately and is only for shape comparison.
- peak_evolution_long.csv includes F2, N*F2, N*F2*LP, and both R_hkl
  conventions at every y or trajectory step.
- R_hkl_with_LP = N * F2 * LP / V_cell^2; R_hkl_no_LP = N * F2 / V_cell^2.
  These are model reference factors, not instrument-calibrated absolute intensity.

Origin heatmap
1. Import spectra_matrix_global.csv.
2. Set two_theta_deg as X and all step columns as Y data.
3. Use Plot > Contour > Heat Map; map columns with sweep_steps.csv.

Python heatmap

    import numpy as np
    import matplotlib.pyplot as plt
    data = np.genfromtxt("spectra_matrix_global.csv", delimiter=",", names=True)
    z = np.column_stack([data[name] for name in data.dtype.names[1:]]).T
    plt.imshow(z, aspect="auto", origin="lower",
               extent=[data["two_theta_deg"][0], data["two_theta_deg"][-1], 0, z.shape[0]])
    plt.xlabel("2theta (deg)")
    plt.ylabel("Sweep step")
    plt.colorbar(label="Global relative intensity (%)")
    plt.show()

HKL evolution
Import peak_evolution_long.csv and group by series_id, or use one of the
peak_evolution_matrix files for direct multi-curve plotting. Separate matrices
are provided for F2, N_F2, R_hkl_with_LP, R_hkl_no_LP, I_model, and
I_rel_global.
"""


def fit_readme() -> str:
    return """# Discrete peak intensity fit export

This package records a **discrete peak intensity fit** of Wyckoff y and a single
scale factor S. It is **not** a Rietveld, Le Bail, Pawley, or full-pattern
profile refinement. Lattice a, b, c, radiation, and intensity corrections are
fixed from the active simulation configuration; only y and S are free.

Method
- Model peak intensity: I_model_peak = F² × applied_multiplicity × applied_LP ×
  applied_volume_factor × line_weight (same forward contract as the rest of
  CrystalShift XRD).
- When the cell-volume correction is enabled, applied_volume_factor = 1 / V_cell.
- Objective: chi2(y, S) = sum_i w_i (I_obs,i - S * I_model,i(y))^2.
- Closed-form scale: S(y) = sum w I_obs I_model / sum w I_model^2 (S clamped >= 0).
- Default weights (poisson): w_i = 1 / max(I_obs,i, epsilon). Equal weights are
  optional; per-peak weight or sigma overrides global mode.
- Search: uniform y grid (default full [0, 0.5]) then local refinement around the
  grid minimum. Local minima on the grid are reported as candidates only.

Observable modes
- peak_area: preferred integral-intensity path vs I_model_peak.
- peak_height: equal-width proxy; height proportional to area so y and relative
  residuals match peak_area in v1; S absorbs any common constant. No per-peak
  FWHM modelling.

Files
- observations.csv: input peaks with matched series_id / line and inclusion flags.
  Columns input_weight and sigma are optional input fields; resolved_weight is the
  weight used in chi2 (poisson/equal/override). Do not confuse weight names.
- grid_scan.csv: y, S(y), chi2 for the scan grid.
- refine_trace.csv: local-refinement evaluations (may be empty if refine is off).
- best_fit.json / best_point.csv: y*, S*, chi2*, shuffle_signed, shuffle_magnitude.
- residual_at_best.csv: per-peak residuals at the selected best point only
  (weight column is resolved_weight used in chi2).
- local_minima.csv: neighbourhood minima on the grid chi2 curve.
- analysis.xlsx: Excel-oriented process tables plus parameter and column explanations.
- config.json: simulation payload (including panel wyckoff_y at Run — not free),
  fit options, notes explaining simulation.y vs best.y, and best summary.
- manifest.json: schema, formulas, units, limits, and file checksums.

Not included by default
- Full residual long-table for every grid y (keeps the package small).

Python chi2 curve

    import numpy as np
    import matplotlib.pyplot as plt
    data = np.genfromtxt("grid_scan.csv", delimiter=",", names=True)
    plt.plot(data["y"], data["chi2"])
    plt.xlabel("Wyckoff y")
    plt.ylabel("chi2(y)")
    plt.show()
"""
