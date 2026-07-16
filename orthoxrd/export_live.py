from __future__ import annotations

import hashlib
import json
import math
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Final

import numpy as np

import orthoxrd.batch as batch_engine
from orthoxrd.batch_models import SweepResult, SweepStep, TrajectoryConfig
from orthoxrd.export_excel_packages import build_live_excel_workbook
from orthoxrd.export_manifest import manifest_json
from orthoxrd.export_schema import CsvValue
from orthoxrd.export_sweep_zip import BATCH_EXPORT_FILES, write_sweep_payload
from orthoxrd.export_writer import (
    ExportFileMeta,
    PreparedExport,
    cleanup_export,
    create_export_path,
    finalize_export,
    write_csv_entry,
    write_text_entry,
)
from orthoxrd.live import LivePreviewResult, config_for_live_value
from orthoxrd.structure_factor import signed_shuffle_from_y
from orthoxrd.ui_plot_state import PlotState

LIVE_COMPARISON_FIELDS: Final[tuple[str, ...]] = (
    "point_index",
    "two_theta_deg",
    "baseline_axis_value",
    "current_axis_value",
    "baseline_q_A_inv",
    "current_q_A_inv",
    "baseline_d_A",
    "current_d_A",
    "baseline_intensity_model",
    "current_intensity_model",
    "difference_intensity_model",
    "baseline_intensity_rel_global",
    "current_intensity_rel_global",
    "difference_intensity_rel_global",
)
LIVE_EXPORT_FILES = (
    *(name for name in BATCH_EXPORT_FILES if name != "manifest.json"),
    "live_state.json",
    "baseline_current_comparison.csv",
    "manifest.json",
)


def prepare_live_export(
    result: LivePreviewResult,
    current_index: int,
    baseline_index: int | None = None,
    plot_state: PlotState | None = None,
) -> PreparedExport:
    index = _clamp_index(current_index, len(result.axis_values))
    baseline = _clamp_index(
        result.baseline_index if baseline_index is None else baseline_index,
        len(result.axis_values),
    )
    sweep = _live_sweep(result)
    digest = _live_export_hash(result, index, baseline, plot_state)
    path = create_export_path()
    metadata: dict[str, ExportFileMeta] = {}
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        workbook = build_live_excel_workbook(
            result,
            sweep,
            index,
            baseline,
            LIVE_COMPARISON_FIELDS,
            comparison_rows(result, index, baseline),
        )
        write_sweep_payload(
            archive,
            sweep,
            metadata,
            plot_state,
            excel_workbook=workbook,
        )
        metadata["live_state.json"] = write_text_entry(
            archive, "live_state.json", _live_state_json(result, index, baseline)
        )
        metadata["baseline_current_comparison.csv"] = write_csv_entry(
            archive,
            "baseline_current_comparison.csv",
            LIVE_COMPARISON_FIELDS,
            comparison_rows(result, index, baseline),
        )
        write_text_entry(
            archive,
            "manifest.json",
            manifest_json(digest, metadata, sweep.base_config, "live"),
        )
    return finalize_export(path, digest)


def build_live_zip(
    result: LivePreviewResult,
    current_index: int,
    baseline_index: int | None = None,
) -> bytes:
    prepared = prepare_live_export(result, current_index, baseline_index)
    try:
        return Path(prepared.path).read_bytes()
    finally:
        cleanup_export(prepared)


