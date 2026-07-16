# CrystalShift XRD

Kinematic powder XRD workbench for the orthorhombic Cmcm 4c phase: forward simulation of peak positions and model intensities, plus discrete-peak inverse estimation of Wyckoff y (and derived shuffle) from observed peak strengths.

## Language

### Structure

**Wyckoff y**:
Fractional coordinate of the Cmcm 4c site that sets structure factors; it does not change d-spacings.
_Avoid_: free parameter (unqualified), position parameter

**Basal shuffle**:
The basal-plane displacement parameter linked to y by `shuffle_signed = 2(y - 0.25)` and `shuffle_magnitude = |shuffle_signed|`.
_Avoid_: displacement (unqualified), shuffle without signed/magnitude

**Shuffle branch**:
Which of the two y values maps from a given shuffle magnitude: lower `y = 0.25 - s/2` or upper `y = 0.25 + s/2`.

**Zero-shuffle reference**:
The `y=0.25` special-position state in the same `Cmcm` unit cell. It is used to
show the 4c atom paths `±b(y-0.25)` along `b`; it is not assigned to another
parent phase without independent evidence.
_Avoid_: parent phase, phase transformation endpoint

**Structure display coordinate**:
A read-only plot projection of canonical `y` as `y`, signed shuffle, or
branch-safe shuffle magnitude. It never changes the calculated result or the
exported canonical axis.
_Avoid_: fit parameter transformation, recalculated sweep

### Forward intensity

**Model peak intensity**:
Theoretical peak weight `I_model_peak = F² × applied_multiplicity × applied_LP × applied_volume × line_weight` for one radiation line and HKL.
_Avoid_: measured intensity, absolute intensity, calibrated intensity, Rietveld intensity

**Relative intensity**:
Model intensity renormalised for display or comparison (`I_rel_local` per spectrum/step, `I_rel_global` across a sweep).
_Avoid_: experimental relative intensity (unless explicitly observed)

**Reference R factor**:
Unnormalised theoretical peak reference in either with-LP form
`R_hkl = N × F² × LP / V²` or no-LP form `R_hkl_no_LP = N × F² / V²`.
It always uses crystallographic multiplicity and the raw LP factor, independent
of model correction toggles and radiation-line weight. The no-LP form applies
only when experimental integrated areas have received the corresponding LP,
polarisation, or geometry correction.
_Avoid_: absolute intensity, calibrated intensity, Rietveld residual

### Inverse fit (discrete peaks)

**Observed peak intensity**:
User-supplied strength of one measured reflection, in either **peak-area mode** (integral-intensity proxy) or **peak-height mode** (height under an equal-width assumption).
_Avoid_: raw counts (unqualified), intensity without mode

**Observable mode**:
Which observed quantity enters the fit: peak area or peak height; recorded in config and export.

**Scale factor S**:
Single non-negative multiplier mapping model peak intensities onto the observed intensity scale for a given y.
_Avoid_: calibration constant (implies absolute metrology), absorption factor

**Discrete peak intensity fit**:
Estimation of y (and S) from a table of HKL-matched observed peak intensities; not a full-pattern profile refinement.
_Avoid_: Rietveld, full-pattern fit, Le Bail, Pawley (for this feature)

**Weighted residual**:
Per-peak contribution `(I_obs - S · I_model)² · w`, with default Poisson-like `w = 1/max(I_obs, ε)`, optional equal weights, or per-peak weight/σ overrides.

**Chi-squared surface**:
χ²(y) after substituting the closed-form optimal S(y); explored by a y-grid then local refinement.
_Avoid_: loss (unqualified), cost function (prefer χ² when this definition applies)

**Grid scan**:
Uniform evaluation of χ²(y) and S(y) over a user y-range (default full [0, 0.5]).

**Refine trace**:
Sequence of local-refinement evaluations around the grid minimum.

**Local minimum candidate**:
A one-dimensional neighbourhood minimum on the grid χ² curve, reported for inspection; not auto-selected as the physical answer.
_Avoid_: solution (unqualified) when only a candidate is meant

**Fit export package**:
ZIP of process tables (observations, grid scan, refine trace, best point, residuals at best, config, manifest) for external visualisation.
_Avoid_: black-box result, fit summary only

**Analysis workbook**:
The additive `analysis.xlsx` human-inspection mirror inside an export ZIP. Its
README, Parameters, and Columns sheets explain the data, and text identifiers
preserve leading zeroes. CSV remains the canonical machine-readable contract.
_Avoid_: replacement export, canonical Excel schema
