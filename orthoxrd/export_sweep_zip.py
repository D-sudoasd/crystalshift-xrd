from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Literal

from orthoxrd.batch_models import SweepResult
from orthoxrd.export_excel_packages import build_sweep_excel_workbook
from orthoxrd.export_manifest import manifest_json, sweep_config_json, sweep_hash, sweep_readme
from orthoxrd.export_origin import (
    ORIGIN_COLUMN_MAP_FIELDS,
    SweepExportPlotState,
    origin_import_script,
    origin_readme,
    plot_state_json,
    sweep_origin_rows,
)
from orthoxrd.export_rows import (
    peak_evolution_rows,
    peak_matrix_fields,
    peak_matrix_rows,
    series_map_rows,
    spectra_long_rows,
    spectrum_matrix_fields,
    spectrum_matrix_rows,
    sweep_step_rows,
)
from orthoxrd.export_schema import (
    PEAK_EVOLUTION_V2_FIELDS,
    SERIES_MAP_FIELDS,
    SPECTRA_LONG_V2_FIELDS,
    SWEEP_STEPS_FIELDS,
)
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
from orthoxrd.peak_metrics import PEAK_METRICS, PeakMetric
from orthoxrd.ui_plot_state import PlotState

SpectrumKind = Literal["model", "local", "global"]

BATCH_EXPORT_FILES = (
    "peak_evolution_long.csv",
    "spectra_long.csv",
    "spectra_matrix_local.csv",
    "spectra_matrix_global.csv",
    "sweep_steps.csv",
    "series_map.csv",
    "spectra_matrix_model.csv",
    *(f"peak_evolution_matrix_{metric}.csv" for metric in PEAK_METRICS),
    "analysis.xlsx",
    "config.json",
    "README.md",
    "plot_state.json",
    "origin_column_map.csv",
    "origin_import.py",
    "ORIGIN_README.md",
    "manifest.json",
)
_SPECTRUM_MATRICES: tuple[tuple[str, SpectrumKind], ...] = (
    ("spectra_matrix_local.csv", "local"),
    ("spectra_matrix_global.csv", "global"),
    ("spectra_matrix_model.csv", "model"),
)
_PEAK_MATRICES: tuple[tuple[str, PeakMetric], ...] = tuple(
    (f"peak_evolution_matrix_{metric}.csv", metric) for metric in PEAK_METRICS
)


def write_sweep_payload(
    archive: zipfile.ZipFile,
    result: SweepResult,
    metadata: dict[str, ExportFileMeta],
    plot_state: PlotState | SweepExportPlotState | None = None,
    excel_workbook: bytes | None = None,
) -> None:
    metadata["peak_evolution_long.csv"] = write_csv_entry(
        archive, "peak_evolution_long.csv", PEAK_EVOLUTION_V2_FIELDS, peak_evolution_rows(result)
    )
    metadata["spectra_long.csv"] = write_csv_entry(
        archive, "spectra_long.csv", SPECTRA_LONG_V2_FIELDS, spectra_long_rows(result)
    )
    for name, kind in _SPECTRUM_MATRICES:
        metadata[name] = write_csv_entry(
            archive, name, spectrum_matrix_fields(result), spectrum_matrix_rows(result, kind)
        )
    metadata["sweep_steps.csv"] = write_csv_entry(
        archive, "sweep_steps.csv", SWEEP_STEPS_FIELDS, sweep_step_rows(result)
    )
    metadata["series_map.csv"] = write_csv_entry(
        archive, "series_map.csv", SERIES_MAP_FIELDS, series_map_rows(result)
    )
    for name, metric in _PEAK_MATRICES:
        metadata[name] = write_csv_entry(
            archive, name, peak_matrix_fields(result), peak_matrix_rows(result, metric)
        )
    metadata["analysis.xlsx"] = write_binary_entry(
        archive,
        "analysis.xlsx",
        build_sweep_excel_workbook(result) if excel_workbook is None else excel_workbook,
    )
    metadata["config.json"] = write_text_entry(
        archive, "config.json", sweep_config_json(result)
    )
    metadata["README.md"] = write_text_entry(archive, "README.md", sweep_readme())
    metadata["plot_state.json"] = write_text_entry(
        archive, "plot_state.json", plot_state_json(result.base_config, plot_state)
    )
    metadata["origin_column_map.csv"] = write_csv_entry(
        archive,
        "origin_column_map.csv",
        ORIGIN_COLUMN_MAP_FIELDS,
        sweep_origin_rows(result),
    )
    metadata["origin_import.py"] = write_text_entry(
        archive, "origin_import.py", origin_import_script()
    )
    metadata["ORIGIN_README.md"] = write_text_entry(
        archive, "ORIGIN_README.md", origin_readme()
    )


def prepare_sweep_export(
    result: SweepResult,
    plot_state: PlotState | SweepExportPlotState | None = None,
) -> PreparedExport:
    path = create_export_path()
    digest = sweep_hash(result)
    metadata: dict[str, ExportFileMeta] = {}
    with open_deterministic_zip(path) as archive:
        write_sweep_payload(archive, result, metadata, plot_state)
        write_text_entry(
            archive,
            "manifest.json",
            manifest_json(digest, metadata, result.base_config, "sweep"),
        )
    return finalize_export(path, digest)


def build_sweep_zip(result: SweepResult) -> bytes:
    prepared = prepare_sweep_export(result)
    try:
        return Path(prepared.path).read_bytes()
    finally:
        cleanup_export(prepared)
