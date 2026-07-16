from __future__ import annotations

import math
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from numbers import Integral, Real
from pathlib import Path

import xlsxwriter
from xlsxwriter.format import Format
from xlsxwriter.worksheet import Worksheet

from orthoxrd.export_schema import CsvValue

EXCEL_MAX_ROWS = 1_048_576
EXCEL_MAX_COLUMNS = 16_384
EXCEL_MAX_CELL_CHARACTERS = 32_767
_METADATA_SHEETS = ("README", "Parameters", "Columns")


@dataclass(frozen=True, slots=True)
class ExcelColumnSpec:
    description: str
    unit: str = ""
    data_type: str = "auto"


@dataclass(frozen=True, slots=True)
class ExcelParameterSpec:
    section: str
    name: str
    value: CsvValue | bool | None
    description: str
    unit: str = ""
    role: str = ""


@dataclass(frozen=True, slots=True)
class ExcelSheetSpec:
    name: str
    fields: Sequence[str]
    rows: Iterable[Mapping[str, CsvValue | bool | None]]
    columns: Mapping[str, ExcelColumnSpec] = field(default_factory=dict)
    text_fields: frozenset[str] = frozenset()


def build_excel_workbook(
    *,
    title: str,
    sheets: Iterable[ExcelSheetSpec],
    parameters: Iterable[ExcelParameterSpec] = (),
    readme: Sequence[str] = (),
    max_rows_per_sheet: int = EXCEL_MAX_ROWS,
    max_columns_per_sheet: int = EXCEL_MAX_COLUMNS,
) -> bytes:
    """Build an analysis-ready XLSX workbook from existing export row mappings."""
    sheet_specs = tuple(sheets)
    parameter_specs = tuple(parameters)
    _validate_limits(max_rows_per_sheet, max_columns_per_sheet)
    _validate_specs(sheet_specs, parameter_specs, readme)
    skipped_sheets = tuple(
        spec for spec in sheet_specs if len(tuple(spec.fields)) > max_columns_per_sheet
    )
    writable_sheets = tuple(
        spec for spec in sheet_specs if len(tuple(spec.fields)) <= max_columns_per_sheet
    )

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
        path = Path(handle.name)
    try:
        workbook = xlsxwriter.Workbook(
            str(path),
            {
                "constant_memory": True,
                "strings_to_formulas": False,
                "strings_to_urls": False,
            },
        )
        try:
            formats = _formats(workbook)
            _write_readme(
                workbook,
                title,
                readme,
                skipped_sheets,
                max_rows_per_sheet,
                max_columns_per_sheet,
                formats,
            )
            _write_parameters(workbook, parameter_specs, formats)
            _write_columns(workbook, sheet_specs, formats)
            _write_data_sheets(
                workbook,
                writable_sheets,
                max_rows_per_sheet,
                formats,
            )
        finally:
            workbook.close()
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)


def _validate_limits(max_rows_per_sheet: int, max_columns_per_sheet: int) -> None:
    if not 2 <= max_rows_per_sheet <= EXCEL_MAX_ROWS:
        raise ValueError(f"max_rows_per_sheet must lie within 2..{EXCEL_MAX_ROWS}")
    if not 1 <= max_columns_per_sheet <= EXCEL_MAX_COLUMNS:
        raise ValueError(f"max_columns_per_sheet must lie within 1..{EXCEL_MAX_COLUMNS}")


def _validate_specs(
    sheets: Sequence[ExcelSheetSpec],
    parameters: Sequence[ExcelParameterSpec],
    readme: Sequence[str],
) -> None:
    if len(parameters) + 1 > EXCEL_MAX_ROWS:
        raise ValueError("Parameters sheet exceeds the Excel row limit")
    if sum(len(tuple(spec.fields)) for spec in sheets) + 1 > EXCEL_MAX_ROWS:
        raise ValueError("Columns sheet exceeds the Excel row limit")
    if len(readme) + 7 + len(sheets) > EXCEL_MAX_ROWS:
        raise ValueError("README sheet exceeds the Excel row limit")
    seen = {name.casefold() for name in _METADATA_SHEETS}
    for spec in sheets:
        _validate_sheet_name(spec.name)
        folded = spec.name.casefold()
        if folded in seen:
            raise ValueError(f"duplicate or reserved Excel sheet name: {spec.name}")
        seen.add(folded)
        fields = tuple(spec.fields)
        if not fields:
            raise ValueError(f"Excel sheet {spec.name!r} requires at least one field")
        if len(fields) != len(set(fields)):
            raise ValueError(f"Excel sheet {spec.name!r} has duplicate fields")
        unknown = set(spec.columns) - set(fields)
        if unknown:
            raise ValueError(
                f"Excel sheet {spec.name!r} has metadata for unknown fields: "
                + ", ".join(sorted(unknown))
            )


