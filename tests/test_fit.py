from __future__ import annotations

from dataclasses import replace

import pytest

from orthoxrd.config import SimulationConfig
from orthoxrd.fit import (
    _local_minimum_candidates,
    chi_squared,
    closed_form_scale,
    resolve_weight,
    run_discrete_peak_fit,
)
from orthoxrd.fit_models import FitError, FitOptions, GridScanPoint, PeakObservation
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.powder import calculate_reflections


def _config(*, y: float = 0.222, multi_line: bool = False) -> SimulationConfig:
    lines: tuple[RadiationLine, ...]
    if multi_line:
        lines = (
            RadiationLine("Ka1", 1.5406, 0.5),
            RadiationLine("Ka2", 1.5444, 0.25),
        )
    else:
        lines = (RadiationLine("Cu Ka1", 1.5406, 1.0),)
    return SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=y,
        lines=lines,
        scattering_mode="unit",
        composition=(),
        two_theta_min=5.0,
        two_theta_max=80.0,
        hkl_max=4,
        min_peak=0.0,
        profile_kind="gaussian",
        fwhm_deg=0.1,
        pseudo_voigt_eta=0.5,
        spectrum_points=100,
        include_lorentz_polarization=True,
        include_multiplicity=True,
        include_cell_volume=False,
    )


def _model_i(
    config: SimulationConfig,
    h: int,
    k: int,
    l: int,
    *,
    y: float | None = None,
    line_index: int = 0,
) -> float:
    y_value = config.y if y is None else y
    line = config.lines[line_index]
    reflections = calculate_reflections(
        lattice=config.lattice,
        y=y_value,
        wavelength_a=line.wavelength_a,
        two_theta_min=config.two_theta_min,
        two_theta_max=config.two_theta_max,
        hkl_max=config.hkl_max,
        scattering_mode=config.scattering_mode,
        composition=config.composition,
        include_lorentz_polarization=config.include_lorentz_polarization,
        include_multiplicity=config.include_multiplicity,
        include_cell_volume=config.include_cell_volume,
    )
    peak = next(row for row in reflections if (row.h, row.k, row.l) == (h, k, l))
    return peak.intensity_model * line.weight


def _synthetic_observations(
    config: SimulationConfig,
    hkls: list[tuple[int, int, int]],
    *,
    scale: float = 1.0,
    y: float | None = None,
) -> tuple[PeakObservation, ...]:
    rows: list[PeakObservation] = []
    for index, (h, k, l) in enumerate(hkls, start=2):
        i_model = _model_i(config, h, k, l, y=y)
        rows.append(PeakObservation(h=h, k=k, l=l, I_obs=scale * i_model, row=index))
    return tuple(rows)


