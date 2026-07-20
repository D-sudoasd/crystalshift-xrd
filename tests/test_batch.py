import csv
import io
import json
import zipfile
from dataclasses import replace

import pytest

from orthoxrd.batch import SweepConfig, generate_sweep
from orthoxrd.export_zip import BATCH_EXPORT_FILES, build_sweep_zip
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.ui_tables import PEAK_EVOLUTION_FIELDS


def _small_config() -> SweepConfig:
    return SweepConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        lines=(RadiationLine("30 keV", 0.4132806614, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=1.0,
        two_theta_max=12.0,
        hkl_max=3,
        include_lorentz_polarization=False,
        include_multiplicity=False,
        include_cell_volume=False,
        profile_kind="gaussian",
        fwhm_deg=0.05,
        pseudo_voigt_eta=0.5,
        spectrum_points=101,
        sweep_axis="y",
        sweep_start=0.214,
        sweep_stop=0.216,
        sweep_step=0.001,
    )


def test_sweep_includes_stop_and_keeps_positions_for_y_scan() -> None:
    result = generate_sweep(_small_config())
    assert [step.step.y for step in result.steps] == pytest.approx([0.214, 0.215, 0.216])

    first_020 = next(
        peak.reflection for peak in result.steps[0].peaks if peak.reflection.hkl_label == "020"
    )
    last_020 = next(
        peak.reflection for peak in result.steps[-1].peaks if peak.reflection.hkl_label == "020"
    )
    assert first_020.two_theta_deg == pytest.approx(last_020.two_theta_deg)
    assert first_020.structure_factor_squared != pytest.approx(last_020.structure_factor_squared)


def test_shuffle_sweep_uses_default_ti_nb_branch() -> None:
    config = _small_config().with_sweep(axis="shuffle", start=0.0, stop=0.004, step=0.002)
    result = generate_sweep(config)
    assert [step.step.y for step in result.steps] == pytest.approx([0.25, 0.249, 0.248])


def test_zip_export_contains_stable_files_and_manifest() -> None:
    result = generate_sweep(_small_config())
    package = build_sweep_zip(result)

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert set(archive.namelist()) == set(BATCH_EXPORT_FILES)
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        assert manifest["model"] == "orthorhombic alpha-double-prime Cmcm 4c"
        assert manifest["normalization"]["local"] == "each sweep step scaled to max 100"

        with archive.open("peak_evolution_long.csv") as file:
            rows = list(csv.DictReader(io.TextIOWrapper(file, encoding="utf-8")))
        assert rows
        assert {
            "sweep_index",
            "sweep_axis",
            "y",
            "shuffle_signed",
            "shuffle_magnitude",
            "normalized_shuffle",
            "hkl",
            "two_theta_deg",
            "I_rel_local",
            "I_rel_global",
        } <= set(rows[0])
        for row in rows:
            magnitude = float(row["shuffle_magnitude"])
            assert float(row["normalized_shuffle"]) == pytest.approx(magnitude / 0.5)


def test_zip_export_keeps_peak_headers_when_no_reflections_are_in_range() -> None:
    config = replace(_small_config(), two_theta_min=1.0, two_theta_max=2.0)
    result = generate_sweep(config)
    package = build_sweep_zip(result)

    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        csv_text = archive.read("peak_evolution_long.csv").decode("utf-8")

    reader = csv.DictReader(io.StringIO(csv_text))
    assert reader.fieldnames[: len(PEAK_EVOLUTION_FIELDS)] == list(PEAK_EVOLUTION_FIELDS)
    assert list(reader) == []
