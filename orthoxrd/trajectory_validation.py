from __future__ import annotations

import math

from orthoxrd.batch_models import SweepStep
from orthoxrd.config import SimulationConfig


def step_changes_base(step: SweepStep, base: SimulationConfig) -> bool:
    lattice_values = (
        (step.lattice.a, base.lattice.a),
        (step.lattice.b, base.lattice.b),
        (step.lattice.c, base.lattice.c),
    )
    if any(not math.isclose(left, right, abs_tol=1e-12) for left, right in lattice_values):
        return True
    if not math.isclose(step.y, base.y, abs_tol=1e-12):
        return True
    if len(step.lines) != len(base.lines):
        return True
    return any(
        not math.isclose(step_line.wavelength_a, base_line.wavelength_a, abs_tol=1e-12)
        or not math.isclose(step_line.weight, base_line.weight, abs_tol=1e-12)
        for step_line, base_line in zip(step.lines, base.lines, strict=True)
    )
