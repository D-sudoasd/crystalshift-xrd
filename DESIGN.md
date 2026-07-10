# Orthorhombic XRD Simulator Design

## Purpose

This is a dense scientific analysis workbench, not a landing page. Its first viewport must make the active physical inputs and current result discoverable without opening hidden navigation.

## Scientific Contract

- Model phase: orthorhombic alpha-double-prime, space group `Cmcm`, 4c Wyckoff positions.
- `a`, `b`, `c`, wavelength, and energy control Bragg positions.
- Wyckoff `y` and basal shuffle control structure factors and model intensities, not d-spacing.
- Peak model intensity is `F2 x applied_multiplicity x applied_LP x applied_volume x line_weight`.
- `I_profile_model` is unnormalized. `I_rel_local` is normalized per step. `I_rel_global` is normalized across a complete sweep.
- All output is theoretical model intensity. It is not measured raw intensity, absolute calibrated intensity, or a fitted phase fraction.
- The model excludes texture, absorption, anomalous dispersion, preferred orientation, microstrain, crystallite-size broadening, zero shift, background, and experimental fitting.

## Information Architecture

- Header: compact title, model identifier, active configuration hash, advanced-settings popover, and current-result ZIP download.
- Persistent input band: incident source, energy or wavelength, lattice preset, editable `a`, `b`, `c`, Wyckoff `y`, and shuffle magnitude.
- Advanced-settings popover: scattering mode, composition, 2theta and hkl ranges, profile parameters, and correction toggles. The sidebar is not used.
- Segmented navigation: `Pattern`, `Peaks`, `F2 evolution`, `Sweep`, `Method`.
- Navigation is lazy: only the selected view may execute its calculation path. `generate_sweep()` is never called outside an explicit Sweep run.
- Pattern: switchable `2theta`, `q_primary`, or `d_primary` x-axis; line, sticks, or combined display; model or relative intensity; optional HKL labels.
- Peaks: filterable, selectable scientific table with full and filtered exports. Selection is reflected on the pattern.
- F2 evolution: up to 12 HKLs versus `y`, signed shuffle, or shuffle magnitude.
- Sweep: one-axis or row-wise CSV trajectory, explicit Run action, stale-result state, Heatmap, Waterfall, Peak evolution, and Data preview.
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

## Export Contract 2.1

- Current and Sweep ZIPs add plot_state.json, origin_column_map.csv, origin_import.py, and ORIGIN_README.md without renaming legacy CSV files.
- live_evolution.zip contains the complete float64 sweep tables plus live_state.json and baseline_current_comparison.csv.
- The comparison table stores separate baseline/current q, d, model intensity, global relative intensity, and differences on the common 2theta grid.
- Origin mappings declare Long Name, unit, designation, and physical meaning. Regular sweeps use the spectrum matrix route; row-wise trajectories use XYZ.
