from __future__ import annotations

from typing import Literal, assert_never

from orthoxrd.structure_factor import (
    signed_shuffle_from_y,
    validate_y,
    y_from_shuffle_magnitude,
)

StructureAxis = Literal["y", "signed_shuffle", "shuffle_magnitude"]
StructureBranch = Literal["lower", "upper"]


def structure_coordinate_from_y(y: float, axis: StructureAxis) -> float:
    """Project canonical Cmcm 4c Wyckoff ``y`` onto a display coordinate."""
    signed_shuffle = signed_shuffle_from_y(y)
    match axis:
        case "y":
            return y
        case "signed_shuffle":
            return signed_shuffle
        case "shuffle_magnitude":
            return abs(signed_shuffle)
        case unreachable:
            assert_never(unreachable)


def y_from_structure_coordinate(
    value: float,
    axis: StructureAxis,
    *,
    branch: StructureBranch | None = None,
) -> float:
    """Resolve a display coordinate to canonical ``y`` without losing branch data."""
    match axis:
        case "y":
            validate_y(value)
            return value
        case "signed_shuffle":
            y = 0.25 + value / 2.0
            validate_y(y)
            return y
        case "shuffle_magnitude":
            if branch is None:
                raise ValueError("shuffle magnitude requires an explicit lower or upper branch")
            if branch not in {"lower", "upper"}:
                raise ValueError("branch must be lower or upper")
            return y_from_shuffle_magnitude(value, upper_branch=branch == "upper")
        case unreachable:
            assert_never(unreachable)


def structure_branch_from_y(y: float) -> StructureBranch | None:
    """Return the magnitude branch, or ``None`` at the zero-shuffle point."""
    validate_y(y)
    if y < 0.25:
        return "lower"
    if y > 0.25:
        return "upper"
    return None
