from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from orthoxrd.batch import SweepConfig, generate_sweep
from orthoxrd.config import SimulationConfig
from orthoxrd.export_fit_rows import (
    BEST_POINT_FIELDS,
    GRID_SCAN_FIELDS,
    LOCAL_MINIMA_FIELDS,
    OBSERVATION_EXPORT_FIELDS,
    REFINE_TRACE_FIELDS,
    RESIDUAL_AT_BEST_FIELDS,
)
from orthoxrd.export_fit_zip import (
    FIT_EXPORT_FILES,
    build_fit_zip,
    fit_export_hash,
    prepare_fit_export,
)
from orthoxrd.export_writer import cleanup_export
from orthoxrd.export_zip import (
    BATCH_EXPORT_FILES,
    CURRENT_EXPORT_FILES,
    build_current_zip,
    build_sweep_zip,
)
from orthoxrd.fit import run_discrete_peak_fit
from orthoxrd.fit_models import FitOptions, PeakObservation
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.powder import calculate_reflections
from orthoxrd.simulation import calculate_simulation
from tests.xlsx_assertions import xlsx_sheet_cells, xlsx_sheet_names


def _config() -> SimulationConfig:
    return SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.25,
        lines=(RadiationLine("Cu Ka1", 1.5406, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=5.0,
        two_theta_max=80.0,
        hkl_max=4,
        min_peak=0.0,
        profile_kind="gaussian",
        fwhm_deg=0.1,
        pseudo_voigt_eta=0.5,
        spectrum_points=100,
        include_lorentz_polarization=True,
        include_multiplicity=True,
        include_cell_volume=False,
    )


def _model_i(config: SimulationConfig, h: int, k: int, l: int, y: float) -> float:
    line = config.lines[0]
    reflections = calculate_reflections(
        lattice=config.lattice,
        y=y,
        wavelength_a=line.wavelength_a,
        two_theta_min=config.two_theta_min,
        two_theta_max=config.two_theta_max,
        hkl_max=config.hkl_max,
        scattering_mode=config.scattering_mode,
        composition=config.composition,
        include_lorentz_polarization=config.include_lorentz_polarization,
        include_multiplicity=config.include_multiplicity,
        include_cell_volume=config.include_cell_volume,
    )
    peak = next(row for row in reflections if (row.h, row.k, row.l) == (h, k, l))
    return peak.intensity_model * line.weight


def _fit_result():
    truth_y = 0.22
    truth_s = 2.5
    config = _config()
    hkls = [(1, 1, 0), (0, 2, 0), (0, 0, 2), (1, 1, 1), (0, 2, 1)]
    observations = tuple(
        PeakObservation(
            h=h,
            k=k,
            l=l,
            I_obs=truth_s * _model_i(config, h, k, l, truth_y),
            row=index,
        )
        for index, (h, k, l) in enumerate(hkls, start=2)
    )
    options = FitOptions(
        observable_mode="peak_area",
        weight_mode="poisson",
        y_start=0.0,
        y_stop=0.5,
        grid_points=51,
        refine=True,
    )
    return run_discrete_peak_fit(config, observations, options)


def test_fit_export_modules_import_without_streamlit() -> None:
    import orthoxrd.export_fit_rows as rows_mod
    import orthoxrd.export_fit_zip as zip_mod

    for mod in (rows_mod, zip_mod):
        tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "streamlit"
                    assert not alias.name.startswith("streamlit.")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module != "streamlit"
                assert not module.startswith("streamlit.")


def test_prepare_fit_export_members_and_key_columns() -> None:
    result = _fit_result()
    package = build_fit_zip(result)

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        names = set(archive.namelist())
        assert names == set(FIT_EXPORT_FILES)

        observations = list(
            csv.DictReader(io.StringIO(archive.read("observations.csv").decode("utf-8")))
        )
        grid = list(csv.DictReader(io.StringIO(archive.read("grid_scan.csv").decode("utf-8"))))
        refine = list(
            csv.DictReader(io.StringIO(archive.read("refine_trace.csv").decode("utf-8")))
        )
        best_point = list(
            csv.DictReader(io.StringIO(archive.read("best_point.csv").decode("utf-8")))
        )
        residuals = list(
            csv.DictReader(io.StringIO(archive.read("residual_at_best.csv").decode("utf-8")))
        )
        minima = list(
            csv.DictReader(io.StringIO(archive.read("local_minima.csv").decode("utf-8")))
        )
        best_fit = json.loads(archive.read("best_fit.json"))
        config_payload = json.loads(archive.read("config.json"))
        manifest = json.loads(archive.read("manifest.json"))
        diagnostics_payload = json.loads(archive.read("fit_diagnostics.json"))
        workbook = archive.read("analysis.xlsx")
        readme = archive.read("README.md").decode("utf-8")

        # Headers stay stable (order matters for tooling).
        obs_header = next(
            csv.reader(io.StringIO(archive.read("observations.csv").decode("utf-8")))
        )
        grid_header = next(
            csv.reader(io.StringIO(archive.read("grid_scan.csv").decode("utf-8")))
        )
        residual_header = next(
            csv.reader(io.StringIO(archive.read("residual_at_best.csv").decode("utf-8")))
        )
        refine_header = next(
            csv.reader(io.StringIO(archive.read("refine_trace.csv").decode("utf-8")))
        )
        best_header = next(
            csv.reader(io.StringIO(archive.read("best_point.csv").decode("utf-8")))
        )
        minima_header = next(
            csv.reader(io.StringIO(archive.read("local_minima.csv").decode("utf-8")))
        )

    assert obs_header == list(OBSERVATION_EXPORT_FIELDS)
    assert grid_header == list(GRID_SCAN_FIELDS)
    assert refine_header == list(REFINE_TRACE_FIELDS)
    assert best_header == list(BEST_POINT_FIELDS)
    assert residual_header == list(RESIDUAL_AT_BEST_FIELDS)
    assert minima_header == list(LOCAL_MINIMA_FIELDS)
    assert GRID_SCAN_FIELDS == (
        "y",
        "scale_s",
        "chi2",
        "shuffle_signed",
        "shuffle_magnitude",
        "normalized_shuffle",
        "branch",
    )
    assert REFINE_TRACE_FIELDS == (
        "evaluation",
        "y",
        "scale_s",
        "chi2",
        "shuffle_signed",
        "shuffle_magnitude",
        "normalized_shuffle",
        "branch",
    )
    assert LOCAL_MINIMA_FIELDS == (
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

    assert observations
    assert {
        "h",
        "k",
        "l",
        "I_obs",
        "series_id",
        "included",
        "input_weight",
        "resolved_weight",
    } <= set(observations[0])
    assert "weight" not in observations[0]  # renamed to avoid input/resolved clash
    assert len(grid) == result.options.grid_points
    assert {
        "y",
        "scale_s",
        "chi2",
        "shuffle_signed",
        "shuffle_magnitude",
        "normalized_shuffle",
        "branch",
    } <= set(grid[0])
    assert float(grid[0]["y"]) == 0.0
    assert float(grid[0]["shuffle_signed"]) == -0.5
    assert float(grid[0]["shuffle_magnitude"]) == 0.5
    assert float(grid[0]["normalized_shuffle"]) == 1.0
    assert grid[0]["branch"] == "lower"
    assert float(grid[25]["y"]) == 0.25
    assert float(grid[25]["shuffle_signed"]) == 0.0
    assert float(grid[25]["shuffle_magnitude"]) == 0.0
    assert float(grid[25]["normalized_shuffle"]) == 0.0
    assert grid[25]["branch"] == "reference"
    assert float(grid[-1]["y"]) == 0.5
    assert float(grid[-1]["shuffle_signed"]) == 0.5
    assert float(grid[-1]["shuffle_magnitude"]) == 0.5
    assert float(grid[-1]["normalized_shuffle"]) == 1.0
    assert grid[-1]["branch"] == "upper"
    assert refine
    assert {
        "shuffle_signed",
        "shuffle_magnitude",
        "normalized_shuffle",
        "branch",
    } <= set(refine[0])
    for process_rows in (grid, refine, minima):
        for row in process_rows:
            y_value = float(row["y"])
            signed = float(row["shuffle_signed"])
            magnitude = float(row["shuffle_magnitude"])
            assert signed == pytest.approx(2.0 * (y_value - 0.25))
            assert magnitude == pytest.approx(abs(signed))
            assert float(row["normalized_shuffle"]) == pytest.approx(magnitude / 0.5)
            expected_branch = (
                "lower" if y_value < 0.25 else "upper" if y_value > 0.25 else "reference"
            )
            assert row["branch"] == expected_branch
    assert best_point and best_point[0]["source"] in {"grid", "refine"}
    assert residuals
    assert {"I_obs", "I_model", "S_I_model", "residual", "weight"} <= set(residuals[0])
    assert minima  # synthetic unimodal surface still has at least one candidate
    assert all(row["refine_status"] == "refined" for row in minima)
    assert {"refined_y", "refined_scale_s", "refined_chi2", "delta_chi2"} <= set(minima[0])

    assert "y" in best_fit and "scale_s" in best_fit and "chi2" in best_fit
    assert config_payload["fit"]["observable_mode"] == "peak_area"
    assert config_payload["fit"]["weight_mode"] == "poisson"
    assert config_payload["fit"]["y_start"] == 0.0
    assert config_payload["fit"]["y_stop"] == 0.5
    assert config_payload["fit"]["grid_points"] == 51
    assert "exclusions" in config_payload["fit"]
    assert "simulation" in config_payload
    assert "best" in config_payload
    assert "notes" in config_payload
    assert "simulation_wyckoff_y" in config_payload["notes"]
    assert "best.y" in config_payload["notes"]["simulation_wyckoff_y"]
    assert config_payload["fit"]["profile_delta_chi2"] == 1.0
    assert config_payload["fit"]["identifiability"]["heuristic"] is True
    assert config_payload["fit"]["free_parameters"] == ["y", "scale_s"]
    assert "resolved_weight" in config_payload["notes"]["observations_weight_columns"]
    assert "resolved_weight" in readme.lower() or "resolved weight" in readme.lower()

    assert manifest["export_kind"] == "fit"
    assert manifest["schema_version"] == "2.4"
    assert manifest["generated_at_utc"] is None
    assert manifest["deterministic"] is True
    assert manifest["config_hash"] == fit_export_hash(result)
    assert "not" in readme.lower() and "rietveld" in readme.lower()
    # Fit manifests drop sweep-centric legacy fields and note non-Rietveld limits.
    assert "legacy_peak_fields" not in manifest["compatibility"]
    assert "legacy_spectra_fields" not in manifest["compatibility"]
    assert manifest["compatibility"]["method"] == "discrete_peak_intensity_fit"
    assert any("rietveld" in item.lower() for item in manifest["limits"])
    assert "objective" in manifest["intensity"]
    assert "I_rel_local" not in manifest["intensity"]
    assert "analysis.xlsx" in manifest["files"]
    assert diagnostics_payload["method"] == "profile_delta_chi2"
    assert diagnostics_payload["heuristic"] is True
    assert diagnostics_payload["status"] == "multi_modal"
    assert xlsx_sheet_names(workbook) == [
        "README",
        "Parameters",
        "Columns",
        "Observations",
        "GridScan",
        "RefineTrace",
        "BestPoint",
        "Residuals",
        "LocalMinima",
    ]
    grid_cells = xlsx_sheet_cells(workbook, "GridScan")
    assert grid_cells["A1"] == ("text", "y")
    assert grid_cells["D1"] == ("text", "shuffle_signed")
    assert grid_cells["E1"] == ("text", "shuffle_magnitude")
    assert grid_cells["F1"] == ("text", "normalized_shuffle")
    assert grid_cells["G1"] == ("text", "branch")
    assert grid_cells["D2"] == ("number", "-0.5")
    assert grid_cells["E2"] == ("number", "0.5")
    assert grid_cells["F2"] == ("number", "1")
    assert grid_cells["G2"] == ("text", "lower")
    assert grid_cells["G27"] == ("text", "reference")

    column_cells = xlsx_sheet_cells(workbook, "Columns")
    metadata_rows = {
        (column_cells[f"A{row}"][1], column_cells[f"B{row}"][1]): (
            column_cells[f"C{row}"][1],
            column_cells[f"D{row}"][1],
            column_cells[f"E{row}"][1],
        )
        for row in range(2, 500)
        if f"A{row}" in column_cells
    }
    for sheet_name in ("GridScan", "RefineTrace", "LocalMinima"):
        assert metadata_rows[(sheet_name, "shuffle_signed")] == (
            "number",
            "fractional",
            "Signed basal shuffle, 2*(y-0.25).",
        )
        assert metadata_rows[(sheet_name, "shuffle_magnitude")] == (
            "number",
            "fractional",
            "Basal-shuffle magnitude, abs(shuffle_signed).",
        )
        assert metadata_rows[(sheet_name, "normalized_shuffle")] == (
            "number",
            "1",
            "Normalized basal-shuffle magnitude |s|/0.5, range [0,1].",
        )
        assert metadata_rows[(sheet_name, "branch")] == (
            "text",
            "",
            "Shuffle-magnitude branch: lower, upper, or zero-shuffle reference.",
        )

    # No full residual cube for every grid y.
    residual_names = [name for name in names if "residual" in name]
    assert residual_names == ["residual_at_best.csv"]


def test_fit_zip_is_byte_deterministic_for_same_result() -> None:
    result = _fit_result()
    assert build_fit_zip(result) == build_fit_zip(result)


def test_fit_manifest_checksums_match_members() -> None:
    result = _fit_result()
    package = build_fit_zip(result)

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        for name, metadata in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == metadata["sha256"]
            assert metadata["rows"] >= 0
            assert metadata["columns"] >= 1


def test_prepared_fit_export_is_file_backed() -> None:
    prepared = prepare_fit_export(_fit_result())
    assert Path(prepared.path).is_file()
    assert prepared.size_bytes > 0
    assert len(prepared.sha256) == 64
    assert len(prepared.config_hash) == 64
    cleanup_export(prepared)
    assert not Path(prepared.path).exists()


def test_legacy_current_and_sweep_export_contracts_unchanged() -> None:
    current = build_current_zip(calculate_simulation(_config()))
    with zipfile.ZipFile(io.BytesIO(current)) as archive:
        assert set(archive.namelist()) == set(CURRENT_EXPORT_FILES)
        current_manifest = json.loads(archive.read("manifest.json"))
        assert "legacy_peak_fields" in current_manifest["compatibility"]
        assert "I_rel_local" in current_manifest["intensity"]

    base = _config()
    sweep = generate_sweep(
        SweepConfig.from_simulation(base, axis="y", start=0.22, stop=0.23, step=0.01)
    )
    batch = build_sweep_zip(sweep)
    with zipfile.ZipFile(io.BytesIO(batch)) as archive:
        assert set(archive.namelist()) == set(BATCH_EXPORT_FILES)
        sweep_manifest = json.loads(archive.read("manifest.json"))
        assert "legacy_peak_fields" in sweep_manifest["compatibility"]
        assert "legacy_spectra_fields" in sweep_manifest["compatibility"]
