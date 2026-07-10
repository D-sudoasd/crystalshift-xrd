from __future__ import annotations

import streamlit as st

from orthoxrd.ui_css import UI_CSS

CANVAS = "#0b0f14"
SURFACE = "#121821"
SURFACE_RAISED = "#18202b"
BORDER = "#2a3441"
TEXT = "#f3f6fa"
MUTED = "#aeb8c5"
ACCENT = "#22c7d6"
AMBER = "#f2b84b"
RED = "#ff5a67"
GREEN = "#48c78e"
GRID = "rgba(174,184,197,0.14)"


def apply_style() -> None:
    st.markdown(UI_CSS, unsafe_allow_html=True)


def summary_grid(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        '<div class="xrd-summary-card">'
        f'<div class="xrd-summary-label">{label}</div>'
        f'<div class="xrd-summary-value" title="{value}">{value}</div>'
        "</div>"
        for label, value in items
    )
    st.markdown(f'<div class="xrd-summary-grid">{cards}</div>', unsafe_allow_html=True)


def kpi_grid(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        '<div class="xrd-summary-card">'
        f'<div class="xrd-summary-label">{label}</div>'
        f'<div class="xrd-summary-value">{value}</div>'
        "</div>"
        for label, value in items
    )
    st.markdown(f'<div class="xrd-kpi-row">{cards}</div>', unsafe_allow_html=True)
