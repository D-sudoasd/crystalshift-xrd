from __future__ import annotations

from dataclasses import dataclass, replace

from orthoxrd.config import SimulationConfig
from orthoxrd.models import RadiationLine, Reflection
from orthoxrd.powder import calculate_reflections
from orthoxrd.profiles import SpectrumArrays, calculate_spectrum_arrays


@dataclass(frozen=True, slots=True)
class CalculatedPeak:
    line_id: str
    line_label: str
    wavelength_a: float
    line_weight: float
    reflection: Reflection

    @property
    def series_id(self) -> str:
        return f"{self.line_id}__{self.reflection.hkl_id}"


@dataclass(frozen=True, slots=True)
class SimulationResult:
    config: SimulationConfig
    peaks: tuple[CalculatedPeak, ...]
    spectrum: SpectrumArrays


def calculate_simulation(config: SimulationConfig) -> SimulationResult:
    weighted: list[tuple[int, RadiationLine, Reflection, float]] = []
    for line_index, line in enumerate(config.lines):
        reflections = calculate_reflections(
            lattice=config.lattice,
            y=config.y,
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
        for reflection in reflections:
            weighted.append(
                (line_index, line, reflection, reflection.intensity_model * line.weight)
            )
    maximum = max((item[3] for item in weighted), default=0.0)
    peaks = tuple(
        CalculatedPeak(
            line_id=f"line_{line_index:02d}",
            line_label=line.label,
            wavelength_a=line.wavelength_a,
            line_weight=line.weight,
            reflection=replace(
                reflection,
                intensity_raw=intensity,
                intensity_scaled=intensity / maximum * 100.0 if maximum > 0 else 0.0,
            ),
        )
        for line_index, line, reflection, intensity in weighted
    )
    ordered = tuple(sorted(peaks, key=lambda peak: peak.reflection.two_theta_deg))
    spectrum = calculate_spectrum_arrays(
        tuple(
            replace(peak.reflection, intensity_scaled=peak.reflection.intensity_model)
            for peak in ordered
        ),
        two_theta_min=config.two_theta_min,
        two_theta_max=config.two_theta_max,
        points=config.spectrum_points,
        fwhm_deg=config.fwhm_deg,
        profile_kind=config.profile_kind,
        pseudo_voigt_eta=config.pseudo_voigt_eta,
    )
    return SimulationResult(config=config, peaks=ordered, spectrum=spectrum)
