from __future__ import annotations

import math

import pytest

from orthoxrd.models import LatticeParameters
from orthoxrd.structure_geometry import build_cmcm_shuffle_geometry
from orthoxrd.ui_plot_structure import plot_cmcm_shuffle_structure


def test_structure_plot_exposes_cell_sites_and_four_shuffle_arrows() -> None:
    geometry = build_cmcm_shuffle_geometry(
        LatticeParameters(a=3.187, b=4.8, c=4.659),
        y=0.214,
    )

    figure = plot_cmcm_shuffle_structure(geometry)

    traces = {trace.name: trace for trace in figure.data}
    assert set(traces) == {
        "cell",
        "y=0.25 reference",
        "shuffle paths",
        "shuffle arrowheads",
        "current Cmcm 4c",
    }
    assert len(traces["y=0.25 reference"].x) == 4
    assert len(traces["current Cmcm 4c"].x) == 4
    arrows = traces["shuffle arrowheads"]
    assert arrows.type == "cone"
    assert len(arrows.x) == 4
    assert list(arrows.u) == pytest.approx([0.0, 0.0, 0.0, 0.0])
    assert list(arrows.v) == pytest.approx([-0.1728, 0.1728, -0.1728, 0.1728])
    assert list(arrows.w) == pytest.approx([0.0, 0.0, 0.0, 0.0])
    assert figure.layout.scene.aspectmode == "data"
    assert figure.layout.scene.camera.projection.type == "orthographic"


def test_structure_plot_omits_undefined_arrows_at_zero_shuffle() -> None:
    geometry = build_cmcm_shuffle_geometry(
        LatticeParameters(a=3.187, b=4.8, c=4.659),
        y=0.25,
    )

    figure = plot_cmcm_shuffle_structure(geometry)

    traces = {trace.name: trace for trace in figure.data}
    assert set(traces) == {"cell", "y=0.25 reference", "current Cmcm 4c"}
    current = traces["current Cmcm 4c"]
    reference = traces["y=0.25 reference"]
    assert list(current.x) == pytest.approx(list(reference.x))
    assert list(current.y) == pytest.approx(list(reference.y))
    assert list(current.z) == pytest.approx(list(reference.z))
    assert all(
        math.isfinite(float(value))
        for trace in figure.data
        for coordinate in (trace.x, trace.y, trace.z)
        for value in coordinate
        if value is not None
    )
