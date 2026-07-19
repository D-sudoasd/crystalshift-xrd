import pytest

from orthoxrd.models import ElementFraction, LatticeParameters
from orthoxrd.powder import (
    calculate_reflection_for_hkl,
    calculate_reflections,
    energy_kev_to_wavelength_a,
)


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


def test_single_hkl_evaluator_has_reference_parity() -> None:
    lattice = LatticeParameters(a=3.222, b=4.759, c=4.668)
    kwargs = {
        "lattice": lattice,
        "y": 0.222,
        "wavelength_a": 0.41328,
        "two_theta_min": 1.0,
        "two_theta_max": 20.0,
        "hkl_max": 4,
        "scattering_mode": "unit",
        "include_lorentz_polarization": True,
        "include_multiplicity": True,
        "include_cell_volume": True,
    }
    reflections = calculate_reflections(**kwargs)
    for reflection in reflections:
        direct = calculate_reflection_for_hkl(
            h=reflection.h,
            k=reflection.k,
            l=reflection.l,
            lattice=lattice,
            y=0.222,
            wavelength_a=0.41328,
            two_theta_min=1.0,
            two_theta_max=20.0,
            scattering_mode="unit",
            include_lorentz_polarization=True,
            include_multiplicity=True,
            include_cell_volume=True,
        )
        assert direct is not None
        assert direct.intensity_model == pytest.approx(reflection.intensity_model)
        assert direct.two_theta_deg == pytest.approx(reflection.two_theta_deg)


def test_model_intensity_switches_scale_only_their_applied_factors() -> None:
    lattice = LatticeParameters(a=3.222, b=4.759, c=4.668)
    common = {
        "h": 0,
        "k": 2,
        "l": 0,
        "lattice": lattice,
        "y": 0.222,
        "wavelength_a": 0.41328,
        "two_theta_min": 1.0,
        "two_theta_max": 20.0,
        "scattering_mode": "unit",
    }
    bare = calculate_reflection_for_hkl(
        **common,
        include_lorentz_polarization=False,
        include_multiplicity=False,
        include_cell_volume=False,
    )
    with_multiplicity = calculate_reflection_for_hkl(
        **common,
        include_lorentz_polarization=False,
        include_multiplicity=True,
        include_cell_volume=False,
    )
    with_lp = calculate_reflection_for_hkl(
        **common,
        include_lorentz_polarization=True,
        include_multiplicity=False,
        include_cell_volume=False,
    )
    with_volume = calculate_reflection_for_hkl(
        **common,
        include_lorentz_polarization=False,
        include_multiplicity=False,
        include_cell_volume=True,
    )
    assert bare is not None
    assert with_multiplicity is not None
    assert with_lp is not None
    assert with_volume is not None
    assert with_multiplicity.intensity_model == pytest.approx(
        bare.intensity_model * bare.multiplicity
    )
    assert with_lp.intensity_model == pytest.approx(
        bare.intensity_model * with_lp.lorentz_polarization
    )
    assert with_volume.intensity_model == pytest.approx(
        bare.intensity_model / lattice.volume_a3
    )


def test_composition_scattering_scales_f2_and_model_intensity() -> None:
    lattice = LatticeParameters(a=3.222, b=4.759, c=4.668)
    kwargs = {
        "h": 0,
        "k": 2,
        "l": 0,
        "lattice": lattice,
        "y": 0.222,
        "wavelength_a": 0.41328,
        "two_theta_min": 1.0,
        "two_theta_max": 20.0,
        "include_lorentz_polarization": False,
        "include_multiplicity": False,
        "include_cell_volume": False,
    }
    unit = calculate_reflection_for_hkl(**kwargs, scattering_mode="unit")
    composition = calculate_reflection_for_hkl(
        **kwargs,
        scattering_mode="composition",
        composition=(ElementFraction("Fe", 1.0),),
    )
    assert unit is not None
    assert composition is not None
    ratio = composition.form_factor_effective / unit.form_factor_effective
    assert composition.structure_factor_squared == pytest.approx(
        unit.structure_factor_squared * ratio**2
    )
    assert composition.intensity_model == pytest.approx(unit.intensity_model * ratio**2)
