from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from orthoxrd.config import SimulationConfig

ObservableMode = Literal["peak_area", "peak_height"]
WeightMode = Literal["poisson", "equal"]


@dataclass(frozen=True, slots=True)
class PeakObservation:
    """One observed peak intensity row for the discrete peak intensity fit."""

    h: int
    k: int
    l: int
    I_obs: float
    row: int = 0
    line: str | None = None
    weight: float | None = None
    sigma: float | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class FitOptions:
    """Controls for the discrete peak intensity fit (not Rietveld).

    ``observable_mode`` selects the experimental intensity contract:
    - ``peak_area``: integral (area) intensities — preferred, ADR-aligned path.
    - ``peak_height``: peak heights under an equal-width proxy.

    In v1 both modes share the same objective: model peak intensity
    (``intensity_model * line.weight``) is compared to ``I_obs`` with closed-form
    S. Under the equal-width height proxy, height ∝ area so y and relative
    residuals are unchanged and S absorbs any common constant; there is no
    separate height conversion. Modes may diverge in a later version if width
    modelling is introduced.
    """

    observable_mode: ObservableMode = "peak_area"
    weight_mode: WeightMode = "poisson"
    y_start: float = 0.0
    y_stop: float = 0.5
    grid_points: int = 201
    poisson_epsilon: float = 1e-12
    model_zero_tol: float = 1e-12
    exclude_vanishing_model: bool = True
    max_local_minima: int = 20
    refine: bool = True
    refine_xtol: float = 1e-10
    refine_max_iter: int = 80

    def __post_init__(self) -> None:
        if self.observable_mode not in ("peak_area", "peak_height"):
            raise ValueError("observable_mode must be 'peak_area' or 'peak_height'")
        if self.weight_mode not in ("poisson", "equal"):
            raise ValueError("weight_mode must be 'poisson' or 'equal'")
        if not math.isfinite(self.y_start) or not math.isfinite(self.y_stop):
            raise ValueError("y_start and y_stop must be finite")
        if self.y_stop < self.y_start:
            raise ValueError("y_stop must be greater than or equal to y_start")
        if not 0.0 <= self.y_start <= 0.5 or not 0.0 <= self.y_stop <= 0.5:
            raise ValueError("y range must lie within [0, 0.5]")
        if self.grid_points < 2:
            raise ValueError("grid_points must be at least 2")
        if not math.isfinite(self.poisson_epsilon) or self.poisson_epsilon <= 0:
            raise ValueError("poisson_epsilon must be positive")
        if not math.isfinite(self.model_zero_tol) or self.model_zero_tol < 0:
            raise ValueError("model_zero_tol must be non-negative")
        if self.max_local_minima < 1:
            raise ValueError("max_local_minima must be at least 1")
        if not math.isfinite(self.refine_xtol) or self.refine_xtol <= 0:
            raise ValueError("refine_xtol must be positive")
        if self.refine_max_iter < 1:
            raise ValueError("refine_max_iter must be at least 1")


@dataclass(frozen=True, slots=True)
class MatchedObservation:
    observation: PeakObservation
    line_id: str
    line_label: str
    series_id: str
    weight: float
    included: bool
    exclude_reason: str | None = None


@dataclass(frozen=True, slots=True)
class GridScanPoint:
    y: float
    scale_s: float
    chi2: float


@dataclass(frozen=True, slots=True)
class RefineTracePoint:
    y: float
    scale_s: float
    chi2: float
    evaluation: int


@dataclass(frozen=True, slots=True)
class ResidualAtBest:
    h: int
    k: int
    l: int
    line_id: str
    line_label: str
    series_id: str
    I_obs: float
    I_model: float
    S_I_model: float
    residual: float
    weight: float
    included: bool


@dataclass(frozen=True, slots=True)
class LocalMinimumCandidate:
    y: float
    scale_s: float
    chi2: float
    grid_index: int


@dataclass(frozen=True, slots=True)
class BestFit:
    y: float
    scale_s: float
    chi2: float
    shuffle_signed: float
    shuffle_magnitude: float
    source: str


@dataclass(frozen=True, slots=True)
class FitIssue:
    row: int
    column: str
    value: str
    message: str


class FitError(ValueError):
    """Structured failure for discrete peak intensity fit / observation validation."""

    def __init__(self, issues: tuple[FitIssue, ...]) -> None:
        self.issues = issues
        super().__init__(str(self))

    def __str__(self) -> str:
        first = self.issues[0]
        if first.row > 0:
            return f"fit row {first.row}, {first.column}: {first.message}"
        return f"fit {first.column}: {first.message}"


@dataclass(frozen=True, slots=True)
class FitResult:
    config: SimulationConfig
    options: FitOptions
    matched: tuple[MatchedObservation, ...]
    grid_scan: tuple[GridScanPoint, ...]
    refine_trace: tuple[RefineTracePoint, ...]
    best: BestFit
    residuals_at_best: tuple[ResidualAtBest, ...]
    local_minima: tuple[LocalMinimumCandidate, ...]
    warnings: tuple[str, ...]
