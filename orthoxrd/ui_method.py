from __future__ import annotations

import streamlit as st

from orthoxrd.i18n import t


def render_method_view() -> None:
    st.subheader(t("method.title"))
    left, right = st.columns(2)
    with left:
        st.markdown(t("method.left"))
    with right:
        st.markdown(t("method.right"))
    st.info(t("method.info"))
