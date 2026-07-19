from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from orthoxrd.config import SimulationConfig
from orthoxrd.fit_models import (
    BestFit,
    CandidateRefineStatus,
    FitError,
    FitIdentifiability,
    FitIssue,
    FitOptions,
    FitResult,
    GridScanPoint,
    LocalMinimumCandidate,
    MatchedObservation,
    PeakObservation,
    RefineTracePoint,
    ResidualAtBest,
)
from orthoxrd.powder import (
    calculate_model_peak_intensity,
    calculate_reflection_for_hkl,
    calculate_reflections,
)
from orthoxrd.structure_factor import (
    cmcm_4c_structure_factor,
    signed_shuffle_from_y,
    validate_y,
)


@dataclass(frozen=True, slots=True)
class _PeakGeometry:
    h: int
    k: int
    l: int
    line_id: str
    line_weight: float
    d_spacing: float
    two_theta: float
    form_factor: float
    multiplicity: int
    lp_factor: float
    cell_volume: float
    applied_multiplicity: float
    applied_lp: float
    applied_volume_factor: float


@dataclass(frozen=True, slots=True)
class _CandidateRefinement:
    y: float | None
    scale_s: float | None
    chi2: float | None
    status: CandidateRefineStatus


def run_discrete_peak_fit(
    config: SimulationConfig,
    observations: Sequence[PeakObservation],
    fit_options: FitOptions | None = None,
) -> FitResult:
    """Estimate Wyckoff y and scale factor S from observed peak intensities.

    Pure scientific seam: no Streamlit. Reuses the forward model peak intensity
    contract with a, b, c, radiation, and corrections fixed from ``config``.
    Free parameters are y and S only.

    ``FitOptions.observable_mode`` is accepted for API stability; v1 treats
    ``peak_height`` as an equal-width proxy of model peak intensity (same
    objective as ``peak_area`` — see ``FitOptions``).
    """
    options = fit_options if fit_options is not None else FitOptions()
    matched = list(
        validate_discrete_peak_fit_observations(config, observations, options)
    )
    warnings: list[str] = []
    for item in matched:
        obs = item.observation
        if obs.h < 0 or obs.k < 0 or obs.l < 0:
            warnings.append(
                f"row {obs.row}: negative Miller index mapped to "
                f"(|h|,|k|,|l|)=({abs(obs.h)},{abs(obs.k)},{abs(obs.l)}) for "
                "matching (forward model enumerates the non-negative octant)"
            )
    included = [item for item in matched if item.included]
    geometry = _build_peak_geometry(config, matched)

    y_grid = _uniform_grid(options.y_start, options.y_stop, options.grid_points)
    model_matrix, vanishing = _model_intensity_matrix(geometry, included, y_grid, options)
    # ``vanishing`` is a non-empty list[bool]; only rebuild when at least one peak
    # is actually flagged (a non-empty list is always truthy in Python).
    if options.exclude_vanishing_model and any(vanishing):
        kept: list[MatchedObservation] = []
        for index, item in enumerate(included):
            if vanishing[index]:
                obs = item.observation
                reason = (
                    f"I_model ≈ 0 over the full y grid while I_obs > 0 "
                    f"(hkl={obs.h}{obs.k}{obs.l}, line={item.line_id})"
                )
                warnings.append(
                    f"row {obs.row}: excluded peak with vanishing model intensity "
                    f"({obs.h} {obs.k} {obs.l}, {item.line_id})"
                )
                kept.append(replace(item, included=False, exclude_reason=reason))
            else:
                kept.append(item)
        # Rebuild matched list with updated inclusion flags.
        matched = _merge_matched_exclusions(matched, kept)
        included = [item for item in matched if item.included]
        if len(included) < 2:
            raise FitError(
                (
                    FitIssue(
                        0,
                        "observations",
                        str(len(included)),
                        "at least two valid peaks are required after excluding "
                        "vanishing-model peaks",
                    ),
                )
            )
        model_matrix, _ = _model_intensity_matrix(geometry, included, y_grid, options)

    weights = [item.weight for item in included]
    i_obs = [item.observation.I_obs for item in included]

    grid_scan: list[GridScanPoint] = []
    for grid_index, y_value in enumerate(y_grid):
        i_model = model_matrix[grid_index]
        scale_s, chi2 = _closed_form_scale_and_chi2(i_obs, i_model, weights)
        grid_scan.append(GridScanPoint(y=y_value, scale_s=scale_s, chi2=chi2))

    all_local_minima = _local_minimum_candidates(grid_scan, None)
    best_grid_index = min(range(len(grid_scan)), key=lambda i: grid_scan[i].chi2)
    best_grid = grid_scan[best_grid_index]

    refine_trace: list[RefineTracePoint] = []
    best_y = best_grid.y
    best_s = best_grid.scale_s
    best_chi2 = best_grid.chi2
    source = "grid"

    candidate_refinements: dict[int, _CandidateRefinement] = {}

    if options.refine and options.y_stop > options.y_start:

        def objective(y_trial: float) -> tuple[float, float, float]:
            i_model = _model_intensities_at_y(geometry, included, y_trial)
            scale_s, chi2 = _closed_form_scale_and_chi2(i_obs, i_model, weights)
            return chi2, scale_s, y_trial

        try:
            best_refinement = _refine_grid_candidate(
                objective,
                y_grid,
                best_grid_index,
                options,
            )
        except (FloatingPointError, ValueError):
            candidate_refinements[best_grid_index] = _CandidateRefinement(
                None,
                None,
                None,
                "failed",
            )
        else:
            refined_y, refined_s, refined_chi2, refine_trace = best_refinement
            candidate_refinements[best_grid_index] = _CandidateRefinement(
                refined_y,
                refined_s,
                refined_chi2,
                "refined",
            )
            if refined_chi2 <= best_chi2:
                best_y, best_s, best_chi2 = refined_y, refined_s, refined_chi2
                source = "refine"

        for candidate in all_local_minima:
            if candidate.grid_index == best_grid_index:
                continue
            try:
                refined = _refine_grid_candidate(
                    objective,
                    y_grid,
                    candidate.grid_index,
                    options,
                )
            except (FloatingPointError, ValueError):
                candidate_refinements[candidate.grid_index] = _CandidateRefinement(
                    None,
                    None,
                    None,
                    "failed",
                )
            else:
                candidate_refinements[candidate.grid_index] = _CandidateRefinement(
                    refined[0],
                    refined[1],
                    refined[2],
                    "refined",
                )

    refined_local_minima = [
        _attach_candidate_refinement(candidate, candidate_refinements)
        for candidate in all_local_minima
    ]
    local_minima = refined_local_minima[: options.max_local_minima]

    shuffle = signed_shuffle_from_y(best_y)
    best = BestFit(
        y=best_y,
        scale_s=best_s,
        chi2=best_chi2,
        shuffle_signed=shuffle,
        shuffle_magnitude=abs(shuffle),
        source=source,
    )
    identifiability = _profile_identifiability(
        grid_scan,
        best,
        refined_local_minima,
        options,
    )
    residuals = _residuals_at_best(geometry, matched, best_y, best_s)
    return FitResult(
        config=config,
        options=options,
        matched=tuple(matched),
        grid_scan=tuple(grid_scan),
        refine_trace=tuple(refine_trace),
        best=best,
        residuals_at_best=tuple(residuals),
        local_minima=tuple(local_minima),
        warnings=tuple(warnings),
        identifiability=identifiability,
    )


