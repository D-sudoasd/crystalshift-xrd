"""Measure the cached direct evaluator on one representative fit configuration.

Run from the repository root with ``.venv\\Scripts\\python.exe
benchmarks/fit_direct_evaluator.py``. The reported time is measured on the
current machine; no speed-up factor is assumed by the application.
"""

from __future__ import annotations

import json
import statistics
import time

from orthoxrd.config import SimulationConfig
from orthoxrd.fit import run_discrete_peak_fit, validate_discrete_peak_fit_observations
from orthoxrd.fit_models import FitOptions, PeakObservation
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.powder import calculate_reflection_for_hkl


def _config() -> SimulationConfig:
    return SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.222,
        lines=(RadiationLine("30 keV", 0.4132806614, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=1.0,
        two_theta_max=12.0,
        hkl_max=4,
        min_peak=0.0,
        profile_kind="gaussian",
        fwhm_deg=0.05,
        pseudo_voigt_eta=0.5,
        spectrum_points=101,
        include_lorentz_polarization=True,
        include_multiplicity=True,
        include_cell_volume=True,
    )


def _observations(config: SimulationConfig) -> tuple[PeakObservation, ...]:
    hkls = ((0, 2, 0), (0, 0, 2), (1, 1, 1), (1, 1, 0), (0, 2, 1))
    rows: list[PeakObservation] = []
    for row, (h, k, l) in enumerate(hkls, start=2):
        reflection = calculate_reflection_for_hkl(
            h=h,
            k=k,
            l=l,
            lattice=config.lattice,
            y=config.y,
            wavelength_a=config.lines[0].wavelength_a,
            two_theta_min=config.two_theta_min,
            two_theta_max=config.two_theta_max,
            scattering_mode=config.scattering_mode,
            composition=config.composition,
            include_lorentz_polarization=config.include_lorentz_polarization,
            include_multiplicity=config.include_multiplicity,
            include_cell_volume=config.include_cell_volume,
        )
        if reflection is None:
            raise RuntimeError(f"benchmark HKL is outside the active window: {(h, k, l)}")
        rows.append(PeakObservation(h=h, k=k, l=l, I_obs=2.0 * reflection.intensity_model, row=row))
    return tuple(rows)


def main() -> None:
    config = _config()
    observations = _observations(config)
    options = FitOptions(grid_points=201, refine=False)
    matched = validate_discrete_peak_fit_observations(config, observations, options)
    for _ in range(2):
        run_discrete_peak_fit(config, observations, options)

    elapsed: list[float] = []
    for _ in range(5):
        started = time.perf_counter()
        run_discrete_peak_fit(config, observations, options)
        elapsed.append(time.perf_counter() - started)

    full_hkl_candidates_per_line = (config.hkl_max + 1) ** 3 - 1
    payload = {
        "grid_points": options.grid_points,
        "matched_peak_count": sum(item.included for item in matched),
        "full_reference_hkl_candidates_per_line": full_hkl_candidates_per_line,
        "direct_structure_factor_evaluations_per_grid": sum(
            item.included for item in matched
        ),
        "refine": options.refine,
        "runs": len(elapsed),
        "seconds": {
            "min": min(elapsed),
            "median": statistics.median(elapsed),
            "max": max(elapsed),
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
