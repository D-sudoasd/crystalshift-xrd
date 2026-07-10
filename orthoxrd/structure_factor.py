from __future__ import annotations

import cmath
import math

from orthoxrd.constants import (
    SHUFFLE_MAGNITUDE_MAX,
    SHUFFLE_MAGNITUDE_MIN,
    WYCKOFF_Y_MAX,
    WYCKOFF_Y_MIN,
)


def validate_y(y: float) -> None:
    if not math.isfinite(y) or y < WYCKOFF_Y_MIN or y > WYCKOFF_Y_MAX:
        raise ValueError(f"Wyckoff y must be between {WYCKOFF_Y_MIN:.3f} and {WYCKOFF_Y_MAX:.3f}")


def signed_shuffle_from_y(y: float) -> float:
    validate_y(y)
    return 2.0 * (y - 0.25)


def y_from_shuffle_magnitude(shuffle: float, *, upper_branch: bool = False) -> float:
    if (
        not math.isfinite(shuffle)
        or shuffle < SHUFFLE_MAGNITUDE_MIN
        or shuffle > SHUFFLE_MAGNITUDE_MAX
    ):
        raise ValueError(
            "shuffle magnitude must be between "
            f"{SHUFFLE_MAGNITUDE_MIN:.3f} and {SHUFFLE_MAGNITUDE_MAX:.3f}"
        )
    if upper_branch:
        return 0.25 + shuffle / 2.0
    return 0.25 - shuffle / 2.0


def cmcm_4c_positions(y: float) -> tuple[tuple[float, float, float], ...]:
    validate_y(y)
    return (
        (0.0, y, 0.25),
        (0.0, -y, 0.75),
        (0.5, 0.5 + y, 0.25),
        (0.5, 0.5 - y, 0.75),
    )


def cmcm_4c_structure_factor(h: int, k: int, l: int, y: float, form_factor: float) -> complex:
    positions = cmcm_4c_positions(y)
    phase_sum = 0.0 + 0.0j
    for x_coord, y_coord, z_coord in positions:
        phase = 2.0 * math.pi * (h * x_coord + k * y_coord + l * z_coord)
        phase_sum += cmath.exp(1j * phase)
    return form_factor * phase_sum


def cmcm_4c_structure_factor_squared(
    h: int,
    k: int,
    l: int,
    y: float,
    form_factor: float,
) -> float:
    f_hkl = cmcm_4c_structure_factor(h, k, l, y, form_factor)
    value = float((f_hkl * f_hkl.conjugate()).real)
    if abs(value) < 1e-12:
        return 0.0
    return value


def analytic_unit_structure_factor_squared(h: int, k: int, l: int, y: float) -> float:
    validate_y(y)
    if (h + k) % 2 != 0:
        return 0.0
    angle = 2.0 * math.pi * k * y - math.pi * l / 2.0
    return 16.0 * math.cos(angle) ** 2