def _validate_sheet_name(name: str) -> None:
    if not name or len(name) > 31:
        raise ValueError("Excel sheet names must contain 1..31 characters")
    if any(character in name for character in "[]:*?/\\"):
        raise ValueError(f"invalid Excel sheet name: {name}")
    if name.startswith("'") or name.endswith("'"):
        raise ValueError(f"invalid Excel sheet name: {name}")


def _formats(workbook: xlsxwriter.Workbook) -> dict[str, Format]:
    return {
        "title": workbook.add_format({"bold": True, "font_size": 16}),
        "section": workbook.add_format({"bold": True, "font_size": 12}),
        "header": workbook.add_format(
            {
                "bold": True,
                "bg_color": "#D9EAF7",
                "border": 1,
                "text_wrap": True,
            }
        ),
        "text": workbook.add_format({"num_format": "@"}),
    }


def _write_readme(
    workbook: xlsxwriter.Workbook,
    title: str,
    readme: Sequence[str],
    skipped_sheets: Sequence[ExcelSheetSpec],
    max_rows_per_sheet: int,
    max_columns_per_sheet: int,
    formats: Mapping[str, Format],
) -> None:
    sheet = workbook.add_worksheet("README")
    _write_string(sheet, 0, 0, title, formats["title"])
    _write_string(sheet, 2, 0, "Notes", formats["section"])
    row_index = 3
    for line in readme:
        _write_string(sheet, row_index, 0, str(line), formats["text"])
        row_index += 1
    _write_string(sheet, row_index + 1, 0, "Excel limits", formats["section"])
    _write_string(
        sheet,
        row_index + 2,
        0,
        (
            "No data is silently truncated. Data sheets that exceed Excel's "
            f"configured {max_rows_per_sheet:,}-row limit are split into numbered parts; "
            f"sheets over {max_columns_per_sheet:,} columns are explicitly reported "
            "as skipped."
        ),
        formats["text"],
    )
    notice_row = row_index + 3
    for spec in skipped_sheets:
        _write_string(
            sheet,
            notice_row,
            0,
            (
                f"Skipped data sheet '{spec.name}': {len(tuple(spec.fields)):,} columns "
                f"exceed the configured {max_columns_per_sheet:,}-column limit."
            ),
            formats["text"],
        )
        notice_row += 1
    sheet.set_column(0, 0, 110)


def _write_parameters(
    workbook: xlsxwriter.Workbook,
    parameters: Sequence[ExcelParameterSpec],
    formats: Mapping[str, Format],
) -> None:
    sheet = workbook.add_worksheet("Parameters")
    fields = ("section", "parameter", "value", "unit", "role", "description")
    _write_header(sheet, fields, formats["header"])
    for row_index, parameter in enumerate(parameters, start=1):
        values: tuple[CsvValue | bool | None, ...] = (
            parameter.section,
            parameter.name,
            parameter.value,
            parameter.unit,
            parameter.role,
            parameter.description,
        )
        for column_index, value in enumerate(values):
            _write_value(sheet, row_index, column_index, value, formats["text"])
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, max(1, len(parameters)), len(fields) - 1)
    sheet.set_column(0, 0, 20)
    sheet.set_column(1, 1, 26)
    sheet.set_column(2, 4, 16)
    sheet.set_column(5, 5, 60)


def _write_columns(
    workbook: xlsxwriter.Workbook,
    sheets: Sequence[ExcelSheetSpec],
    formats: Mapping[str, Format],
) -> None:
    sheet = workbook.add_worksheet("Columns")
    fields = ("sheet", "column", "data_type", "unit", "description")
    _write_header(sheet, fields, formats["header"])
    row_index = 1
    for spec in sheets:
        for name in spec.fields:
            metadata = spec.columns.get(
                name,
                ExcelColumnSpec(description=f"Export column {name}."),
            )
            data_type = "text" if _force_text(name, spec.text_fields) else metadata.data_type
            values = (spec.name, name, data_type, metadata.unit, metadata.description)
            for column_index, value in enumerate(values):
                _write_string(
                    sheet,
                    row_index,
                    column_index,
                    str(value),
                    formats["text"],
                )
            row_index += 1
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, max(1, row_index - 1), len(fields) - 1)
    sheet.set_column(0, 0, 20)
    sheet.set_column(1, 1, 54)
    sheet.set_column(2, 3, 18)
    sheet.set_column(4, 4, 70)


def _write_data_sheets(
    workbook: xlsxwriter.Workbook,
    specs: Sequence[ExcelSheetSpec],
    max_rows_per_sheet: int,
    formats: Mapping[str, Format],
) -> None:
    declared_names = {spec.name.casefold() for spec in specs}
    used_names = {name.casefold() for name in _METADATA_SHEETS}
    for spec in specs:
        _write_split_data_sheet(
            workbook,
            spec,
            max_rows_per_sheet,
            formats,
            declared_names,
            used_names,
        )


