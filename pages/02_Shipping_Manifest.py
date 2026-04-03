from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import shipping_manifest_breakdown, shipping_manifest_live_code
from services.storage import initialize_session_state
from services.ui import (
    bootstrap_app,
    configure_page,
    handle_tutor_interaction,
    inject_styles,
    render_kpis,
    render_last_tutor_response,
    render_live_code_panel,
    render_plain_note,
    render_python_breakdown,
    render_quiz,
    render_section_heading,
    render_sidebar,
    render_study_notes_panel,
    render_what_you_will_learn,
)


def main() -> None:
    configure_page("NEBULOUS-CORE | Shipping Manifest")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("shipping_manifest", gemini_service, kimi_service)

    st.session_state.setdefault("manifest_coils", ["COIL-101", "COIL-103"])
    st.session_state.setdefault("manifest_suppliers", {"PT Meratus": 42.0, "PT Cakra": 38.0})

    bootstrap_app("shipping_manifest")
    render_kpis(
        [
            ("Focus", "Lists & Dictionaries", "This lesson teaches how Python stores collections, not just single values."),
            ("List Size", str(len(st.session_state["manifest_coils"])), "How many coils are currently in the manifest list."),
            ("Next Unlock", "Module 3", "Pass this quiz to unlock logic and functions."),
        ]
    )
    render_what_you_will_learn("shipping_manifest")

    render_section_heading(
        "Manifest Builder",
        "Add coils to a list and supplier quantities to a dictionary like a shipping manifest clerk.",
    )
    builder_column, preview_column = st.columns([0.9, 1.1], gap="large")
    with builder_column:
        new_coil_id = st.text_input("New coil ID", value="COIL-107")
        if st.button("Add coil to list", key="add-coil"):
            st.session_state["manifest_coils"].append(new_coil_id)
        supplier_name = st.text_input("Supplier key", value="PT Baru")
        supplier_quantity = st.number_input("Supplier quantity", min_value=0.0, max_value=500.0, value=24.0, step=1.0)
        if st.button("Add supplier to dictionary", key="add-supplier"):
            st.session_state["manifest_suppliers"][supplier_name] = float(supplier_quantity)
        if st.button("Reset manifest", key="reset-manifest"):
            st.session_state["manifest_coils"] = ["COIL-101", "COIL-103"]
            st.session_state["manifest_suppliers"] = {"PT Meratus": 42.0, "PT Cakra": 38.0}
            st.rerun()
        render_plain_note(
            "Use a list when order matters and a dictionary when you need a label-value relationship."
        )

    coil_manifest = list(st.session_state["manifest_coils"])
    supplier_manifest = dict(st.session_state["manifest_suppliers"])
    with preview_column:
        preview_tabs = st.tabs(["List View", "Dictionary View", "Chart View"])
        with preview_tabs[0]:
            st.json({"coil_manifest": coil_manifest})
        with preview_tabs[1]:
            st.json({"supplier_manifest": supplier_manifest})
        with preview_tabs[2]:
            supplier_frame = pd.DataFrame(
                {"supplier_name": list(supplier_manifest.keys()), "quantity": list(supplier_manifest.values())}
            )
            figure = px.bar(
                supplier_frame,
                x="supplier_name",
                y="quantity",
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=[ACCENT_COLOR],
            )
            figure.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(figure, width="stretch")

    active_python_snippet = render_live_code_panel(
        "Live Code",
        shipping_manifest_live_code(coil_manifest=coil_manifest, supplier_manifest=supplier_manifest),
        key="shipping-manifest-live-code",
    )
    render_python_breakdown("How this works in Python", shipping_manifest_breakdown())

    render_section_heading("Vibe Explanation", "This is where single bins become a real manifest.")
    st.markdown(
        (
            f"The list now stores **{len(coil_manifest)}** coil IDs in order, while the dictionary stores **{len(supplier_manifest)}** "
            "supplier-to-quantity relationships. Ain is learning that Python chooses different containers for different logistics jobs."
        )
    )

    render_study_notes_panel("shipping_manifest", gemini_service)
    module_state = {
        "coil_manifest": coil_manifest,
        "supplier_manifest": supplier_manifest,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("shipping_manifest", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("shipping_manifest")


if __name__ == "__main__":
    main()

