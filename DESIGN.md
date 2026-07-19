# Orthorhombic XRD Simulator Design

## Purpose

This is a dense scientific analysis workbench, not a landing page. Its first viewport must make the active physical inputs and current result discoverable without opening hidden navigation.

## Scientific Contract

- Model phase: orthorhombic alpha-double-prime, space group `Cmcm`, 4c Wyckoff positions.
- `a`, `b`, `c`, wavelength, and energy control Bragg positions.
- Wyckoff `y` and basal shuffle control structure factors and model intensities, not d-spacing.
- `y` is canonical; signed shuffle is one-to-one, while magnitude is two-to-one and must retain a lower/upper branch. `y=0.25` is the zero-shuffle reference in the same Cmcm cell, and the 4c displacement is `±b(y-0.25)` along `b`.
- Peak model intensity is `I_model_peak = F² × applied_multiplicity × applied_LP × applied_volume_factor × line_weight`.
- `applied_volume_factor = 1 / V_cell` when the cell-volume correction is enabled (otherwise `1`).
- Reference factors are `R_hkl = N x F2 x LP / V^2` and
  `R_hkl_no_LP = N x F2 / V^2`; they ignore applied-factor toggles and line
  weight and are never described as instrument-calibrated absolute intensity.
- `I_profile_model` is unnormalized. `I_rel_local` is normalized per step. `I_rel_global` is normalized across a complete sweep.
- All output is theoretical model intensity. It is not measured raw intensity, absolute calibrated intensity, or a fitted phase fraction.
- Beyond the discrete-peak intensity fit, the model excludes full-pattern/profile
  refinement (Rietveld, Le Bail, or Pawley), texture, absorption, anomalous
  dispersion, preferred orientation, microstrain, crystallite-size broadening,
  zero shift, background, and absolute intensity calibration.

## Information Architecture

- Header: compact title, model identifier, active configuration hash, advanced-settings popover, and current-result ZIP download.
- Persistent input band: incident source, energy or wavelength, lattice preset, editable `a`, `b`, `c`, Wyckoff `y`, and shuffle magnitude.
- Advanced-settings popover: scattering mode, composition, 2theta and hkl ranges, profile parameters, and correction toggles. The sidebar is not used.
- Segmented navigation: `Pattern`, `Peaks`, `F2 evolution`, `Sweep`, `Method`.
- Navigation is lazy: only the selected view may execute its calculation path. `generate_sweep()` is never called outside an explicit Sweep run.
- Pattern: switchable `2theta`, `q_primary`, or `d_primary` x-axis; line, sticks, or combined display; model or relative intensity; optional HKL labels.
- Peaks: filterable, selectable scientific table with full and filtered exports. Selection is reflected on the pattern.
- F2 evolution: up to 12 HKLs versus `y`, signed shuffle, or shuffle magnitude, plus a preview-only real `Cmcm 4c` unit-cell diagram using the same axis, range, and branch.
- Sweep: one-axis or row-wise CSV trajectory, explicit Run action, stale-result state, Heatmap, Waterfall, Peak evolution, and Data preview. Structure sweeps can switch their display coordinate without recomputation or export mutation.
- Fit: the user chooses peak area or equal-width peak height before entering at least two valid observations; fixed inputs remain visible, and results include chi-squared, optimal-scale, parity, and per-peak contribution diagnostics.
- Method: formulas, units, normalization definitions, model boundaries, and interpretation warnings.

## Visual System

- Fixed dark scientific-tool palette. Canvas `#0b0f14`, raised surface `#121821`, control surface `#18202b`, border `#2a3441`, primary text `#f3f6fa`, secondary text `#aeb8c5`.
- Accent colors are functional: cyan `#22c7d6` for active data, amber `#f2b84b` for warnings/stale state, red `#ff5a67` for errors, green `#48c78e` for valid/export-ready state.
- Spacing uses a 4 px base scale. Cards and controls use at most 8 px radius. No decorative gradients, blobs, hero sections, nested cards, or oversized metrics.
- Numeric summaries and tabular values use a monospace font with tabular numerals.
- Focus uses a visible cyan outline. Disabled controls retain readable labels. Loading, error, empty, stale, and export-ready states are explicit.
- Plotly figures share the page palette, use restrained grid lines, and avoid white plot or paper backgrounds.
- Tables prioritize scanability: sticky headers, compact rows, explicit units, stable IDs, and no silent truncation.

