# Orthorhombic XRD Simulator

Orthorhombic XRD Simulator is a Streamlit scientific workbench for theoretical powder XRD of an orthorhombic `Cmcm` phase with the `4c` Wyckoff position. It is designed for studying how lattice constants, Wyckoff `y`, basal shuffle, and incident X-ray energy or wavelength affect peak positions, structure factors, and calculated powder profiles.

Version: `2.1.0`
Export schema: `2.1`

The application is a theoretical model. It does not replace a Rietveld refinement package or provide experimental intensity calibration.

## Highlights

- Edit incident source, energy or wavelength, `a`, `b`, `c`, `y`, and shuffle directly on the first screen.
- Inspect static powder patterns with `2theta`, `q_primary`, or `d_primary` axes.
- Use Live evolution to drag one active parameter locally through exact precomputed frames. The browser does not run frame interpolation or trigger a Python rerun for every slider movement.
- Preserve multi-line radiation sources during live energy or wavelength changes, including relative line wavelengths and weights.
- Examine peak tables, HKL selection, F2 evolution, heatmaps, waterfalls, and peak-evolution curves.
- Export current, sweep, trajectory, and live-evolution results as schema 2.1 CSV/ZIP packages for Origin or Python.
- Keep scientific inputs, formulas, units, normalisation rules, configuration hashes, and file checksums in the exported metadata.

## Quick Start

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m streamlit run app.py --server.port 8508
```

### Linux or macOS

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m streamlit run app.py --server.port 8508
```

Open <http://localhost:8508/> in a browser.

Runtime requirements are Python `>=3.11`, NumPy, Plotly, pymatgen, and Streamlit. The optional development dependencies add pytest, Ruff, and BasedPyright.

## Typical Workflow

1. Select an incident source and enter energy in `keV` or wavelength in `A`.
2. Set lattice constants and either Wyckoff `y` or shuffle magnitude. The application keeps the relation
   `shuffle_signed = 2 * (y - 0.25)` and `shuffle_magnitude = abs(shuffle_signed)` visible.
3. Use Advanced settings for scattering mode, composition, simulation `2theta` window, HKL limit, peak profile, and intensity corrections.
4. Use Pattern for static comparison or Live evolution for one-parameter exploration.
5. Use Sweep for explicit batch calculations. A changed configuration makes an earlier sweep preview stale and disables its export until `Run sweep` is pressed again.

## Live Evolution

The Live view uses a backend/browser split:

- Scientific frames are calculated in NumPy `float64`.
- The browser receives a compact `float32` drawing payload only after the exact frames are prepared.
- Slider `input` events switch among exact frames locally.
- Slider `change` events commit one final value to the main parameter state.
- The baseline remains fixed until `Set current as baseline` is used.
- The optional difference trace is calculated against the fixed baseline; it is not an experimental residual.

Supported active axes are `y`, shuffle magnitude, `a`, `b`, `c`, energy, and wavelength. Energy or wavelength scans use each frame's own wavelength for `2theta`, `q`, and `d`. Multi-line sources keep their relative line structure when a live frame is committed.

## Scientific Contract

The `Cmcm 4c` positions are:

```text
(0, y, 1/4), (0, -y, 3/4),
(1/2, 1/2 + y, 1/4), (1/2, 1/2 - y, 3/4)
```

The principal relations are:

```text
shuffle_signed = 2 * (y - 0.25)
shuffle_magnitude = abs(shuffle_signed)
wavelength_A = 12.398419843320026 / energy_keV
q_A_inv = 2 * pi / d_A
```

The calculated peak model intensity is:

```text
I_model_peak = F2
                * applied_multiplicity
                * applied_LP
                * applied_volume_factor
                * radiation_line_weight
```

`I_profile_model` is the unnormalised theoretical profile. `I_rel_local` is normalised independently for each spectrum or sweep step. `I_rel_global` uses one maximum across the complete sweep and is the appropriate field for comparing calculated amplitude evolution between steps.

