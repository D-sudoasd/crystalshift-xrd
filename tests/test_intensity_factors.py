import math

import pytest

from orthoxrd.config import SimulationConfig
from orthoxrd.models import LatticeParameters, RadiationLine, Reflection
from orthoxrd.powder import calculate_reflections
from orthoxrd.simulation import calculate_simulation


def test_reference_r_factors_follow_the_workbook_definition() -> None:
    reflection = Reflection(
        h=1,
        k=1,
        l=0,
        d_spacing_a=2.0,
        two_theta_deg=60.0,
        q_a_inv=math.pi,
        multiplicity=4,
        structure_factor_squared=9.0,
        lorentz_polarization=5.0,
        intensity_raw=0.0,
        intensity_scaled=0.0,
        cell_volume_a3=10.0,
    )

    assert reflection.structure_factor_abs == pytest.approx(3.0)
    assert reflection.n_f2 == pytest.approx(36.0)
    assert reflection.n_f2_lp == pytest.approx(180.0)
    assert reflection.reference_r_hkl_with_lp == pytest.approx(1.8)
    assert reflection.reference_r_hkl_no_lp == pytest.approx(0.36)
    assert reflection.inverse_reference_r_hkl_with_lp == pytest.approx(1.0 / 1.8)
    assert reflection.inverse_reference_r_hkl_no_lp == pytest.approx(1.0 / 0.36)
    assert reflection.g_a_inv == pytest.approx(0.5)
    assert reflection.theta_deg == pytest.approx(30.0)
    assert reflection.sin_theta == pytest.approx(0.5)
    assert reflection.cos_theta == pytest.approx(math.sqrt(3.0) / 2.0)
    assert reflection.sin_theta_over_lambda_a_inv == pytest.approx(0.25)
    assert reflection.sin2_theta_over_lambda2_a_inv2 == pytest.approx(0.0625)


def test_reference_r_factors_do_not_use_applied_correction_toggles() -> None:
    reflection = Reflection(
        h=0,
        k=2,
        l=0,
        d_spacing_a=2.5,
        two_theta_deg=20.0,
        q_a_inv=2.0,
        multiplicity=2,
        structure_factor_squared=8.0,
        lorentz_polarization=3.0,
        intensity_raw=8.0,
        intensity_scaled=100.0,
        applied_multiplicity=1.0,
        applied_lorentz_polarization=1.0,
        applied_volume_factor=1.0,
        cell_volume_a3=4.0,
    )

    assert reflection.reference_r_hkl_with_lp == pytest.approx(3.0)
    assert reflection.reference_r_hkl_no_lp == pytest.approx(1.0)
    assert reflection.intensity_model == pytest.approx(8.0)


def test_extinct_reflection_has_blank_safe_inverse_factors() -> None:
    reflection = Reflection(
        h=1,
        k=0,
        l=0,
        d_spacing_a=3.0,
        two_theta_deg=10.0,
        q_a_inv=1.0,
        multiplicity=2,
        structure_factor_squared=0.0,
        lorentz_polarization=2.0,
        intensity_raw=0.0,
        intensity_scaled=0.0,
        cell_volume_a3=5.0,
    )

    assert reflection.reference_r_hkl_with_lp == 0.0
    assert reflection.reference_r_hkl_no_lp == 0.0
    assert reflection.inverse_reference_r_hkl_with_lp is None
    assert reflection.inverse_reference_r_hkl_no_lp is None


def test_calculated_r_factors_ignore_model_correction_toggles() -> None:
    common = {
        "lattice": LatticeParameters(a=3.222, b=4.759, c=4.668),
        "y": 0.222,
        "wavelength_a": 0.4132806614,
        "two_theta_min": 1.0,
        "two_theta_max": 20.0,
        "hkl_max": 3,
        "scattering_mode": "unit",
    }
    corrected = calculate_reflections(
        **common,
        include_lorentz_polarization=True,
        include_multiplicity=True,
        include_cell_volume=True,
    )
    bare = calculate_reflections(
        **common,
        include_lorentz_polarization=False,
        include_multiplicity=False,
        include_cell_volume=False,
    )
    corrected_020 = next(item for item in corrected if item.hkl_label == "020")
    bare_020 = next(item for item in bare if item.hkl_label == "020")

    assert corrected_020.reference_r_hkl_with_lp == pytest.approx(
        bare_020.reference_r_hkl_with_lp
    )
    assert corrected_020.reference_r_hkl_no_lp == pytest.approx(
        bare_020.reference_r_hkl_no_lp
    )
    assert corrected_020.intensity_model != pytest.approx(bare_020.intensity_model)


def test_radiation_line_weight_changes_model_intensity_but_not_r_factors() -> None:
    result = calculate_simulation(
        SimulationConfig(
            lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
            y=0.222,
            lines=(
                RadiationLine("full", 0.4132806614, 1.0),
                RadiationLine("half", 0.4132806614, 0.5),
            ),
            scattering_mode="unit",
            composition=(),
            two_theta_min=1.0,
            two_theta_max=20.0,
            hkl_max=3,
            min_peak=0.0,
            profile_kind="gaussian",
            fwhm_deg=0.05,
            pseudo_voigt_eta=0.5,
            spectrum_points=101,
            include_lorentz_polarization=True,
            include_multiplicity=True,
            include_cell_volume=True,
        )
    )
    full = next(
        peak
        for peak in result.peaks
        if peak.line_label == "full" and peak.reflection.hkl_label == "020"
    )
    half = next(
        peak
        for peak in result.peaks
        if peak.line_label == "half" and peak.reflection.hkl_label == "020"
    )

    assert full.reflection.reference_r_hkl_with_lp == pytest.approx(
        half.reflection.reference_r_hkl_with_lp
    )
    assert full.reflection.reference_r_hkl_no_lp == pytest.approx(
        half.reflection.reference_r_hkl_no_lp
    )
    assert full.reflection.intensity_model == pytest.approx(2.0 * half.reflection.intensity_model)
