from __future__ import annotations

from pathlib import Path
from typing import Final

import streamlit as st

from orthoxrd.export_live import prepare_live_export
from orthoxrd.export_writer import PreparedExport
from orthoxrd.i18n import t, th
from orthoxrd.live import LivePreviewResult
from orthoxrd.ui_export import discard_prepared
from orthoxrd.ui_plot_state import PlotState

LIVE_EXPORT_KEY: Final = "live_prepared_export"
LIVE_EXPORT_SIGNATURE_KEY: Final = "live_export_signature"


def render_live_export(
    result: LivePreviewResult,
    plot_state: PlotState,
    current_index: int,
    baseline_index: int,
) -> None:
    signature = _signature(result, plot_state, current_index, baseline_index)
    if st.button(
        t("live.export.prepare"),
        key="prepare_live_zip",
        help=th("live.export.prepare"),
        use_container_width=True,
    ):
        discard_prepared(LIVE_EXPORT_KEY)
        with st.spinner(t("live.export.spinner")):
            prepared = prepare_live_export(
                result,
                current_index,
                baseline_index,
                plot_state,
            )
        st.session_state[LIVE_EXPORT_KEY] = prepared
        st.session_state[LIVE_EXPORT_SIGNATURE_KEY] = signature
    prepared = st.session_state.get(LIVE_EXPORT_KEY)
    if not isinstance(prepared, PreparedExport):
        st.caption(t("live.export.caption_prepare"))
        return
    path = Path(prepared.path)
    if (
        st.session_state.get(LIVE_EXPORT_SIGNATURE_KEY) != signature
        or not path.exists()
    ):
        discard_prepared(LIVE_EXPORT_KEY)
        st.caption(t("live.export.caption_changed"))
        return
    with path.open("rb") as handle:
        st.download_button(
            t("live.export.download"),
            data=handle,
            file_name="live_evolution.zip",
            mime="application/zip",
            key="download_live_zip",
            use_container_width=True,
            help=th("live.export.download"),
        )
    st.caption(
        t(
            "live.export.size",
            kib=prepared.size_bytes / 1024,
            sha=prepared.sha256[:12],
        )
    )


def invalidate_live_export() -> None:
    discard_prepared(LIVE_EXPORT_KEY)
    st.session_state.pop(LIVE_EXPORT_SIGNATURE_KEY, None)


def _signature(
    result: LivePreviewResult,
    state: PlotState,
    current_index: int,
    baseline_index: int,
) -> str:
    return (
        f"{result.signature}:{baseline_index}:{current_index}:"
        f"{state.x_axis}:{state.x_minimum}:{state.x_maximum}:"
        f"{state.y_auto}:{state.y_minimum}:{state.y_maximum}"
    )
