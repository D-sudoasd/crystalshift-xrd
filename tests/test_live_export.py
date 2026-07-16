import csv
import hashlib
import io
import json
import zipfile

from orthoxrd.config import SimulationConfig
from orthoxrd.export_live import (
    LIVE_EXPORT_FILES,
    build_live_zip,
    prepare_live_export,
)
from orthoxrd.export_writer import cleanup_export
from orthoxrd.live import LivePreviewConfig, generate_live_preview
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.ui_plot_state import PlotState
from tests.xlsx_assertions import xlsx_sheet_names


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


def test_live_export_contains_float64_analysis_tables_and_frame_comparison() -> None:
    preview = generate_live_preview(
        LivePreviewConfig(
            base=_config(),
            axis="energy_keV",
            start=29.0,
            stop=31.0,
            step=1.0,
            preview_points=101,
        )
    )
    package = build_live_zip(preview, current_index=0)

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert set(archive.namelist()) == set(LIVE_EXPORT_FILES)
        manifest = json.loads(archive.read("manifest.json"))
        workbook = archive.read("analysis.xlsx")
        comparison = list(
            csv.DictReader(
                io.StringIO(
                    archive.read("baseline_current_comparison.csv").decode("utf-8")
                )
            )
        )
        live_state = json.loads(archive.read("live_state.json"))

    assert manifest["schema_version"] == "2.2"
    assert manifest["export_kind"] == "live"
    assert "analysis.xlsx" in manifest["files"]
    assert hashlib.sha256(workbook).hexdigest() == manifest["files"]["analysis.xlsx"][
        "sha256"
    ]
    assert {
        "README",
        "Parameters",
        "Columns",
        "SweepSteps",
        "FrameComparison",
    } <= set(xlsx_sheet_names(workbook))
    assert len(comparison) == 101
    assert live_state["baseline_index"] != live_state["current_index"]
    assert comparison[20]["baseline_q_A_inv"] != comparison[20]["current_q_A_inv"]
    assert comparison[20]["baseline_d_A"] != comparison[20]["current_d_A"]


def test_live_export_hash_includes_plot_state() -> None:
    preview = generate_live_preview(
        LivePreviewConfig(
            base=_config(),
            axis="y",
            start=0.221,
            stop=0.223,
            step=0.001,
            preview_points=101,
        )
    )
    first = prepare_live_export(
        preview,
        current_index=0,
        plot_state=PlotState("2theta", 1.0, 8.0, True, 0.0, 100.0),
    )
    second = prepare_live_export(
        preview,
        current_index=0,
        plot_state=PlotState("2theta", 2.0, 9.0, True, 0.0, 100.0),
    )
    try:
        with zipfile.ZipFile(first.path) as archive:
            first_manifest = json.loads(archive.read("manifest.json"))
        with zipfile.ZipFile(second.path) as archive:
            second_manifest = json.loads(archive.read("manifest.json"))

        assert first.config_hash != second.config_hash
        assert first_manifest["config_hash"] != second_manifest["config_hash"]
    finally:
        cleanup_export(first)
        cleanup_export(second)
