from __future__ import annotations

import math
import re
from collections.abc import Sequence

from pymatgen.analysis.diffraction.xrd import ATOMIC_SCATTERING_PARAMS
from pymatgen.core.periodic_table import Element

from orthoxrd.constants import SCATTERING_FACTOR_COEFFICIENT
from orthoxrd.models import ElementFraction


def atomic_form_factor(symbol: str, s_a_inv: float) -> float:
    if not math.isfinite(s_a_inv) or s_a_inv < 0:
        raise ValueError("s must be non-negative")
    normalized_symbol = normalize_symbol(symbol)
    if normalized_symbol not in ATOMIC_SCATTERING_PARAMS:
        raise ValueError(f"no XRD scattering parameters for {normalized_symbol}")
    s2 = s_a_inv * s_a_inv
    total = 0.0
    for pair in ATOMIC_SCATTERING_PARAMS[normalized_symbol]:
        coefficient = float(pair[0])
        exponent = float(pair[1])
        total += coefficient * math.exp(-exponent * s2)
    atomic_number = float(Element(normalized_symbol).Z)
    return atomic_number - SCATTERING_FACTOR_COEFFICIENT * s2 * total


def normalize_symbol(symbol: str) -> str:
    stripped = symbol.strip()
    if not stripped:
        raise ValueError("element symbol is empty")
    if len(stripped) == 1:
        return stripped.upper()
    return stripped[0].upper() + stripped[1:].lower()


def normalize_composition(composition: Sequence[ElementFraction]) -> tuple[ElementFraction, ...]:
    if not composition:
        raise ValueError("composition is empty")
    total = sum(item.fraction for item in composition)
    if total <= 0:
        raise ValueError("composition total must be positive")
    return tuple(
        ElementFraction(symbol=normalize_symbol(item.symbol), fraction=item.fraction / total)
        for item in composition
    )


def effective_form_factor(composition: Sequence[ElementFraction], s_a_inv: float) -> float:
    normalized = normalize_composition(composition)
    return sum(item.fraction * atomic_form_factor(item.symbol, s_a_inv) for item in normalized)


def parse_composition(text: str) -> tuple[ElementFraction, ...]:
    entries = re.split(r"[,;\n]+", text)
    parsed: list[ElementFraction] = []
    for entry in entries:
        stripped = entry.strip()
        if not stripped:
            continue
        parts = re.split(r"[:=\s]+", stripped)
        if len(parts) != 2:
            raise ValueError(f"cannot parse composition entry: {stripped}")
        parsed.append(ElementFraction(symbol=parts[0], fraction=float(parts[1])))
    return normalize_composition(parsed)


def composition_to_text(composition: Sequence[ElementFraction]) -> str:
    normalized = normalize_composition(composition)
    return ", ".join(f"{item.symbol}:{item.fraction:g}" for item in normalized)
