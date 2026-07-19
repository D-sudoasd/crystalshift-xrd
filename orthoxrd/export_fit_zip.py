from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Final

from orthoxrd.config import config_json, config_payload
from orthoxrd.export_excel_packages import build_fit_excel_workbook
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
from orthoxrd.export_manifest import fit_readme, manifest_json
from orthoxrd.export_writer import (
    ExportFileMeta,
    PreparedExport,
    cleanup_export,
    create_export_path,
    finalize_export,
    open_deterministic_zip,
    write_binary_entry,
    write_csv_entry,
    write_text_entry,
)
from orthoxrd.fit_models import FitResult

FIT_EXPORT_FILES: Final[tuple[str, ...]] = (
    "observations.csv",
    "grid_scan.csv",
    "refine_trace.csv",
    "best_fit.json",
    "best_point.csv",
    "residual_at_best.csv",
    "local_minima.csv",
    "fit_diagnostics.json",
    "analysis.xlsx",
    "config.json",
    "README.md",
    "manifest.json",
)


def prepare_fit_export(result: FitResult) -> PreparedExport:
    """Build an on-demand fit process-table ZIP (schema 2.x style).

    Does **not** export full residual long-tables for every grid y — only
    residuals at the best point, plus grid χ²(y) and refine trace.
    """
    path = create_export_path()
    digest = fit_export_hash(result)
    metadata: dict[str, ExportFileMeta] = {}
    with open_deterministic_zip(path) as archive:
        metadata["observations.csv"] = write_csv_entry(
            archive,
            "observations.csv",
            OBSERVATION_EXPORT_FIELDS,
            observation_export_rows(result),
        )
        metadata["grid_scan.csv"] = write_csv_entry(
            archive,
            "grid_scan.csv",
            GRID_SCAN_FIELDS,
            grid_scan_rows(result),
        )
        metadata["refine_trace.csv"] = write_csv_entry(
            archive,
            "refine_trace.csv",
            REFINE_TRACE_FIELDS,
            refine_trace_rows(result),
        )
        metadata["best_fit.json"] = write_text_entry(
            archive, "best_fit.json", _best_fit_json(result)
        )
        metadata["best_point.csv"] = write_csv_entry(
            archive,
            "best_point.csv",
            BEST_POINT_FIELDS,
            best_point_rows(result),
        )
        metadata["residual_at_best.csv"] = write_csv_entry(
            archive,
            "residual_at_best.csv",
            RESIDUAL_AT_BEST_FIELDS,
            residual_at_best_rows(result),
        )
        metadata["local_minima.csv"] = write_csv_entry(
            archive,
            "local_minima.csv",
            LOCAL_MINIMA_FIELDS,
            local_minima_rows(result),
        )
        metadata["fit_diagnostics.json"] = write_text_entry(
            archive,
            "fit_diagnostics.json",
            fit_diagnostics_json(result),
        )
        metadata["analysis.xlsx"] = write_binary_entry(
            archive,
            "analysis.xlsx",
            build_fit_excel_workbook(result),
        )
        metadata["config.json"] = write_text_entry(
            archive, "config.json", fit_config_json(result)
        )
        metadata["README.md"] = write_text_entry(archive, "README.md", fit_readme())
        write_text_entry(
            archive,
            "manifest.json",
            manifest_json(digest, metadata, result.config, "fit"),
        )
    return finalize_export(path, digest)


def build_fit_zip(result: FitResult) -> bytes:
    prepared = prepare_fit_export(result)
    try:
        return Path(prepared.path).read_bytes()
    finally:
        cleanup_export(prepared)


