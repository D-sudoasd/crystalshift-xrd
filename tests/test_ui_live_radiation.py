from unittest.mock import patch

import pytest

from orthoxrd.models import RadiationLine
from orthoxrd.powder import energy_kev_to_wavelength_a
from orthoxrd.ui_live import _apply_axis_value
from orthoxrd.ui_radiation import (
    CUSTOM_TEMPLATE_KEY,
    CUSTOM_TEMPLATE_MODE_KEY,
    ENERGY_KEY,
    MODE_KEY,
    _lines_from_mode,
)


def test_live_energy_commit_preserves_multiline_radiation_template() -> None:
    primary = energy_kev_to_wavelength_a(31.0)
    lines = (
        RadiationLine("K-alpha1", primary, 2.0),
        RadiationLine("K-alpha2", primary * 1.0025, 1.0),
    )
    state: dict[str, object] = {}

    with (
        patch("orthoxrd.ui_live.st.session_state", state),
        patch("orthoxrd.ui_radiation.st.session_state", state),
    ):
        _apply_axis_value("energy_keV", 31.0, "lower", lines)
        with patch("orthoxrd.ui_radiation.st.number_input", return_value=31.0):
            rebuilt = _lines_from_mode("Custom energy")

    assert state[MODE_KEY] == "Custom energy"
    assert state[ENERGY_KEY] == pytest.approx(31.0)
    assert state[CUSTOM_TEMPLATE_MODE_KEY] == "Custom energy"
    assert state[CUSTOM_TEMPLATE_KEY] == lines
    assert len(rebuilt) == 2
    assert [line.weight for line in rebuilt] == pytest.approx([2.0, 1.0])
    assert rebuilt[1].wavelength_a / rebuilt[0].wavelength_a == pytest.approx(1.0025)


def test_manual_source_mode_change_clears_live_multiline_template() -> None:
    state: dict[str, object] = {
        CUSTOM_TEMPLATE_MODE_KEY: "Custom energy",
        CUSTOM_TEMPLATE_KEY: (
            RadiationLine("K-alpha1", 0.4, 2.0),
            RadiationLine("K-alpha2", 0.401, 1.0),
        ),
    }

    with (
        patch("orthoxrd.ui_radiation.st.session_state", state),
        patch("orthoxrd.ui_radiation.st.number_input", return_value=1.0),
    ):
        rebuilt = _lines_from_mode("Custom wavelength")

    assert len(rebuilt) == 1
    assert CUSTOM_TEMPLATE_KEY not in state
    assert CUSTOM_TEMPLATE_MODE_KEY not in state
