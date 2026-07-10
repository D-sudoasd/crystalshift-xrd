import pytest

from orthoxrd.models import LatticeParameters
from orthoxrd.powder import calculate_reflections
from orthoxrd.profiles import calculate_spectrum, calculate_spectrum_arrays


def test_vectorized_spectrum_matches_legacy_point_contract() -> None:
    given = calculate_reflections(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.222,
        wavelength_a=0.4132806614,
        two_theta_min=1.0,
        two_theta_max=20.0,
        hkl_max=4,
        scattering_mode="unit",
    )

    when_points = calculate_spectrum(
        given,
        two_theta_min=1.0,
        two_theta_max=20.0,
        points=501,
        fwhm_deg=0.06,
        profile_kind="pseudo_voigt",
        pseudo_voigt_eta=0.5,
    )
    when_arrays = calculate_spectrum_arrays(
        given,
        two_theta_min=1.0,
        two_theta_max=20.0,
        points=501,
        fwhm_deg=0.06,
        profile_kind="pseudo_voigt",
        pseudo_voigt_eta=0.5,
    )

    assert when_arrays.two_theta_deg.tolist() == pytest.approx(
        [point.two_theta_deg for point in when_points], abs=1e-12
    )
    assert when_arrays.intensity_rel_local.tolist() == pytest.approx(
        [point.intensity for point in when_points], rel=1e-12, abs=1e-12
    )


def test_reflection_exposes_model_intensity_decomposition() -> None:
    lattice = LatticeParameters(a=3.222, b=4.759, c=4.668)

    reflection = next(
        row
        for row in calculate_reflections(
            lattice=lattice,
            y=0.222,
            wavelength_a=0.4132806614,
            two_theta_min=1.0,
            two_theta_max=20.0,
            hkl_max=4,
            scattering_mode="unit",
            include_lorentz_polarization=True,
            include_multiplicity=True,
            include_cell_volume=True,
        )
        if row.hkl_label == "020"
    )

    expected = (
        reflection.structure_factor_squared
        * reflection.applied_multiplicity
        * reflection.applied_lorentz_polarization
        * reflection.applied_volume_factor
    )
    assert reflection.intensity_model == pytest.approx(expected)
    assert reflection.intensity_model == pytest.approx(reflection.intensity_raw)
    assert reflection.scattering_vector_s_a_inv == pytest.approx(
        1.0 / (2.0 * reflection.d_spacing_a)
    )


def test_profile_model_intensity_applies_radiation_line_weights() -> None:
    from dataclasses import replace

    import numpy as np

    from orthoxrd.config import SimulationConfig
    from orthoxrd.models import RadiationLine
    from orthoxrd.simulation import calculate_simulation

    base = SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.222,
        lines=(RadiationLine("single", 0.4132806614, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=1.0,
        two_theta_max=12.0,
        hkl_max=3,
        min_peak=0.0,
        profile_kind="gaussian",
        fwhm_deg=0.05,
        pseudo_voigt_eta=0.5,
        spectrum_points=301,
        include_lorentz_polarization=False,
        include_multiplicity=False,
        include_cell_volume=False,
    )
    single = calculate_simulation(base)
    weighted = calculate_simulation(
        replace(
            base,
            lines=(
                RadiationLine("primary", 0.4132806614, 2.0),
                RadiationLine("secondary", 0.4132806614, 1.0),
            ),
        )
    )

    np.testing.assert_allclose(
        weighted.spectrum.intensity_model,
        single.spectrum.intensity_model * 3.0,
        rtol=1e-12,
        atol=1e-12,
    )