def validate_discrete_peak_fit_observations(
    config: SimulationConfig,
    observations: Sequence[PeakObservation],
    fit_options: FitOptions | None = None,
) -> tuple[MatchedObservation, ...]:
    """Validate rows against the active model before the expensive y-grid scan.

    This gate covers row values, weights, duplicate series, HKL availability,
    and radiation-line resolution. Peaks that vanish over the requested y grid
    remain a run-time exclusion because identifying them is part of the scan.
    """
    options = fit_options if fit_options is not None else FitOptions()
    _validate_observations(observations)
    matched = _match_observations(observations, _build_peak_catalog(config), options)
    included = [item for item in matched if item.included]
    if len(included) < 2:
        raise FitError(
            (
                FitIssue(
                    0,
                    "observations",
                    str(len(included)),
                    "at least two valid peaks are required after model matching",
                ),
            )
        )
    return tuple(matched)


def closed_form_scale(
    i_obs: Sequence[float],
    i_model: Sequence[float],
    weights: Sequence[float],
) -> float:
    """Weighted least-squares scale S for fixed model intensities."""
    scale_s, _ = _closed_form_scale_and_chi2(i_obs, i_model, weights)
    return scale_s


def chi_squared(
    i_obs: Sequence[float],
    i_model: Sequence[float],
    weights: Sequence[float],
    scale_s: float,
) -> float:
    total = 0.0
    for obs, model, weight in zip(i_obs, i_model, weights, strict=True):
        residual = obs - scale_s * model
        total += weight * residual * residual
    return total


