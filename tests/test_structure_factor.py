import math

import pytest

from orthoxrd.models import LatticeParameters
from orthoxrd.powder import calculate_reflections
from orthoxrd.structure_factor import (
    analytic_unit_structure_factor_squared,
    cmcm_4c_structure_factor,
    cmcm_4c_structure_factor_squared,
    normalized_shuffle_from_y,
    signed_shuffle_from_y,
    validate_y,
    y_from_shuffle_magnitude,
)


@pytest.mark.parametrize("y", [0.0, 0.125, 0.25, 0.333, 0.5])
@pytest.mark.parametrize("hkl", [(0, 0, 1), (0, 2, 0), (0, 2, 1), (1, 3, 1), (4, 2, 3)])
def test_analytic_unit_f2_matches_numerical_structure_factor(
    y: float,
    hkl: tuple[int, int, int],
) -> None:
    h, k, l = hkl
    numerical = cmcm_4c_structure_factor(h, k, l, y, 1.0)
    expected = float((numerical * numerical.conjugate()).real)
    assert analytic_unit_structure_factor_squared(h, k, l, y) == pytest.approx(
        expected,
        abs=1e-12,
    )


def test_analytic_unit_f2_special_position_and_extinction_are_explicit() -> None:
    assert analytic_unit_structure_factor_squared(0, 2, 0, 0.25) == pytest.approx(16.0)
    assert analytic_unit_structure_factor_squared(0, 2, 1, 0.25) == pytest.approx(0.0)
    assert analytic_unit_structure_factor_squared(1, 0, 0, 0.25) == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("hkl", "expected"),
    [
        ((1, 1, 0), 0.0),
        ((0, 2, 0), 16.0),
        ((0, 2, 1), 0.0),
        ((1, 3, 1), 16.0),
    ],
)
def test_bcc_limit_y_quarter_matches_extinction_pattern(
    hkl: tuple[int, int, int], expected: float
) -> None:
    h, k, l = hkl
    assert cmcm_4c_structure_factor_squared(h, k, l, 0.25, 1.0) == pytest.approx(
        expected,
        abs=1e-12,
    )


def test_paper_y_examples_change_selected_relative_intensities() -> None:
    low_shuffle = cmcm_4c_structure_factor_squared(0, 2, 0, 0.228, 1.0)
    high_shuffle = cmcm_4c_structure_factor_squared(0, 2, 0, 0.20, 1.0)
    assert low_shuffle > high_shuffle

    weak_at_low_shuffle = cmcm_4c_structure_factor_squared(0, 2, 1, 0.228, 1.0)
    stronger_at_high_shuffle = cmcm_4c_structure_factor_squared(0, 2, 1, 0.20, 1.0)
    assert stronger_at_high_shuffle > weak_at_low_shuffle


def test_signed_shuffle_uses_crystallographic_y_convention() -> None:
    assert signed_shuffle_from_y(0.0) == pytest.approx(-0.5)
    assert signed_shuffle_from_y(0.25) == pytest.approx(0.0)
    assert signed_shuffle_from_y(0.5) == pytest.approx(0.5)
    assert signed_shuffle_from_y(0.214) == pytest.approx(-0.072)
    assert abs(signed_shuffle_from_y(0.214)) == pytest.approx(0.072)


def test_normalized_shuffle_from_y_endpoints_and_ti_nb_example() -> None:
    assert normalized_shuffle_from_y(0.25) == pytest.approx(0.0)
    assert normalized_shuffle_from_y(0.0) == pytest.approx(1.0)
    assert normalized_shuffle_from_y(0.5) == pytest.approx(1.0)
    assert normalized_shuffle_from_y(0.214) == pytest.approx(0.072 / 0.5)
    assert normalized_shuffle_from_y(0.214) == pytest.approx(0.144)


def test_validate_y_accepts_crystallographic_bounds() -> None:
    validate_y(0.0)
    validate_y(0.5)


def test_validate_y_rejects_values_outside_crystallographic_bounds() -> None:
    with pytest.raises(ValueError):
        validate_y(-1e-9)
    with pytest.raises(ValueError):
        validate_y(0.500000001)


def test_y_shuffle_magnitude_round_trip_uses_ti_nb_branch() -> None:
    y_value = 0.214
    shuffle = abs(signed_shuffle_from_y(y_value))
    assert y_from_shuffle_magnitude(shuffle) == pytest.approx(y_value)


def test_y_from_shuffle_magnitude_maps_ti_nb_default_window() -> None:
    assert y_from_shuffle_magnitude(0.166) == pytest.approx(0.167)
    assert y_from_shuffle_magnitude(0.166, upper_branch=True) == pytest.approx(0.333)


def test_y_from_shuffle_magnitude_can_preserve_upper_branch() -> None:
    shuffle = abs(signed_shuffle_from_y(0.30))
    assert y_from_shuffle_magnitude(shuffle) == pytest.approx(0.20)
    assert y_from_shuffle_magnitude(shuffle, upper_branch=True) == pytest.approx(0.30)


def test_y_changes_intensity_without_moving_peak_positions() -> None:
    lattice = LatticeParameters(a=3.222, b=4.759, c=4.668)
    y_low = calculate_reflections(
        lattice=lattice,
        y=0.214,
        wavelength_a=0.41328,
        two_theta_min=1.0,
        two_theta_max=12.0,
        hkl_max=4,
        scattering_mode="unit",
        include_lorentz_polarization=False,
        include_multiplicity=False,
    )
    y_high = calculate_reflections(
        lattice=lattice,
        y=0.228,
        wavelength_a=0.41328,
        two_theta_min=1.0,
        two_theta_max=12.0,
        hkl_max=4,
        scattering_mode="unit",
        include_lorentz_polarization=False,
        include_multiplicity=False,
    )

    positions_low = [(row.h, row.k, row.l, round(row.two_theta_deg, 8)) for row in y_low]
    positions_high = [(row.h, row.k, row.l, round(row.two_theta_deg, 8)) for row in y_high]
    assert positions_low == positions_high

    i_020_low = next(row.intensity_raw for row in y_low if row.hkl_label == "020")
    i_020_high = next(row.intensity_raw for row in y_high if row.hkl_label == "020")
    assert not math.isclose(i_020_low, i_020_high)
