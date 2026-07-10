from __future__ import annotations

from dataclasses import dataclass

from orthoxrd.models import LatticeParameters
from orthoxrd.structure_factor import signed_shuffle_from_y, y_from_shuffle_magnitude


@dataclass(frozen=True, slots=True)
class StructureState:
    lattice: LatticeParameters
    y: float

    @property
    def shuffle_signed(self) -> float:
        return signed_shuffle_from_y(self.y)

    @property
    def shuffle_magnitude(self) -> float:
        return abs(self.shuffle_signed)

    @classmethod
    def from_y(cls, lattice: LatticeParameters, y_value: float) -> StructureState:
        signed_shuffle_from_y(y_value)
        return cls(lattice=lattice, y=y_value)

    @classmethod
    def from_shuffle_magnitude(
        cls,
        lattice: LatticeParameters,
        shuffle_magnitude: float,
    ) -> StructureState:
        return cls.from_y(lattice=lattice, y_value=y_from_shuffle_magnitude(shuffle_magnitude))
