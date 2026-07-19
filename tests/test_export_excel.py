from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree as ET

from orthoxrd.export_excel import (
    ExcelColumnSpec,
    ExcelParameterSpec,
    ExcelSheetSpec,
    build_excel_workbook,
)

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def test_workbook_is_analysis_ready_and_preserves_hkl_as_safe_text() -> None:
    payload = build_excel_workbook(
        title="CrystalShift XRD current simulation",
        readme=("CSV remains the canonical machine-readable export.",),
        parameters=(
            ExcelParameterSpec(
                section="Structure",
                name="wyckoff_y",
                value=0.222,
                unit="fractional",
                role="input",
                description="Cmcm 4c fractional coordinate.",
            ),
        ),
        sheets=(
            ExcelSheetSpec(
                name="Peaks",
                fields=("hkl", "I_model_peak", "notes"),
                rows=(
                    {
                        "hkl": "021",
                        "I_model_peak": 12.5,
                        "notes": '=HYPERLINK("https://example.invalid","unsafe")',
                    },
                ),
                columns={
                    "hkl": ExcelColumnSpec(
                        data_type="text",
                        description="Reflection label with leading zeroes preserved.",
                    ),
                    "I_model_peak": ExcelColumnSpec(
                        data_type="number",
                        unit="a.u.",
                        description="Calculated model peak intensity.",
                    ),
                    "notes": ExcelColumnSpec(
                        data_type="text",
                        description="User-provided annotation.",
                    ),
                },
            ),
        ),
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        core = archive.read("docProps/core.xml")
        assert b"1980-01-01T00:00:00Z" in core
        sheets = _sheet_paths(archive)
        assert list(sheets) == ["README", "Parameters", "Columns", "Peaks"]

        peaks = _cells(archive, sheets["Peaks"])
        assert peaks["A2"] == ("text", "021")
        assert peaks["B2"] == ("number", "12.5")
        assert peaks["C2"] == (
            "text",
            '=HYPERLINK("https://example.invalid","unsafe")',
        )

        peaks_xml = ET.fromstring(archive.read(sheets["Peaks"]))
        assert peaks_xml.find(f".//{{{_MAIN_NS}}}f") is None


def test_metadata_sheets_explain_parameters_and_source_columns() -> None:
    payload = build_excel_workbook(
        title="Metadata contract",
        parameters=(
            ExcelParameterSpec(
                section="Fit",
                name="observable_mode",
                value="peak_area",
                unit="",
                role="input",
                description="Observed peak area enters the discrete-peak fit.",
            ),
        ),
        sheets=(
            ExcelSheetSpec(
                name="GridScan",
                fields=("y", "scale_s", "chi2"),
                rows=({"y": 0.2, "scale_s": 3.0, "chi2": 1.5},),
                columns={
                    "y": ExcelColumnSpec(
                        data_type="number",
                        description="Wyckoff fractional coordinate.",
                    ),
                    "scale_s": ExcelColumnSpec(
                        data_type="number",
                        description="Closed-form non-negative scale factor.",
                    ),
                    "chi2": ExcelColumnSpec(
                        data_type="number",
                        description="Weighted residual sum of squares.",
                    ),
                },
            ),
        ),
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        sheets = _sheet_paths(archive)
        parameters = _cells(archive, sheets["Parameters"])
        columns = _cells(archive, sheets["Columns"])
        grid = _cells(archive, sheets["GridScan"])

        assert parameters["A2"] == ("text", "Fit")
        assert parameters["B2"] == ("text", "observable_mode")
        assert parameters["C2"] == ("text", "peak_area")
        assert parameters["F2"] == (
            "text",
            "Observed peak area enters the discrete-peak fit.",
        )
        assert columns["A2"] == ("text", "GridScan")
        assert columns["B2"] == ("text", "y")
        assert columns["E2"] == ("text", "Wyckoff fractional coordinate.")
        assert grid["A2"] == ("number", "0.2")
        assert grid["B2"] == ("number", "3")
        assert grid["C2"] == ("number", "1.5")


def test_all_user_strings_are_literal_cells_never_formulas() -> None:
    formula_like = '=HYPERLINK("https://example.invalid","unsafe")'
    payload = build_excel_workbook(
        title=formula_like,
        readme=(formula_like,),
        parameters=(
            ExcelParameterSpec(
                section=formula_like,
                name="notes",
                value=formula_like,
                description=formula_like,
            ),
        ),
        sheets=(
            ExcelSheetSpec(
                name="SafeText",
                fields=("step_label",),
                rows=({"step_label": formula_like},),
                columns={
                    "step_label": ExcelColumnSpec(description=formula_like),
                },
            ),
        ),
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        sheets = _sheet_paths(archive)
        for path in sheets.values():
            root = ET.fromstring(archive.read(path))
            assert root.find(f".//{{{_MAIN_NS}}}f") is None
        assert _cells(archive, sheets["README"])["A1"] == ("text", formula_like)
        assert _cells(archive, sheets["Parameters"])["C2"] == ("text", formula_like)
        assert _cells(archive, sheets["SafeText"])["A2"] == ("text", formula_like)


def test_hkl_ids_and_labels_are_forced_to_text_even_for_numeric_values() -> None:
    payload = build_excel_workbook(
        title="Semantic text fields",
        sheets=(
            ExcelSheetSpec(
                name="Typed",
                fields=("hkl", "series_id", "step_label", "ordinary_number"),
                rows=(
                    {
                        "hkl": 21,
                        "series_id": 21,
                        "step_label": 21,
                        "ordinary_number": 21,
                    },
                ),
            ),
        ),
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        cells = _cells(archive, _sheet_paths(archive)["Typed"])
        assert cells["A2"] == ("text", "21")
        assert cells["B2"] == ("text", "21")
        assert cells["C2"] == ("text", "21")
        assert cells["D2"] == ("number", "21")


def test_large_row_sets_split_without_truncation_and_are_documented() -> None:
    payload = build_excel_workbook(
        title="Split rows",
        sheets=(
            ExcelSheetSpec(
                name="Data",
                fields=("step_id", "value"),
                rows=tuple(
                    {"step_id": f"step_{index:04d}", "value": index}
                    for index in range(5)
                ),
            ),
        ),
        max_rows_per_sheet=4,
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        sheets = _sheet_paths(archive)
        assert list(sheets) == [
            "README",
            "Parameters",
            "Columns",
            "Data",
            "Data_part02",
        ]
        first = _cells(archive, sheets["Data"])
        second = _cells(archive, sheets["Data_part02"])
        assert [first[f"B{row}"] for row in range(2, 5)] == [
            ("number", "0"),
            ("number", "1"),
            ("number", "2"),
        ]
        assert [second[f"B{row}"] for row in range(2, 4)] == [
            ("number", "3"),
            ("number", "4"),
        ]
        readme = "\n".join(value for _, value in _cells(archive, sheets["README"]).values())
        assert "4-row limit" in readme
        assert "split into numbered parts" in readme


def test_overwide_sheet_is_explicitly_skipped_and_documented() -> None:
    payload = build_excel_workbook(
        title="Column limits",
        sheets=(
            ExcelSheetSpec(
                name="Usable",
                fields=("x",),
                rows=({"x": 1.0},),
            ),
            ExcelSheetSpec(
                name="TooWide",
                fields=("a", "b", "c"),
                rows=({"a": 1, "b": 2, "c": 3},),
            ),
        ),
        max_columns_per_sheet=2,
    )

    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        sheets = _sheet_paths(archive)
        assert "Usable" in sheets
        assert "TooWide" not in sheets
        readme = "\n".join(value for _, value in _cells(archive, sheets["README"]).values())
        assert "TooWide" in readme
        assert "3 columns" in readme
        assert "skipped" in readme.lower()


def _sheet_paths(archive: zipfile.ZipFile) -> dict[str, str]:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in relationships.findall(f"{{{_PKG_REL_NS}}}Relationship")
    }
    paths: dict[str, str] = {}
    for sheet in workbook.findall(f".//{{{_MAIN_NS}}}sheet"):
        relation_id = sheet.attrib[f"{{{_DOC_REL_NS}}}id"]
        paths[sheet.attrib["name"]] = "xl/" + targets[relation_id].lstrip("/")
    return paths


def _cells(archive: zipfile.ZipFile, path: str) -> dict[str, tuple[str, str]]:
    shared = _shared_strings(archive)
    root = ET.fromstring(archive.read(path))
    values: dict[str, tuple[str, str]] = {}
    for cell in root.findall(f".//{{{_MAIN_NS}}}c"):
        reference = cell.attrib["r"]
        cell_type = cell.attrib.get("t")
        if cell_type == "inlineStr":
            text = "".join(
                node.text or "" for node in cell.findall(f".//{{{_MAIN_NS}}}t")
            )
            values[reference] = ("text", text)
        elif cell_type == "s":
            index = int(cell.findtext(f"{{{_MAIN_NS}}}v", default="0"))
            values[reference] = ("text", shared[index])
        else:
            values[reference] = (
                "number",
                cell.findtext(f"{{{_MAIN_NS}}}v", default=""),
            )
    return values


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.findall(f".//{{{_MAIN_NS}}}t"))
        for item in root.findall(f"{{{_MAIN_NS}}}si")
    ]
