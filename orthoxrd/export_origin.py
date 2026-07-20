from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Final

from orthoxrd.batch_models import SweepResult
from orthoxrd.config import SimulationConfig
from orthoxrd.export_schema import CsvValue
from orthoxrd.ui_plot_state import PlotState


@dataclass(frozen=True, slots=True)
class SweepExportPlotState:
    two_theta_minimum: float
    two_theta_maximum: float
    sweep_axis_minimum: float
    sweep_axis_maximum: float
    display_axis: str | None = None

ORIGIN_COLUMN_MAP_FIELDS: Final[tuple[str, ...]] = (
    "file",
    "column",
    "designation",
    "long_name",
    "unit",
    "comment",
)


def plot_state_json(
    config: SimulationConfig,
    state: PlotState | SweepExportPlotState | None = None,
) -> str:
    payload: dict[str, object] = {
        "x_axis": "2theta",
        "x_minimum": config.two_theta_min,
        "x_maximum": config.two_theta_max,
        "y_auto": True,
        "y_minimum": 0.0,
        "y_maximum": 105.0,
        "display_only": True,
    }
    if isinstance(state, SweepExportPlotState):
        payload.update(
            {
                "x_axis": "2theta",
                "x_minimum": state.two_theta_minimum,
                "x_maximum": state.two_theta_maximum,
                "two_theta_minimum": state.two_theta_minimum,
                "two_theta_maximum": state.two_theta_maximum,
                "sweep_axis_minimum": state.sweep_axis_minimum,
                "sweep_axis_maximum": state.sweep_axis_maximum,
                "sweep_display_axis": state.display_axis or "native",
            }
        )
    elif state is not None:
        payload.update(
            {
                "x_axis": state.x_axis,
                "x_minimum": state.x_minimum,
                "x_maximum": state.x_maximum,
                "y_auto": state.y_auto,
                "y_minimum": state.y_minimum,
                "y_maximum": state.y_maximum,
            }
        )
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n"


def current_origin_rows() -> Iterable[Mapping[str, CsvValue]]:
    spectrum = (
        ("point_index", "L", "Point index", "", "Stable row index"),
        ("two_theta_deg", "X", "2theta", "deg", "Primary plotting coordinate"),
        ("q_primary_A_inv", "X", "q primary", "A^-1", "Alternative X coordinate"),
        ("d_primary_A", "X", "d primary", "A", "Alternative reversed X coordinate"),
        ("intensity_model", "Y", "Model intensity", "a.u.", "Unnormalized model profile"),
        ("intensity_rel_local", "Y", "Relative intensity", "%", "Current-pattern normalization"),
    )
    peaks = (
        ("two_theta_deg", "X", "Peak 2theta", "deg", "Bragg peak center"),
        ("y", "X", "Wyckoff y", "", "Active Cmcm 4c fractional coordinate"),
        ("hkl", "L", "HKL", "", "Reflection label"),
        ("line", "L", "Radiation line", "", "Radiation label"),
        ("F2", "Y", "Structure factor squared", "a.u.", "Calculated F squared"),
        ("F_abs", "Y", "Structure factor magnitude", "a.u.", "Calculated absolute F"),
        (
            "multiplicity_structure_factor_sq",
            "Y",
            "N x F2",
            "a.u.",
            "Crystallographic multiplicity times F squared",
        ),
        (
            "material_scattering_factor_R_hkl",
            "Y",
            "R hkl with LP",
            "model A^-6",
            "N x F2 x LP / V^2; model reference factor",
        ),
        (
            "material_scattering_factor_R_hkl_no_lp",
            "Y",
            "R hkl without LP",
            "model A^-6",
            "N x F2 / V^2; use only with correspondingly corrected peak areas",
        ),
        ("I_model_peak", "Y", "Model peak intensity", "a.u.", "Corrected model intensity"),
        ("I_rel_local", "Y", "Relative peak intensity", "%", "Current-pattern normalization"),
    )
    yield from _mapped("spectrum.csv", spectrum)
    yield from _mapped("peaks.csv", peaks)


