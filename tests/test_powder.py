import pytest

from orthoxrd.models import LatticeParameters
from orthoxrd.powder import calculate_reflections, energy_kev_to_wavelength_a


def test_energy_wavelength_conversion_uses_xray_constant() -> None:
    assert energy_kev_to_wavelength_a(30.0) == pytest.approx(0.4132806614)


def test_wavelength_changes_two_theta_not_d_spacing() -> None:
    lattice = LatticeParameters(a=3.222, b=4.759, c=4.668)
    short = calculate_reflections(
        lattice=lattice,
        y=0.222,
        wavelength_a=0.41328,
        two_theta_min=1.0,
        two_theta_max=20.0,
        hkl_max=3,
        scattering_mode="unit",
    )
    long = calculate_reflections(
        lattice=lattice,
        y=0.222,
        wavelength_a=1.5406,
        two_theta_min=1.0,
        two_theta_max=90.0,
        hkl_max=3,
        scattering_mode="unit",
    )

    short_020 = next(row for row in short if row.hkl_label == "020")
    long_020 = next(row for row in long if row.hkl_label == "020")
    assert short_020.d_spacing_a == pytest.approx(long_020.d_spacing_a)
    assert short_020.two_theta_deg < long_020.two_theta_deg


def test_lattice_change_moves_peak_position() -> None:
    compact = calculate_reflections(
        lattice=LatticeParameters(a=3.187, b=4.800, c=4.659),
        y=0.214,
        wavelength_a=0.41328,
        two_theta_min=1.0,
        two_theta_max=20.0,
        hkl_max=3,
        scattering_mode="unit",
    )
    expanded = calculate_reflections(
        lattice=LatticeParameters(a=3.187, b=4.950, c=4.659),
        y=0.214,
        wavelength_a=0.41328,
        two_theta_min=1.0,
        two_theta_max=20.0,
        hkl_max=3,
        scattering_mode="unit",
    )

    compact_020 = next(row for row in compact if row.hkl_label == "020")
    expanded_020 = next(row for row in expanded if row.hkl_label == "020")
    assert compact_020.two_theta_deg > expanded_020.two_theta_deg


def test_invalid_lattice_parameter_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive"):
        LatticeParameters(a=0.0, b=4.7, c=4.6)