def comparison_rows(
    result: LivePreviewResult,
    current_index: int,
    baseline_index: int | None = None,
) -> Iterable[Mapping[str, CsvValue]]:
    baseline = _clamp_index(
        result.baseline_index if baseline_index is None else baseline_index,
        len(result.axis_values),
    )
    index = _clamp_index(current_index, len(result.axis_values))
    baseline_model = result.intensity_model[baseline]
    current_model = result.intensity_model[index]
    maximum = result.global_maximum
    baseline_global = (
        baseline_model / maximum * 100.0
        if maximum > 0
        else np.zeros_like(baseline_model)
    )
    current_global = (
        current_model / maximum * 100.0
        if maximum > 0
        else np.zeros_like(current_model)
    )
    baseline_q, baseline_d = _q_d(
        result.two_theta_deg, float(result.wavelengths_a[baseline])
    )
    current_q, current_d = _q_d(
        result.two_theta_deg, float(result.wavelengths_a[index])
    )
    for point_index, two_theta in enumerate(result.two_theta_deg):
        yield {
            "point_index": point_index,
            "two_theta_deg": float(two_theta),
            "baseline_axis_value": float(result.axis_values[baseline]),
            "current_axis_value": float(result.axis_values[index]),
            "baseline_q_A_inv": float(baseline_q[point_index]),
            "current_q_A_inv": float(current_q[point_index]),
            "baseline_d_A": float(baseline_d[point_index]),
            "current_d_A": float(current_d[point_index]),
            "baseline_intensity_model": float(baseline_model[point_index]),
            "current_intensity_model": float(current_model[point_index]),
            "difference_intensity_model": float(
                current_model[point_index] - baseline_model[point_index]
            ),
            "baseline_intensity_rel_global": float(baseline_global[point_index]),
            "current_intensity_rel_global": float(current_global[point_index]),
            "difference_intensity_rel_global": float(
                current_global[point_index] - baseline_global[point_index]
            ),
        }


def _live_sweep(result: LivePreviewResult) -> SweepResult:
    base = replace(result.config.base, spectrum_points=result.config.preview_points)
    steps: list[SweepStep] = []
    for index, value in enumerate(result.axis_values):
        frame = config_for_live_value(result.config, float(value))
        signed = signed_shuffle_from_y(frame.y)
        steps.append(
            SweepStep(
                index=index,
                step_id=f"step_{index:04d}",
                label=f"{result.config.axis}={value:.8g}",
                axis=result.config.axis,
                axis_value=float(value),
                lattice=frame.lattice,
                y=frame.y,
                shuffle_signed=signed,
                shuffle_magnitude=abs(signed),
                lines=frame.lines,
            )
        )
    return batch_engine.generate_sweep(TrajectoryConfig(base=base, steps=tuple(steps)))


def _live_state_json(
    result: LivePreviewResult,
    current_index: int,
    baseline_index: int,
) -> str:
    payload = {
        "signature": result.signature,
        "axis": result.config.axis,
        "start": result.config.start,
        "stop": result.config.stop,
        "step": result.config.step,
        "shuffle_branch": result.config.shuffle_branch,
        "preview_points": result.config.preview_points,
        "frame_count": len(result.axis_values),
        "baseline_index": baseline_index,
        "baseline_axis_value": float(result.axis_values[baseline_index]),
        "current_index": current_index,
        "current_axis_value": float(result.axis_values[current_index]),
        "browser_payload_dtype": "float32",
        "export_dtype": "float64",
    }
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def _q_d(two_theta_deg: np.ndarray, wavelength_a: float) -> tuple[np.ndarray, np.ndarray]:
    theta = np.deg2rad(two_theta_deg / 2.0)
    q_values = 4.0 * math.pi * np.sin(theta) / wavelength_a
    d_values = np.divide(
        2.0 * math.pi,
        q_values,
        out=np.full_like(q_values, np.nan),
        where=q_values > 0,
    )
    return q_values, d_values


def _live_export_hash(
    result: LivePreviewResult,
    current_index: int,
    baseline_index: int,
    plot_state: PlotState | None,
) -> str:
    state_payload = None
    if plot_state is not None:
        state_payload = {
            "x_axis": plot_state.x_axis,
            "x_minimum": plot_state.x_minimum,
            "x_maximum": plot_state.x_maximum,
            "y_auto": plot_state.y_auto,
            "y_minimum": plot_state.y_minimum,
            "y_maximum": plot_state.y_maximum,
        }
    payload = {
        "signature": result.signature,
        "baseline_index": baseline_index,
        "current_index": current_index,
        "plot_state": state_payload,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _clamp_index(index: int, count: int) -> int:
    return max(0, min(index, count - 1))
