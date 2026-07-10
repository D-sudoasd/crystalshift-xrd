from dataclasses import replace

import pytest

from orthoxrd.batch import SweepConfig, generate_sweep
from orthoxrd.sweep_limits import (
    MAX_ESTIMATED_UNCOMPRESSED_BYTES,
    estimate_sweep_export_size,
)
from tests.test_sweep_v2 import _base


def test_export_size_estimate_reports_uncompressed_and_zip_bytes() -> None:
    estimate = estimate_sweep_export_size(
        spectrum_cells=1000,
        estimated_peak_rows=500,
    )

    assert estimate.uncompressed_bytes > 0
    assert estimate.zip_bytes == estimate.uncompressed_bytes // 2


def test_sweep_blocks_estimated_export_over_one_gib_before_calculation() -> None:
    base = replace(_base(), hkl_max=9, spectrum_points=1200)
    config = SweepConfig.from_simulation(
        base,
        axis="y",
        start=0.0,
        stop=0.5,
        step=0.0005,
    )

    with pytest.raises(ValueError, match="1 GiB"):
        generate_sweep(config)


def test_one_gib_limit_constant_is_exact() -> None:
    assert MAX_ESTIMATED_UNCOMPRESSED_BYTES == 1024**3
