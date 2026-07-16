from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import product

from pymatgen.core import Lattice as PymatgenLattice

from orthoxrd.models import LatticeParameters
from orthoxrd.structure_factor import cmcm_4c_positions

Vector3 = tuple[float, float, float]
ZERO_SHUFFLE_Y = 0.25


@dataclass(frozen=True, slots=True)
class ShuffleSiteGeometry:
    site_index: int
    reference_fractional: Vector3
    current_fractional: Vector3
    reference_cartesian_a: Vector3
    current_cartesian_a: Vector3
    displacement_cartesian_a: Vector3


@dataclass(frozen=True, slots=True)
class CellEdgeGeometry:
    start_cartesian_a: Vector3
    end_cartesian_a: Vector3


@dataclass(frozen=True, slots=True)
class CmcmShuffleGeometry:
    lattice: LatticeParameters
    reference_y: float
    current_y: float
    sites: tuple[ShuffleSiteGeometry, ...]
    cell_edges: tuple[CellEdgeGeometry, ...]


def build_cmcm_shuffle_geometry(
    lattice: LatticeParameters,
    y: float,
) -> CmcmShuffleGeometry:
    """Pair zero-shuffle and current Cmcm 4c sites in one continuous cell."""
    pymatgen_lattice = PymatgenLattice.orthorhombic(lattice.a, lattice.b, lattice.c)
    reference_positions = cmcm_4c_positions(ZERO_SHUFFLE_Y)
    current_positions = cmcm_4c_positions(y)
    sites: list[ShuffleSiteGeometry] = []
    for index, (reference, current) in enumerate(
        zip(reference_positions, current_positions, strict=True)
    ):
        translation: Vector3 = (
            float(-math.floor(reference[0])),
            float(-math.floor(reference[1])),
            float(-math.floor(reference[2])),
        )
        reference_fractional = _add(reference, translation)
        current_fractional = _add(current, translation)
        reference_cartesian = _clean(pymatgen_lattice.get_cartesian_coords(reference_fractional))
        current_cartesian = _clean(pymatgen_lattice.get_cartesian_coords(current_fractional))
        sites.append(
            ShuffleSiteGeometry(
                site_index=index,
                reference_fractional=reference_fractional,
                current_fractional=current_fractional,
                reference_cartesian_a=reference_cartesian,
                current_cartesian_a=current_cartesian,
                displacement_cartesian_a=_subtract(
                    current_cartesian,
                    reference_cartesian,
                ),
            )
        )
    return CmcmShuffleGeometry(
        lattice=lattice,
        reference_y=ZERO_SHUFFLE_Y,
        current_y=y,
        sites=tuple(sites),
        cell_edges=_cell_edges(pymatgen_lattice),
    )


def _cell_edges(lattice: PymatgenLattice) -> tuple[CellEdgeGeometry, ...]:
    edges: list[CellEdgeGeometry] = []
    for corner in product((0.0, 1.0), repeat=3):
        for axis in range(3):
            if corner[axis] != 0.0:
                continue
            end = list(corner)
            end[axis] = 1.0
            edges.append(
                CellEdgeGeometry(
                    start_cartesian_a=_clean(lattice.get_cartesian_coords(corner)),
                    end_cartesian_a=_clean(lattice.get_cartesian_coords(end)),
                )
            )
    return tuple(edges)


def _add(left: Vector3, right: Vector3) -> Vector3:
    return (
        float(left[0] + right[0]),
        float(left[1] + right[1]),
        float(left[2] + right[2]),
    )


def _subtract(left: Vector3, right: Vector3) -> Vector3:
    return (
        float(left[0] - right[0]),
        float(left[1] - right[1]),
        float(left[2] - right[2]),
    )


def _clean(values: Iterable[float]) -> Vector3:
    raw = tuple(float(value) for value in values)
    if len(raw) != 3:
        raise ValueError("a three-dimensional coordinate is required")
    return (
        _snap_zero(raw[0]),
        _snap_zero(raw[1]),
        _snap_zero(raw[2]),
    )


def _snap_zero(value: float) -> float:
    return 0.0 if abs(value) < 1e-12 else value