def fit_config_json(result: FitResult) -> str:
    options = result.options
    exclusions = [
        {
            "row": item.observation.row,
            "series_id": item.series_id,
            "h": item.observation.h,
            "k": item.observation.k,
            "l": item.observation.l,
            "line_id": item.line_id,
            "reason": item.exclude_reason or "",
        }
        for item in result.matched
        if not item.included
    ]
    simulation = config_payload(result.config)
    payload = {
        "simulation": simulation,
        "notes": {
            "simulation_wyckoff_y": (
                "simulation.wyckoff_y is the UI structure panel value at Run time; "
                "it is not a free fit parameter. The engine scans y over fit.y_start.."
                "fit.y_stop. Use best.y for the fitted result (y*)."
            ),
            "observations_weight_columns": (
                "observations.csv uses input_weight (optional CSV column) and "
                "resolved_weight (weight actually used in chi2)."
            ),
        },
        "fit": {
            "observable_mode": options.observable_mode,
            "weight_mode": options.weight_mode,
            "y_start": options.y_start,
            "y_stop": options.y_stop,
            "grid_points": options.grid_points,
            "poisson_epsilon": options.poisson_epsilon,
            "model_zero_tol": options.model_zero_tol,
            "exclude_vanishing_model": options.exclude_vanishing_model,
            "max_local_minima": options.max_local_minima,
            "profile_delta_chi2": options.profile_delta_chi2,
            "refine": options.refine,
            "refine_xtol": options.refine_xtol,
            "refine_max_iter": options.refine_max_iter,
            "warnings": list(result.warnings),
            "included_peak_count": sum(1 for item in result.matched if item.included),
            "matched_peak_count": len(result.matched),
            "exclusions": exclusions,
            "free_parameters": ["y", "scale_s"],
            "fixed_from_simulation": [
                "lattice",
                "radiation",
                "scattering_mode",
                "composition",
                "corrections",
                "two_theta_window",
                "hkl_max",
            ],
            "identifiability": _identifiability_payload(result),
        },
        "best": {
            "y": result.best.y,
            "scale_s": result.best.scale_s,
            "chi2": result.best.chi2,
            "shuffle_signed": result.best.shuffle_signed,
            "shuffle_magnitude": result.best.shuffle_magnitude,
            "source": result.best.source,
            "identifiability": _identifiability_payload(result),
        },
    }
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def fit_export_hash(result: FitResult) -> str:
    """Stable content hash for the fit package (simulation + options + tables)."""
    options = result.options
    options_payload = {
        "observable_mode": options.observable_mode,
        "weight_mode": options.weight_mode,
        "y_start": options.y_start,
        "y_stop": options.y_stop,
        "grid_points": options.grid_points,
        "poisson_epsilon": options.poisson_epsilon,
        "model_zero_tol": options.model_zero_tol,
        "exclude_vanishing_model": options.exclude_vanishing_model,
        "max_local_minima": options.max_local_minima,
        "profile_delta_chi2": options.profile_delta_chi2,
        "refine": options.refine,
        "refine_xtol": options.refine_xtol,
        "refine_max_iter": options.refine_max_iter,
    }
    observations_payload = [
        {
            "row": item.observation.row,
            "h": item.observation.h,
            "k": item.observation.k,
            "l": item.observation.l,
            "I_obs": item.observation.I_obs,
            "line": item.observation.line,
            "weight": item.observation.weight,
            "sigma": item.observation.sigma,
            "line_id": item.line_id,
            "series_id": item.series_id,
            "included": item.included,
            "exclude_reason": item.exclude_reason,
            "resolved_weight": item.weight,
        }
        for item in result.matched
    ]
    best_payload = {
        "y": result.best.y,
        "scale_s": result.best.scale_s,
        "chi2": result.best.chi2,
        "source": result.best.source,
    }
    diagnostics_payload = _identifiability_payload(result)
    local_minima_payload = list(local_minima_rows(result))
    material = (
        config_json(result.config)
        + json.dumps(options_payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + json.dumps(
            observations_payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        + json.dumps(best_payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + json.dumps(
            diagnostics_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + json.dumps(
            local_minima_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _best_fit_json(result: FitResult) -> str:
    best = result.best
    payload = {
        "y": best.y,
        "scale_s": best.scale_s,
        "chi2": best.chi2,
        "shuffle_signed": best.shuffle_signed,
        "shuffle_magnitude": best.shuffle_magnitude,
        "source": best.source,
        "observable_mode": result.options.observable_mode,
        "weight_mode": result.options.weight_mode,
        "identifiability": _identifiability_payload(result),
    }
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def fit_diagnostics_json(result: FitResult) -> str:
    """Serialize the profile-delta-chi2 identifiability diagnostic."""
    payload = {
        **_identifiability_payload(result),
        "best_y": result.best.y,
        "best_chi2": result.best.chi2,
        "note": (
            "Profile Δχ² interval is a heuristic built from grid points and refined "
            "local candidates; it is not a full covariance estimate."
        ),
    }
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _identifiability_payload(result: FitResult) -> dict[str, object]:
    diagnostic = result.identifiability
    if diagnostic is None:
        return {
            "method": "profile_delta_chi2",
            "heuristic": True,
            "delta_chi2_threshold": result.options.profile_delta_chi2,
            "y_lower": None,
            "y_upper": None,
            "status": "not_available",
            "reasons": ["not_recorded"],
            "near_best_candidate_count": 0,
        }
    return {
        "method": diagnostic.method,
        "heuristic": True,
        "delta_chi2_threshold": diagnostic.delta_chi2_threshold,
        "y_lower": diagnostic.y_lower,
        "y_upper": diagnostic.y_upper,
        "status": diagnostic.status,
        "reasons": list(diagnostic.reasons),
        "near_best_candidate_count": diagnostic.near_best_candidate_count,
    }
