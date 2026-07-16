from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from orthoxrd.export_excel_packages import build_f2_excel_workbook
from orthoxrd.export_schema import F2_EVOLUTION_FIELDS
from orthoxrd.locales.zh import ZH_TEXT
from orthoxrd.ui_f2 import F2_EXPORT_FIELDS
from orthoxrd.ui_plot_f2 import plot_f2_evolution
from orthoxrd.ui_structure_context import structure_context_caption
from orthoxrd.ui_tables import rows_to_csv
from tests.xlsx_assertions import xlsx_sheet_cells, xlsx_sheet_names

APP_PATH = Path(__file__).parents[1] / "app.py"
NAV_OPTIONS = [
    ZH_TEXT["nav.pattern"],
    ZH_TEXT["nav.peaks"],
    ZH_TEXT["nav.f2"],
    ZH_TEXT["nav.sweep"],
    ZH_TEXT["nav.fit"],
    ZH_TEXT["nav.method"],
]


def test_f2_rows_keep_display_and_canonical_structure_coordinates() -> None:
    _, rows = plot_f2_evolution(
        [(0, 2, 1)],
        axis="signed_shuffle",
        start=-0.072,
        stop=0.072,
        points=3,
        branch="lower",
        active_y=0.214,
    )

    assert [row["axis_value"] for row in rows] == pytest.approx([-0.072, 0.0, 0.072])
    assert [row["axis_code"] for row in rows] == ["signed_shuffle"] * 3
    assert [row["y"] for row in rows] == pytest.approx([0.214, 0.25, 0.286])
    assert [row["shuffle_signed"] for row in rows] == pytest.approx([-0.072, 0.0, 0.072])
    assert [row["shuffle_magnitude"] for row in rows] == pytest.approx([0.072, 0.0, 0.072])
    assert [row["branch"] for row in rows] == ["lower", "reference", "upper"]
    assert [row["hkl"] for row in rows] == ["021"] * 3
    exported = rows_to_csv(rows, F2_EXPORT_FIELDS)
    assert exported.splitlines()[0] == (
        "axis_value,hkl,F2,axis_code,y,shuffle_signed,shuffle_magnitude,branch"
    )
    assert ",021," in exported


def test_f2_magnitude_rows_use_the_selected_upper_branch() -> None:
    _, rows = plot_f2_evolution(
        [(0, 2, 1)],
        axis="shuffle_magnitude",
        start=0.0,
        stop=0.072,
        points=2,
        branch="upper",
        active_y=0.286,
    )

    assert [row["axis_value"] for row in rows] == pytest.approx([0.0, 0.072])
    assert [row["y"] for row in rows] == pytest.approx([0.25, 0.286])
    assert [row["shuffle_signed"] for row in rows] == pytest.approx([0.0, 0.072])
    assert [row["branch"] for row in rows] == ["reference", "upper"]


def test_f2_excel_workbook_preserves_hkl_and_documents_the_model() -> None:
    _, rows = plot_f2_evolution(
        [(0, 2, 1)],
        axis="signed_shuffle",
        start=-0.072,
        stop=0.072,
        points=3,
        branch="lower",
        active_y=0.214,
    )

    workbook = build_f2_excel_workbook(
        rows,
        axis="signed_shuffle",
        branch="lower",
        start=-0.072,
        stop=0.072,
        points=3,
        active_y=0.214,
    )

    assert F2_EXPORT_FIELDS == F2_EVOLUTION_FIELDS
    assert xlsx_sheet_names(workbook) == [
        "README",
        "Parameters",
        "Columns",
        "F2Evolution",
    ]
    data = xlsx_sheet_cells(workbook, "F2Evolution")
    assert data["B1"] == ("text", "hkl")
    assert data["B2"] == ("text", "021")
    assert data["D2"] == ("text", "signed_shuffle")
    assert data["H2"] == ("text", "lower")

    columns = xlsx_sheet_cells(workbook, "Columns")
    metadata = {
        columns[f"B{row}"][1]: columns[f"C{row}"][1]
        for row in range(2, 100)
        if columns.get(f"A{row}") == ("text", "F2Evolution")
    }
    assert metadata["hkl"] == "text"
    assert metadata["axis_code"] == "text"
    assert metadata["branch"] == "text"

    readme = "\n".join(
        value for kind, value in xlsx_sheet_cells(workbook, "README").values() if kind == "text"
    )
    assert "F2 = 16*cos" in readme
    assert "manifest.json" not in readme


def test_f2_magnitude_active_marker_is_not_mirrored_onto_the_wrong_branch() -> None:
    matching, _ = plot_f2_evolution(
        [(0, 2, 1)],
        axis="shuffle_magnitude",
        start=0.0,
        stop=0.166,
        points=10,
        branch="upper",
        active_y=0.286,
    )
    opposite, _ = plot_f2_evolution(
        [(0, 2, 1)],
        axis="shuffle_magnitude",
        start=0.0,
        stop=0.166,
        points=10,
        branch="lower",
        active_y=0.286,
    )
    outside_range, _ = plot_f2_evolution(
        [(0, 2, 1)],
        axis="shuffle_magnitude",
        start=0.1,
        stop=0.166,
        points=10,
        branch="upper",
        active_y=0.286,
    )

    assert len(matching.layout.shapes) == 1
    assert matching.layout.shapes[0].x0 == pytest.approx(0.072)
    assert not opposite.layout.shapes
    assert not outside_range.layout.shapes


def test_structure_context_caption_keeps_physical_plot_axis_explicit() -> None:
    with patch("orthoxrd.i18n.get_lang", return_value="zh"):
        caption = structure_context_caption(
            0.214,
        )

    assert "当前结构：y=0.214000" in caption
    assert "有符号 shuffle=-0.072000" in caption
    assert "shuffle 幅度=0.072000" in caption
    assert "下分支" in caption
    assert "物理横轴仍为 2θ、q 或 d" in caption


def test_f2_structure_slider_is_preview_only() -> None:
    app = AppTest.from_file(str(APP_PATH))
    app.run(timeout=30)
    y_input = next(
        item
        for item in app.main.number_input
        if item.label == ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5)
    )
    original_y = float(y_input.value)
    navigation = next(
        item for item in app.main.segmented_control if list(item.options) == NAV_OPTIONS
    )
    navigation.select("f2").run(timeout=30)

    structure_slider = next(
        item
        for item in app.main.slider
        if item.label
        == (
            f"{ZH_TEXT['f2.structure_preview.slider']} · "
            f"{ZH_TEXT['axis.shuffle_magnitude']}"
        )
    )
    structure_slider.set_value(0.1).run(timeout=30)

    assert not app.exception
    y_after = next(
        item
        for item in app.main.number_input
        if item.label == ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5)
    )
    assert float(y_after.value) == original_y
    assert len(app.get("plotly_chart")) == 2
