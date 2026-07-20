from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Final

from orthoxrd.export_schema import CsvValue
from orthoxrd.fit_models import FitResult
from orthoxrd.structure_coordinates import (
    structure_branch_from_y,
    structure_coordinate_from_y,
)
from orthoxrd.structure_factor import normalized_shuffle_from_y

OBSERVATION_EXPORT_FIELDS: Final[tuple[str, ...]] = (
    "row",
    "h",
    "k",
    "l",
    "I_obs",
    "line",
    "line_id",
    "line_label",
    "series_id",
    "input_weight",
    "sigma",
    "resolved_weight",
    "notes",
    "included",
    "exclude_reason",
)
GRID_SCAN_FIELDS: Final[tuple[str, ...]] = (
    "y",
    "scale_s",
    "chi2",
    "shuffle_signed",
    "shuffle_magnitude",
    "normalized_shuffle",
    "branch",
)
REFINE_TRACE_FIELDS: Final[tuple[str, ...]] = (
    "evaluation",
    "y",
    "scale_s",
    "chi2",
    "shuffle_signed",
    "shuffle_magnitude",
    "normalized_shuffle",
    "branch",
)
BEST_POINT_FIELDS: Final[tuple[str, ...]] = (
    "y",
    "scale_s",
    "chi2",
    "shuffle_signed",
    "shuffle_magnitude",
    "normalized_shuffle",
    "source",
)
RESIDUAL_AT_BEST_FIELDS: Final[tuple[str, ...]] = (
    "h",
    "k",
    "l",
    "line_id",
    "line_label",
    "series_id",
    "I_obs",
    "I_model",
    "S_I_model",
    "residual",
    "weight",
    "included",
)
LOCAL_MINIMA_FIELDS: Final[tuple[str, ...]] = (
    "grid_index",
    "y",
    "scale_s",
    "chi2",
    "refined_y",
    "refined_scale_s",
    "refined_chi2",
    "delta_chi2",
    "refine_status",
    "shuffle_signed",
    "shuffle_magnitude",
    "normalized_shuffle",
    "branch",
)


def observation_export_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    for item in result.matched:
        obs = item.observation
        yield {
            "row": obs.row,
            "h": obs.h,
            "k": obs.k,
            "l": obs.l,
            "I_obs": obs.I_obs,
            "line": obs.line if obs.line is not None else "",
            "line_id": item.line_id,
            "line_label": item.line_label,
            "series_id": item.series_id,
            "input_weight": obs.weight if obs.weight is not None else "",
            "sigma": obs.sigma if obs.sigma is not None else "",
            "resolved_weight": item.weight,
            "notes": obs.notes,
            "included": int(item.included),
            "exclude_reason": item.exclude_reason or "",
        }


def grid_scan_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    for point in result.grid_scan:
        yield {
            "y": point.y,
            "scale_s": point.scale_s,
            "chi2": point.chi2,
            **_structure_coordinate_fields(point.y),
        }


def refine_trace_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    for point in result.refine_trace:
        yield {
            "evaluation": point.evaluation,
            "y": point.y,
            "scale_s": point.scale_s,
            "chi2": point.chi2,
            **_structure_coordinate_fields(point.y),
        }


def best_point_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    best = result.best
    yield {
        "y": best.y,
        "scale_s": best.scale_s,
        "chi2": best.chi2,
        "shuffle_signed": best.shuffle_signed,
        "shuffle_magnitude": best.shuffle_magnitude,
        "normalized_shuffle": best.normalized_shuffle,
        "source": best.source,
    }


def residual_at_best_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    for residual in result.residuals_at_best:
        yield {
            "h": residual.h,
            "k": residual.k,
            "l": residual.l,
            "line_id": residual.line_id,
            "line_label": residual.line_label,
            "series_id": residual.series_id,
            "I_obs": residual.I_obs,
            "I_model": residual.I_model,
            "S_I_model": residual.S_I_model,
            "residual": residual.residual,
            "weight": residual.weight,  # resolved weight used in chi2
            "included": int(residual.included),
        }


def local_minima_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    for candidate in result.local_minima:
        refined_y = candidate.refined_y
        refined_chi2 = candidate.refined_chi2
        effective_chi2 = refined_chi2 if refined_chi2 is not None else candidate.chi2
        yield {
            "grid_index": candidate.grid_index,
            "y": candidate.y,
            "scale_s": candidate.scale_s,
            "chi2": candidate.chi2,
            "refined_y": refined_y if refined_y is not None else "",
            "refined_scale_s": (
                candidate.refined_scale_s if candidate.refined_scale_s is not None else ""
            ),
            "refined_chi2": refined_chi2 if refined_chi2 is not None else "",
            "delta_chi2": effective_chi2 - result.best.chi2,
            "refine_status": candidate.refine_status,
            **_structure_coordinate_fields(candidate.y),
        }


def _structure_coordinate_fields(y: float) -> dict[str, CsvValue]:
    branch = structure_branch_from_y(y)
    return {
        "shuffle_signed": structure_coordinate_from_y(y, "signed_shuffle"),
        "shuffle_magnitude": structure_coordinate_from_y(y, "shuffle_magnitude"),
        "normalized_shuffle": normalized_shuffle_from_y(y),
        "branch": branch if branch is not None else "reference",
    }
