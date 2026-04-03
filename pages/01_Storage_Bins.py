from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import storage_bins_breakdown, storage_bins_live_code
from services.storage import initialize_session_state
from services.ui import (
    bootstrap_app,
    configure_page,
    enforce_unlock,
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
    sync_sources_if_needed,
)


def main() -> None:
    configure_page("NEBULOUS-CORE | Storage Bins")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)
    enforce_unlock("storage_bins")

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sync_sources_if_needed(gemini_service)
    sidebar_payload = render_sidebar("storage_bins", gemini_service, kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]

    bootstrap_app("storage_bins")
    render_kpis(
        [
            ("Focus", "Variables & Types", "The goal is to understand what kind of value Python is storing."),
            ("Factory Analogy", "Storage Bins", "Each variable is a labeled bin on the factory floor."),
            ("Next Unlock", "Module 2", "Pass this quiz to unlock the shipping manifest lesson."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("storage_bins")

    render_section_heading(
        "Bin Labeler",
        "Type a few logistics values and watch Python classify them as text, numbers, or yes/no status flags.",
    )
    controls_column, chart_column = st.columns([0.92, 1.08], gap="large")
    with controls_column:
        supplier_name = st.text_input("Supplier name", value="PT Steel Nusantara")
        coil_weight = st.number_input("Coil weight (tons)", min_value=0.0, max_value=100.0, value=18.75, step=0.25)
        shipment_confirmed = st.toggle("Shipment confirmed", value=True)
        render_plain_note(
            "Ain does not need to memorize syntax yet. She only needs to notice that text, measured quantities, and yes/no states live in different bins."
        )

    value_types = {
        "supplier_name": type(supplier_name).__name__,
        "coil_weight": type(coil_weight).__name__,
        "shipment_confirmed": type(shipment_confirmed).__name__,
    }
    with chart_column:
        figure = go.Figure()
        figure.add_trace(
            go.Bar(
                x=["supplier_name", "coil_weight", "shipment_confirmed"],
                y=[len(supplier_name), float(coil_weight), 1.0 if shipment_confirmed else 0.0],
                marker_color=[TEXT_COLOR, ACCENT_COLOR, "rgba(30, 41, 59, 0.45)"],
                text=[value_types["supplier_name"], value_types["coil_weight"], value_types["shipment_confirmed"]],
                textposition="outside",
            )
        )
        figure.update_layout(
            template=PLOTLY_TEMPLATE,
            height=360,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Variable bin",
            yaxis_title="Example stored value",
            showlegend=False,
        )
        st.plotly_chart(figure, width="stretch")

    active_python_snippet = render_live_code_panel(
        "Live Code",
        storage_bins_live_code(
            supplier_name=supplier_name,
            coil_weight=float(coil_weight),
            shipment_confirmed=shipment_confirmed,
        ),
        key="storage-bins-live-code",
    )
    render_python_breakdown("How this works in Python", storage_bins_breakdown())

    render_section_heading(
        "Vibe Explanation",
        "This is Ain's first step into Python grammar.",
    )
    st.markdown(
        (
            f"`supplier_name` is stored as **{value_types['supplier_name']}** because it is text, `coil_weight` is a "
            f"**{value_types['coil_weight']}** because it behaves like a measured number, and `shipment_confirmed` is a "
            f"**{value_types['shipment_confirmed']}** because operations often need a clean yes/no decision."
        )
    )

    render_study_notes_panel("storage_bins", gemini_service)
    module_state = {
        "supplier_name": supplier_name,
        "coil_weight": float(coil_weight),
        "shipment_confirmed": shipment_confirmed,
        "value_types": value_types,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("storage_bins", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("storage_bins")


if __name__ == "__main__":
    main()

