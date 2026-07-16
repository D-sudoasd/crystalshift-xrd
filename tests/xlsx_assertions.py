from __future__ import annotations

import io
import zipfile
from xml.etree import ElementTree as ET

_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def xlsx_sheet_names(payload: bytes) -> list[str]:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    return [
        sheet.attrib["name"]
        for sheet in workbook.findall(f".//{{{_MAIN_NS}}}sheet")
    ]


def xlsx_sheet_xml(payload: bytes, sheet_name: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships.findall(f"{{{_PKG_REL_NS}}}Relationship")
        }
        for sheet in workbook.findall(f".//{{{_MAIN_NS}}}sheet"):
            if sheet.attrib["name"] != sheet_name:
                continue
            relation_id = sheet.attrib[f"{{{_DOC_REL_NS}}}id"]
            return archive.read("xl/" + targets[relation_id].lstrip("/"))
    raise AssertionError(f"missing worksheet: {sheet_name}")


def xlsx_sheet_cells(
    payload: bytes,
    sheet_name: str,
) -> dict[str, tuple[str, str]]:
    """Return worksheet cell references as ``(kind, displayed value)`` pairs."""
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        path = _sheet_path(archive, sheet_name)
        shared = _shared_strings(archive)
        root = ET.fromstring(archive.read(path))

    values: dict[str, tuple[str, str]] = {}
    for cell in root.findall(f".//{{{_MAIN_NS}}}c"):
        reference = cell.attrib["r"]
        cell_type = cell.attrib.get("t")
        if cell_type == "inlineStr":
            value = "".join(
                node.text or "" for node in cell.findall(f".//{{{_MAIN_NS}}}t")
            )
            values[reference] = ("text", value)
        elif cell_type == "s":
            index = int(cell.findtext(f"{{{_MAIN_NS}}}v", default="0"))
            values[reference] = ("text", shared[index])
        else:
            values[reference] = (
                "number",
                cell.findtext(f"{{{_MAIN_NS}}}v", default=""),
            )
    return values


def _sheet_path(archive: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    targets = {
        item.attrib["Id"]: item.attrib["Target"]
        for item in relationships.findall(f"{{{_PKG_REL_NS}}}Relationship")
    }
    for sheet in workbook.findall(f".//{{{_MAIN_NS}}}sheet"):
        if sheet.attrib["name"] == sheet_name:
            relation_id = sheet.attrib[f"{{{_DOC_REL_NS}}}id"]
            return "xl/" + targets[relation_id].lstrip("/")
    raise AssertionError(f"missing worksheet: {sheet_name}")


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(node.text or "" for node in item.findall(f".//{{{_MAIN_NS}}}t"))
        for item in root.findall(f"{{{_MAIN_NS}}}si")
    ]
