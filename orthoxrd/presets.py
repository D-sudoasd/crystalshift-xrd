from __future__ import annotations

from dataclasses import dataclass

from orthoxrd.models import ElementFraction, LatticeParameters, RadiationLine


@dataclass(frozen=True, slots=True)
class LatticePreset:
    label: str
    lattice: LatticeParameters
    y: float
    note: str


TI2448_COMPOSITION = (
    ElementFraction("Ti", 64.0),
    ElementFraction("Nb", 24.0),
    ElementFraction("Zr", 4.0),
    ElementFraction("Sn", 8.0),
)

LATTICE_PRESETS = {
    "S08 Table 5.5": LatticePreset(
        label="S08 Table 5.5",
        lattice=LatticeParameters(a=3.187, b=4.800, c=4.659),
        y=0.214,
        note="Rietveld stress 665 MPa, source paper Table 5.5",
    ),
    "S15 Table 5.5": LatticePreset(
        label="S15 Table 5.5",
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.222,
        note="Rietveld stress 797 MPa, source paper Table 5.5",
    ),
    "S20 Table 5.5": LatticePreset(
        label="S20 Table 5.5",
        lattice=LatticeParameters(a=3.234, b=4.744, c=4.666),
        y=0.225,
        note="Rietveld stress 852 MPa, source paper Table 5.5",
    ),
    "S40 Table 5.5": LatticePreset(
        label="S40 Table 5.5",
        lattice=LatticeParameters(a=3.254, b=4.732, c=4.660),
        y=0.228,
        note="Rietveld stress 778 MPa, source paper Table 5.5",
    ),
    "Figure 3.9 example": LatticePreset(
        label="Figure 3.9 example",
        lattice=LatticeParameters(a=3.220, b=4.840, c=4.750),
        y=0.214,
        note="Peak-position example from source paper Fig. 3.9; y is not specified there",
    ),
}

RADIATION_PRESETS = {
    "Cu K-alpha doublet": (
        RadiationLine("Cu K-alpha1", 1.540593, 2.0),
        RadiationLine("Cu K-alpha2", 1.544414, 1.0),
    ),
    "Co K-alpha doublet": (
        RadiationLine("Co K-alpha1", 1.788965, 2.0),
        RadiationLine("Co K-alpha2", 1.792850, 1.0),
    ),
    "Mo K-alpha doublet": (
        RadiationLine("Mo K-alpha1", 0.709317, 2.0),
        RadiationLine("Mo K-alpha2", 0.713607, 1.0),
    ),
    "30 keV synchrotron": (RadiationLine("30 keV", 0.4132806614, 1.0),),
}
