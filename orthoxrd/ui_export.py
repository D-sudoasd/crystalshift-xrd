from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import streamlit as st

from orthoxrd.export_writer import PreparedExport, cleanup_export
from orthoxrd.i18n import t, th
from orthoxrd.simulation import SimulationResult

CURRENT_EXPORT_KEY = "current_prepared_export"
CURRENT_EXPORT_SIGNATURE_KEY = "current_export_state_signature"


def render_current_export(
    result: SimulationResult,
    config_digest: str,
    prepare: Callable[[SimulationResult], PreparedExport],
    state_signature: str = "",
) -> None:
    prepared = _valid_prepared(CURRENT_EXPORT_KEY, config_digest)
    if (
        prepared is not None
        and st.session_state.get(CURRENT_EXPORT_SIGNATURE_KEY) != state_signature
    ):
        _discard(CURRENT_EXPORT_KEY)
        prepared = None
    if st.button(
        t("export.prepare"),
        key="prepare_current_zip",
        help=th("export.prepare"),
        use_container_width=True,
    ):
        _discard(CURRENT_EXPORT_KEY)
        with st.spinner(t("export.spinner")):
            prepared = prepare(result)
        st.session_state[CURRENT_EXPORT_KEY] = prepared
        st.session_state[CURRENT_EXPORT_SIGNATURE_KEY] = state_signature
    if prepared is None:
        st.caption(t("export.caption"))
        return
    path = Path(prepared.path)
    if not path.exists():
        st.session_state.pop(CURRENT_EXPORT_KEY, None)
        st.warning(t("export.expired"))
        return
    with path.open("rb") as handle:
        st.download_button(
            t("export.download"),
            data=handle,
            file_name="current_simulation.zip",
            mime="application/zip",
            key="download_current_zip",
            use_container_width=True,
            help=th("export.download"),
        )
    st.caption(
        t("export.size", kib=prepared.size_bytes / 1024, sha=prepared.sha256[:12])
    )


def discard_prepared(key: str) -> None:
    _discard(key)


def _valid_prepared(key: str, digest: str) -> PreparedExport | None:
    prepared = st.session_state.get(key)
    if not isinstance(prepared, PreparedExport):
        return None
    if prepared.config_hash != digest:
        _discard(key)
        return None
    return prepared


def _discard(key: str) -> None:
    prepared = st.session_state.pop(key, None)
    if key == CURRENT_EXPORT_KEY:
        st.session_state.pop(CURRENT_EXPORT_SIGNATURE_KEY, None)
    if isinstance(prepared, PreparedExport):
        cleanup_export(prepared)