## Responsive Contract

- At 1280 px and wider: compact desktop grid with radiation and structure sharing the first input band.
- At 768 px: tight two-column groups where values remain readable.
- At 375 px: a single-column flow; summaries wrap without horizontal overflow; buttons and inputs remain at least 40 px high.
- Fixed-format controls use stable dimensions. No input, plot, table, popover, or notification may cause page-level horizontal overflow.
- The active result must begin near the first viewport; explanatory text stays compact and moves to Method where possible.

## Workflow States

- Configuration changes invalidate cached exports and mark existing Sweep results stale.
- A fit cannot run until at least two valid observation rows are present. Changing observations, options, or fixed model context marks an earlier fit stale.
- A stale Sweep remains inspectable, but export is disabled until rerun.
- Trajectory validation errors include row, column, and offending value and must not replace a valid single-point result.
- Local sweep normalization always displays a warning that amplitudes cannot be compared between steps.
- Limits are checked before execution and provide a concrete reduction suggestion.
## Live Evolution Contract

- Live evolution scans one active axis at a time: y, shuffle, a, b, c, energy, or wavelength.
- NumPy float64 remains the scientific backend and export source. The browser receives a base64 float32 drawing payload only.
- Canvas rendering uses requestAnimationFrame, ResizeObserver, high-DPI scaling, keyboard input, a fixed gray baseline, a cyan current profile, HKL labels, and an optional amber difference trace.
- Slider input events switch exact frames without interpolation or Python reruns. Change events commit one final frame to the main parameter state.
- The active-axis value is excluded from the Live cache signature; all other physical, profile, simulation-window, and correction settings are included.
- A stale Live result stays visible but all component controls and export are disabled until it is rebuilt.
- Energy and wavelength frames use their own wavelength for q and d. An untouched q/d domain expands to cover every frame.
- Preview limits are 401 frames, 2000 points per frame, and 800,000 browser cells.

## Display Range Contract

- Advanced settings defines the Simulation 2theta window used by the calculation and export.
- Pattern Display range crops only the visible 2theta, q, d, or Y domain.
- Sweep display range crops only visible 2theta and scan-axis domains for Heatmap and Waterfall.
- Display controls never change peak rows, profile rows, or exported matrices. A reversed d axis keeps matching reversed labels.
- Structure display-coordinate controls project canonical `y` to signed shuffle or branch-safe magnitude for plots only. Magnitude traces on opposite sides of `y=0.25` are never connected.

## Export Contract 2.3

- Current and Sweep ZIPs add plot_state.json, origin_column_map.csv, origin_import.py, and ORIGIN_README.md without renaming legacy CSV files.
- Current, Sweep, Live, and Fit packages add `analysis.xlsx` without removing or rewriting CSVs. Every workbook contains README, Parameters, and Columns sheets; HKL labels and stable identifiers use Excel text cells to preserve leading zeroes.
- CSV is the canonical machine contract. XLSX is a documented human-inspection mirror and is covered by the same ZIP checksum manifest.
- The analytical F2 view additionally provides a standalone `f2_evolution.xlsx` beside its CSV. Because it is not inside a ZIP, its README and Parameters sheets record the unit-scatterer formula, exclusions, coordinates, branch, and selected HKLs directly rather than referring to a manifest.
- Current peak rows include geometry, current y/lattice/radiation, F/F2,
  N*F2, N*F2*LP, and both R_hkl conventions. Sweep exports provide matching
  long-form fields and matrices for F2, N_F2, both R factors, model intensity,
  and global relative intensity.
- live_evolution.zip contains the complete float64 sweep tables plus live_state.json and baseline_current_comparison.csv.
- The comparison table stores separate baseline/current q, d, model intensity, global relative intensity, and differences on the common 2theta grid.
- Origin mappings declare Long Name, unit, designation, and physical meaning. Regular sweeps use the spectrum matrix route; row-wise trajectories use XYZ.
