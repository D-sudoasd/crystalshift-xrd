import pytest

from orthoxrd.batch import (
    SweepAxis,
    SweepConfig,
    TrajectoryValidationError,
    generate_sweep,
    parse_trajectory_csv,
)
from orthoxrd.config import SimulationConfig
from orthoxrd.models import LatticeParameters, RadiationLine


def _base() -> SimulationConfig:
    return SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.222,
        lines=(RadiationLine("30 keV", 0.4132806614, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=1.0,
        two_theta_max=20.0,
        hkl_max=4,
        min_peak=0.0,
        profile_kind="gaussian",
        fwhm_deg=0.05,
        pseudo_voigt_eta=0.5,
        spectrum_points=101,
        include_lorentz_polarization=False,
        include_multiplicity=False,
        include_cell_volume=False,
    )


@pytest.mark.parametrize(
    ("axis", "start", "stop", "expected"),
    [
        ("y", 0.220, 0.222, [0.220, 0.221, 0.222]),
        ("shuffle_magnitude", 0.0, 0.004, [0.0, 0.002, 0.004]),
        ("a_A", 3.220, 3.222, [3.220, 3.221, 3.222]),
        ("b_A", 4.758, 4.760, [4.758, 4.759, 4.760]),
        ("c_A", 4.667, 4.669, [4.667, 4.668, 4.669]),
        ("energy_keV", 29.0, 31.0, [29.0, 30.0, 31.0]),
        ("wavelength_A", 0.40, 0.42, [0.40, 0.41, 0.42]),
    ],
)
def test_range_sweep_supports_all_scientific_axes(
    axis: SweepAxis,
    start: float,
    stop: float,
    expected: list[float],
) -> None:
    given = SweepConfig.from_simulation(
        _base(),
        axis=axis,
        start=start,
        stop=stop,
        step=(stop - start) / 2,
    )

    result = generate_sweep(given)

    assert [step.step.axis_value for step in result.steps] == pytest.approx(expected)
    assert [step.step.step_id for step in result.steps] == ["step_0000", "step_0001", "step_0002"]


def test_upper_shuffle_branch_maps_magnitude_above_y_quarter() -> None:
    given = SweepConfig.from_simulation(
        _base(),
        axis="shuffle_magnitude",
        start=0.0,
        stop=0.004,
        step=0.002,
        shuffle_branch="upper",
    )

    result = generate_sweep(given)

    assert [step.step.y for step in result.steps] == pytest.approx([0.25, 0.251, 0.252])


def test_lattice_sweep_moves_peak_while_y_sweep_does_not() -> None:
    y_result = generate_sweep(
        SweepConfig.from_simulation(_base(), axis="y", start=0.220, stop=0.222, step=0.002)
    )
    b_result = generate_sweep(
        SweepConfig.from_simulation(_base(), axis="b_A", start=4.759, stop=4.859, step=0.1)
    )

    y_positions = [
        next(
            peak.reflection.two_theta_deg
            for peak in step.peaks
            if peak.reflection.hkl_label == "020"
        )
        for step in y_result.steps
    ]
    b_positions = [
        next(
            peak.reflection.two_theta_deg
            for peak in step.peaks
            if peak.reflection.hkl_label == "020"
        )
        for step in b_result.steps
    ]

    assert y_positions[0] == pytest.approx(y_positions[1])
    assert b_positions[0] != pytest.approx(b_positions[1])


def test_trajectory_rows_inherit_base_and_preserve_order() -> None:
    given = """step_label,a_A,b_A,c_A,y,shuffle_magnitude,shuffle_branch,energy_keV,wavelength_A
initial,,,,0.222,,,,
loaded,,4.800,,,,,31,
"""

    trajectory = parse_trajectory_csv(given, _base())
    result = generate_sweep(trajectory)

    assert [step.step.label for step in result.steps] == ["initial", "loaded"]
    assert result.steps[0].step.lattice == _base().lattice
    assert result.steps[1].step.lattice.b == pytest.approx(4.8)
    assert result.steps[1].step.lines[0].wavelength_a == pytest.approx(12.398419843320026 / 31)


def test_trajectory_reports_y_shuffle_conflict_with_row_and_column() -> None:
    given = """step_label,y,shuffle_magnitude,shuffle_branch
bad,0.214,0.020,lower
"""

    with pytest.raises(TrajectoryValidationError) as caught:
        parse_trajectory_csv(given, _base())

    issue = caught.value.issues[0]
    assert issue.row == 2
    assert issue.column == "shuffle_magnitude"
    assert "inconsistent" in issue.message


def test_trajectory_accepts_consistent_energy_and_wavelength() -> None:
    given = """step_label,energy_keV,wavelength_A
same,31,0.3999490272038718
"""

    trajectory = parse_trajectory_csv(given, _base())

    assert trajectory.steps[0].lines[0].wavelength_a == pytest.approx(0.3999490272038718)


@pytest.mark.parametrize(
    ("axis", "start", "stop"),
    [
        ("y", -0.001, 0.1),
        ("shuffle_magnitude", 0.0, 0.501),
        ("a_A", 0.99, 3.0),
        ("b_A", 4.0, 20.01),
        ("c_A", float("nan"), 5.0),
        ("energy_keV", 0.9, 30.0),
        ("wavelength_A", 0.04, 0.5),
    ],
)
def test_range_sweep_rejects_nonfinite_or_out_of_bounds_values(
    axis: SweepAxis,
    start: float,
    stop: float,
) -> None:
    config = SweepConfig.from_simulation(
        _base(),
        axis=axis,
        start=start,
        stop=stop,
        step=0.001,
    )

    with pytest.raises(ValueError, match=r"finite|within"):
        generate_sweep(config)


def test_all_sweep_steps_share_the_same_two_theta_grid() -> None:
    result = generate_sweep(
        SweepConfig.from_simulation(
            _base(),
            axis="energy_keV",
            start=29.0,
            stop=31.0,
            step=1.0,
        )
    )

    reference = result.steps[0].two_theta_deg
    assert all((step.two_theta_deg == reference).all() for step in result.steps[1:])


def test_trajectory_requires_a_real_change_from_base_config() -> None:
    given = """step_label,y
same,0.222
"""

    with pytest.raises(TrajectoryValidationError, match="must change"):
        parse_trajectory_csv(given, _base())


def test_trajectory_rejects_duplicate_labels_and_nonfinite_values() -> None:
    duplicate = """step_label,b_A
same,4.8
same,4.9
"""
    nonfinite = """step_label,y
bad,nan
"""

    with pytest.raises(TrajectoryValidationError) as duplicate_error:
        parse_trajectory_csv(duplicate, _base())
    with pytest.raises(TrajectoryValidationError) as nonfinite_error:
        parse_trajectory_csv(nonfinite, _base())

    assert duplicate_error.value.issues[0].column == "step_label"
    assert nonfinite_error.value.issues[0].column == "y"


def test_sweep_rejects_more_than_two_million_spectrum_cells() -> None:
    base = _base()
    large = SweepConfig.from_simulation(
        SimulationConfig(
            lattice=base.lattice,
            y=base.y,
            lines=base.lines,
            scattering_mode=base.scattering_mode,
            composition=base.composition,
            two_theta_min=base.two_theta_min,
            two_theta_max=base.two_theta_max,
            hkl_max=base.hkl_max,
            min_peak=base.min_peak,
            profile_kind=base.profile_kind,
            fwhm_deg=base.fwhm_deg,
            pseudo_voigt_eta=base.pseudo_voigt_eta,
            spectrum_points=10_000,
            include_lorentz_polarization=base.include_lorentz_polarization,
            include_multiplicity=base.include_multiplicity,
            include_cell_volume=base.include_cell_volume,
        ),
        axis="y",
        start=0.0,
        stop=0.5,
        step=0.002,
    )

    with pytest.raises(ValueError, match="2,000,000"):
        generate_sweep(large)


def test_sweep_display_range_only_changes_plot_view() -> None:
    from orthoxrd.export_rows import spectra_long_rows
    from orthoxrd.ui_plot_sweep import plot_sweep_heatmap
    from orthoxrd.ui_sweep_range import SweepDisplayRange

    result = generate_sweep(
        SweepConfig.from_simulation(
            _base(),
            axis="y",
            start=0.220,
            stop=0.222,
            step=0.001,
        )
    )
    rows_before = len(list(spectra_long_rows(result)))
    display = SweepDisplayRange(2.0, 10.0, 0.2205, 0.2215)

    figure = plot_sweep_heatmap(result, "global", display)

    assert tuple(figure.layout.xaxis.range) == pytest.approx((2.0, 10.0))
    assert tuple(figure.layout.yaxis.range) == pytest.approx((0.2205, 0.2215))
    assert len(list(spectra_long_rows(result))) == rows_before


def test_sweep_display_key_is_stable_and_result_scoped() -> None:
    from orthoxrd.ui_sweep_range import sweep_display_key

    first = generate_sweep(
        SweepConfig.from_simulation(
            _base(), axis="y", start=0.220, stop=0.222, step=0.001
        )
    )
    same = generate_sweep(
        SweepConfig.from_simulation(
            _base(), axis="y", start=0.220, stop=0.222, step=0.001
        )
    )
    energy = generate_sweep(
        SweepConfig.from_simulation(
            _base(), axis="energy_keV", start=29.0, stop=31.0, step=1.0
        )
    )

    assert sweep_display_key(first) == sweep_display_key(same)
    assert sweep_display_key(first) != sweep_display_key(energy)