def resolve_weight(
    observation: PeakObservation,
    *,
    weight_mode: str,
    poisson_epsilon: float,
) -> float:
    """Resolve per-peak weight: explicit weight/sigma override global mode."""
    if observation.weight is not None:
        if not math.isfinite(observation.weight) or observation.weight <= 0:
            raise FitError(
                (
                    FitIssue(
                        observation.row,
                        "weight",
                        str(observation.weight),
                        "weight must be finite and positive",
                    ),
                )
            )
        return float(observation.weight)
    if observation.sigma is not None:
        if not math.isfinite(observation.sigma) or observation.sigma <= 0:
            raise FitError(
                (
                    FitIssue(
                        observation.row,
                        "sigma",
                        str(observation.sigma),
                        "sigma must be finite and positive",
                    ),
                )
            )
        return 1.0 / (observation.sigma * observation.sigma)
    if weight_mode == "equal":
        return 1.0
    if weight_mode == "poisson":
        return 1.0 / max(observation.I_obs, poisson_epsilon)
    raise FitError((FitIssue(0, "weight_mode", str(weight_mode), "unsupported weight mode"),))


def _validate_observations(observations: Sequence[PeakObservation]) -> None:
    if not observations:
        raise FitError((FitIssue(0, "observations", "", "at least one observation is required"),))
    issues: list[FitIssue] = []
    for obs in observations:
        if not math.isfinite(obs.I_obs) or obs.I_obs <= 0:
            issues.append(
                FitIssue(
                    obs.row,
                    "I_obs",
                    str(obs.I_obs),
                    "I_obs must be finite and positive",
                )
            )
    if issues:
        raise FitError(tuple(issues))


def _build_peak_catalog(
    config: SimulationConfig,
) -> dict[tuple[int, int, int, str], tuple[str, str]]:
    """Map (h,k,l,line_id) → (line_id, line_label) for peaks in the config window.

    Positions depend on lattice and wavelength only, not y, so cataloguing at
    ``config.y`` is sufficient for matching.
    """
    catalog: dict[tuple[int, int, int, str], tuple[str, str]] = {}
    for line_index, line in enumerate(config.lines):
        line_id = f"line_{line_index:02d}"
        reflections = calculate_reflections(
            lattice=config.lattice,
            y=config.y,
            wavelength_a=line.wavelength_a,
            two_theta_min=config.two_theta_min,
            two_theta_max=config.two_theta_max,
            hkl_max=config.hkl_max,
            scattering_mode=config.scattering_mode,
            composition=config.composition,
            include_lorentz_polarization=config.include_lorentz_polarization,
            include_multiplicity=config.include_multiplicity,
            include_cell_volume=config.include_cell_volume,
            min_scaled_intensity=0.0,
        )
        for reflection in reflections:
            key = (reflection.h, reflection.k, reflection.l, line_id)
            catalog[key] = (line_id, line.label)
    return catalog


