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
DETERMINISTIC_ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
DETERMINISTIC_ZIP_COMPRESSLEVEL = 9
DETERMINISTIC_ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)


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


def open_deterministic_zip(path: Path) -> zipfile.ZipFile:
    """Open an export archive with stable compression settings."""
    return zipfile.ZipFile(
        path,
        mode="w",
        compression=DETERMINISTIC_ZIP_COMPRESSION,
        compresslevel=DETERMINISTIC_ZIP_COMPRESSLEVEL,
    )


def write_csv_entry(
    archive: zipfile.ZipFile,
    name: str,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, CsvValue]],
) -> ExportFileMeta:
    digest = hashlib.sha256()
    row_count = 0
    with archive.open(_zip_info(name), mode="w", force_zip64=True) as destination:
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
    _write_bytes_entry(archive, name, payload)
    return ExportFileMeta(_text_rows(text), 1, hashlib.sha256(payload).hexdigest())


def write_binary_entry(
    archive: zipfile.ZipFile,
    name: str,
    payload: bytes,
    *,
    rows: int = 0,
    columns: int = 1,
) -> ExportFileMeta:
    """Write an opaque binary export member and record its exact checksum."""
    if rows < 0 or columns < 1:
        raise ValueError("binary export metadata requires rows >= 0 and columns >= 1")
    _write_bytes_entry(archive, name, payload)
    return ExportFileMeta(rows, columns, hashlib.sha256(payload).hexdigest())


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


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=DETERMINISTIC_ZIP_DATE_TIME)
    info.compress_type = DETERMINISTIC_ZIP_COMPRESSION
    info.create_system = 0
    info.external_attr = 0
    info.internal_attr = 0
    return info


def _write_bytes_entry(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    archive.writestr(
        _zip_info(name),
        payload,
        compress_type=DETERMINISTIC_ZIP_COMPRESSION,
        compresslevel=DETERMINISTIC_ZIP_COMPRESSLEVEL,
    )
