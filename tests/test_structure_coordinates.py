from __future__ import annotations

import pytest

from orthoxrd.structure_coordinates import (
    structure_branch_from_y,
    structure_coordinate_from_y,
    y_from_structure_coordinate,
)


def test_structure_coordinate_preserves_signed_shuffle_information() -> None:
    assert structure_coordinate_from_y(0.214, "y") == pytest.approx(0.214)
    assert structure_coordinate_from_y(0.214, "signed_shuffle") == pytest.approx(-0.072)
    assert structure_coordinate_from_y(0.214, "shuffle_magnitude") == pytest.approx(0.072)


def test_shuffle_magnitude_inverse_requires_and_respects_branch() -> None:
    with pytest.raises(ValueError, match="branch"):
        y_from_structure_coordinate(0.072, "shuffle_magnitude")

    assert y_from_structure_coordinate(0.072, "shuffle_magnitude", branch="lower") == pytest.approx(
        0.214
    )
    assert y_from_structure_coordinate(0.072, "shuffle_magnitude", branch="upper") == pytest.approx(
        0.286
    )


def test_structure_branch_classifies_both_sides_without_assigning_zero_shuffle() -> None:
    assert structure_branch_from_y(0.214) == "lower"
    assert structure_branch_from_y(0.286) == "upper"
    assert structure_branch_from_y(0.25) is None
