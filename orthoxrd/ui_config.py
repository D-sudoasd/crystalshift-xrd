from __future__ import annotations

import streamlit as st

from orthoxrd.config import SimulationConfig
from orthoxrd.simulation import SimulationResult, calculate_simulation
from orthoxrd.structure_state import StructureState
from orthoxrd.ui_radiation import RadiationState
from orthoxrd.ui_sidebar import AdvancedState


def build_simulation_config(
    structure: StructureState,
    radiation: RadiationState,
    advanced: AdvancedState,
) -> SimulationConfig:
    return SimulationConfig(
        lattice=structure.lattice,
        y=structure.y,
        lines=radiation.lines,
        scattering_mode=advanced.scattering_mode,
        composition=advanced.composition,
        two_theta_min=advanced.two_theta_min,
        two_theta_max=advanced.two_theta_max,
        hkl_max=advanced.hkl_max,
        min_peak=advanced.min_peak,
        profile_kind=advanced.profile_kind,
        fwhm_deg=advanced.fwhm,
        pseudo_voigt_eta=advanced.eta,
        spectrum_points=advanced.spectrum_points,
        include_lorentz_polarization=advanced.include_lorentz_polarization,
        include_multiplicity=advanced.include_multiplicity,
        include_cell_volume=advanced.include_cell_volume,
    )


@st.cache_data(max_entries=32, show_spinner=False)
def calculate_cached(config: SimulationConfig) -> SimulationResult:
    return calculate_simulation(config)
