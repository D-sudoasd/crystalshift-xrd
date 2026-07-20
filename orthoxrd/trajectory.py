from __future__ import annotations

import csv
import math
from io import StringIO

from orthoxrd.batch_models import (
    ShuffleBranch,
    SweepStep,
    TrajectoryConfig,
    TrajectoryIssue,
    TrajectoryValidationError,
)
from orthoxrd.config import SimulationConfig
from orthoxrd.models import LatticeParameters, RadiationLine
from orthoxrd.powder import energy_kev_to_wavelength_a
from orthoxrd.structure_factor import (
    normalized_shuffle_from_y,
    signed_shuffle_from_y,
    y_from_shuffle_magnitude,
)
from orthoxrd.trajectory_validation import step_changes_base

_ALLOWED_COLUMNS = {
    "step_label",
    "a_A",
    "b_A",
    "c_A",
    "y",
    "shuffle_magnitude",
    "shuffle_branch",
    "energy_keV",
    "wavelength_A",
}
_SCIENTIFIC_COLUMNS = _ALLOWED_COLUMNS - {"step_label", "shuffle_branch"}


def parse_trajectory_csv(text: str, base: SimulationConfig) -> TrajectoryConfig:
    reader = csv.DictReader(StringIO(text))
    headers = tuple(reader.fieldnames or ())
    if not headers:
        raise TrajectoryValidationError(
            (TrajectoryIssue(1, "header", "", "CSV header is required"),)
        )
    unknown = sorted(set(headers) - _ALLOWED_COLUMNS)
    if unknown:
        raise TrajectoryValidationError(
            tuple(
                TrajectoryIssue(1, column, "", "unsupported trajectory column")
                for column in unknown
            )
        )

    raw_rows = [row for row in reader if any((value or "").strip() for value in row.values())]
    if not raw_rows:
        raise TrajectoryValidationError(
            (TrajectoryIssue(2, "row", "", "at least one trajectory row is required"),)
        )
    if len(raw_rows) > 1001:
        raise TrajectoryValidationError(
            (TrajectoryIssue(1002, "row", "", "trajectory is limited to 1001 rows"),)
        )
    if not any(
        (row.get(column) or "").strip() for row in raw_rows for column in _SCIENTIFIC_COLUMNS
    ):
        raise TrajectoryValidationError(
            (TrajectoryIssue(2, "row", "", "at least one scientific value must be supplied"),)
        )

    issues: list[TrajectoryIssue] = []
    steps: list[SweepStep] = []
    labels: set[str] = set()
    for index, row in enumerate(raw_rows):
        row_number = index + 2
        step = _parse_row(row, row_number, index, base, issues)
        if step is None:
            continue
        if step.label in labels:
            issues.append(
                TrajectoryIssue(row_number, "step_label", step.label, "step label must be unique")
            )
        labels.add(step.label)
        steps.append(step)
    if issues:
        raise TrajectoryValidationError(tuple(issues))
    if not any(step_changes_base(step, base) for step in steps):
        raise TrajectoryValidationError(
            (
                TrajectoryIssue(
                    2,
                    "row",
                    "",
                    "at least one scientific parameter must change from the base config",
                ),
            )
        )
    return TrajectoryConfig(base=base, steps=tuple(steps))


