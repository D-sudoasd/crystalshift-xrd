from __future__ import annotations

import json
from pathlib import Path

from orthoxrd.config import config_hash, config_payload
from orthoxrd.export_excel_packages import build_current_excel_workbook
from orthoxrd.export_manifest import current_readme, manifest_json
from orthoxrd.export_origin import (
    ORIGIN_COLUMN_MAP_FIELDS,
    current_origin_rows,
    origin_import_script,
    origin_readme,
    plot_state_json,
)
from orthoxrd.export_rows import current_peak_rows, current_spectrum_rows
from orthoxrd.export_schema import CURRENT_PEAK_FIELDS, CURRENT_SPECTRUM_FIELDS
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
from orthoxrd.simulation import SimulationResult
from orthoxrd.ui_plot_state import PlotState

CURRENT_EXPORT_FILES = (
    "spectrum.csv",
    "peaks.csv",
    "analysis.xlsx",
    "config.json",
    "README.md",
    "plot_state.json",
    "origin_column_map.csv",
    "origin_import.py",
    "ORIGIN_README.md",
    "manifest.json",
)


def prepare_current_export(
    result: SimulationResult,
    plot_state: PlotState | None = None,
) -> PreparedExport:
    path = create_export_path()
    digest = config_hash(result.config)
    metadata: dict[str, ExportFileMeta] = {}
    with open_deterministic_zip(path) as archive:
        metadata["spectrum.csv"] = write_csv_entry(
            archive, "spectrum.csv", CURRENT_SPECTRUM_FIELDS, current_spectrum_rows(result)
        )
        metadata["peaks.csv"] = write_csv_entry(
            archive, "peaks.csv", CURRENT_PEAK_FIELDS, current_peak_rows(result)
        )
        metadata["analysis.xlsx"] = write_binary_entry(
            archive,
            "analysis.xlsx",
            build_current_excel_workbook(result),
        )
        metadata["config.json"] = write_text_entry(
            archive,
            "config.json",
            json.dumps(config_payload(result.config), indent=2, sort_keys=True) + "\n",
        )
        metadata["README.md"] = write_text_entry(archive, "README.md", current_readme())
        metadata["plot_state.json"] = write_text_entry(
            archive, "plot_state.json", plot_state_json(result.config, plot_state)
        )
        metadata["origin_column_map.csv"] = write_csv_entry(
            archive,
            "origin_column_map.csv",
            ORIGIN_COLUMN_MAP_FIELDS,
            current_origin_rows(),
        )
        metadata["origin_import.py"] = write_text_entry(
            archive, "origin_import.py", origin_import_script()
        )
        metadata["ORIGIN_README.md"] = write_text_entry(
            archive, "ORIGIN_README.md", origin_readme()
        )
        write_text_entry(
            archive,
            "manifest.json",
            manifest_json(digest, metadata, result.config, "current"),
        )
    return finalize_export(path, digest)


def build_current_zip(result: SimulationResult) -> bytes:
    prepared = prepare_current_export(result)
    try:
        return Path(prepared.path).read_bytes()
    finally:
        cleanup_export(prepared)
