from __future__ import annotations

import csv
import math
from io import StringIO

from orthoxrd.fit_models import FitError, FitIssue, PeakObservation

# Stable template for download / documentation (issue #3).
# Miller indices use the non-negative powder convention (0..hkl_max); see module notes.
# For multi-line radiation (e.g. Cu K-alpha doublet), fill line or line_id
# (line_00, line_01, ...) on every row — empty line hard-fails with multi-line ambiguity.
OBSERVATION_CSV_TEMPLATE = """h,k,l,I_obs,line,weight,sigma,notes
2,0,0,100.0,,,,
1,1,1,250.0,,,,
0,2,0,80.0,,,,
"""

OBSERVATION_CSV_REQUIRED_COLUMNS: tuple[str, ...] = ("h", "k", "l", "I_obs")
OBSERVATION_CSV_OPTIONAL_COLUMNS: tuple[str, ...] = (
    "line",
    "line_id",
    "weight",
    "sigma",
    "notes",
)
OBSERVATION_CSV_ALLOWED_COLUMNS: frozenset[str] = frozenset(
    OBSERVATION_CSV_REQUIRED_COLUMNS + OBSERVATION_CSV_OPTIONAL_COLUMNS
)


def observation_csv_template() -> str:
    """Return the documented observation CSV template content (stable text).

    Notes for authors:
    - Required columns: ``h,k,l,I_obs`` (header names must be exact; no padding).
    - Optional: ``line`` / ``line_id``, ``weight``, ``sigma``, ``notes``.
    - Multi-line sources: set ``line`` or ``line_id`` on every row (e.g. ``line_00``).
    - Miller indices follow the forward-model non-negative convention
      (``0..hkl_max``). Negative indices are accepted by the fit engine and
      mapped to ``(|h|,|k|,|l|)`` for matching (powder-equivalent octant).
    - At most one row per (HKL, radiation line); duplicates hard-fail.
    """
    return OBSERVATION_CSV_TEMPLATE


def parse_observation_csv(text: str) -> tuple[PeakObservation, ...]:
    """Parse and validate an observation CSV into fit-ready records.

    Required columns: h, k, l, I_obs.
    Optional: line / line_id, weight, sigma, notes.

    Header names must match the allowed set exactly (no leading/trailing
    whitespace). Physical file line numbers (1-based, header = 1) are stored on
    each ``PeakObservation.row`` and on ``FitIssue.row``. Blank lines are skipped
    for parsing but do not shift subsequent row numbers.

    Raises FitError with row-level issues; never silently drops invalid rows.
    """
    # Use csv.reader (not DictReader) so reader.line_num tracks physical lines.
    # DictReader silently skips empty rows and would desync row identity.
    stream = StringIO(text)
    reader = csv.reader(stream)
    try:
        header_cells = next(reader)
    except StopIteration:
        raise FitError((FitIssue(1, "header", "", "CSV header is required"),)) from None

    if not header_cells or not any(cell.strip() for cell in header_cells):
        raise FitError((FitIssue(1, "header", "", "CSV header is required"),))

    headers = tuple(header_cells)

    # Reject padded headers so keys match the canonical names used by _parse_row.
    padded = [header for header in headers if header != header.strip()]
    if padded:
        raise FitError(
            tuple(
                FitIssue(
                    1,
                    header.strip() or "header",
                    header,
                    "CSV header names must not have leading or trailing whitespace",
                )
                for header in padded
            )
        )

    normalized = tuple(header.strip() for header in headers)
    if len(normalized) != len(set(normalized)):
        raise FitError((FitIssue(1, "header", "", "duplicate CSV columns are not allowed"),))

    missing = [column for column in OBSERVATION_CSV_REQUIRED_COLUMNS if column not in normalized]
    if missing:
        raise FitError(
            tuple(
                FitIssue(1, column, "", f"required column '{column}' is missing")
                for column in missing
            )
        )

    unknown = sorted(set(normalized) - OBSERVATION_CSV_ALLOWED_COLUMNS)
    if unknown:
        raise FitError(
            tuple(
                FitIssue(1, column, "", "unsupported observation column") for column in unknown
            )
        )

    issues: list[FitIssue] = []
    observations: list[PeakObservation] = []
    saw_data_row = False
    for cells in reader:
        row_number = reader.line_num
        if not cells or not any(cell.strip() for cell in cells):
            continue
        saw_data_row = True
        # Pad/truncate to header width the same way DictReader would.
        values: list[str | None] = list(cells)
        if len(values) < len(normalized):
            values.extend([None] * (len(normalized) - len(values)))
        row = {
            name: (values[index] if index < len(values) else None)
            for index, name in enumerate(normalized)
        }
        parsed = _parse_row(row, row_number, issues)
        if parsed is not None:
            observations.append(parsed)

    if not saw_data_row:
        raise FitError(
            (FitIssue(2, "row", "", "at least one observation row is required"),)
        )

    if issues:
        raise FitError(tuple(issues))
    return tuple(observations)