def _write_split_data_sheet(
    workbook: xlsxwriter.Workbook,
    spec: ExcelSheetSpec,
    max_rows_per_sheet: int,
    formats: Mapping[str, Format],
    declared_names: set[str],
    used_names: set[str],
) -> None:
    fields = tuple(spec.fields)
    max_data_rows = max_rows_per_sheet - 1
    part_number = 1
    sheet = _add_data_sheet(
        workbook,
        spec.name,
        part_number,
        fields,
        formats,
        declared_names,
        used_names,
    )
    rows_in_part = 0
    for row in spec.rows:
        if rows_in_part == max_data_rows:
            _finish_data_sheet(sheet, fields, rows_in_part)
            part_number += 1
            sheet = _add_data_sheet(
                workbook,
                spec.name,
                part_number,
                fields,
                formats,
                declared_names,
                used_names,
            )
            rows_in_part = 0
        excel_row = rows_in_part + 1
        for column_index, name in enumerate(fields):
            _write_value(
                sheet,
                excel_row,
                column_index,
                row.get(name, ""),
                formats["text"],
                force_text=_force_text(name, spec.text_fields),
            )
        rows_in_part += 1
    _finish_data_sheet(sheet, fields, rows_in_part)


def _add_data_sheet(
    workbook: xlsxwriter.Workbook,
    base_name: str,
    part_number: int,
    fields: Sequence[str],
    formats: Mapping[str, Format],
    declared_names: set[str],
    used_names: set[str],
) -> Worksheet:
    name = _part_sheet_name(base_name, part_number)
    folded = name.casefold()
    if folded in used_names or (part_number > 1 and folded in declared_names):
        raise ValueError(f"generated Excel sheet name collides with another sheet: {name}")
    used_names.add(folded)
    sheet = workbook.add_worksheet(name)
    _write_header(sheet, fields, formats["header"])
    for column_index, name in enumerate(fields):
        sheet.set_column(column_index, column_index, min(max(len(name) + 2, 12), 36))
    return sheet


def _finish_data_sheet(
    sheet: Worksheet,
    fields: Sequence[str],
    data_row_count: int,
) -> None:
    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, data_row_count, len(fields) - 1)


def _part_sheet_name(base_name: str, part_number: int) -> str:
    if part_number == 1:
        return base_name
    suffix = f"_part{part_number:02d}"
    return f"{base_name[: 31 - len(suffix)]}{suffix}"


def _write_header(sheet: Worksheet, fields: Sequence[str], header_format: Format) -> None:
    for column_index, name in enumerate(fields):
        _write_string(sheet, 0, column_index, name, header_format)
    sheet.set_row(0, 30)


def _write_value(
    sheet: Worksheet,
    row: int,
    column: int,
    value: CsvValue | bool | None,
    text_format: Format,
    *,
    force_text: bool = False,
) -> None:
    if force_text:
        _write_string(sheet, row, column, "" if value is None else str(value), text_format)
        return
    if isinstance(value, str):
        _write_string(sheet, row, column, value, text_format)
        return
    if value is None:
        sheet.write_blank(row, column, None)
        return
    if isinstance(value, bool):
        sheet.write_boolean(row, column, value)
        return
    if isinstance(value, Integral):
        sheet.write_number(row, column, int(value))
        return
    if isinstance(value, Real):
        number = float(value)
        if math.isfinite(number):
            sheet.write_number(row, column, number)
        else:
            _write_string(sheet, row, column, str(number), text_format)
        return
    raise TypeError(f"unsupported Excel cell value: {type(value).__name__}")


def _write_string(
    sheet: Worksheet,
    row: int,
    column: int,
    value: str,
    cell_format: Format,
) -> None:
    if len(value) > EXCEL_MAX_CELL_CHARACTERS:
        raise ValueError(
            "Excel cell text exceeds the 32,767-character limit "
            f"at row {row + 1}, column {column + 1}"
        )
    sheet.write_string(row, column, value, cell_format)


def _force_text(field_name: str, extra_fields: frozenset[str]) -> bool:
    if field_name in extra_fields:
        return True
    normalized = field_name.casefold()
    return (
        normalized == "hkl"
        or normalized.startswith("hkl_")
        or normalized == "id"
        or normalized.endswith("_id")
        or "label" in normalized
    )


__all__ = [
    "EXCEL_MAX_CELL_CHARACTERS",
    "EXCEL_MAX_COLUMNS",
    "EXCEL_MAX_ROWS",
    "ExcelColumnSpec",
    "ExcelParameterSpec",
    "ExcelSheetSpec",
    "build_excel_workbook",
]