All intensity fields are calculated model values. They are not measured raw intensity, absolute calibrated intensity, fitted intensity, phase fraction, or a substitute for experimental uncertainty analysis.

## Sweep and Trajectory Inputs

One-dimensional sweep axes and supported ranges are:

| Axis | Range |
| --- | --- |
| `y` | `0` to `0.5` |
| `shuffle_magnitude` | `0` to `0.5` |
| `a_A`, `b_A`, `c_A` | `1` to `20 A` |
| `energy_keV` | `1` to `200 keV` |
| `wavelength_A` | `0.05` to `5 A` |

The default Ti-Nb lower branch is `y=0.167..0.250`, corresponding to shuffle magnitude `0..0.166`. The upper shuffle branch is available where applicable.

Trajectory CSV columns are:

```text
step_label,a_A,b_A,c_A,y,shuffle_magnitude,shuffle_branch,energy_keV,wavelength_A
```

Rows are processed in input order and are not expanded into a Cartesian product. Empty fields inherit the active base configuration. `step_label` values must be unique. If both `y` and shuffle are supplied they must agree within `1e-8`; if both energy and wavelength are supplied they must satisfy `lambda = hc / E`.

Execution limits are 1001 steps, 10,000 points per spectrum, 2,000,000 total spectrum cells, 1,000,000 peak records, and a 512 MiB final ZIP.

## Export Packages

The current simulation ZIP contains `spectrum.csv`, `peaks.csv`, `config.json`, `manifest.json`, `plot_state.json`, and Origin helpers.

The sweep ZIP contains long-form tables, local/global/model spectrum matrices, `sweep_steps.csv`, `series_map.csv`, three peak-evolution matrices, configuration metadata, checksums, and Origin helpers.

The live-evolution ZIP adds `live_state.json` and `baseline_current_comparison.csv`. The comparison table stores separate baseline/current `q`, `d`, model intensity, global relative intensity, and differences on a common `2theta` grid.

Stable identifiers include `step_0000`, `line_00`, `h0k2l0`, and `line_00__h0k2l0`. Extinct reflections remain as zero-value rows so HKL evolution curves do not silently break.

Each package includes `origin_column_map.csv`, `origin_import.py`, and `ORIGIN_README.md`. The package can be imported into Origin using its Python support and plotted in Python using the included CSV mappings. See the [Origin Python documentation](https://docs.originlab.com/python/) and [Origin heat-map data requirements](https://docs.originlab.com/origin-help/heat_map/).

## Model Boundaries

The current model intentionally does not implement texture or preferred orientation, absorption or fluorescence, anomalous dispersion, microstrain, crystallite-size broadening, instrumental zero shift, background, phase fractions, experimental fitting, or absolute intensity calibration.

## Development

Run the Python checks from the repository root:

```bash
python -m pytest -q
python -m ruff check .
python -m basedpyright
python -m compileall -q orthoxrd tests app.py
```

Run the browser component checks:

```bash
cd frontend
bun install
bun test
bun run typecheck
bun run build
```

The generated browser bundle at `orthoxrd/_live_component/live-component.js` is kept in the repository because the Streamlit application loads it at runtime. `frontend/node_modules`, caches, local Playwright sessions, and QA screenshots are intentionally ignored.

## Project Layout

```text
app.py                         Streamlit entry point
orthoxrd/                      Scientific model, UI, plotting, and export code
frontend/src/                  TypeScript Live Canvas component
tests/                         Numerical, export, and AppTest coverage
DESIGN.md                      UI and scientific design contract
pyproject.toml                 Runtime and development dependencies
```

## License and Citation

This repository is public, but no open-source license has been selected yet. Until a `LICENSE` file is added, publication of the source does not grant permission to redistribute modified versions.

For scientific use, cite the underlying `Cmcm 4c` structure source and record the exported `config.json`, `manifest.json`, application version, and configuration hash alongside any derived figure or table.