def _match_observations(
    observations: Sequence[PeakObservation],
    catalog: dict[tuple[int, int, int, str], tuple[str, str]],
    options: FitOptions,
) -> list[MatchedObservation]:
    line_by_token, ambiguous_labels, line_ids = _line_lookup(catalog)
    issues: list[FitIssue] = []
    matched: list[MatchedObservation] = []

    for obs in observations:
        # Forward model enumerates non-negative (h,k,l); map signed indices to
        # the powder-equivalent positive octant for matching and intensity lookup.
        h_key, k_key, l_key = abs(obs.h), abs(obs.k), abs(obs.l)
        candidates = [
            (line_id, line_label)
            for (h, k, l, line_id), (_, line_label) in catalog.items()
            if h == h_key and k == k_key and l == l_key
        ]
        if not candidates:
            issues.append(
                FitIssue(
                    obs.row,
                    "hkl",
                    f"{obs.h},{obs.k},{obs.l}",
                    "unmatched HKL: no model reflection in the active 2θ window "
                    "(indices use the non-negative powder convention 0..hkl_max; "
                    "negative signs are mapped to |h|,|k|,|l|)",
                )
            )
            continue

        if obs.line is None or str(obs.line).strip() == "":
            unique_lines = sorted({line_id for line_id, _ in candidates})
            if len(unique_lines) > 1:
                issues.append(
                    FitIssue(
                        obs.row,
                        "line",
                        "",
                        "multi-line ambiguity: specify line or line_id "
                        f"(candidates: {', '.join(unique_lines)})",
                    )
                )
                continue
            line_id, line_label = next(
                (lid, ll) for lid, ll in candidates if lid == unique_lines[0]
            )
        else:
            token = str(obs.line).strip()
            # Prefer exact line_id matches so synthetic ids remain usable even when a
            # duplicate label string collides with an id token (e.g. both labeled
            # "line_00"). Ambiguous-label hard-fail runs only for non-id tokens.
            if token in line_ids:
                resolved = line_by_token[token]
            elif token in ambiguous_labels:
                issues.append(
                    FitIssue(
                        obs.row,
                        "line",
                        token,
                        f"duplicate radiation line label '{token}'; match by "
                        "line_id (line_00, line_01, ...) instead",
                    )
                )
                continue
            else:
                resolved = line_by_token.get(token)
                if resolved is None:
                    issues.append(
                        FitIssue(
                            obs.row,
                            "line",
                            token,
                            "unknown radiation line; use line_id (line_00) or line label",
                        )
                    )
                    continue
            line_id, line_label = resolved
            if (h_key, k_key, l_key, line_id) not in catalog:
                issues.append(
                    FitIssue(
                        obs.row,
                        "hkl",
                        f"{obs.h},{obs.k},{obs.l},{line_id}",
                        "unmatched HKL for the specified radiation line",
                    )
                )
                continue

        try:
            weight = resolve_weight(
                obs,
                weight_mode=options.weight_mode,
                poisson_epsilon=options.poisson_epsilon,
            )
        except FitError as exc:
            issues.extend(exc.issues)
            continue

        series_id = f"{line_id}__h{h_key}k{k_key}l{l_key}"
        matched.append(
            MatchedObservation(
                observation=obs,
                line_id=line_id,
                line_label=line_label,
                series_id=series_id,
                weight=weight,
                included=True,
            )
        )

    if issues:
        raise FitError(tuple(issues))

    # Duplicate HKL+line rows would double-count in S and chi2.
    by_series: dict[str, list[int]] = {}
    for item in matched:
        by_series.setdefault(item.series_id, []).append(item.observation.row)
    for series_id, rows in sorted(by_series.items()):
        if len(rows) > 1:
            row_list = ", ".join(str(row) for row in rows)
            issues.append(
                FitIssue(
                    rows[0],
                    "hkl",
                    series_id,
                    "duplicate observation for the same HKL and radiation line "
                    f"(rows {row_list}); keep a single row per series_id",
                )
            )
    if issues:
        raise FitError(tuple(issues))
    return matched


def _line_lookup(
    catalog: dict[tuple[int, int, int, str], tuple[str, str]],
) -> tuple[dict[str, tuple[str, str]], frozenset[str], frozenset[str]]:
    """Map line_id and unique labels → (line_id, label).

    Duplicate labels are omitted from the token map. Synthetic ``line_id`` keys
    are always present and take precedence over label matching (including when a
    colliding label string equals a synthetic id such as ``line_00``). The second
    return value lists labels that collide so callers can emit a structured error
    when those tokens are used as labels. The third return value is the set of
    known ``line_id`` tokens.
    """
    lookup: dict[str, tuple[str, str]] = {}
    label_to_ids: dict[str, set[str]] = {}
    seen_pairs: set[tuple[str, str]] = set()
    for line_id, line_label in catalog.values():
        pair = (line_id, line_label)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        lookup[line_id] = (line_id, line_label)
        label_to_ids.setdefault(line_label, set()).add(line_id)

    ambiguous_labels = frozenset(label for label, ids in label_to_ids.items() if len(ids) > 1)
    line_ids = frozenset(line_id for line_id, _ in seen_pairs)
    for line_id, line_label in seen_pairs:
        if line_label in ambiguous_labels:
            continue
        # Do not overwrite a line_id token with a label that happens to match it.
        if line_label in lookup and lookup[line_label][0] != line_id:
            continue
        lookup[line_label] = (line_id, line_label)
    return lookup, ambiguous_labels, line_ids


def _uniform_grid(start: float, stop: float, points: int) -> list[float]:
    if points == 1 or stop == start:
        return [float(start)]
    step = (stop - start) / (points - 1)
    return [start + index * step for index in range(points)]


