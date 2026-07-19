"""English UI catalog."""

from __future__ import annotations


def _h(purpose: str, importance: str, example: str, notes: str) -> str:
    return (
        f"[Purpose] {purpose}\n"
        f"[Why it matters] {importance}\n"
        f"[Beginner example] {example}\n"
        f"[Notes] {notes}"
    )


EN_TEXT: dict[str, str] = {
    "lang.label": "Interface language",
    "lang.zh": "中文",
    "lang.en": "English",
    "common.on": "on",
    "common.off": "off",
    "app.page_title": "CrystalShift XRD",
    "app.model_tag": "Cmcm 4c | schema 2.3",
    "app.subtitle": (
        "Kinematic powder model for lattice, Wyckoff-y, shuffle, and incident-radiation studies."
    ),
    "app.spinner": "Calculating active model...",
    "app.summary.a": "a (A)",
    "app.summary.b": "b (A)",
    "app.summary.c": "c (A)",
    "app.summary.y": "Wyckoff y",
    "app.summary.shuffle": "shuffle |s|",
    "app.summary.energy": "energy (keV)",
    "app.summary.lambda": "lambda (A)",
    "app.summary.hash": "config hash",
    "app.active_model.composition_na": "not applicable (unit scatterer)",
    "app.active_model_details": (
        "**Active model** · Scattering: {scattering} · Composition: {composition} · "
        "2theta {tth_min:g}-{tth_max:g} deg · {profile} · FWHM {fwhm:.4f} deg · "
        "Corrections: LP {lp} · multiplicity {multiplicity} · volume 1/V {volume}"
    ),
    "inputs.required_review": (
        '<div class="xrd-note xrd-note-warn"><strong>Review before analysis or export:</strong> '
        "incident radiation, lattice, Wyckoff y, and signed/magnitude shuffle, plus "
        "scattering/composition, "
        "2theta window, profile, and intensity corrections in Material and calculation settings.</div>"
    ),
    "nav.label": "Result view",
    "nav.pattern": "Pattern",
    "nav.peaks": "Peaks",
    "nav.f2": "F2 evolution",
    "nav.sweep": "Sweep",
    "nav.fit": "Fit",
    "nav.method": "Method",
    "axis.y": "Wyckoff y",
    "axis.signed_shuffle": "Signed shuffle",
    "axis.shuffle_magnitude": "Shuffle magnitude",
    "axis.shuffle": "Shuffle magnitude",
    "axis.a_A": "Lattice a",
    "axis.b_A": "Lattice b",
    "axis.c_A": "Lattice c",
    "axis.energy_keV": "Energy",
    "axis.wavelength_A": "Wavelength",
    "branch.lower": "Lower",
    "branch.upper": "Upper",
    "radiation.title": "Radiation",
    "radiation.source": "Incident source",
    "radiation.mode.Custom energy": "Custom energy",
    "radiation.mode.Custom wavelength": "Custom wavelength",
    "radiation.mode.Cu K-alpha doublet": "Cu K-alpha doublet",
    "radiation.mode.Co K-alpha doublet": "Co K-alpha doublet",
    "radiation.mode.Mo K-alpha doublet": "Mo K-alpha doublet",
    "radiation.mode.30 keV synchrotron": "30 keV synchrotron",
    "radiation.energy": "Energy (keV)",
    "radiation.wavelength": "Wavelength (A)",
    "radiation.include_k_alpha2": "Include K-alpha2 component",
    "radiation.primary_wavelength": "Primary wavelength: {wavelength:.6f} A{suffix}",
    "radiation.primary_energy": "Primary energy: {energy:.4f} keV{suffix}",
    "radiation.primary_line_single": (
        "Primary line: {label}, lambda={wavelength:.6f} A, energy={energy:.4f} keV"
    ),
    "radiation.primary_line_doublet": (
        "Primary line: {primary} ({w1:.1f}), secondary line: {secondary} ({w2:.1f})"
    ),
    "radiation.scaled_suffix": (
        " | scaled {count}-line source; relative wavelengths and weights preserved"
    ),
    "structure.title": "Structure",
    "structure.preset": "Lattice preset",
    "structure.a": "a (A)",
    "structure.b": "b (A)",
    "structure.c": "c (A)",
    "structure.y": "Wyckoff y ({ymin:.3f}-{ymax:.3f})",
    "structure.shuffle": "Basal shuffle magnitude ({smin:.3f}-{smax:.3f})",
    "structure.branch": "Shuffle-magnitude branch",
    "structure.signed_label": "signed shuffle",
    "structure.signed_meta": "2(y - 0.25) · current {branch}",
    "structure.branch.lower": "lower branch",
    "structure.branch.upper": "upper branch",
    "structure.branch.reference": "zero-shuffle reference",
    "structure.relation_note": (
        '<div class="xrd-note"><strong>y / shuffle relation</strong> '
        "signed = 2(y - 0.25); magnitude = abs(signed). "
        "Ti-Nb lower branch: y={y_min:.3f}..{y_max:.3f}, "
        "magnitude=0..{s_max:.3f}.</div>"
    ),
    "structure.expander": "Valid ranges and branch details",
    "structure.range_y": "Wyckoff y valid range: {ymin:.3f} to {ymax:.3f}",
    "structure.range_signed": (
        "shuffle_signed = 2(y - 0.25), range: {smin:.3f} to {smax:+.3f}"
    ),
    "structure.range_mag": (
        "shuffle_magnitude = abs(shuffle_signed), range: {smin:.3f} to {smax:.3f}"
    ),
    "structure.range_tinb": (
        "Default Ti-Nb lower-branch sweep: y={ymin:.3f}..{ymax:.3f}, "
        "shuffle_magnitude={smin:.3f}..{smax:.3f}"
    ),
    "structure.branch_detail": (
        "Lower branch: y = 0.25 - shuffle_magnitude / 2; "
        "upper branch: y = 0.25 + shuffle_magnitude / 2."
    ),
    "structure.context.caption": (
        "Active structure: y={y:.6f} | signed shuffle={signed:+.6f} | "
        "shuffle magnitude={magnitude:.6f} | {branch}. "
        "These coordinates modulate structure factors and model intensity; the physical "
        "Pattern/Peaks axis remains 2theta, q, or d."
    ),
    "structure.plot.cell": "Cmcm unit cell",
    "structure.plot.reference": "y=0.25 reference sites",
    "structure.plot.current": "Current 4c sites",
    "structure.plot.shuffle_path": "Shuffle paths along b",
    "structure.plot.shuffle_arrow": "Shuffle direction",
    "advanced.popover": "Material and calculation settings (review)",
    "advanced.intro": "These settings change which peaks appear, their profile, and theoretical intensity. The active values remain visible in the model summary after this panel closes.",
    "advanced.scattering_section": "##### Scattering",
    "advanced.window_section": "##### Simulation window",
    "advanced.profile_section": "##### Peak profile",
    "advanced.factors_section": "##### Applied factors",
    "advanced.scattering": "Atomic scattering",
    "advanced.scattering.composition": "Composition form factor",
    "advanced.scattering.unit": "Unit scatterer F2",
    "advanced.unit_caption": "All sites use f=1. Best for isolating the analytical F2(y) trend.",
    "advanced.composition": "Composition fractions",
    "advanced.tth_min": "Simulation 2theta min (deg)",
    "advanced.tth_max": "Simulation 2theta max (deg)",
    "advanced.hkl_max": "Max h, k, l",
    "advanced.points": "Spectrum points",
    "advanced.cutoff": "Table cutoff (%)",
    "advanced.profile": "Peak shape",
    "advanced.profile.pseudo_voigt": "Pseudo-Voigt",
    "advanced.profile.gaussian": "Gaussian",
    "advanced.profile.lorentzian": "Lorentzian",
    "advanced.fwhm": "FWHM (deg 2theta)",
    "advanced.eta": "Pseudo-Voigt eta",
    "advanced.lp": "Lorentz-polarization",
    "advanced.multiplicity": "Orthorhombic multiplicity",
    "advanced.volume": "Scale by unit-cell volume (1/V)",
    "pattern.title": "Theoretical powder pattern",
    "pattern.mode": "Pattern mode",
    "pattern.mode.static": "Static",
    "pattern.mode.live": "Live evolution",
    "pattern.axis": "Horizontal axis",
    "pattern.intensity": "Intensity",
    "pattern.intensity.relative": "Relative",
    "pattern.intensity.model": "Model",
    "pattern.display": "Display",
    "pattern.display.combined": "Combined",
    "pattern.display.line": "Line",
    "pattern.display.sticks": "Sticks",
    "pattern.hkl_labels": "HKL labels",
    "pattern.live_caption": (
        "Each slider position is an exact backend frame; no frame interpolation is used."
    ),
    "pattern.static_caption": (
        "Model intensity is calculated, uncalibrated intensity. "
        "q_primary and d_primary use the primary wavelength."
    ),
    "pattern.download_spectrum": "Spectrum CSV",
    "pattern.download_peaks": "Peak table CSV",
    "export.csv_excel_hint.current": (
        "CSV is for Origin/Python or other machine processing. For Excel, use "
        "analysis.xlsx in the current-result ZIP to preserve leading-zero HKLs and read the notes."
    ),
    "plot.display_range": "Display range",
    "plot.display_caption": "Display-only crop. Simulation and exported rows remain unchanged.",
    "plot.x_min": "X minimum",
    "plot.x_max": "X maximum",
    "plot.y_auto": "Automatic Y range",
    "plot.y_min": "Y minimum",
    "plot.y_max": "Y maximum",
    "plot.reset": "Reset display range",
    "plot.x_error": "X maximum must be greater than X minimum.",
    "plot.y_error": "Y maximum must be greater than Y minimum.",
    "plot.x_title.2theta": "2theta (deg)",
    "plot.x_title.q_primary": "q_primary (A^-1)",
    "plot.x_title.d_primary": "d_primary (A)",
    "plot.y_title.model": "model intensity (calculated units)",
    "plot.y_title.relative": "relative intensity (%)",
    "plot.trace.model": "profile model",
    "plot.trace.relative": "profile relative",
    "plot.trace.bragg": "Bragg reflections",
    "plot.trace.selected": "selected reflection",
    "peaks.title": "Bragg peaks",
    "peaks.caption": (
        "Showing {shown:,} of {total:,} calculated peak rows. "
        "Scroll the table horizontally for all fields; CSV exports include every column."
    ),
    "peaks.empty_filtered": "No peaks match the active filters. Broaden the HKL, radiation-line, intensity, or 2theta criteria.",
    "peaks.selected": (
        "Selected {line} {hkl} | 2theta={two_theta:.6f} deg | {series_id}"
    ),
    "peaks.hkl_filter": "HKL filter",
    "peaks.hkl_placeholder": "e.g. 110 or 02",
    "peaks.line_filter": "Radiation line",
    "peaks.min_irel": "Minimum I_rel (%)",
    "peaks.angle_filter": "2theta filter (deg)",
    "peaks.download_all": "All peaks CSV",
    "peaks.download_filtered": "Filtered peaks CSV",
    "f2.title": "Structure-factor evolution",
    "f2.caption": (
        "Analytical unit-scatterer Cmcm 4c F2. Peak-profile, LP, multiplicity, "
        "composition, and volume factors are intentionally excluded."
    ),
    "f2.hkls": "HKL series (maximum 12)",
    "f2.axis": "Evolution axis",
    "f2.branch": "Shuffle branch",
    "f2.empty": "Select at least one HKL series.",
    "f2.preview": "Data preview",
    "f2.download": "F2 evolution CSV",
    "f2.download_excel": "F2 evolution Excel",
    "export.csv_excel_hint.f2": (
        "CSV is for Origin/Python or other machine processing. Use f2_evolution.xlsx in "
        "Excel to preserve leading-zero HKLs and read the Parameters and Columns notes."
    ),
    "f2.start": "Evolution start",
    "f2.stop": "Evolution stop",
    "f2.points": "Evolution points",
    "f2.structure_preview.title": "##### Cmcm 4c basal-displacement structure",
    "f2.structure_preview.slider": "Structure preview coordinate",
    "f2.structure_preview.caption": (
        "Grey marks the zero-shuffle y=0.25 reference sites in the same Cmcm cell; "
        "cyan marks the current sites. Motion is strictly along b, with single-atom "
        "|Δb| = b|y−0.25|. This slider changes only the diagram and does not write back "
        "to the main structure inputs."
    ),
    "f2.structure_preview.help": (
        "Preview the real 4c sites and displacement paths for the selected Wyckoff-y, "
        "signed-shuffle, or shuffle-magnitude coordinate. It does not recalculate the "
        "active simulation or change exports."
    ),
    "f2.stop_error": "Evolution stop must be greater than start.",
    "f2.x_title.y": "Wyckoff y",
    "f2.x_title.signed_shuffle": "signed shuffle = 2(y - 0.25)",
    "f2.x_title.shuffle_magnitude": "shuffle magnitude",
    "f2.y_title": "unit-scatterer F2",
    "live.stale": (
        '<div class="xrd-state xrd-state--warning">Live preview is stale. '
        "Rebuild after changing non-active physics or range settings.</div>"
    ),
    "live.valid": (
        '<div class="xrd-state xrd-state--valid">Live preview matches the '
        "active scientific configuration.</div>"
    ),
    "live.rebuild": "Rebuild live preview",
    "live.stale_caption": (
        "The previous preview is retained, but interaction and export are disabled."
    ),
    "live.frames_caption": (
        "{frames} exact frames | {points} points/frame | "
        "{cells:,} browser preview cells"
    ),
    "live.baseline_caption": "Baseline {baseline:.7g} | Current {current:.7g}",
    "live.set_baseline": "Set current as baseline",
    "live.spinner": "Preparing exact live frames...",
    "live.parameter": "Live parameter",
    "live.branch": "Shuffle branch",
    "live.start": "Live start",
    "live.stop": "Live stop",
    "live.step": "Live step",
    "live.points": "Preview points",
    "live.caption": (
        "The slider switches precomputed exact frames locally. Python receives only "
        "the final frame when the slider is released."
    ),
    "live.export.prepare": "Prepare live evolution ZIP",
    "live.export.spinner": "Building schema 2.3 live analysis package...",
    "live.export.caption_prepare": "Prepare the full-precision live ZIP on demand.",
    "live.export.caption_changed": "The live selection changed. Prepare the ZIP again.",
    "live.export.download": "Download live_evolution.zip",
    "live.export.size": "{kib:.1f} KiB | SHA-256 {sha}...",
    "live.ui.intensity": "Intensity",
    "live.ui.global": "Global relative",
    "live.ui.local": "Local relative",
    "live.ui.model": "Model",
    "live.ui.difference": "Difference",
    "live.ui.baseline": "baseline",
    "live.ui.current": "current",
    "live.ui.aria_canvas": "Live theoretical XRD pattern",
    "live.ui.aria_slider": "Live parameter frame",
    "sweep.title": "Sweep and trajectory",
    "sweep.empty": (
        "Configure the sweep and select Run sweep. No batch calculation runs automatically."
    ),
    "sweep.stale": (
        '<div class="xrd-state xrd-state--warning">'
        "Result is stale because the active configuration changed. "
        "The preview is retained, but export is disabled until rerun."
        "</div>"
    ),
    "sweep.valid": (
        '<div class="xrd-state xrd-state--valid">'
        "Sweep result matches the active configuration."
        "</div>"
    ),
    "sweep.result_view": "Sweep result view",
    "sweep.view.heatmap": "Heatmap",
    "sweep.view.waterfall": "Waterfall",
    "sweep.view.peak_evolution": "Peak evolution",
    "sweep.view.data_preview": "Data preview",
    "sweep.kpi.steps": "steps",
    "sweep.kpi.peak_rows": "peak rows",
    "sweep.kpi.spectrum_cells": "spectrum cells",
    "sweep.kpi.global_max": "global profile max",
    "sweep.peak_metric": "Peak metric",
    "sweep.metric.F2": "F2",
    "sweep.metric.N_F2": "N x F2 (multiplicity x structure factor)",
    "sweep.metric.R_hkl_with_LP": "R_hkl (with LP, model reference)",
    "sweep.metric.R_hkl_no_LP": "R_hkl_no_LP (model reference)",
    "sweep.metric.I_model": "Model peak intensity",
    "sweep.metric.I_rel_global": "Global relative peak intensity",
    "sweep.peak_series": "Peak series (maximum 12)",
    "sweep.steps_header": "##### Sweep steps",
    "sweep.peak_sample_header": "##### Peak evolution sample",
    "sweep.preview_caption": (
        "Preview is limited to 500 peak rows. The ZIP contains the complete tables."
    ),
    "sweep.prepare": "Prepare sweep ZIP",
    "sweep.spinner": "Streaming schema 2.3 files into ZIP...",
    "sweep.prepare_caption": "Run the active configuration, then prepare the schema 2.3 ZIP.",
    "sweep.download": "Download sweep ZIP",
    "sweep.export_size": "{kib:.1f} KiB | SHA-256 {sha}...",
    "sweep.calc_spinner": "Calculating sweep...",
    "sweep.err.no_trajectory": "Select a trajectory CSV before running.",
    "sweep.err.incomplete_range": "Range sweep configuration is incomplete.",
    "sweep.spectrum_points": "Sweep spectrum points",
    "sweep.input_mode": "Sweep input",
    "sweep.input.range": "Range sweep",
    "sweep.input.trajectory": "CSV trajectory",
    "sweep.normalization": "Heatmap normalization",
    "sweep.norm.global": "Global across sweep",
    "sweep.norm.local": "Local per step",
    "sweep.norm.model": "Model intensity",
    "sweep.local_warning": (
        "Local normalization rescales every step independently; "
        "you cannot compare amplitude between steps."
    ),
    "sweep.axis": "Sweep axis",
    "sweep.branch": "Shuffle branch",
    "sweep.branch_lower": "Lower branch: y = 0.25 - shuffle_magnitude / 2",
    "sweep.branch_upper": "Upper branch: y = 0.25 + shuffle_magnitude / 2",
    "sweep.start": "Sweep start",
    "sweep.stop": "Sweep stop",
    "sweep.step": "Sweep step",
    "sweep.run": "Run sweep",
    "sweep.estimate": (
        "Estimate: {steps:,} steps | {cells:,} spectrum cells | "
        "up to {peaks:,} peak rows."
    ),
    "sweep.trajectory_file": "Trajectory CSV",
    "sweep.trajectory_template": "Trajectory template CSV",
    "sweep.trajectory_caption": (
        "Columns: step_label, a_A, b_A, c_A, y, shuffle_magnitude, "
        "shuffle_branch, energy_keV, wavelength_A. Limit: 1-1001 rows."
    ),
    "sweep.display_range": "Sweep display range",
    "sweep.display_coordinate": "Structure display coordinate",
    "sweep.display_coordinate_cross_branch": (
        "This y sweep crosses y=0.25. Shuffle magnitude would fold the lower and "
        "upper branches onto the same values, so only y and signed shuffle are offered."
    ),
    "sweep.display_caption": (
        "Display-only crop. The ZIP always contains the complete simulation window."
    ),
    "sweep.display_tth_min": "Sweep 2theta minimum",
    "sweep.display_tth_max": "Sweep 2theta maximum",
    "sweep.display_axis_min": "Sweep axis minimum",
    "sweep.display_axis_max": "Sweep axis maximum",
    "sweep.display_reset": "Reset sweep display range",
    "sweep.display_tth_error": "Sweep 2theta maximum must be greater than the minimum.",
    "sweep.display_axis_error": "Sweep axis maximum must be greater than the minimum.",
    "sweep.plot.i_model": "I model",
    "sweep.plot.i_global": "I global (%)",
    "sweep.plot.i_local": "I local (%)",
    "sweep.plot.two_theta": "2theta (deg)",
    "sweep.plot.step": "sweep step",
    "sweep.plot.intensity": "intensity",
    "export.prepare": "Prepare current ZIP",
    "export.spinner": "Preparing current simulation export...",
    "export.caption": "Schema 2.3 export is prepared on demand.",
    "export.expired": "Prepared export expired. Prepare it again.",
    "export.download": "Download current ZIP",
    "export.size": "{kib:.1f} KiB | SHA-256 {sha}...",
    # Discrete peak intensity fit
    "fit.title": "Discrete peak intensity fit",
    "fit.subtitle": (
        "Estimate Wyckoff y and scale factor S from observed peak strengths. "
        "Not Rietveld / not full-pattern profile refinement."
    ),
    "fit.empty": (
        "Load or edit observations, set fit options, then select Run fit. "
        "No inverse calculation runs automatically."
    ),
    "fit.stale": (
        '<div class="xrd-note xrd-note-warn">Fit result is stale relative to the '
        "active configuration or observations. Re-run fit before applying y* or "
        "exporting.</div>"
    ),
    "fit.valid": (
        '<div class="xrd-note">Fit result matches the active configuration and '
        "observations.</div>"
    ),
    "fit.context.header": "##### Fixed fit context (review first)",
    "fit.context.details": (
        "These quantities are not refined: a={a:.6g} Å, b={b:.6g} Å, c={c:.6g} Å; "
        "radiation={radiation}; scattering={scattering} ({composition}); "
        "2theta={tth_min:.6g}–{tth_max:.6g} deg, HKL limit={hkl_max}; "
        "LP={lp}, multiplicity={multiplicity}, 1/V={volume}."
    ),
    "fit.context.profile_excluded": (
        "This is a discrete peak-strength fit: profile shape, FWHM, background, and "
        "peak-position offsets are not refined. Peak height is only an equal-width proxy; "
        "use peak area when integrated intensities are available."
    ),
    "fit.observable.header": "##### 1. Choose the experimental observable first",
    "fit.obs.header": "##### 2. Enter at least two real observed peaks",
    "fit.obs.upload": "Observation CSV",
    "fit.obs.editor": "Observation table (CSV text)",
    "fit.obs.template": "Download observation template CSV",
    "fit.obs.caption": (
        "Required columns: h, k, l, I_obs. Optional: line / line_id, weight, sigma, notes. "
        "Miller indices use the non-negative powder convention. "
        "Upload limit ~2 MiB / {max_rows} data rows; one row per (HKL, radiation line)."
    ),
    "fit.obs.multiline_warning": (
        "The active source has multiple radiation lines ({lines}). "
        "Every observation row must set line or line_id (e.g. line_00), "
        "or matching will hard-fail with multi-line ambiguity."
    ),
    "fit.obs.invalid": "The current observation table cannot run: {error}",
    "fit.obs.need_two": (
        "{count} valid observation(s) detected; at least 2 real peaks are required to run."
    ),
    "fit.options.header": "##### 3. Set weights and the y scan",
    "fit.options.scan_note": (
        "The full y grid exposes multiple local minima; local refinement improves precision "
        "only around the best grid point."
    ),
    "fit.observable_mode": "Observable mode",
    "fit.mode.peak_area": "Peak area (preferred)",
    "fit.mode.peak_height": "Peak height (equal-width proxy)",
    "fit.weight_mode": "Weight mode",
    "fit.weight.poisson": "Poisson-like (1 / max(I_obs, ε))",
    "fit.weight.equal": "Equal weights",
    "fit.y_start": "y grid start",
    "fit.y_stop": "y grid stop",
    "fit.grid_points": "Grid points",
    "fit.peak_height_note": (
        "Peak-height mode assumes equal peak widths so height ∝ area. In v1 the "
        "numeric objective matches peak-area mode; S absorbs any common constant. "
        "Prefer peak-area when integral intensities are available."
    ),
    "fit.run": "4. Run fit",
    "fit.err.y_range": "y grid stop must be greater than or equal to y grid start.",
    "fit.err.obs_encoding": (
        "Observation file is not valid UTF-8 text. Save as UTF-8 CSV/TXT and upload again."
    ),
    "fit.err.obs_too_large": (
        "Observation file is too large ({size_kib:.1f} KiB). Keep uploads under {max_mib:.0f} MiB."
    ),
    "fit.err.obs_too_many_rows": (
        "Too many observation data rows ({rows}). Keep at most {max_rows} rows (excluding header)."
    ),
    "fit.calc_spinner": "Running discrete peak intensity fit...",
    "fit.kpi.y_star": "y*",
    "fit.kpi.s_star": "S*",
    "fit.kpi.chi2_star": "χ²*",
    "fit.kpi.shuffle_signed": "shuffle signed",
    "fit.kpi.shuffle_mag": "shuffle |s|",
    "fit.kpi.source": "source",
    "fit.kpi.peaks": "peaks used",
    "fit.kpi.mode": "observable",
    "fit.plot.chi2": "χ²(y)",
    "fit.plot.scale": "Optimal scale S(y)",
    "fit.plot.refine_trace": "Local refine trace",
    "fit.plot.best": "Best point",
    "fit.plot.local_minima": "Local minima",
    "fit.plot.x_y": "Wyckoff y",
    "fit.plot.y_chi2": "χ²(y)",
    "fit.plot.y_scale": "Optimal scale S(y)",
    "fit.plot.parity_line": "Ideal agreement",
    "fit.plot.observations": "Observed and fitted peaks",
    "fit.plot.x_observed": "Observed peak strength I_obs",
    "fit.plot.y_fitted": "Fitted peak strength S* · I_model",
    "fit.plot.chi2_contribution": "Per-peak χ² contribution",
    "fit.plot.x_hkl": "HKL",
    "fit.plot.y_chi2_contribution": "w · residual²",
    "fit.diagnostics.header": "##### Fit-path and agreement diagnostics",
    "fit.display_coordinate": "Structure display coordinate",
    "fit.display_coordinate_magnitude_note": (
        "Shuffle magnitude is two-to-one across y=0.25. Lower and upper branches are "
        "drawn separately and are never joined through the zero-shuffle point."
    ),
    "fit.diagnostics.chi2": "χ² grid, local refine trace, local minima, and final best point.",
    "fit.diagnostics.scale": "Closed-form optimal scale S(y) at each structure coordinate.",
    "fit.diagnostics.parity": (
        "Observed peak strength versus best-fit strength; points nearer the diagonal agree better."
    ),
    "fit.diagnostics.contributions": (
        "Per-HKL w·residual²; the bar total reconstructs the best χ²."
    ),
    "fit.identifiability.header": "##### y identifiability (profile Δχ² heuristic)",
    "fit.identifiability.status_label": "Status",
    "fit.identifiability.interval_label": "Heuristic y interval",
    "fit.identifiability.no_interval": "not available",
    "fit.identifiability.no_reason": "none recorded",
    "fit.identifiability.note": (
        "Threshold Δχ²={threshold:.6g}; reasons: {reasons}. This profile is built from "
        "the grid and refined candidates, not a full covariance estimate."
    ),
    "fit.identifiability.status.identified": "identified",
    "fit.identifiability.status.boundary_limited": "boundary-limited",
    "fit.identifiability.status.multi_modal": "multi-modal",
    "fit.identifiability.status.flat": "flat",
    "fit.identifiability.status.not_available": "not available",
    "fit.identifiability.warning.multi_modal": (
        "Multiple local candidates fall within the profile threshold; the best candidate "
        "is not automatically a unique physical solution."
    ),
    "fit.identifiability.warning.boundary_limited": (
        "The profile interval reaches the selected y scan boundary; extend the scan before "
        "treating the interval as internally bounded."
    ),
    "fit.identifiability.warning.flat": (
        "The profile stays within the threshold across the scan; y is weakly identified "
        "by these observations."
    ),
    "fit.identifiability.identified": (
        "The profile is internally bounded and no additional near-best candidate was found. "
        "This remains a heuristic diagnostic."
    ),
    "fit.identifiability.unavailable": "The profile identifiability diagnostic is not available.",
    "fit.local_minima.header": "##### Local minimum candidates",
    "fit.local_minima.empty": "No neighbourhood minima on the grid χ² curve.",
    "fit.local_minima.select": "Candidate to apply",
    "fit.local_minima.select_help": (
        "Choose a reported local candidate. The refined y is used when refinement succeeded."
    ),
    "fit.apply_candidate": "Apply selected candidate",
    "fit.apply_candidate_help": (
        "Apply only the selected candidate to the structure panel; this never changes the "
        "fit's automatically selected best point."
    ),
    "fit.residuals.header": "##### Residuals at best",
    "fit.apply": "Apply y* to structure",
    "fit.apply_caption": (
        "Apply is manual only: Run fit never overwrites the structure panel. "
        "Applying y* updates Wyckoff y and shuffle magnitude."
    ),
    "fit.apply_success": "Applied y* = {y:.6f} to structure parameters.",
    "fit.apply_candidate_success": "Applied selected candidate y = {y:.6f} to structure parameters.",
    "fit.prepare": "Prepare fit ZIP",
    "fit.spinner": "Streaming fit process tables into ZIP...",
    "fit.prepare_caption": "Run a fresh fit, then prepare the process-table ZIP.",
    "fit.download": "Download fit ZIP",
    "fit.export_size": "{kib:.1f} KiB | SHA-256 {sha}...",
    "method.title": "Method and interpretation",
    "method.workflow": """
#### First-use order

1. **Review inputs**: before analysis or export, check incident radiation, lattice, Wyckoff y, signed shuffle, shuffle magnitude, and Material and calculation settings.
2. **Choose the question**: lattice and radiation control peak positions; Wyckoff y, signed/magnitude shuffle, scattering, and corrections control intensities; use Live or Sweep for evolution.
3. **Plot before table**: confirm the trend and anomalies first, then inspect the exact HKL and values in Peaks or Data preview.
4. **Review before export**: confirm the active model summary, normalization, and valid-result state before preparing a package.
""",
    "method.view_guide": """
#### What each view is for

- **Pattern**: inspect peak positions, profiles, sticks, and one-parameter live evolution for the active model.
- **Peaks**: filter radiation lines and HKLs, then inspect F2, peak position, and applied intensity factors.
- **F2 evolution**: isolate the unit-scatterer structure factor and relate Wyckoff y and signed/magnitude shuffle to real Cmcm 4c motion in a unit-cell diagram.
- **Sweep**: calculate a range or row-wise CSV trajectory; heatmaps, waterfalls, and peak evolution can display y, signed shuffle, or safe magnitude coordinates.
- **Fit**: estimate y and scale S from experimental peak areas or equal-width peak heights, then inspect χ², S, observed-versus-fitted agreement, and per-peak residuals; not full-pattern refinement.
- **Method**: reference formulas, normalization definitions, fit assumptions, and model boundaries.
""",
    "method.left": """
#### Cmcm 4c model

The occupied fractional coordinates are generated for the orthorhombic
Cmcm 4c site. The Wyckoff parameter controls the basal shuffle:

**shuffle_signed = 2(y - 0.25)**

**shuffle_magnitude = abs(shuffle_signed)**

Changing y changes the structure factor but does not change d-spacing.
Changing a, b, or c changes d-spacing and the Bragg position.

The diagram's **y=0.25** state is the zero-shuffle special-position reference
inside the same Cmcm cell. It is not identified as another parent phase without
independent evidence. Each 4c site's displacement from that reference is
**±b(y−0.25) = ±b·shuffle_signed/2**, strictly along b.

#### Peak intensity

**I_model_peak = F² × applied_multiplicity × applied_LP × applied_volume_factor × line_weight**

Each applied factor is exported separately. applied_volume_factor is 1/V_cell
when the volume correction is enabled, and 1 otherwise.

The export also provides reference factors that do not use correction toggles
or radiation-line weight:

**R_hkl (with LP) = N x F2 x LP / V^2**

**R_hkl_no_LP = N x F2 / V^2**

Use the no-LP convention only when the experimental integrated intensity has
already received the corresponding LP, polarization, or geometry correction.
Neither quantity is an instrument-calibrated absolute intensity.

#### Discrete peak intensity fit (not Rietveld)

Recover **y** and a single scale **S ≥ 0** from HKL-matched observed peak
strengths while holding a, b, c, radiation, and corrections fixed:

**χ²(y, S) = Σ_i w_i (I_obs,i − S · I_model,i(y))²**

**S(y) = Σ w I_obs I_model / Σ w I_model²** (closed form; S clamped ≥ 0)

Default **Poisson-like** weights: `w = 1 / max(I_obs, ε)`. Optional equal
weights; per-peak `weight` or `sigma` overrides the global mode. Search uses a
uniform **y grid** (default full [0, 0.5]) plus local refinement. Local minima
on the grid are candidates only — not auto-selected as the physical answer.
""",
    "method.right": """
#### Profile and normalization

**I_profile_model** is the unnormalized sum of peak profiles.

**I_rel_local** uses one maximum per spectrum or sweep step. It supports shape
comparison but not cross-step amplitude comparison.

**I_rel_global** uses one maximum for the complete sweep. Use it for intensity
evolution across steps.

#### Observable modes and caveats

**Peak-area mode** is the preferred integral-intensity path versus
`I_model_peak`. **Peak-height mode** is an equal-width proxy (height ∝ area in
v1); do not treat it as free peak-shape refinement. The fit is a discrete peak
table inverse estimate — not full-pattern profile fitting, background,
zero-shift, microstrain, texture, absorption, or absolute calibration.

#### Model boundary

The output is theoretical model intensity, not measured raw intensity,
absolute calibrated intensity, phase fraction, or a Rietveld fit. The model
does not include texture, absorption, anomalous dispersion, preferred
orientation, microstrain, crystallite-size broadening, zero shift, or
background. Applying y* to the structure panel is always explicit.
""",
    "method.info": (
        "For paper-style orthorhombic F2(y) trends, use Unit scatterer F2. "
        "For a composition-aware X-ray pattern, use Composition form factor. "
        "For inverse y from measured peak strengths, use Fit (not Rietveld)."
    ),
}

