from __future__ import annotations

from dataclasses import replace

import pytest

from orthoxrd.config import SimulationConfig
from orthoxrd.fit_models import (
    BestFit,
    FitOptions,
    FitResult,
    GridScanPoint,
    LocalMinimumCandidate,
    RefineTracePoint,
    ResidualAtBest,
)
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.ui_plot_fit import (
    plot_chi2_curve,
    plot_observed_vs_fitted,
    plot_residual_contributions,
    plot_scale_curve,
)


def _result() -> FitResult:
    config = SimulationConfig(
        lattice=LatticeParameters(3.2, 4.7, 4.6),
        y=0.22,
        lines=(RadiationLine("line", 1.0, 1.0),),
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
    return FitResult(
        config=config,
        options=FitOptions(y_start=0.2, y_stop=0.3, grid_points=3),
        matched=(),
        grid_scan=(
            GridScanPoint(0.2, 2.0, 4.0),
            GridScanPoint(0.25, 2.1, 1.0),
            GridScanPoint(0.3, 1.9, 3.0),
        ),
        refine_trace=(
            RefineTracePoint(0.248, 2.08, 1.1, 1),
            RefineTracePoint(0.25, 2.1, 1.0, 2),
        ),
        best=BestFit(0.25, 2.1, 1.0, 0.0, 0.0, 0.0, "refine"),
        residuals_at_best=(
            ResidualAtBest(0, 2, 1, "line_00", "line", "s1", 10.0, 4.0, 9.0, 1.0, 0.25, True),
            ResidualAtBest(1, 1, 0, "line_00", "line", "s2", 8.0, 4.0, 8.5, -0.5, 3.0, True),
        ),
        local_minima=(LocalMinimumCandidate(0.25, 2.1, 1.0, 1),),
        warnings=(),
    )


def _role_traces(figure, role: str):
    return [trace for trace in figure.data if (trace.meta or {}).get("role") == role]


def test_fit_objective_supports_signed_shuffle_and_refinement_trace() -> None:
    figure = plot_chi2_curve(_result(), "signed_shuffle")

    grid = _role_traces(figure, "grid")
    assert len(grid) == 1
    assert tuple(grid[0].x) == pytest.approx((-0.1, 0.0, 0.1))
    assert len(_role_traces(figure, "refine")) == 1
    assert len(_role_traces(figure, "best")) == 1


def test_fit_magnitude_projection_keeps_lower_and_upper_branches_separate() -> None:
    figure = plot_chi2_curve(_result(), "shuffle_magnitude")

    grid = _role_traces(figure, "grid")
    assert {(trace.meta or {}).get("branch") for trace in grid} == {"lower", "upper"}
    lower = next(trace for trace in grid if trace.meta["branch"] == "lower")
    upper = next(trace for trace in grid if trace.meta["branch"] == "upper")
    assert tuple(lower.x) == pytest.approx((0.1, 0.0))
    assert tuple(upper.x) == pytest.approx((0.0, 0.1))


def test_fit_magnitude_projection_does_not_invent_an_unscanned_branch() -> None:
    result = _result()
    result = replace(result, grid_scan=result.grid_scan[:2])

    grid = _role_traces(plot_chi2_curve(result, "shuffle_magnitude"), "grid")

    assert {(trace.meta or {}).get("branch") for trace in grid} == {"lower"}


def test_scale_curve_uses_the_same_display_coordinate_contract() -> None:
    figure = plot_scale_curve(_result(), "signed_shuffle")
    grid = _role_traces(figure, "grid")

    assert tuple(grid[0].x) == pytest.approx((-0.1, 0.0, 0.1))
    assert tuple(grid[0].y) == pytest.approx((2.0, 2.1, 1.9))


def test_fit_diagnostics_show_parity_and_reconstruct_chi2_by_peak() -> None:
    result = _result()
    parity = plot_observed_vs_fitted(result)
    contributions = plot_residual_contributions(result)

    observations = _role_traces(parity, "observations")
    assert len(observations) == 1
    assert tuple(observations[0].text) == ("021", "110")
    bars = _role_traces(contributions, "chi2_contribution")
    assert len(bars) == 1
    assert sum(bars[0].y) == pytest.approx(result.best.chi2)


def test_residual_contributions_keep_radiation_lines_separate() -> None:
    result = _result()
    first = result.residuals_at_best[0]
    second_line = replace(
        first,
        line_id="line_01",
        line_label="line 2",
        series_id="s3",
    )
    result = replace(result, residuals_at_best=(first, second_line))

    bars = _role_traces(plot_residual_contributions(result), "chi2_contribution")

    assert tuple(bars[0].x) == ("021 · line_00", "021 · line_01")
