from dataclasses import replace

from orthoxrd.config import SimulationConfig, config_hash, config_json
from orthoxrd.models import LatticeParameters, RadiationLine


def _config() -> SimulationConfig:
    return SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.222,
        lines=(RadiationLine("30 keV", 0.4132806614, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=1.0,
        two_theta_max=20.0,
        hkl_max=6,
        min_peak=0.1,
        profile_kind="pseudo_voigt",
        fwhm_deg=0.06,
        pseudo_voigt_eta=0.5,
        spectrum_points=5000,
        include_lorentz_polarization=True,
        include_multiplicity=True,
        include_cell_volume=True,
    )


def test_config_hash_is_stable_and_changes_with_scientific_input() -> None:
    given = _config()

    when_same = config_hash(given)
    when_changed = config_hash(replace(given, y=0.223))

    assert when_same == config_hash(given)
    assert when_changed != when_same
    assert config_json(given).startswith('{"composition":')


def test_config_rejects_invalid_pattern_range() -> None:
    given = _config()

    try:
        replace(given, two_theta_min=20.0, two_theta_max=10.0)
    except ValueError as exc:
        assert "two-theta" in str(exc)
    else:
        raise AssertionError("invalid two-theta range was accepted")
