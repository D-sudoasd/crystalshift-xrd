from __future__ import annotations

from typing import Final, Literal, assert_never

from orthoxrd.models import Reflection

PeakMetric = Literal[
    "F2",
    "N_F2",
    "R_hkl_with_LP",
    "R_hkl_no_LP",
    "I_model",
    "I_rel_global",
]

PEAK_METRICS: Final[tuple[PeakMetric, ...]] = (
    "F2",
    "N_F2",
    "R_hkl_with_LP",
    "R_hkl_no_LP",
    "I_model",
    "I_rel_global",
)


def peak_metric_value(
    reflection: Reflection,
    metric: PeakMetric,
    *,
    peak_global_max: float,
) -> float:
    match metric:
        case "F2":
            return reflection.structure_factor_squared
        case "N_F2":
            return reflection.n_f2
        case "R_hkl_with_LP":
            return reflection.reference_r_hkl_with_lp
        case "R_hkl_no_LP":
            return reflection.reference_r_hkl_no_lp
        case "I_model":
            return reflection.intensity_model
        case "I_rel_global":
            return (
                reflection.intensity_model / peak_global_max * 100.0
                if peak_global_max > 0
                else 0.0
            )
        case unreachable:
            assert_never(unreachable)
