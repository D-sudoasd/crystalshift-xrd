from __future__ import annotations

import csv
import hashlib
import tempfile
import time
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from orthoxrd.export_schema import CsvValue

MAX_ZIP_BYTES = 512 * 1024 * 1024
_EXPORT_DIR = Path(tempfile.gettempdir()) / "orthoxrd_exports"


@dataclass(frozen=True, slots=True)
class ExportFileMeta:
    rows: int
    columns: int
    sha256: str


@dataclass(frozen=True, slots=True)
class PreparedExport:
    path: str
    size_bytes: int
    sha256: str
    config_hash: str


def create_export_path() -> Path:
    _EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_stale_exports()
    with tempfile.NamedTemporaryFile(
        prefix="orthoxrd_",
        suffix=".zip",
        dir=_EXPORT_DIR,
        delete=False,
    ) as handle:
        return Path(handle.name)


def write_csv_entry(
    archive: zipfile.ZipFile,
    name: str,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, CsvValue]],
) -> ExportFileMeta:
    digest = hashlib.sha256()
    row_count = 0
    with archive.open(name, mode="w") as destination:
        header = _csv_line(fieldnames)
        destination.write(header)
        digest.update(header)
        for row in rows:
            payload = _csv_line([row.get(field, "") for field in fieldnames])
            destination.write(payload)
            digest.update(payload)
            row_count += 1
    return ExportFileMeta(row_count, len(fieldnames), digest.hexdigest())


def write_text_entry(
    archive: zipfile.ZipFile,
    name: str,
    text: str,
) -> ExportFileMeta:
    payload = text.encode("utf-8")
    archive.writestr(name, payload)
    return ExportFileMeta(_text_rows(text), 1, hashlib.sha256(payload).hexdigest())


def finalize_export(path: Path, config_hash: str) -> PreparedExport:
    size = path.stat().st_size
    if size > MAX_ZIP_BYTES:
        path.unlink(missing_ok=True)
        raise ValueError("prepared ZIP exceeds the 512 MiB limit")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return PreparedExport(str(path), size, digest.hexdigest(), config_hash)


def cleanup_export(export: PreparedExport) -> None:
    path = Path(export.path)
    if path.parent == _EXPORT_DIR and path.name.startswith("orthoxrd_"):
        path.unlink(missing_ok=True)


def cleanup_stale_exports() -> None:
    if not _EXPORT_DIR.exists():
        return
    cutoff = time.time() - 24 * 60 * 60
    for path in _EXPORT_DIR.glob("orthoxrd_*.zip"):
        if path.stat().st_mtime < cutoff:
            path.unlink(missing_ok=True)


def _csv_line(values: Sequence[CsvValue | str]) -> bytes:
    output = StringIO()
    writer = csv.writer(output, lineterminator=chr(10))
    writer.writerow(values)
    return output.getvalue().encode("utf-8")


def _text_rows(text: str) -> int:
    return len(text.splitlines())
