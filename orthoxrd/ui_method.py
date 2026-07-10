from __future__ import annotations

import streamlit as st


def render_method_view() -> None:
    st.subheader("Method and interpretation")
    left, right = st.columns(2)
    with left:
        st.markdown(
            """
#### Cmcm 4c model

The occupied fractional coordinates are generated for the orthorhombic
Cmcm 4c site. The Wyckoff parameter controls the basal shuffle:

**shuffle_signed = 2(y - 0.25)**

**shuffle_magnitude = abs(shuffle_signed)**

Changing y changes the structure factor but does not change d-spacing.
Changing a, b, or c changes d-spacing and the Bragg position.

#### Peak intensity

**I_model_peak = F2 x applied_multiplicity x applied_LP x applied_volume x line_weight**

Each applied factor is exported separately. applied_volume is either 1/V
or 1, preserving the selected model contract.
"""
        )
    with right:
        st.markdown(
            """
#### Profile and normalization

**I_profile_model** is the unnormalized sum of peak profiles.

**I_rel_local** uses one maximum per spectrum or sweep step. It supports shape
comparison but not cross-step amplitude comparison.

**I_rel_global** uses one maximum for the complete sweep. Use it for intensity
evolution across steps.

#### Model boundary

The output is theoretical model intensity, not measured raw intensity,
absolute calibrated intensity, phase fraction, or a Rietveld fit. The model
does not include texture, absorption, anomalous dispersion, preferred
orientation, microstrain, crystallite-size broadening, zero shift, or
background.
"""
        )
    st.info(
        "For paper-style orthorhombic F2(y) trends, use Unit scatterer F2. "
        "For a composition-aware X-ray pattern, use Composition form factor."
    )