def sweep_origin_rows(result: SweepResult) -> Iterable[Mapping[str, CsvValue]]:
    long_columns = (
        ("two_theta_deg", "X", "2theta", "deg", "Heatmap X"),
        ("axis_value", "Y", "Sweep coordinate", "", "Heatmap Y"),
        ("intensity_model", "Z", "Model intensity", "a.u.", "Heatmap Z"),
        ("intensity_rel_global", "Z", "Global relative intensity", "%", "Comparable Z"),
        ("intensity_rel_local", "Z", "Local relative intensity", "%", "Shape-only Z"),
        ("step_id", "L", "Step ID", "", "Stable step identifier"),
    )
    yield from _mapped("spectra_long.csv", long_columns)
    peak_columns = (
        ("axis_value", "X", "Sweep coordinate", "", "Evolution X"),
        ("hkl", "L", "HKL", "", "Reflection label"),
        ("series_id", "L", "Series ID", "", "Stable line and HKL identifier"),
        ("F2", "Y", "Structure factor squared", "a.u.", "Calculated F squared"),
        (
            "multiplicity_structure_factor_sq",
            "Y",
            "N x F2",
            "a.u.",
            "Crystallographic multiplicity times F squared",
        ),
        (
            "material_scattering_factor_R_hkl",
            "Y",
            "R hkl with LP",
            "model A^-6",
            "N x F2 x LP / V^2; unnormalized model reference",
        ),
        (
            "material_scattering_factor_R_hkl_no_lp",
            "Y",
            "R hkl without LP",
            "model A^-6",
            "N x F2 / V^2; unnormalized model reference",
        ),
        ("I_model_peak", "Y", "Model peak intensity", "a.u.", "Corrected model intensity"),
        ("I_rel_global", "Y", "Global relative peak intensity", "%", "Comparable evolution"),
    )
    yield from _mapped("peak_evolution_long.csv", peak_columns)
    step_columns = (
        ("step_id", "L", "Step ID", "", "Stable step identifier"),
        ("axis_value", "X", "Sweep coordinate", "", "Primary evolution coordinate"),
        ("y", "Y", "Wyckoff y", "", "4c fractional coordinate"),
        ("shuffle_magnitude", "Y", "Shuffle magnitude", "", "Unsigned basal shuffle"),
        (
            "normalized_shuffle",
            "Y",
            "Normalized shuffle",
            "1",
            "Basal-shuffle progress |s|/0.5 in [0,1]",
        ),
        ("a_A", "Y", "Lattice a", "A", "Orthorhombic lattice parameter"),
        ("b_A", "Y", "Lattice b", "A", "Orthorhombic lattice parameter"),
        ("c_A", "Y", "Lattice c", "A", "Orthorhombic lattice parameter"),
        ("primary_energy_keV", "Y", "Energy", "keV", "Primary radiation energy"),
    )
    yield from _mapped("sweep_steps.csv", step_columns)
    yield from _mapped(
        "series_map.csv",
        (
            ("series_id", "L", "Series ID", "", "Stable line and HKL identifier"),
            ("hkl", "L", "HKL", "", "Reflection label"),
            ("line_id", "L", "Line ID", "", "Stable radiation identifier"),
        ),
    )
    series_ids = sorted(
        {peak.series_id for step in result.steps for peak in step.peaks}
    )
    for filename, long_name, unit in (
        ("peak_evolution_matrix_F2.csv", "Structure factor squared", "a.u."),
        ("peak_evolution_matrix_N_F2.csv", "N x F2", "a.u."),
        (
            "peak_evolution_matrix_R_hkl_with_LP.csv",
            "R hkl with LP",
            "model A^-6",
        ),
        (
            "peak_evolution_matrix_R_hkl_no_LP.csv",
            "R hkl without LP",
            "model A^-6",
        ),
        ("peak_evolution_matrix_I_model.csv", "Model peak intensity", "a.u."),
        ("peak_evolution_matrix_I_rel_global.csv", "Global relative peak intensity", "%"),
    ):
        yield _row(filename, "step_id", "L", "Step ID", "", "Matrix row identifier")
        for series_id in series_ids:
            yield _row(filename, series_id, "Y", long_name, unit, "One HKL series column")
    for filename in (
        "spectra_matrix_model.csv",
        "spectra_matrix_global.csv",
        "spectra_matrix_local.csv",
    ):
        yield _row(filename, "two_theta_deg", "X", "2theta", "deg", "Matrix row coordinate")
        for step in result.steps:
            yield _row(
                filename,
                step.step.step_id,
                "Z",
                step.step.label,
                "",
                "One spectrum column; map with sweep_steps.csv",
            )