def test_run_discrete_peak_fit_importable_without_streamlit() -> None:
    import ast
    from pathlib import Path

    import orthoxrd.fit as fit_mod
    import orthoxrd.fit_models as fit_models_mod
    import orthoxrd.fit_observations as fit_obs_mod

    assert hasattr(fit_mod, "run_discrete_peak_fit")
    for mod in (fit_mod, fit_models_mod, fit_obs_mod):
        tree = ast.parse(Path(mod.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "streamlit"
                    assert not alias.name.startswith("streamlit.")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module != "streamlit"
                assert not module.startswith("streamlit.")


def test_closed_form_scale_matches_weighted_least_squares() -> None:
    i_obs = [10.0, 20.0, 5.0]
    i_model = [2.0, 4.0, 1.0]
    weights = [1.0, 0.5, 2.0]
    # S = Σ w I_obs I_model / Σ w I_model²
    expected_num = sum(w * o * m for o, m, w in zip(i_obs, i_model, weights, strict=True))
    expected_den = sum(w * m * m for m, w in zip(i_model, weights, strict=True))
    expected = expected_num / expected_den
    assert closed_form_scale(i_obs, i_model, weights) == pytest.approx(expected)
    # Perfect scale-5 data.
    i_obs_scaled = [5.0 * m for m in i_model]
    assert closed_form_scale(i_obs_scaled, i_model, weights) == pytest.approx(5.0)
    chi2 = chi_squared(i_obs_scaled, i_model, weights, 5.0)
    assert chi2 == pytest.approx(0.0)


def test_noise_free_round_trip_recovers_y_and_s() -> None:
    # Mid-step y forces refine off the grid (step = 0.5/250 = 0.002).
    truth_y = 0.213
    truth_s = 3.5
    config = _config(y=0.25)  # base y differs from truth; lattice etc. fixed
    hkls = [(1, 1, 0), (0, 2, 0), (0, 0, 2), (1, 1, 1), (0, 2, 1), (1, 1, 2)]
    observations = _synthetic_observations(config, hkls, scale=truth_s, y=truth_y)
    options = FitOptions(
        y_start=0.0,
        y_stop=0.5,
        grid_points=251,
        refine=True,
        refine_xtol=1e-10,
    )

    result = run_discrete_peak_fit(config, observations, options)

    assert result.best.source == "refine"
    assert result.best.y == pytest.approx(truth_y, abs=1e-5)
    assert result.best.scale_s == pytest.approx(truth_s, rel=1e-6)
    assert result.best.chi2 == pytest.approx(0.0, abs=1e-6)
    assert result.best.shuffle_signed == pytest.approx(2.0 * (result.best.y - 0.25))
    assert result.best.shuffle_magnitude == pytest.approx(abs(result.best.shuffle_signed))
    assert len(result.grid_scan) == 251
    assert result.refine_trace  # refinement ran
    assert all(item.included for item in result.matched)
    assert len(result.residuals_at_best) == len(observations)


def test_unmatched_hkl_hard_fails_with_row_identity() -> None:
    config = _config()
    observations = (
        PeakObservation(h=0, k=2, l=0, I_obs=10.0, row=2),
        PeakObservation(h=9, k=9, l=9, I_obs=10.0, row=3),
    )
    with pytest.raises(FitError) as exc_info:
        run_discrete_peak_fit(config, observations)
    assert any(issue.row == 3 and "unmatched" in issue.message for issue in exc_info.value.issues)


def test_multi_line_ambiguity_without_line_hard_fails() -> None:
    config = _config(multi_line=True)
    observations = (
        PeakObservation(h=0, k=2, l=0, I_obs=10.0, row=2),
        PeakObservation(h=1, k=1, l=1, I_obs=20.0, row=3),
    )
    with pytest.raises(FitError) as exc_info:
        run_discrete_peak_fit(config, observations)
    assert any("multi-line ambiguity" in issue.message for issue in exc_info.value.issues)


def test_multi_line_with_line_id_succeeds() -> None:
    config = _config(y=0.222, multi_line=True)
    truth_y = 0.222
    scale = 2.0
    hkls = [(0, 2, 0), (0, 0, 2), (1, 1, 1), (1, 1, 0)]
    observations = tuple(
        PeakObservation(
            h=h,
            k=k,
            l=l,
            I_obs=scale * _model_i(config, h, k, l, y=truth_y, line_index=0),
            row=index,
            line="line_00",
        )
        for index, (h, k, l) in enumerate(hkls, start=2)
    )
    result = run_discrete_peak_fit(
        config,
        observations,
        FitOptions(grid_points=101, y_start=0.15, y_stop=0.30),
    )
    assert result.best.y == pytest.approx(truth_y, abs=1e-3)
    assert result.best.scale_s == pytest.approx(scale, rel=1e-2)


def test_weight_modes_change_chi2_on_toy_set() -> None:
    config = _config(y=0.222)
    # Use model at truth, then perturb one strong peak so weights matter.
    base = list(
        _synthetic_observations(
            config,
            [(0, 2, 0), (0, 0, 2), (1, 1, 1)],
            scale=1.0,
            y=0.222,
        )
    )
    # Inflate the strongest observation so Poisson down-weights it relative to equal.
    strong = base[2]
    base[2] = replace(strong, I_obs=strong.I_obs * 3.0)
    observations = tuple(base)

    poisson = run_discrete_peak_fit(
        config, observations, FitOptions(weight_mode="poisson", grid_points=51)
    )
    equal = run_discrete_peak_fit(
        config, observations, FitOptions(weight_mode="equal", grid_points=51)
    )
    assert poisson.best.chi2 != pytest.approx(equal.best.chi2)

    # Per-peak sigma override must change resolved weights vs Poisson default.
    with_sigma = tuple(
        replace(obs, sigma=1.0 if index == 0 else 10.0) for index, obs in enumerate(observations)
    )
    sigma_fit = run_discrete_peak_fit(
        config, with_sigma, FitOptions(weight_mode="poisson", grid_points=51)
    )
    assert sigma_fit.matched[0].weight == pytest.approx(1.0)
    assert sigma_fit.matched[1].weight == pytest.approx(0.01)
    assert sigma_fit.best.chi2 != pytest.approx(poisson.best.chi2)

    # Explicit weight override.
    with_weight = tuple(replace(obs, weight=2.5) for obs in observations)
    weight_fit = run_discrete_peak_fit(
        config, with_weight, FitOptions(weight_mode="equal", grid_points=21)
    )
    assert all(item.weight == pytest.approx(2.5) for item in weight_fit.matched)


def test_resolve_weight_precedence() -> None:
    obs = PeakObservation(h=0, k=2, l=0, I_obs=100.0, weight=3.0, sigma=2.0)
    assert resolve_weight(obs, weight_mode="poisson", poisson_epsilon=1e-12) == 3.0
    obs_sigma = PeakObservation(h=0, k=2, l=0, I_obs=100.0, sigma=2.0)
    assert resolve_weight(obs_sigma, weight_mode="poisson", poisson_epsilon=1e-12) == pytest.approx(
        0.25
    )
    obs_poisson = PeakObservation(h=0, k=2, l=0, I_obs=100.0)
    assert resolve_weight(
        obs_poisson, weight_mode="poisson", poisson_epsilon=1e-12
    ) == pytest.approx(0.01)
    assert resolve_weight(obs_poisson, weight_mode="equal", poisson_epsilon=1e-12) == 1.0


def test_vanishing_model_peaks_excluded_with_warning() -> None:
    config = _config(y=0.222)
    # 100 is systematically extinct for unit Cmcm 4c ((h+k) odd).
    observations = (
        PeakObservation(h=1, k=0, l=0, I_obs=50.0, row=2),
        PeakObservation(h=0, k=2, l=0, I_obs=_model_i(config, 0, 2, 0), row=3),
        PeakObservation(h=0, k=0, l=2, I_obs=_model_i(config, 0, 0, 2), row=4),
        PeakObservation(h=1, k=1, l=1, I_obs=_model_i(config, 1, 1, 1), row=5),
    )
    result = run_discrete_peak_fit(config, observations, FitOptions(grid_points=41))
    excluded = [item for item in result.matched if not item.included]
    assert len(excluded) == 1
    assert excluded[0].observation.h == 1
    assert excluded[0].observation.k == 0
    assert excluded[0].observation.l == 0
    assert result.warnings
    assert any("vanishing" in warning for warning in result.warnings)


def test_fewer_than_two_valid_peaks_fails() -> None:
    config = _config()
    with pytest.raises(FitError, match="at least two valid peaks"):
        run_discrete_peak_fit(
            config,
            (PeakObservation(h=0, k=2, l=0, I_obs=10.0, row=2),),
        )


def test_vanishing_exclusion_leaving_one_peak_fails() -> None:
    config = _config()
    observations = (
        PeakObservation(h=1, k=0, l=0, I_obs=10.0, row=2),  # extinct
        PeakObservation(h=0, k=2, l=0, I_obs=_model_i(config, 0, 2, 0), row=3),
    )
    with pytest.raises(FitError, match="at least two valid peaks"):
        run_discrete_peak_fit(config, observations, FitOptions(grid_points=21))


def test_non_positive_i_obs_rejected() -> None:
    config = _config()
    with pytest.raises(FitError) as exc_info:
        run_discrete_peak_fit(
            config,
            (
                PeakObservation(h=0, k=2, l=0, I_obs=0.0, row=2),
                PeakObservation(h=0, k=0, l=2, I_obs=10.0, row=3),
            ),
        )
    assert any(issue.column == "I_obs" for issue in exc_info.value.issues)


def test_duplicate_hkl_line_hard_fails() -> None:
    config = _config()
    observations = (
        PeakObservation(h=0, k=2, l=0, I_obs=10.0, row=2),
        PeakObservation(h=0, k=2, l=0, I_obs=12.0, row=3),
        PeakObservation(h=0, k=0, l=2, I_obs=8.0, row=4),
    )
    with pytest.raises(FitError) as exc_info:
        run_discrete_peak_fit(config, observations, FitOptions(grid_points=21))
    assert any("duplicate" in issue.message.lower() for issue in exc_info.value.issues)


def test_peak_height_mode_matches_peak_area_numerically() -> None:
    """v1 equal-width proxy: same objective for peak_height and peak_area."""
    truth_y = 0.22
    truth_s = 2.0
    config = _config()
    observations = _synthetic_observations(
        config,
        [(1, 1, 0), (0, 2, 0), (0, 0, 2), (1, 1, 1)],
        scale=truth_s,
        y=truth_y,
    )
    area = run_discrete_peak_fit(
        config,
        observations,
        FitOptions(observable_mode="peak_area", grid_points=81, refine=True),
    )
    height = run_discrete_peak_fit(
        config,
        observations,
        FitOptions(observable_mode="peak_height", grid_points=81, refine=True),
    )
    assert height.best.y == pytest.approx(area.best.y, abs=1e-10)
    assert height.best.scale_s == pytest.approx(area.best.scale_s, rel=1e-10)
    assert height.best.chi2 == pytest.approx(area.best.chi2, abs=1e-10)
    for left, right in zip(height.residuals_at_best, area.residuals_at_best, strict=True):
        assert left.residual == pytest.approx(right.residual, abs=1e-12)
        assert left.weight == pytest.approx(right.weight, abs=1e-12)


def test_residuals_at_best_reconstruct_chi2() -> None:
    truth_y = 0.21
    config = _config()
    observations = _synthetic_observations(
        config,
        [(1, 1, 0), (0, 2, 0), (0, 0, 2), (1, 1, 1)],
        scale=1.7,
        y=truth_y,
    )
    # Perturb one peak so chi2 > 0.
    from dataclasses import replace

    observations = tuple(
        replace(obs, I_obs=obs.I_obs * 1.2) if index == 0 else obs
        for index, obs in enumerate(observations)
    )
    result = run_discrete_peak_fit(config, observations, FitOptions(grid_points=61))
    reconstructed = sum(
        residual.weight * residual.residual * residual.residual
        for residual in result.residuals_at_best
        if residual.included
    )
    assert reconstructed == pytest.approx(result.best.chi2, rel=1e-10, abs=1e-12)


def test_local_minima_reported_on_unimodal_curve() -> None:
    config = _config(y=0.222)
    observations = _synthetic_observations(
        config,
        [(0, 2, 0), (0, 0, 2), (1, 1, 1), (1, 1, 0)],
        scale=1.0,
        y=0.222,
    )
    result = run_discrete_peak_fit(config, observations, FitOptions(grid_points=101))
    # Unimodal (or weakly multi-modal) should still return without crash.
    assert isinstance(result.local_minima, tuple)
    assert len(result.local_minima) >= 1
    assert result.local_minima[0].chi2 == min(point.chi2 for point in result.grid_scan)


def test_local_minimum_candidates_neighbourhood_endpoint_and_cap() -> None:
    # Two interior wells; right endpoint flat with neighbour (not strictly better).
    # indices: 0:5, 1:3 (well), 2:4, 3:1 (global well), 4:2.5, 5:3.0, 6:3.0
    chi2s = [5.0, 3.0, 4.0, 1.0, 2.5, 3.0, 3.0]
    grid = tuple(
        GridScanPoint(y=0.1 * index, scale_s=1.0, chi2=value) for index, value in enumerate(chi2s)
    )
    candidates = _local_minimum_candidates(grid, max_count=10)
    indices = [item.grid_index for item in candidates]
    assert 1 in indices
    assert 3 in indices
    assert 6 not in indices  # endpoint requires strict improvement
    assert 5 not in indices
    # Global-best first after sort by chi2.
    assert candidates[0].grid_index == 3
    assert candidates[0].chi2 == pytest.approx(1.0)

    # Cap: keep only the best N by chi2.
    capped = _local_minimum_candidates(grid, max_count=1)
    assert len(capped) == 1
    assert capped[0].grid_index == 3

    # Left endpoint counts only when strictly below its sole neighbour.
    left_well = (
        GridScanPoint(y=0.0, scale_s=1.0, chi2=0.5),
        GridScanPoint(y=0.1, scale_s=1.0, chi2=2.0),
        GridScanPoint(y=0.2, scale_s=1.0, chi2=1.5),
    )
    left_candidates = _local_minimum_candidates(left_well, max_count=5)
    assert any(item.grid_index == 0 for item in left_candidates)

    left_flat = (
        GridScanPoint(y=0.0, scale_s=1.0, chi2=2.0),
        GridScanPoint(y=0.1, scale_s=1.0, chi2=2.0),
        GridScanPoint(y=0.2, scale_s=1.0, chi2=1.0),
    )
    left_flat_candidates = _local_minimum_candidates(left_flat, max_count=5)
    assert not any(item.grid_index == 0 for item in left_flat_candidates)


def test_duplicate_radiation_line_labels_hard_fail() -> None:
    config = replace(
        _config(multi_line=True),
        lines=(
            RadiationLine("Ka", 1.5406, 0.5),
            RadiationLine("Ka", 1.5444, 0.25),
        ),
    )
    observations = (
        PeakObservation(h=0, k=2, l=0, I_obs=10.0, row=2, line="Ka"),
        PeakObservation(h=1, k=1, l=1, I_obs=20.0, row=3, line="Ka"),
    )
    with pytest.raises(FitError) as exc_info:
        run_discrete_peak_fit(config, observations)
    assert any("duplicate radiation line label" in issue.message for issue in exc_info.value.issues)

    # line_id matching still works when labels collide.
    hkls = [(0, 2, 0), (0, 0, 2), (1, 1, 1), (1, 1, 0)]
    by_id = tuple(
        PeakObservation(
            h=h,
            k=k,
            l=l,
            I_obs=_model_i(config, h, k, l, line_index=0),
            row=index,
            line="line_00",
        )
        for index, (h, k, l) in enumerate(hkls, start=2)
    )
    result = run_discrete_peak_fit(config, by_id, FitOptions(grid_points=21))
    assert all(item.line_id == "line_00" for item in result.matched)


def test_line_id_match_when_duplicate_label_equals_synthetic_id() -> None:
    """line_id tokens win even if a colliding label string equals that id."""
    config = replace(
        _config(multi_line=True),
        lines=(
            RadiationLine("line_00", 1.5406, 0.5),
            RadiationLine("line_00", 1.5444, 0.25),
        ),
    )
    hkls = [(0, 2, 0), (0, 0, 2), (1, 1, 1), (1, 1, 0)]
    by_line_00 = tuple(
        PeakObservation(
            h=h,
            k=k,
            l=l,
            I_obs=_model_i(config, h, k, l, line_index=0),
            row=index,
            line="line_00",
        )
        for index, (h, k, l) in enumerate(hkls, start=2)
    )
    result_00 = run_discrete_peak_fit(config, by_line_00, FitOptions(grid_points=21))
    assert all(item.line_id == "line_00" for item in result_00.matched)

    by_line_01 = tuple(
        PeakObservation(
            h=h,
            k=k,
            l=l,
            I_obs=_model_i(config, h, k, l, line_index=1),
            row=index,
            line="line_01",
        )
        for index, (h, k, l) in enumerate(hkls, start=2)
    )
    result_01 = run_discrete_peak_fit(config, by_line_01, FitOptions(grid_points=21))
    assert all(item.line_id == "line_01" for item in result_01.matched)


def test_negative_miller_indices_map_to_positive_octant() -> None:
    config = _config(y=0.222)
    scale = 1.5
    # Forward model only has non-negative HKL; signed indices should still match.
    observations = (
        PeakObservation(h=0, k=-2, l=0, I_obs=scale * _model_i(config, 0, 2, 0), row=2),
        PeakObservation(h=-1, k=-1, l=1, I_obs=scale * _model_i(config, 1, 1, 1), row=3),
        PeakObservation(h=0, k=0, l=2, I_obs=scale * _model_i(config, 0, 0, 2), row=4),
    )
    result = run_discrete_peak_fit(
        config, observations, FitOptions(grid_points=51, y_start=0.15, y_stop=0.30)
    )
    assert all(item.included for item in result.matched)
    assert any("negative Miller" in warning for warning in result.warnings)
    assert result.best.y == pytest.approx(0.222, abs=1e-3)


def test_residuals_at_best_have_expected_fields() -> None:
    config = _config(y=0.222)
    observations = _synthetic_observations(
        config, [(0, 2, 0), (1, 1, 1), (0, 0, 2)], scale=2.0, y=0.222
    )
    result = run_discrete_peak_fit(config, observations, FitOptions(grid_points=51))
    for residual in result.residuals_at_best:
        assert residual.S_I_model == pytest.approx(result.best.scale_s * residual.I_model)
        assert residual.residual == pytest.approx(residual.I_obs - residual.S_I_model)
        assert residual.included is True