def _build_peak_geometry(
    config: SimulationConfig,
    matched: Sequence[MatchedObservation],
) -> dict[tuple[str, int, int, int], _PeakGeometry]:
    geometry: dict[tuple[str, int, int, int], _PeakGeometry] = {}
    for item in matched:
        obs = item.observation
        key = (item.line_id, abs(obs.h), abs(obs.k), abs(obs.l))
        if key in geometry:
            continue
        line_index = int(item.line_id.rsplit("_", maxsplit=1)[1])
        line = config.lines[line_index]
        reflection = calculate_reflection_for_hkl(
            h=key[1],
            k=key[2],
            l=key[3],
            lattice=config.lattice,
            y=config.y,
            wavelength_a=line.wavelength_a,
            two_theta_min=config.two_theta_min,
            two_theta_max=config.two_theta_max,
            scattering_mode=config.scattering_mode,
            composition=config.composition,
            include_lorentz_polarization=config.include_lorentz_polarization,
            include_multiplicity=config.include_multiplicity,
            include_cell_volume=config.include_cell_volume,
        )
        if reflection is None:
            raise ValueError(
                f"matched HKL is outside the active model window: {key[1:]} {item.line_id}"
            )
        geometry[key] = _PeakGeometry(
            h=reflection.h,
            k=reflection.k,
            l=reflection.l,
            line_id=item.line_id,
            line_weight=line.weight,
            d_spacing=reflection.d_spacing_a,
            two_theta=reflection.two_theta_deg,
            form_factor=reflection.form_factor_effective,
            multiplicity=reflection.multiplicity,
            lp_factor=reflection.lorentz_polarization,
            cell_volume=reflection.cell_volume_a3,
            applied_multiplicity=reflection.applied_multiplicity,
            applied_lp=reflection.applied_lorentz_polarization,
            applied_volume_factor=reflection.applied_volume_factor,
        )
    return geometry


def _model_intensity_matrix(
    geometry: dict[tuple[str, int, int, int], _PeakGeometry],
    included: Sequence[MatchedObservation],
    y_grid: Sequence[float],
    options: FitOptions,
) -> tuple[list[list[float]], list[bool]]:
    matrix: list[list[float]] = []
    max_abs: list[float] = [0.0] * len(included)
    for y_value in y_grid:
        row = _model_intensities_at_y(geometry, included, y_value)
        matrix.append(row)
        for index, value in enumerate(row):
            max_abs[index] = max(max_abs[index], abs(value))
    vanishing = [value <= options.model_zero_tol for value in max_abs]
    return matrix, vanishing


def _model_intensities_at_y(
    geometry: dict[tuple[str, int, int, int], _PeakGeometry],
    included: Sequence[MatchedObservation],
    y_value: float,
) -> list[float]:
    validate_y(y_value)
    values: list[float] = []
    for item in included:
        obs = item.observation
        key = (item.line_id, abs(obs.h), abs(obs.k), abs(obs.l))
        peak = geometry.get(key)
        if peak is None:
            values.append(0.0)
            continue
        structure_factor = cmcm_4c_structure_factor(
            peak.h,
            peak.k,
            peak.l,
            y_value,
            peak.form_factor,
        )
        structure_factor_squared = float((structure_factor * structure_factor.conjugate()).real)
        if abs(structure_factor_squared) < 1e-12:
            structure_factor_squared = 0.0
        intensity = calculate_model_peak_intensity(
            structure_factor_squared,
            applied_multiplicity=peak.applied_multiplicity,
            applied_lorentz_polarization=peak.applied_lp,
            applied_volume_factor=peak.applied_volume_factor,
            line_weight=peak.line_weight,
        )
        values.append(intensity)
    return values


def evaluate_fit_model_intensities(
    config: SimulationConfig,
    matched: Sequence[MatchedObservation],
    y: float,
) -> tuple[float, ...]:
    """Evaluate only the matched HKLs through the fit's cached direct path."""
    included = tuple(item for item in matched if item.included)
    geometry = _build_peak_geometry(config, included)
    return tuple(_model_intensities_at_y(geometry, included, y))


