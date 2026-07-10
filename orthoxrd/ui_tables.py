from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping, Sequence
from io import StringIO

from orthoxrd.export_schema import (
    PEAK_EVOLUTION_FIELDS,
    SPECTRA_LONG_FIELDS,
    CsvValue,
)


def rows_to_csv(
    rows: Iterable[Mapping[str, CsvValue]],
    fieldnames: Sequence[str],
) -> str:
    output = StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=list(fieldnames),
        lineterminator=chr(10),
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def spectrum_to_csv(points: Iterable[tuple[float, float]]) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator=chr(10))
    writer.writerow(["two_theta_deg", "intensity"])
    writer.writerows(points)
    return output.getvalue()


__all__ = [
    "PEAK_EVOLUTION_FIELDS",
    "SPECTRA_LONG_FIELDS",
    "CsvValue",
    "rows_to_csv",
    "spectrum_to_csv",
]