def origin_import_script() -> str:
    return '''"""Import an Orthorhombic XRD export into Origin.

Run inside Origin embedded Python, or from external Python with originpro installed.
The script prepares either a matrix-style worksheet for a regular sweep or an XYZ
worksheet for a row-wise trajectory. Create the graph with Plot > Contour > Heatmap.
"""
from __future__ import annotations

import csv
from pathlib import Path

import originpro as op

ROOT = Path(__file__).resolve().parent


def _read(name):
    with (ROOT / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _new_xyz(rows):
    sheet = op.new_sheet("w", "XRD_XYZ")
    sheet.from_list(0, [float(row["two_theta_deg"]) for row in rows], "2theta", "deg")
    sheet.from_list(1, [float(row["axis_value"]) for row in rows], "sweep coordinate", "")
    sheet.from_list(
        2,
        [float(row["intensity_rel_global"]) for row in rows],
        "global relative intensity",
        "%",
    )
    sheet.cols_axis("XYZ", 0, 2)
    return sheet


def _new_matrix_table():
    rows = _read("spectra_matrix_global.csv")
    fields = list(rows[0])
    sheet = op.new_sheet("w", "XRD_Matrix_Table")
    for index, field in enumerate(fields):
        values = [float(row[field]) for row in rows]
        sheet.from_list(index, values, field, "deg" if index == 0 else "%")
    sheet.cols_axis("X", 0, 0)
    sheet.cols_axis("Y", 1, len(fields) - 1)
    return sheet


steps = _read("sweep_steps.csv")
is_trajectory = any(row.get("sweep_axis") == "trajectory" for row in steps)
target = _new_xyz(_read("spectra_long.csv")) if is_trajectory else _new_matrix_table()
target.activate()
print(
    "Prepared XYZ data." if is_trajectory else "Prepared regular sweep matrix table.",
    "Use Plot > Contour > Heatmap; see ORIGIN_README.md for column mapping.",
)
'''


def origin_readme() -> str:
    return """# Origin workflow

origin_import.py works with Origin embedded Python or external Python plus
originpro. Run it from the extracted ZIP directory.

- Regular one-axis sweep: the script imports spectra_matrix_global.csv as a
  matrix-style worksheet. Column names are stable step IDs; map values and labels
  with sweep_steps.csv.
- CSV trajectory: the script converts spectra_long.csv into contiguous XYZ
  columns (2theta, axis_value, I_rel_global).
- In Origin, activate the prepared sheet and choose
  Plot > Contour > Heatmap.
- Use I_rel_global to compare amplitude across steps. I_rel_local is only for
  comparing profile shape after each step has independently been scaled to 100.
- origin_column_map.csv records Long Name, unit, designation, and meaning for
  each analysis column.

For current-pattern line plots, import spectrum.csv, designate
two_theta_deg as X, and choose intensity_model or intensity_rel_local as Y.
"""


def _mapped(
    filename: str,
    definitions: Iterable[tuple[str, str, str, str, str]],
) -> Iterable[Mapping[str, CsvValue]]:
    for column, designation, long_name, unit, comment in definitions:
        yield _row(filename, column, designation, long_name, unit, comment)


def _row(
    filename: str,
    column: str,
    designation: str,
    long_name: str,
    unit: str,
    comment: str,
) -> Mapping[str, CsvValue]:
    return {
        "file": filename,
        "column": column,
        "designation": designation,
        "long_name": long_name,
        "unit": unit,
        "comment": comment,
    }