def evaluate_reference_fit_model_intensities(
    config: SimulationConfig,
    matched: Sequence[MatchedObservation],
    y: float,
) -> tuple[float, ...]:
    """Evaluate matched HKLs through the shared single-reflection reference path."""
    validate_y(y)
    values: list[float] = []
    for item in matched:
        if not item.included:
            continue
        obs = item.observation
        line_index = int(item.line_id.rsplit("_", maxsplit=1)[1])
        line = config.lines[line_index]
        reflection = calculate_reflection_for_hkl(
            h=abs(obs.h),
            k=abs(obs.k),
            l=abs(obs.l),
            lattice=config.lattice,
            y=y,
            wavelength_a=line.wavelength_a,
            two_theta_min=config.two_theta_min,
            two_theta_max=config.two_theta_max,
            scattering_mode=config.scattering_mode,
            composition=config.composition,
            include_lorentz_polarization=config.include_lorentz_polarization,
            include_multiplicity=config.include_multiplicity,
            include_cell_volume=config.include_cell_volume,
        )
        if reflection is None:
            raise ValueError("matched HKL is outside the active model window")
        values.append(reflection.intensity_model * line.weight)
    return tuple(values)


def _closed_form_scale_and_chi2(
    i_obs: Sequence[float],
    i_model: Sequence[float],
    weights: Sequence[float],
) -> tuple[float, float]:
    numerator = 0.0
    denominator = 0.0
    for obs, model, weight in zip(i_obs, i_model, weights, strict=True):
        numerator += weight * obs * model
        denominator += weight * model * model
    scale_s = numerator / denominator if denominator > 0.0 else 0.0
    if scale_s < 0.0:
        # Physical scale is non-negative; clamp and recompute χ².
        scale_s = 0.0
    chi2 = chi_squared(i_obs, i_model, weights, scale_s)
    return scale_s, chi2


def _local_minimum_candidates(
    grid_scan: Sequence[GridScanPoint],
    max_count: int | None,
) -> list[LocalMinimumCandidate]:
    if not grid_scan:
        return []
    candidates: list[LocalMinimumCandidate] = []
    n = len(grid_scan)
    for index, point in enumerate(grid_scan):
        left = grid_scan[index - 1].chi2 if index > 0 else point.chi2
        right = grid_scan[index + 1].chi2 if index + 1 < n else point.chi2
        if point.chi2 <= left and point.chi2 <= right:
            # Endpoints: only count if strictly better than the sole neighbour.
            if index == 0 and n > 1 and not (point.chi2 < right):
                continue
            if index == n - 1 and n > 1 and not (point.chi2 < left):
                continue
            candidates.append(
                LocalMinimumCandidate(
                    y=point.y,
                    scale_s=point.scale_s,
                    chi2=point.chi2,
                    grid_index=index,
                )
            )
    candidates.sort(key=lambda item: item.chi2)
    return candidates if max_count is None else candidates[:max_count]


def _attach_candidate_refinement(
    candidate: LocalMinimumCandidate,
    refinements: dict[int, _CandidateRefinement],
) -> LocalMinimumCandidate:
    refinement = refinements.get(candidate.grid_index)
    if refinement is None:
        return candidate
    return replace(
        candidate,
        refined_y=refinement.y,
        refined_scale_s=refinement.scale_s,
        refined_chi2=refinement.chi2,
        refine_status=refinement.status,
    )


def _refine_grid_candidate(
    objective: Callable[[float], tuple[float, float, float]],
    y_grid: Sequence[float],
    grid_index: int,
    options: FitOptions,
) -> tuple[float, float, float, list[RefineTracePoint]]:
    bracket = _refinement_bracket(y_grid, grid_index, options)
    return _brent_minimize(
        objective,
        bracket[0],
        bracket[1],
        xtol=options.refine_xtol,
        max_iter=options.refine_max_iter,
    )


def _candidate_chi2(candidate: LocalMinimumCandidate) -> float:
    return candidate.refined_chi2 if candidate.refined_chi2 is not None else candidate.chi2


def _candidate_y(candidate: LocalMinimumCandidate) -> float:
    return candidate.refined_y if candidate.refined_y is not None else candidate.y


