from __future__ import annotations

from dataclasses import dataclass

from orthoxrd.batch_models import SweepStep
from orthoxrd.config import SimulationConfig

MAX_SPECTRUM_CELLS = 2_000_000
MAX_PEAK_ROWS = 1_000_000
MAX_ESTIMATED_UNCOMPRESSED_BYTES = 1024**3
MAX_ESTIMATED_ZIP_BYTES = 512 * 1024**2

_SPECTRUM_BYTES_PER_CELL = 374
_PEAK_BYTES_PER_ROW = 654
_FIXED_EXPORT_OVERHEAD_BYTES = 5 * 1024**2


@dataclass(frozen=True, slots=True)
class ExportSizeEstimate:
    uncompressed_bytes: int
    zip_bytes: int


def estimate_sweep_export_size(
    *,
    spectrum_cells: int,
    estimated_peak_rows: int,
) -> ExportSizeEstimate:
    uncompressed = (
        spectrum_cells * _SPECTRUM_BYTES_PER_CELL
        + estimated_peak_rows * _PEAK_BYTES_PER_ROW
        + _FIXED_EXPORT_OVERHEAD_BYTES
    )
    return ExportSizeEstimate(
        uncompressed_bytes=uncompressed,
        zip_bytes=uncompressed // 2,
    )


def validate_sweep_preflight(
    steps: tuple[SweepStep, ...],
    base: SimulationConfig,
) -> None:
    spectrum_cells = len(steps) * base.spectrum_points
    if spectrum_cells > MAX_SPECTRUM_CELLS:
        raise ValueError(
            "sweep exceeds the 2,000,000 spectrum-cell limit; reduce steps or spectrum points"
        )
    line_count = max((len(step.lines) for step in steps), default=0)
    candidate_hkls = (base.hkl_max + 1) ** 3 - 1
    estimated_peak_rows = len(steps) * line_count * candidate_hkls
    if estimated_peak_rows > MAX_PEAK_ROWS:
        raise ValueError(
            "sweep may exceed the 1,000,000 peak-row limit; "
            "reduce steps, radiation lines, or hkl_max"
        )
    estimate = estimate_sweep_export_size(
        spectrum_cells=spectrum_cells,
        estimated_peak_rows=estimated_peak_rows,
    )
    if estimate.uncompressed_bytes > MAX_ESTIMATED_UNCOMPRESSED_BYTES:
        raise ValueError(
            "estimated uncompressed export exceeds 1 GiB; reduce steps, spectrum points, or hkl_max"
        )
    if estimate.zip_bytes > MAX_ESTIMATED_ZIP_BYTES:
        raise ValueError("estimated ZIP exceeds 512 MiB; reduce steps, spectrum points, or hkl_max")
