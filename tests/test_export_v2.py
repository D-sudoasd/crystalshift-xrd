import csv
import hashlib
import io
import json
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest

from orthoxrd.batch import SweepConfig, generate_sweep
from orthoxrd.config import SimulationConfig
from orthoxrd.export_rows import current_peak_rows
from orthoxrd.export_zip import (
    BATCH_EXPORT_FILES,
    CURRENT_EXPORT_FILES,
    build_current_zip,
    build_sweep_zip,
    cleanup_export,
    prepare_sweep_export,
)
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.simulation import calculate_simulation
from orthoxrd.ui_tables import PEAK_EVOLUTION_FIELDS, SPECTRA_LONG_FIELDS
from tests.xlsx_assertions import xlsx_sheet_cells, xlsx_sheet_names, xlsx_sheet_xml


def _config() -> SimulationConfig:
    return SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.222,
        lines=(RadiationLine("30 keV", 0.4132806614, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=1.0,
        two_theta_max=12.0,
        hkl_max=3,
        min_peak=0.0,
        profile_kind="gaussian",
        fwhm_deg=0.05,
        pseudo_voigt_eta=0.5,
        spectrum_points=101,
        include_lorentz_polarization=False,
        include_multiplicity=False,
        include_cell_volume=False,
    )


def _sweep():
    base = _config()
    return generate_sweep(
        SweepConfig.from_simulation(
            base,
            axis="y",
            start=0.221,
            stop=0.222,
            step=0.001,
        )
    )


def test_current_simulation_zip_has_analysis_ready_contract() -> None:
    package = build_current_zip(calculate_simulation(_config()))

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert set(archive.namelist()) == set(CURRENT_EXPORT_FILES)
        manifest = json.loads(archive.read("manifest.json"))
        workbook = archive.read("analysis.xlsx")
        assert manifest["schema_version"] == "2.3"
        assert manifest["generated_at_utc"] is None
        assert manifest["deterministic"] is True
        assert {
            "plot_state.json", "origin_column_map.csv", "origin_import.py", "ORIGIN_README.md"
        } <= set(archive.namelist())
        assert manifest["intensity"]["I_model_peak"].startswith("F²")
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
        spectrum = list(csv.DictReader(io.StringIO(archive.read("spectrum.csv").decode("utf-8"))))
        peaks = list(csv.DictReader(io.StringIO(archive.read("peaks.csv").decode("utf-8"))))

    assert spectrum
    assert {"q_primary_A_inv", "d_primary_A", "intensity_model"} <= set(spectrum[0])
    assert peaks
    assert "analysis.xlsx" in manifest["files"]
    assert hashlib.sha256(workbook).hexdigest() == manifest["files"]["analysis.xlsx"][
        "sha256"
    ]
    assert xlsx_sheet_names(workbook) == [
        "README",
        "Parameters",
        "Columns",
        "Spectrum",
        "Peaks",
    ]
    peaks_xml = xlsx_sheet_xml(workbook, "Peaks")
    assert b't="inlineStr"' in peaks_xml
    assert b"<t>021</t>" in peaks_xml
    column_cells = xlsx_sheet_cells(workbook, "Columns")
    peak_units = {
        column_cells[f"B{row}"][1]: column_cells[f"D{row}"][1]
        for row in range(2, 500)
        if column_cells.get(f"A{row}") == ("text", "Peaks")
    }
    assert peak_units["material_scattering_factor_R_hkl"] == (
        "model structure-factor units * angstrom^-6"
    )
    assert peak_units["inverse_material_scattering_factor_1_over_R_hkl"] == (
        "inverse model structure-factor units * angstrom^6"
    )
    assert {
        "F_real",
        "F_imag",
        "I_model_peak",
        "series_id",
        "y",
        "F_abs",
        "multiplicity_structure_factor_sq",
        "theoretical_intensity_unscaled",
        "material_scattering_factor_R_hkl",
        "material_scattering_factor_R_hkl_no_lp",
        "inverse_material_scattering_factor_1_over_R_hkl",
        "inverse_material_scattering_factor_1_over_R_hkl_no_lp",
    } <= set(peaks[0])
    peak = peaks[0]
    volume = float(peak["cell_volume_A3"])
    n_f2 = float(peak["multiplicity_structure_factor_sq"])
    unscaled = float(peak["theoretical_intensity_unscaled"])
    assert float(peak["material_scattering_factor_R_hkl"]) == pytest.approx(
        unscaled / volume**2
    )
    assert float(peak["material_scattering_factor_R_hkl_no_lp"]) == pytest.approx(
        n_f2 / volume**2
    )


def test_current_r_factor_percentages_are_bounded_and_zero_safe() -> None:
    result = calculate_simulation(_config())
    rows = list(current_peak_rows(result))

    for field in ("phase_relative_R_hkl_pct", "phase_relative_R_hkl_no_lp_pct"):
        values = [float(row[field]) for row in rows]
        assert min(values) >= 0.0
        assert max(values) == pytest.approx(100.0)

    extinct = replace(
        result,
        peaks=tuple(
            replace(
                peak,
                reflection=replace(peak.reflection, structure_factor_squared=0.0),
            )
            for peak in result.peaks
        ),
    )
    extinct_rows = list(current_peak_rows(extinct))

    assert extinct_rows
    assert all(float(row["phase_relative_R_hkl_pct"]) == 0.0 for row in extinct_rows)
    assert all(
        float(row["phase_relative_R_hkl_no_lp_pct"]) == 0.0 for row in extinct_rows
    )


def test_current_r_factor_percentages_are_normalized_per_radiation_line() -> None:
    config = replace(
        _config(),
        lines=(
            RadiationLine("short", 0.4, 1.0),
            RadiationLine("long", 1.0, 1.0),
        ),
        two_theta_max=120.0,
        include_lorentz_polarization=True,
    )
    rows = list(current_peak_rows(calculate_simulation(config)))

    for line_id in ("line_00", "line_01"):
        line_rows = [row for row in rows if row["line_id"] == line_id]
        assert line_rows
        assert max(float(row["phase_relative_R_hkl_pct"]) for row in line_rows) == pytest.approx(
            100.0
        )
        assert max(
            float(row["phase_relative_R_hkl_no_lp_pct"]) for row in line_rows
        ) == pytest.approx(100.0)


def test_current_zip_is_byte_deterministic_for_same_result() -> None:
    result = calculate_simulation(_config())
    assert build_current_zip(result) == build_current_zip(result)


def test_batch_zip_preserves_legacy_headers_and_adds_v2_files() -> None:
    package = build_sweep_zip(_sweep())

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert set(archive.namelist()) == set(BATCH_EXPORT_FILES)
        peak_reader = csv.reader(
            io.StringIO(archive.read("peak_evolution_long.csv").decode("utf-8"))
        )
        spectra_reader = csv.reader(io.StringIO(archive.read("spectra_long.csv").decode("utf-8")))
        peak_header = next(peak_reader)
        spectra_header = next(spectra_reader)
        manifest = json.loads(archive.read("manifest.json"))
        workbook = archive.read("analysis.xlsx")

    assert peak_header[: len(PEAK_EVOLUTION_FIELDS)] == list(PEAK_EVOLUTION_FIELDS)
    assert spectra_header[: len(SPECTRA_LONG_FIELDS)] == list(SPECTRA_LONG_FIELDS)
    assert manifest["schema_version"] == "2.3"
    assert manifest["generated_at_utc"] is None
    assert manifest["deterministic"] is True
    assert manifest["compatibility"]["legacy_headers_preserved"] is True
    assert "analysis.xlsx" in manifest["files"]
    assert hashlib.sha256(workbook).hexdigest() == manifest["files"]["analysis.xlsx"][
        "sha256"
    ]
    assert {
        "README",
        "Parameters",
        "Columns",
        "PeakEvolution",
        "SpectrumGlobal",
        "SweepSteps",
        "SeriesMap",
    } <= set(xlsx_sheet_names(workbook))
    columns_xml = xlsx_sheet_xml(workbook, "Columns")
    assert b"Global-relative profile intensity for stable sweep step step_0000." in columns_xml
    assert b"Reference factor N*F2*LP/V_cell^2 for stable series" in columns_xml
    assert b"model structure-factor units * angstrom^-6" in columns_xml


def test_sweep_zip_is_byte_deterministic_for_same_result() -> None:
    result = _sweep()
    assert build_sweep_zip(result) == build_sweep_zip(result)


def test_peak_matrix_step_id_has_identifier_metadata_in_excel() -> None:
    package = build_sweep_zip(_sweep())

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        columns = xlsx_sheet_cells(archive.read("analysis.xlsx"), "Columns")

    row = next(
        index
        for index in range(2, 1000)
        if columns.get(f"A{index}") == ("text", "PeakF2")
        and columns.get(f"B{index}") == ("text", "step_id")
    )
    assert columns[f"C{row}"] == ("text", "text")
    assert columns[f"D{row}"] == ("text", "")
    assert columns[f"E{row}"] == (
        "text",
        "Stable sweep-step identifier; preserve as text.",
    )


def test_sweep_zip_contains_origin_workflow_files() -> None:
    package = build_sweep_zip(_sweep())

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        names = set(archive.namelist())
        column_map = list(
            csv.DictReader(io.StringIO(archive.read("origin_column_map.csv").decode("utf-8")))
        )

    assert {
        "plot_state.json", "origin_column_map.csv", "origin_import.py", "ORIGIN_README.md"
    } <= names
    assert column_map
    assert {"file", "column", "designation", "long_name", "unit", "comment"} == set(
        column_map[0]
    )


def test_batch_manifest_checksums_match_every_non_manifest_file() -> None:
    package = build_sweep_zip(_sweep())

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        for name, metadata in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == metadata["sha256"]
            assert metadata["rows"] >= 0
            assert metadata["columns"] >= 1


def test_peak_evolution_matrices_use_stable_step_and_series_ids() -> None:
    package = build_sweep_zip(_sweep())

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        matrix = list(
            csv.DictReader(
                io.StringIO(archive.read("peak_evolution_matrix_F2.csv").decode("utf-8"))
            )
        )
        series_map = list(
            csv.DictReader(io.StringIO(archive.read("series_map.csv").decode("utf-8")))
        )

    assert [row["step_id"] for row in matrix] == ["step_0000", "step_0001"]
    assert series_map
    assert all(row["series_id"].startswith("line_00__h") for row in series_map)


def test_sweep_zip_exports_unscaled_structure_and_r_factor_matrices() -> None:
    package = build_sweep_zip(_sweep())

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        names = set(archive.namelist())
        long_rows = list(
            csv.DictReader(
                io.StringIO(archive.read("peak_evolution_long.csv").decode("utf-8"))
            )
        )

    assert {
        "peak_evolution_matrix_N_F2.csv",
        "peak_evolution_matrix_R_hkl_with_LP.csv",
        "peak_evolution_matrix_R_hkl_no_LP.csv",
    } <= names
    assert long_rows
    assert {
        "F_abs",
        "multiplicity_structure_factor_sq",
        "theoretical_intensity_unscaled",
        "material_scattering_factor_R_hkl",
        "material_scattering_factor_R_hkl_no_lp",
        "inverse_material_scattering_factor_1_over_R_hkl",
        "inverse_material_scattering_factor_1_over_R_hkl_no_lp",
    } <= set(long_rows[0])


def test_prepared_export_is_file_backed_and_cleanup_is_scoped() -> None:
    prepared = prepare_sweep_export(_sweep())

    assert Path(prepared.path).is_file()
    assert prepared.size_bytes > 0
    assert len(prepared.sha256) == 64

    cleanup_export(prepared)
    assert not Path(prepared.path).exists()


def test_origin_script_compiles_and_map_covers_exported_data_csv() -> None:
    package = build_sweep_zip(_sweep())

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        script = archive.read("origin_import.py").decode("utf-8")
        mapped = {
            row["file"]
            for row in csv.DictReader(
                io.StringIO(archive.read("origin_column_map.csv").decode("utf-8"))
            )
        }
        data_csv = {
            name
            for name in archive.namelist()
            if name.endswith(".csv") and name != "origin_column_map.csv"
        }

    compile(script, "origin_import.py", "exec")
    assert data_csv <= mapped


def test_plot_state_json_records_active_pattern_and_sweep_ranges() -> None:
    from orthoxrd.export_origin import SweepExportPlotState
    from orthoxrd.export_zip import prepare_current_export
    from orthoxrd.ui_plot_state import PlotState

    current = calculate_simulation(_config())
    current_export = prepare_current_export(
        current,
        PlotState("q_primary", 1.5, 4.5, False, 2.0, 80.0),
    )
    sweep_export = prepare_sweep_export(
        _sweep(),
        SweepExportPlotState(2.0, 9.0, 0.2212, 0.2218),
    )
    try:
        with zipfile.ZipFile(current_export.path) as archive:
            current_state = json.loads(archive.read("plot_state.json"))
        with zipfile.ZipFile(sweep_export.path) as archive:
            sweep_state = json.loads(archive.read("plot_state.json"))
    finally:
        cleanup_export(current_export)
        cleanup_export(sweep_export)

    assert current_state["x_axis"] == "q_primary"
    assert current_state["x_minimum"] == 1.5
    assert current_state["y_auto"] is False
    assert current_state["y_maximum"] == 80.0
    assert sweep_state["two_theta_minimum"] == 2.0
    assert sweep_state["two_theta_maximum"] == 9.0
    assert sweep_state["sweep_axis_minimum"] == 0.2212
    assert sweep_state["sweep_axis_maximum"] == 0.2218


def test_origin_script_detects_csv_trajectory_from_exported_step_axis() -> None:
    from orthoxrd.batch import parse_trajectory_csv

    trajectory = parse_trajectory_csv(
        "step_label,a_A,b_A\ninitial,3.200,\nloaded,,4.800\n",
        _config(),
    )
    package = build_sweep_zip(generate_sweep(trajectory))

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        steps = list(
            csv.DictReader(io.StringIO(archive.read("sweep_steps.csv").decode("utf-8")))
        )
        script = archive.read("origin_import.py").decode("utf-8")

    assert steps
    assert {row["sweep_axis"] for row in steps} == {"trajectory"}
    assert 'row.get("sweep_axis") == "trajectory"' in script
