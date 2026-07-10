from dataclasses import replace

import numpy as np
import pytest

from orthoxrd.config import SimulationConfig
from orthoxrd.live import (
    LivePreviewConfig,
    LivePreviewError,
    config_for_live_value,
    generate_live_preview,
    live_signature,
)
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.simulation import calculate_simulation


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


def test_live_frames_equal_single_simulation_when_scanning_y() -> None:
    base = _config()
    config = LivePreviewConfig(
        base=base,
        axis="y",
        start=0.221,
        stop=0.223,
        step=0.001,
        preview_points=101,
    )

    result = generate_live_preview(config)

    assert result.axis_values.tolist() == pytest.approx([0.221, 0.222, 0.223])
    for index, value in enumerate(result.axis_values):
        expected = calculate_simulation(config_for_live_value(config, float(value)))
        np.testing.assert_allclose(
            result.intensity_model[index],
            expected.spectrum.intensity_model,
            rtol=1e-12,
            atol=1e-12,
        )


def test_live_grid_includes_exact_baseline_when_step_does_not_land_on_it() -> None:
    base = _config()
    config = LivePreviewConfig(
        base=base,
        axis="a_A",
        start=3.20,
        stop=3.24,
        step=0.01,
        preview_points=101,
    )

    result = generate_live_preview(config)

    assert result.axis_values[result.baseline_index] == pytest.approx(base.lattice.a)
    assert len(result.axis_values) == 6


def test_live_signature_ignores_active_value_but_tracks_other_inputs() -> None:
    base = _config()
    first = LivePreviewConfig(base=base, axis="a_A", start=3.1, stop=3.3, step=0.01)
    active_changed = replace(
        first,
        base=replace(base, lattice=LatticeParameters(3.25, base.lattice.b, base.lattice.c)),
    )
    other_changed = replace(
        first,
        base=replace(base, lattice=LatticeParameters(base.lattice.a, 4.8, base.lattice.c)),
    )

    assert live_signature(first) == live_signature(active_changed)
    assert live_signature(first) != live_signature(other_changed)


def test_live_preview_rejects_frame_and_cell_limits() -> None:
    base = _config()
    too_many_frames = LivePreviewConfig(
        base=base,
        axis="y",
        start=0.0,
        stop=0.5,
        step=0.001,
    )
    too_many_cells = LivePreviewConfig(
        base=base,
        axis="y",
        start=0.0,
        stop=0.4,
        step=0.001,
        preview_points=2000,
    )

    with pytest.raises(LivePreviewError, match="401-frame"):
        generate_live_preview(too_many_frames)
    with pytest.raises(LivePreviewError, match="800,000-cell"):
        generate_live_preview(too_many_cells)


def test_energy_live_frame_changes_two_theta_but_preserves_d_spacing() -> None:
    base = _config()
    config = LivePreviewConfig(base=base, axis="energy_keV", start=25, stop=35, step=5)
    low = calculate_simulation(config_for_live_value(config, 25.0))
    high = calculate_simulation(config_for_live_value(config, 35.0))
    low_by_hkl = {peak.reflection.hkl_id: peak.reflection for peak in low.peaks}
    high_by_hkl = {peak.reflection.hkl_id: peak.reflection for peak in high.peaks}
    shared = sorted(set(low_by_hkl) & set(high_by_hkl))

    assert shared
    reflection_id = shared[0]
    assert low_by_hkl[reflection_id].two_theta_deg != pytest.approx(
        high_by_hkl[reflection_id].two_theta_deg
    )
    assert low_by_hkl[reflection_id].d_spacing_a == pytest.approx(
        high_by_hkl[reflection_id].d_spacing_a
    )


def test_live_energy_scan_preserves_multiline_source_and_exact_baseline() -> None:
    base = replace(
        _config(),
        lines=(
            RadiationLine("K-alpha1", 0.4132806614, 2.0),
            RadiationLine("K-alpha2", 0.4148000000, 1.0),
        ),
    )
    config = LivePreviewConfig(
        base=base,
        axis="energy_keV",
        start=29.0,
        stop=31.0,
        step=1.0,
        preview_points=101,
    )

    preview = generate_live_preview(config)
    baseline = calculate_simulation(replace(base, spectrum_points=101))
    frame_config = config_for_live_value(
        config,
        float(preview.axis_values[preview.baseline_index]),
    )

    np.testing.assert_allclose(
        preview.intensity_model[preview.baseline_index],
        baseline.spectrum.intensity_model,
        rtol=1e-12,
        atol=1e-12,
    )
    assert len(frame_config.lines) == 2
    assert [line.weight for line in frame_config.lines] == pytest.approx([2.0, 1.0])
    assert (
        frame_config.lines[1].wavelength_a / frame_config.lines[0].wavelength_a
        == pytest.approx(base.lines[1].wavelength_a / base.lines[0].wavelength_a)
    )


def test_live_energy_signature_tracks_secondary_line_contract() -> None:
    base = replace(
        _config(),
        lines=(
            RadiationLine("primary", 0.4132806614, 2.0),
            RadiationLine("secondary", 0.4148, 1.0),
        ),
    )
    config = LivePreviewConfig(
        base=base,
        axis="energy_keV",
        start=29.0,
        stop=31.0,
        step=1.0,
        preview_points=101,
    )
    changed_weight = replace(
        config,
        base=replace(
            base,
            lines=(base.lines[0], replace(base.lines[1], weight=0.5)),
        ),
    )
    scaled_source = replace(
        config,
        base=replace(
            base,
            lines=tuple(
                replace(line, wavelength_a=line.wavelength_a * 1.1)
                for line in base.lines
            ),
        ),
    )
    renamed_source = replace(
        config,
        base=replace(
            base,
            lines=(
                replace(base.lines[0], label="31 keV primary"),
                replace(base.lines[1], label="31 keV secondary"),
            ),
        ),
    )

    assert live_signature(changed_weight) != live_signature(config)
    assert live_signature(scaled_source) == live_signature(config)
    assert live_signature(renamed_source) == live_signature(config)