def _parse_row(
    row: dict[str, str | None],
    row_number: int,
    issues: list[FitIssue],
) -> PeakObservation | None:
    h_value = _require_int(row, row_number, "h", issues)
    k_value = _require_int(row, row_number, "k", issues)
    l_value = _require_int(row, row_number, "l", issues)
    i_obs = _require_positive_float(row, row_number, "I_obs", issues)

    line_col = _optional_text(row, "line")
    line_id_col = _optional_text(row, "line_id")
    if (
        line_col is not None
        and line_id_col is not None
        and line_col != line_id_col
    ):
        issues.append(
            FitIssue(
                row_number,
                "line",
                f"{line_col}|{line_id_col}",
                "line and line_id both set but disagree; use one or make them equal",
            )
        )
        return None
    line = line_col if line_col is not None else line_id_col

    weight = _optional_positive_float(row, row_number, "weight", issues)
    sigma = _optional_positive_float(row, row_number, "sigma", issues)
    notes = _optional_text(row, "notes") or ""

    if h_value is None or k_value is None or l_value is None or i_obs is None:
        return None
    # When both weight and sigma are present, weight takes precedence in the engine.
    return PeakObservation(
        h=h_value,
        k=k_value,
        l=l_value,
        I_obs=i_obs,
        row=row_number,
        line=line,
        weight=weight,
        sigma=sigma,
        notes=notes,
    )


def _text(row: dict[str, str | None], column: str) -> str:
    return (row.get(column) or "").strip()


def _optional_text(row: dict[str, str | None], column: str) -> str | None:
    value = _text(row, column)
    return value if value else None


def _require_int(
    row: dict[str, str | None],
    row_number: int,
    column: str,
    issues: list[FitIssue],
) -> int | None:
    raw = _text(row, column)
    if not raw:
        issues.append(FitIssue(row_number, column, raw, f"{column} is required"))
        return None
    try:
        value = int(raw)
    except ValueError:
        issues.append(FitIssue(row_number, column, raw, f"{column} must be an integer"))
        return None
    return value


def _require_positive_float(
    row: dict[str, str | None],
    row_number: int,
    column: str,
    issues: list[FitIssue],
) -> float | None:
    raw = _text(row, column)
    if not raw:
        issues.append(FitIssue(row_number, column, raw, f"{column} is required"))
        return None
    try:
        value = float(raw)
    except ValueError:
        issues.append(FitIssue(row_number, column, raw, f"{column} must be a number"))
        return None
    if not math.isfinite(value) or value <= 0:
        issues.append(
            FitIssue(row_number, column, raw, f"{column} must be finite and positive")
        )
        return None
    return value


def _optional_positive_float(
    row: dict[str, str | None],
    row_number: int,
    column: str,
    issues: list[FitIssue],
) -> float | None:
    raw = _text(row, column)
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        issues.append(FitIssue(row_number, column, raw, f"{column} must be a number"))
        return None
    if not math.isfinite(value) or value <= 0:
        issues.append(
            FitIssue(row_number, column, raw, f"{column} must be finite and positive")
        )
        return None
    return value