def _profile_identifiability(
    grid_scan: Sequence[GridScanPoint],
    best: BestFit,
    local_minima: Sequence[LocalMinimumCandidate],
    options: FitOptions,
) -> FitIdentifiability:
    samples: list[tuple[float, float]] = [
        (point.y, point.chi2) for point in grid_scan if math.isfinite(point.chi2)
    ]
    samples.extend(
        (candidate.refined_y, candidate.refined_chi2)
        for candidate in local_minima
        if candidate.refined_y is not None
        and candidate.refined_chi2 is not None
        and math.isfinite(candidate.refined_chi2)
    )
    samples.append((best.y, best.chi2))
    samples.sort(key=lambda item: item[0])

    unique_samples: list[tuple[float, float]] = []
    for y_value, chi2 in samples:
        if not math.isfinite(y_value) or not math.isfinite(chi2):
            continue
        if unique_samples and math.isclose(unique_samples[-1][0], y_value, abs_tol=1e-14):
            if chi2 < unique_samples[-1][1]:
                unique_samples[-1] = (y_value, chi2)
        else:
            unique_samples.append((y_value, chi2))

    if not unique_samples or not math.isfinite(best.chi2):
        return FitIdentifiability(
            method="profile_delta_chi2",
            delta_chi2_threshold=options.profile_delta_chi2,
            y_lower=None,
            y_upper=None,
            status="not_available",
            reasons=("non_finite_profile",),
            near_best_candidate_count=0,
        )

    threshold = best.chi2 + options.profile_delta_chi2
    best_index = min(
        range(len(unique_samples)),
        key=lambda index: abs(unique_samples[index][0] - best.y),
    )
    passing = [chi2 <= threshold for _, chi2 in unique_samples]
    left_index = best_index
    while left_index > 0 and passing[left_index - 1]:
        left_index -= 1
    right_index = best_index
    while right_index + 1 < len(unique_samples) and passing[right_index + 1]:
        right_index += 1

    def crossing(outside_index: int, inside_index: int) -> float:
        outside_y, outside_chi2 = unique_samples[outside_index]
        inside_y, inside_chi2 = unique_samples[inside_index]
        denominator = outside_chi2 - inside_chi2
        if math.isclose(denominator, 0.0, abs_tol=1e-15):
            return inside_y
        fraction = (threshold - inside_chi2) / denominator
        fraction = min(max(fraction, 0.0), 1.0)
        return inside_y + fraction * (outside_y - inside_y)

    y_lower = (
        unique_samples[0][0]
        if left_index == 0
        else crossing(left_index - 1, left_index)
    )
    y_upper = (
        unique_samples[-1][0]
        if right_index == len(unique_samples) - 1
        else crossing(right_index + 1, right_index)
    )

    grid_step = abs(options.y_stop - options.y_start) / max(options.grid_points - 1, 1)
    near_best = [
        candidate
        for candidate in local_minima
        if _candidate_chi2(candidate) <= threshold
        and abs(_candidate_y(candidate) - best.y) > max(1.5 * grid_step, 1e-12)
    ]
    near_best_candidate_count = len(near_best) + 1
    reasons: list[str] = []
    if left_index == 0:
        reasons.append("lower_bound_reached")
    if right_index == len(unique_samples) - 1:
        reasons.append("upper_bound_reached")
    if near_best:
        reasons.append("multiple_near_best_candidates")
    if all(passing):
        reasons.append("profile_flat_over_scan")

    if all(passing):
        status = "flat"
    elif near_best:
        status = "multi_modal"
    elif left_index == 0 or right_index == len(unique_samples) - 1:
        status = "boundary_limited"
    else:
        status = "identified"
    return FitIdentifiability(
        method="profile_delta_chi2",
        delta_chi2_threshold=options.profile_delta_chi2,
        y_lower=y_lower,
        y_upper=y_upper,
        status=status,
        reasons=tuple(reasons),
        near_best_candidate_count=near_best_candidate_count,
    )


def _refinement_bracket(
    y_grid: Sequence[float],
    best_index: int,
    options: FitOptions,
) -> tuple[float, float]:
    n = len(y_grid)
    if n == 1:
        return (y_grid[0], y_grid[0])
    left_index = max(0, best_index - 1)
    right_index = min(n - 1, best_index + 1)
    left = y_grid[left_index]
    right = y_grid[right_index]
    if left == right:
        # Expand by one grid step if possible.
        step = (options.y_stop - options.y_start) / max(options.grid_points - 1, 1)
        left = max(options.y_start, y_grid[best_index] - step)
        right = min(options.y_stop, y_grid[best_index] + step)
    return (left, right)


