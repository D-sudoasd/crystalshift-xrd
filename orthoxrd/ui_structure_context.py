from __future__ import annotations

from orthoxrd.i18n import t
from orthoxrd.structure_coordinates import (
    structure_branch_from_y,
    structure_coordinate_from_y,
)
from orthoxrd.structure_factor import normalized_shuffle_from_y


def structure_context_caption(y: float) -> str:
    """Describe the active structure without implying a change to the plot x-axis."""
    signed = structure_coordinate_from_y(y, "signed_shuffle")
    magnitude = structure_coordinate_from_y(y, "shuffle_magnitude")
    normalized = normalized_shuffle_from_y(y)
    branch = structure_branch_from_y(y)
    branch_label = t(f"branch.{branch}") if branch is not None else "y=0.25"
    return t(
        "structure.context.caption",
        y=y,
        signed=signed,
        magnitude=magnitude,
        normalized=normalized,
        branch=branch_label,
    )


__all__ = ["structure_context_caption"]