def _parse_row(
    row: dict[str, str | None],
    row_number: int,
    index: int,
    base: SimulationConfig,
    issues: list[TrajectoryIssue],
) -> SweepStep | None:
    step_id = f"step_{index:04d}"
    label = (row.get("step_label") or "").strip() or step_id
    a_value = _optional_float(row, row_number, "a_A", issues)
    b_value = _optional_float(row, row_number, "b_A", issues)
    c_value = _optional_float(row, row_number, "c_A", issues)
    y_value = _optional_float(row, row_number, "y", issues)
    shuffle = _optional_float(row, row_number, "shuffle_magnitude", issues)
    energy = _optional_float(row, row_number, "energy_keV", issues)
    wavelength = _optional_float(row, row_number, "wavelength_A", issues)
    branch_text = (row.get("shuffle_branch") or "lower").strip().lower()
    if branch_text not in {"lower", "upper"}:
        issues.append(
            TrajectoryIssue(
                row_number,
                "shuffle_branch",
                branch_text,
                "branch must be lower or upper",
            )
        )
        return None
    branch: ShuffleBranch = "upper" if branch_text == "upper" else "lower"
    before = len(issues)
    _check_bounds(
        row_number, a_value, b_value, c_value, y_value, shuffle, energy, wavelength, issues
    )
    if len(issues) > before:
        return None

    resolved_y = base.y if y_value is None and shuffle is None else y_value
    if shuffle is not None:
        mapped_y = y_from_shuffle_magnitude(shuffle, upper_branch=branch == "upper")
        if resolved_y is not None and not math.isclose(
            resolved_y,
            mapped_y,
            rel_tol=1e-8,
            abs_tol=1e-8,
        ):
            issues.append(
                TrajectoryIssue(
                    row_number,
                    "shuffle_magnitude",
                    _text(row, "shuffle_magnitude"),
                    "shuffle magnitude is inconsistent with y and branch",
                )
            )
            return None
        resolved_y = mapped_y
    if resolved_y is None:
        resolved_y = base.y

    resolved_wavelength = wavelength
    if energy is not None:
        energy_wavelength = energy_kev_to_wavelength_a(energy)
        if wavelength is not None and not math.isclose(
            wavelength,
            energy_wavelength,
            rel_tol=1e-8,
            abs_tol=1e-12,
        ):
            issues.append(
                TrajectoryIssue(
                    row_number,
                    "wavelength_A",
                    _text(row, "wavelength_A"),
                    "wavelength is inconsistent with energy",
                )
            )
            return None
        resolved_wavelength = energy_wavelength
    lines = base.lines
    if resolved_wavelength is not None:
        lines = (RadiationLine(f"trajectory {row_number}", resolved_wavelength, 1.0),)

    lattice = LatticeParameters(
        base.lattice.a if a_value is None else a_value,
        base.lattice.b if b_value is None else b_value,
        base.lattice.c if c_value is None else c_value,
    )
    return SweepStep(
        index=index,
        step_id=step_id,
        label=label,
        axis="trajectory",
        axis_value=float(index),
        lattice=lattice,
        y=resolved_y,
        shuffle_signed=signed_shuffle_from_y(resolved_y),
        shuffle_magnitude=abs(signed_shuffle_from_y(resolved_y)),
        normalized_shuffle=normalized_shuffle_from_y(resolved_y),
        lines=lines,
    )


def _optional_float(
    row: dict[str, str | None],
    row_number: int,
    column: str,
    issues: list[TrajectoryIssue],
) -> float | None:
    value = _text(row, column)
    if not value:
        return None
    try:
        parsed = float(value)
    except ValueError:
        issues.append(TrajectoryIssue(row_number, column, value, "value must be numeric"))
        return None
    if not math.isfinite(parsed):
        issues.append(TrajectoryIssue(row_number, column, value, "value must be finite"))
        return None
    return parsed


def _check_bounds(
    row: int,
    a_value: float | None,
    b_value: float | None,
    c_value: float | None,
    y_value: float | None,
    shuffle: float | None,
    energy: float | None,
    wavelength: float | None,
    issues: list[TrajectoryIssue],
) -> None:
    for column, value in (("a_A", a_value), ("b_A", b_value), ("c_A", c_value)):
        if value is not None and not 1.0 <= value <= 20.0:
            issues.append(TrajectoryIssue(row, column, str(value), "value must be within 1-20 A"))
    for column, value in (("y", y_value), ("shuffle_magnitude", shuffle)):
        if value is not None and not 0.0 <= value <= 0.5:
            issues.append(TrajectoryIssue(row, column, str(value), "value must be within 0-0.5"))
    if energy is not None and not 1.0 <= energy <= 200.0:
        issues.append(
            TrajectoryIssue(row, "energy_keV", str(energy), "value must be within 1-200 keV")
        )
    if wavelength is not None and not 0.05 <= wavelength <= 5.0:
        issues.append(
            TrajectoryIssue(row, "wavelength_A", str(wavelength), "value must be within 0.05-5 A")
        )


def _text(row: dict[str, str | None], column: str) -> str:
    return (row.get(column) or "").strip()