EN_HELP: dict[str, str] = {
    "lang.label": _h(
        "Switch the interface language (Chinese / English).",
        "Supports bilingual writing, teaching, and screenshots.",
        "Default is Chinese; switch to English for English figures.",
        "Scientific inputs are preserved across language changes.",
    ),
    "nav.label": _h(
        "Switch among Pattern, Peaks, F2, Sweep, Fit, and Method views.",
        "Only the active view runs its calculation path.",
        "Start with Pattern, then open Peaks for tables.",
        "Sweep and Fit never run until you press their Run buttons.",
    ),
    "radiation.source": _h(
        "Choose a lab doublet, synchrotron line, or custom energy/wavelength.",
        "Wavelength sets Bragg angles and accessible reflections.",
        "Use 30 keV synchrotron or Cu K-alpha for common setups.",
        "Energy and wavelength are linked by E*lambda = hc.",
    ),
    "radiation.energy": _h(
        "Set incident photon energy in keV and derive wavelength.",
        "Energy shifts 2theta positions and the observable HKL set.",
        "Hard X-ray work often uses 20-40 keV; default is 30 keV.",
        "Valid range 1-200 keV; multi-line relative weights are preserved.",
    ),
    "radiation.wavelength": _h(
        "Set the primary wavelength in angstroms.",
        "Controls peak positions via Bragg's law.",
        "Cu K-alpha1 is about 1.5406 A.",
        "Valid range 0.05-5 A.",
    ),
    "radiation.include_k_alpha2": _h(
        "Include the K-alpha2 component of a doublet preset.",
        "Disable to keep only K-alpha1 for monochromatic comparisons.",
        "High-resolution lab data usually keeps both lines.",
        "Weights follow the preset (often ~2:1).",
    ),
    "structure.preset": _h(
        "Load literature or example lattice constants and y.",
        "Aligns inputs with published tables quickly.",
        "Start from S08 Table 5.5, then fine-tune a/b/c.",
        "Changing preset overwrites a/b/c/y/shuffle fields.",
    ),
    "structure.a": _h(
        "Orthorhombic cell edge a in angstroms.",
        "Changes d-spacings and 2theta for reflections with h.",
        "Ti-Nb alpha-double-prime often has a near 3.2 A.",
        "Valid range 1-20 A.",
    ),
    "structure.b": _h(
        "Orthorhombic cell edge b in angstroms.",
        "Affects d-spacings and couples to basal shuffle geometry.",
        "Example presets use b near 4.7-4.8 A.",
        "Valid range 1-20 A.",
    ),
    "structure.c": _h(
        "Orthorhombic cell edge c in angstroms.",
        "Changes positions of reflections with l index.",
        "Example presets use c near 4.66-4.75 A.",
        "Valid range 1-20 A.",
    ),
    "structure.y": _h(
        "Wyckoff y fractional coordinate of the Cmcm 4c site.",
        "Modulates F2 and relative intensities without changing d-spacings.",
        "Ti-Nb lower branch often uses y = 0.167 to 0.250.",
        "Linked to shuffle: signed = 2(y-0.25).",
    ),
    "structure.shuffle": _h(
        "Basal shuffle magnitude |2(y-0.25)|.",
        "Physical amplitude of the shuffle; maps to y once a branch is chosen.",
        "Sweep 0 to 0.166 for a typical lower-branch path.",
        "Magnitude omits sign; sign comes from y relative to 0.25.",
    ),
    "structure.branch": _h(
        "Choose which y branch a non-negative shuffle magnitude maps onto.",
        "At y=0.25 the magnitude alone is ambiguous, so this choice remains visible.",
        "Lower uses y=0.25-s/2; upper uses y=0.25+s/2.",
        "Editing y updates the branch; at zero shuffle the latest valid branch is retained.",
    ),
    "advanced.scattering": _h(
        "Unit scatterer versus composition-weighted form factors.",
        "Unit mode isolates analytical F2(y); composition mode is more X-ray realistic.",
        "Use unit scatterer for F2 trends; composition for alloy patterns.",
        "Composition mode depends on s = 1/(2d).",
    ),
    "advanced.composition": _h(
        "Element=fraction list for composition weighting.",
        "Sets relative atomic scattering contributions.",
        "Example: Ti=64, Nb=24, Zr=4, Sn=8.",
        "Fractions must be positive; separate with commas.",
    ),
    "advanced.tth_min": _h(
        "Lower bound of the simulation 2theta window.",
        "Reflections below this angle are excluded.",
        "Use 1-5 deg for low-angle discussions.",
        "Must be less than the maximum; affects peaks and spectra.",
    ),
    "advanced.tth_max": _h(
        "Upper bound of the simulation 2theta window.",
        "Sets the highest angle and HKL coverage.",
        "Short-wavelength sources can use a smaller max for high q.",
        "Must exceed the minimum.",
    ),
    "advanced.hkl_max": _h(
        "Maximum |h|,|k|,|l| when enumerating reflections.",
        "Caps compute cost and peak-table size.",
        "4-6 is typical; raise for high-angle work.",
        "Large values grow peak counts and export size.",
    ),
    "advanced.points": _h(
        "Number of samples on the continuous spectrum grid.",
        "Trades smoothness against export size.",
        "Use 2000-4000 for viewing; 800 for large sweeps.",
        "Allowed range 200-10000.",
    ),
    "advanced.cutoff": _h(
        "Relative-intensity cutoff (%) for table filtering defaults.",
        "Suppresses extremely weak peaks for readability.",
        "0.1% removes numerical noise-level peaks.",
        "Set 0 to keep every calculated peak.",
    ),
    "advanced.profile": _h(
        "Peak-shape function for the continuous profile.",
        "Gaussian, Lorentzian, or pseudo-Voigt morphology.",
        "Pseudo-Voigt is a common experimental compromise.",
        "eta applies only to pseudo-Voigt.",
    ),
    "advanced.fwhm": _h(
        "Full width at half maximum in deg 2theta.",
        "Sets theoretical peak width (not a full instrument model).",
        "Try 0.05-0.1 deg for sharp patterns.",
        "No anisotropic size/strain broadening is included.",
    ),
    "advanced.eta": _h(
        "Lorentzian weight in the pseudo-Voigt mix.",
        "eta=0 is Gaussian-like; eta=1 is Lorentzian-like.",
        "0.5 is a common starting value.",
        "Disabled for non pseudo-Voigt shapes.",
    ),
    "advanced.lp": _h(
        "Apply the Lorentz-polarization geometric factor.",
        "Changes relative intensities with angle.",
        "Leave on for standard powder XRD.",
        "Off moves intensities closer to pure |F|^2 weighting.",
    ),
    "advanced.multiplicity": _h(
        "Apply orthorhombic powder multiplicity.",
        "Statistical weight of symmetry-equivalent orientations.",
        "Required for powder patterns; optional for single-crystal style checks.",
        "Independent of systematic absences.",
    ),
    "advanced.volume": _h(
        "Scale intensities by 1/V.",
        "Captures unit-cell volume contribution in the kinematic model.",
        "Keep on when comparing different cell volumes.",
        "Exports report the applied volume factor explicitly.",
    ),
    "pattern.mode": _h(
        "Switch between a static spectrum and one-parameter live evolution.",
        "Live mode visualizes continuous parameter effects.",
        "Confirm static peaks first, then drag y or energy live.",
        "Frames are exact backend precomputes; the browser only switches frames.",
    ),
    "pattern.axis": _h(
        "Choose 2theta, q, or d as the horizontal axis.",
        "Matches literature and experimental conventions.",
        "Lab patterns often use 2theta; PDF/HE-XRD often use q.",
        "q and d use the primary wavelength; energy scans use per-frame lambda.",
    ),
    "pattern.intensity": _h(
        "Relative (locally normalized) versus unnormalized model intensity.",
        "Relative emphasizes shape; model keeps theoretical amplitude scale.",
        "Use relative for shape figures; model when checking amplitudes.",
        "Both are theoretical, not experimentally calibrated.",
    ),
    "pattern.display": _h(
        "Continuous profile, sticks, or both.",
        "Sticks highlight discrete reflections; profiles mimic measured spectra.",
        "Start with sticks, then add the profile.",
        "Stick heights follow the selected intensity scale.",
    ),
    "pattern.hkl_labels": _h(
        "Annotate strong peaks with HKL labels.",
        "Helps identify major reflections.",
        "Useful for teaching demos.",
        "Dense regions may overlap; disable if needed.",
    ),
    "pattern.download_spectrum": _h(
        "Download the current theoretical spectrum CSV.",
        "For Origin/Python post-processing.",
        "File name spectrum.csv with English schema columns.",
        "See Method and the export manifest for column meaning.",
    ),
    "pattern.download_peaks": _h(
        "Download the current Bragg peak table CSV.",
        "Includes HKL, 2theta, F2, and intensity factors.",
        "Use for tables or peak tracking.",
        "Field names stay English regardless of UI language.",
    ),
    "plot.display_range": _h(
        "Crop only the on-screen X/Y range.",
        "Does not change the simulation window or exports.",
        "Zoom a 2theta region by editing X bounds.",
        "Reset restores the default full range.",
    ),
    "plot.x_min": _h("Lower display bound for X.", "Defines the view with X max.", "e.g. 5 deg.", "Must be less than X max."),
    "plot.x_max": _h("Upper display bound for X.", "Defines the view with X min.", "e.g. 40 deg.", "Must exceed X min."),
    "plot.y_auto": _h("Autoscale the vertical axis.", "Avoids clipping peaks while browsing.", "On by default.", "Turn off for manual Y limits."),
    "plot.y_min": _h("Manual lower Y bound.", "Emphasize weak-signal regions.", "Often 0 for relative intensity.", "Must be less than Y max."),
    "plot.y_max": _h("Manual upper Y bound.", "Leave headroom above the strongest peak.", "105% is common for relative intensity.", "Must exceed Y min."),
    "plot.reset": _h("Restore default display bounds.", "Undo temporary zooms.", "Also useful after axis changes.", "Does not change scientific inputs."),
    "peaks.hkl_filter": _h(
        "Filter the peak table by HKL substring.",
        "Jump to a reflection family quickly.",
        "Type 110 or 02.",
        "Matches numeric label substrings.",
    ),
    "peaks.line_filter": _h(
        "Filter by radiation-line label.",
        "Separate K-alpha1/2 contributions.",
        "Keep only K-alpha1 when needed.",
        "Defaults to all lines selected.",
    ),
    "peaks.min_irel": _h(
        "Minimum relative intensity filter.",
        "Hide weak peaks to focus on majors.",
        "Set 1 to keep peaks >= 1%.",
        "Independent of the advanced table cutoff.",
    ),
    "peaks.angle_filter": _h(
        "Filter peaks by 2theta interval.",
        "Focus on an angular window.",
        "Drag to 8-18 deg.",
        "Limited by the simulation window.",
    ),
    "peaks.download_all": _h("Download the unfiltered peak table.", "Archival copy.", "peaks_all.csv.", "English schema fields."),
    "peaks.download_filtered": _h("Download the filtered peak table.", "Keep only peaks of interest.", "peaks_filtered.csv.", "Filters are not encoded in the file name."),
    "f2.hkls": _h(
        "Select up to 12 HKLs for F2 evolution curves.",
        "Shows extinctions and intensity swaps vs y/shuffle.",
        "Defaults 110/020/021/131 are teaching-friendly.",
        "Unit-scatterer analytical F2 only; no peak profile.",
    ),
    "f2.axis": _h(
        "Independent variable for the F2 curves.",
        "y and shuffle are analytically related.",
        "Papers often plot versus shuffle magnitude.",
        "Magnitude axis requires a branch choice.",
    ),
    "f2.branch": _h(
        "Maps shuffle magnitude to y = 0.25 +/- s/2.",
        "Same magnitude has two possible y values.",
        "Ti-Nb studies usually use the lower branch.",
        "Changing branch changes the y path.",
    ),
    "f2.start": _h("Evolution axis start.", "Lower sampling bound.", "0 for shuffle magnitude.", "Must be less than stop."),
    "f2.stop": _h("Evolution axis stop.", "Upper sampling bound.", "0.166 for lower-branch shuffle.", "Must exceed start."),
    "f2.points": _h("Number of samples on the curve.", "Controls smoothness.", "301 is usually enough.", "Range 10-2000."),
    "f2.download": _h(
        "Export long-form F2 evolution.",
        "Post-processing with both the selected display axis and canonical y.",
        "f2_evolution.csv.",
        "Columns include axis_value, hkl, F2, axis_code, y, signed/magnitude shuffle, and branch.",
    ),
    "f2.download_excel": _h(
        "Download the same F2 evolution rows as a native Excel workbook.",
        "HKL labels such as 021 remain text with leading zeroes intact.",
        "README, Parameters, and Columns sheets explain the model, path, and fields.",
        "Use the CSV instead for Origin/Python pipelines.",
    ),
    "f2.structure_preview.slider": _h(
        "Select the Wyckoff-y, signed-shuffle, or shuffle-magnitude coordinate shown by the structure diagram.",
        "Maps the abstract evolution coordinate to real Cmcm 4c motion along b.",
        "Use it to inspect one coordinate alongside the F2 curves.",
        "Preview only: it does not write the main inputs, recalculate, or change exports.",
    ),
    "live.parameter": _h(
        "Single active axis for live evolution.",
        "One axis at a time keeps frames unambiguous.",
        "Choose shuffle magnitude to watch intensity trends.",
        "Other physics stay at the active configuration.",
    ),
    "live.branch": _h("Branch for magnitude-to-y mapping.", "Sets the y direction.", "Lower by default.", "Should match the structure panel."),
    "live.start": _h("Live scan start.", "Lower bound of precomputed frames.", "Should cover the current value.", "Together with stop/step sets frame count."),
    "live.stop": _h("Live scan stop.", "Upper bound of precomputed frames.", "Slightly above the current value.", "Capped by the 401-frame limit."),
    "live.step": _h("Parameter step between frames.", "Smaller steps mean more frames and cost.", "0.001 is common for y.", "Must be positive."),
    "live.points": _h("Preview points per frame.", "Balances browser payload and smoothness.", "1600 is near the preview limit.", "Exports still use float64 full precision."),
    "live.rebuild": _h("Rebuild all frames after non-active settings change.", "Required when the preview is stale.", "Click after changing FWHM.", "Active-axis motion is covered by frames."),
    "live.set_baseline": _h("Fix the current frame as the gray baseline.", "Compare later frames against a reference.", "Set baseline at the reference state first.", "Difference traces use this baseline."),
    "live.export.prepare": _h(
        "Package float64 tables plus baseline/current comparison.",
        "Reproducible figures and analysis.",
        "Prepare after choosing baseline and current frames.",
        "Re-prepare if the selection changes.",
    ),
    "live.export.download": _h("Download live_evolution.zip.", "Offline analysis.", "Includes live_state.json.", "Schema 2.3."),
    "sweep.spectrum_points": _h(
        "Spectrum samples per sweep step.",
        "Controls memory and ZIP size.",
        "Use 800 for large batches.",
        "Subject to total-cell limits.",
    ),
    "sweep.input_mode": _h(
        "Uniform range sweep versus row-wise CSV trajectory.",
        "Trajectories encode arbitrary paths without Cartesian expansion.",
        "Use range for 1D sensitivity; CSV for multi-parameter paths.",
        "Blank cells inherit the base configuration.",
    ),
    "sweep.normalization": _h(
        "Intensity normalization for heatmap/waterfall.",
        "Global keeps cross-step amplitudes; local rescales each step.",
        "Choose global or model when comparing evolution.",
        "Local mode shows a non-comparability warning.",
    ),
    "sweep.axis": _h(
        "Independent variable for a range sweep.",
        "Defines which quantity changes each step.",
        "Choose Wyckoff y for shuffle-related paths.",
        "Energy/wavelength sweeps move peak positions.",
    ),
    "sweep.branch": _h("Branch for shuffle-magnitude sweeps.", "Different y mapping formulas.", "Lower by default.", "Matches Method formulas."),
    "sweep.start": _h("Sweep start value.", "Inclusive start of the grid.", "y often starts at 0.167.", "Must be <= stop."),
    "sweep.stop": _h("Sweep stop value.", "Inclusive end of the grid.", "y often ends at 0.250.", "Must be >= start."),
    "sweep.step": _h("Sweep step size.", "steps ~ floor((stop-start)/step)+1.", "0.001 gives a fine grid.", "Must be positive; watch step limits."),
    "sweep.run": _h("Explicitly start the batch calculation.", "Prevents accidental heavy runs.", "Click after setting axis and range.", "Config changes stale previous results."),
    "sweep.trajectory_file": _h(
        "Upload a row-wise parameter trajectory CSV.",
        "Rows run in order without grid expansion.",
        "Download the template, then fill step_label and fields.",
        "step_label must be unique; y and shuffle must agree if both set.",
    ),
    "sweep.trajectory_template": _h("Download a valid header template.", "Reduces format errors.", "trajectory_template.csv.", "Column names stay English."),
    "sweep.result_view": _h("Switch heatmap, waterfall, peak evolution, or data preview.", "Multiple views of one result.", "Heatmap first, then peak evolution.", "Display crop does not shrink exports."),
    "sweep.peak_metric": _h("Vertical metric for peak-evolution curves.", "F2, N x F2, R, and model intensity use different definitions.", "Choose the R convention according to whether experimental areas are LP-corrected.", "R is an unnormalized model reference factor, not instrument-calibrated absolute intensity."),
    "sweep.peak_series": _h("Track up to 12 peak series.", "Follow key HKLs across the sweep.", "Select 110/020 etc.", "Extinct peaks stay as zeros so curves do not break."),
    "sweep.prepare": _h("Build the schema 2.3 sweep ZIP.", "Full reproducible package.", "Available when the result is fresh.", "Disabled while stale."),
    "sweep.download": _h("Download the prepared sweep ZIP.", "Origin/Python workflows.", "Includes matrices and checksums.", "English file names."),
    "sweep.display_range": _h("Crop only heatmap/waterfall display windows.", "ZIP still holds the full simulation window.", "Zoom a 2theta region.", "Bounds must be ordered."),
    "sweep.display_coordinate": _h(
        "Change only the structure coordinate shown on sweep-result plots.",
        "The same canonical-y result can be viewed as y, signed shuffle, or safe shuffle magnitude.",
        "Use signed shuffle when the two sides of y=0.25 must stay distinct.",
        "This does not recalculate, mutate the result, or change exported axis_value.",
    ),
    "sweep.display_tth_min": _h("Display 2theta minimum.", "View control.", "e.g. 5 deg.", "Must be less than max."),
    "sweep.display_tth_max": _h("Display 2theta maximum.", "View control.", "e.g. 20 deg.", "Must exceed min."),
    "sweep.display_axis_min": _h("Display minimum on the sweep axis.", "Crop the scan axis.", "Focus the region of interest.", "Must be less than max."),
    "sweep.display_axis_max": _h("Display maximum on the sweep axis.", "Crop the scan axis.", "Focus the region of interest.", "Must exceed min."),
    "sweep.display_reset": _h("Restore default sweep display bounds.", "Undo zooms.", "One-click reset.", "Does not recompute results."),
    "export.prepare": _h(
        "Package spectrum, peaks, config, and manifest on demand.",
        "Keeps the export aligned with the config hash.",
        "Prepare after the active model looks right.",
        "Config changes invalidate the previous package.",
    ),
    "export.download": _h("Download current_simulation.zip.", "Archival and plotting.", "Includes Origin helpers.", "Schema 2.3."),
    "fit.obs.upload": _h(
        "Upload a discrete peak observation CSV.",
        "Brings lab peak strengths into the inverse fit.",
        "Start from the template, fill I_obs for a few HKL.",
        "Limit ~2 MiB / 500 rows; multi-line sources need line/line_id; unmatched HKL hard-fails.",
    ),
    "fit.obs.editor": _h(
        "Edit observation CSV text in place.",
        "Fix typos without re-uploading.",
        "Required: h,k,l,I_obs.",
        "Optional line/line_id, weight, sigma, notes.",
    ),
    "fit.obs.template": _h(
        "Download the stable observation CSV template.",
        "Documents required columns.",
        "observation_template.csv.",
        "Column names stay English.",
    ),
    "fit.observable_mode": _h(
        "Choose peak-area or peak-height observables.",
        "Defines what I_obs represents scientifically.",
        "Prefer peak_area when integrals are available.",
        "Peak-height is equal-width only in v1.",
    ),
    "fit.display_coordinate": _h(
        "Change only the structure coordinate shown on the χ² and S curves.",
        "The fit remains canonical in Wyckoff y; display can use y, signed shuffle, or magnitude.",
        "Prefer signed shuffle when comparing candidate minima on both sides of y=0.25.",
        "This does not rerun the fit or change y*; magnitude mode separates the two branches.",
    ),
    "fit.weight_mode": _h(
        "Global weight scheme when rows omit weight/sigma.",
        "Poisson-like down-weights huge peaks.",
        "Use equal for textbook comparisons.",
        "Per-peak weight or sigma overrides this mode.",
    ),
    "fit.y_start": _h(
        "Lower bound of the y grid scan.",
        "Default 0 covers both shuffle branches.",
        "Keep 0.0 unless you intentionally crop.",
        "Must be ≤ y stop and within [0, 0.5].",
    ),
    "fit.y_stop": _h(
        "Upper bound of the y grid scan.",
        "Default 0.5 is the full Wyckoff domain.",
        "Keep 0.5 to see multi-modality.",
        "Must be ≥ y start and within [0, 0.5].",
    ),
    "fit.grid_points": _h(
        "Number of uniform y samples on the grid.",
        "Density of χ²(y) before local refine.",
        "201 is a balanced default.",
        "Larger grids cost more forward evaluations.",
    ),
    "fit.run": _h(
        "Explicitly start the discrete peak intensity fit.",
        "Prevents accidental inverse runs.",
        "Click after observations and modes look right.",
        "Does not write y* into structure until Apply.",
    ),
    "fit.apply": _h(
        "Write best y* and |shuffle| into the structure panel.",
        "Commits the inverse result only when you choose.",
        "Use after inspecting χ²(y) and residuals.",
        "Disabled while the fit result is stale.",
    ),
    "fit.prepare": _h(
        "Build the fit process-table ZIP on demand.",
        "Offline visualisation of the full fit path.",
        "Available when the fit result is fresh.",
        "Does not include residual cubes for every grid y.",
    ),
    "fit.download": _h(
        "Download discrete_peak_fit.zip.",
        "Reproducible paper-style process tables.",
        "Includes observations, grid_scan, residuals, config, manifest.",
        "English file names; schema 2.x family.",
    ),
}