def _brent_minimize(
    objective: Callable[[float], tuple[float, float, float]],
    a: float,
    b: float,
    *,
    xtol: float,
    max_iter: int,
) -> tuple[float, float, float, list[RefineTracePoint]]:
    """Golden-section / Brent-style 1-D minimisation of χ²(y) on [a, b]."""
    trace: list[RefineTracePoint] = []
    evaluation = 0

    def evaluate(x: float) -> tuple[float, float]:
        nonlocal evaluation
        chi2, scale_s, _ = objective(x)
        evaluation += 1
        trace.append(RefineTracePoint(y=x, scale_s=scale_s, chi2=chi2, evaluation=evaluation))
        return chi2, scale_s

    if b < a:
        a, b = b, a
    if math.isclose(a, b, abs_tol=xtol):
        chi2, scale_s = evaluate(a)
        return a, scale_s, chi2, trace

    invphi = (math.sqrt(5.0) - 1.0) / 2.0
    invphi2 = (3.0 - math.sqrt(5.0)) / 2.0

    x = w = v = a + invphi2 * (b - a)
    fx, sx = evaluate(x)
    fw = fv = fx
    d = e = 0.0

    for _ in range(max_iter):
        midpoint = 0.5 * (a + b)
        tol1 = xtol * abs(x) + xtol * 0.25
        tol2 = 2.0 * tol1
        if abs(x - midpoint) <= tol2 - 0.5 * (b - a):
            break

        parabolic_ok = False
        if abs(e) > tol1:
            # Try parabolic step through (x, w, v).
            r = (x - w) * (fx - fv)
            q = (x - v) * (fx - fw)
            p = (x - v) * q - (x - w) * r
            q = 2.0 * (q - r)
            if q > 0.0:
                p = -p
            q = abs(q)
            etemp = e
            e = d
            if abs(p) < abs(0.5 * q * etemp) and p > q * (a - x) and p < q * (b - x):
                d = p / q
                u = x + d
                if (u - a) < tol2 or (b - u) < tol2:
                    d = math.copysign(tol1, midpoint - x)
                parabolic_ok = True
            else:
                parabolic_ok = False

        if not parabolic_ok:
            e = (a - x) if x >= midpoint else (b - x)
            d = invphi * e

        u = x + (math.copysign(tol1, d) if abs(d) < tol1 else d)
        fu, su = evaluate(u)

        if fu <= fx:
            if u >= x:
                a = x
            else:
                b = x
            v, fv = w, fw
            w, fw = x, fx
            x, fx, sx = u, fu, su
        else:
            if u < x:
                a = u
            else:
                b = u
            if fu <= fw or w == x:
                v, fv = w, fw
                w, fw = u, fu
            elif fu <= fv or v in (x, w):
                v, fv = u, fu

    return x, sx, fx, trace


def _residuals_at_best(
    geometry: dict[tuple[str, int, int, int], _PeakGeometry],
    matched: Sequence[MatchedObservation],
    y_best: float,
    scale_s: float,
) -> list[ResidualAtBest]:
    included = [item for item in matched if item.included]
    i_model_included = _model_intensities_at_y(geometry, included, y_best) if included else []
    model_by_series = {
        item.series_id: value for item, value in zip(included, i_model_included, strict=True)
    }
    # Evaluate model intensities for excluded rows as well (audit table).
    excluded = [item for item in matched if not item.included]
    i_model_excluded = _model_intensities_at_y(geometry, excluded, y_best) if excluded else []
    for item, value in zip(excluded, i_model_excluded, strict=True):
        model_by_series[item.series_id] = value

    residuals: list[ResidualAtBest] = []
    for item in matched:
        obs = item.observation
        i_model = model_by_series.get(item.series_id, 0.0)
        s_i_model = scale_s * i_model
        residuals.append(
            ResidualAtBest(
                h=obs.h,
                k=obs.k,
                l=obs.l,
                line_id=item.line_id,
                line_label=item.line_label,
                series_id=item.series_id,
                I_obs=obs.I_obs,
                I_model=i_model,
                S_I_model=s_i_model,
                residual=obs.I_obs - s_i_model,
                weight=item.weight,
                included=item.included,
            )
        )
    return residuals


def _merge_matched_exclusions(
    original: Sequence[MatchedObservation],
    updated_included_pool: Sequence[MatchedObservation],
) -> list[MatchedObservation]:
    by_key = {(item.observation.row, item.series_id): item for item in updated_included_pool}
    merged: list[MatchedObservation] = []
    for item in original:
        key = (item.observation.row, item.series_id)
        merged.append(by_key.get(key, item))
    return merged
