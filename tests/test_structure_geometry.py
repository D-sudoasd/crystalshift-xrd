from __future__ import annotations

import pytest

from orthoxrd.models import LatticeParameters
from orthoxrd.structure_geometry import build_cmcm_shuffle_geometry


def test_cmcm_shuffle_geometry_pairs_reference_and_current_4c_sites() -> None:
    geometry = build_cmcm_shuffle_geometry(
        LatticeParameters(a=3.187, b=4.8, c=4.659),
        y=0.214,
    )

    expected_reference = (
        (0.0, 0.25, 0.25),
        (0.0, 0.75, 0.75),
        (0.5, 0.75, 0.25),
        (0.5, 0.25, 0.75),
    )
    expected_current = (
        (0.0, 0.214, 0.25),
        (0.0, 0.786, 0.75),
        (0.5, 0.714, 0.25),
        (0.5, 0.286, 0.75),
    )
    expected_displacements = (
        (0.0, -0.1728, 0.0),
        (0.0, 0.1728, 0.0),
        (0.0, -0.1728, 0.0),
        (0.0, 0.1728, 0.0),
    )
    for site, reference, current, displacement in zip(
        geometry.sites,
        expected_reference,
        expected_current,
        expected_displacements,
        strict=True,
    ):
        assert site.reference_fractional == pytest.approx(reference)
        assert site.current_fractional == pytest.approx(current)
        assert site.displacement_cartesian_a == pytest.approx(displacement)


def test_cmcm_shuffle_geometry_contains_the_full_orthorhombic_cell() -> None:
    geometry = build_cmcm_shuffle_geometry(
        LatticeParameters(a=3.0, b=4.0, c=5.0),
        y=0.214,
    )

    assert len(geometry.cell_edges) == 12
    endpoints = {
        tuple(round(value, 12) for value in point)
        for edge in geometry.cell_edges
        for point in (edge.start_cartesian_a, edge.end_cartesian_a)
    }
    assert len(endpoints) == 8
    assert (0.0, 0.0, 0.0) in endpoints
    assert (3.0, 4.0, 5.0) in endpoints
