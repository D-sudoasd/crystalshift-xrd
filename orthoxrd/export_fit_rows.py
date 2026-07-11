from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Final

from orthoxrd.export_schema import CsvValue
from orthoxrd.fit_models import FitResult

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
GRID_SCAN_FIELDS: Final[tuple[str, ...]] = ("y", "scale_s", "chi2")
REFINE_TRACE_FIELDS: Final[tuple[str, ...]] = ("evaluation", "y", "scale_s", "chi2")
BEST_POINT_FIELDS: Final[tuple[str, ...]] = (
    "y",
    "scale_s",
    "chi2",
    "shuffle_signed",
    "shuffle_magnitude",
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
LOCAL_MINIMA_FIELDS: Final[tuple[str, ...]] = ("grid_index", "y", "scale_s", "chi2")


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
        yield {"y": point.y, "scale_s": point.scale_s, "chi2": point.chi2}


def refine_trace_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    for point in result.refine_trace:
        yield {
            "evaluation": point.evaluation,
            "y": point.y,
            "scale_s": point.scale_s,
            "chi2": point.chi2,
        }


def best_point_rows(result: FitResult) -> Iterable[Mapping[str, CsvValue]]:
    best = result.best
    yield {
        "y": best.y,
        "scale_s": best.scale_s,
        "chi2": best.chi2,
        "shuffle_signed": best.shuffle_signed,
        "shuffle_magnitude": best.shuffle_magnitude,
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
        yield {
            "grid_index": candidate.grid_index,
            "y": candidate.y,
            "scale_s": candidate.scale_s,
            "chi2": candidate.chi2,
        }
