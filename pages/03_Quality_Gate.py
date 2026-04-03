from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import quality_gate_breakdown, quality_gate_live_code
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


def trigger_safety_stock(delay_days: int, threshold_days: int) -> bool:
    return delay_days > threshold_days


def main() -> None:
    configure_page("NEBULOUS-CORE | Quality Gate")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("quality_gate", gemini_service, kimi_service)

    bootstrap_app("quality_gate")
    render_kpis(
        [
            ("Focus", "Logic & Functions", "This lesson teaches Python to make a simple logistics decision."),
            ("Factory Analogy", "Quality Gate", "If a shipment fails the rule, the gate triggers an alert."),
            ("Next Unlock", "Module 4", "Pass this quiz to unlock Pandas warehouse work."),
        ]
    )
    render_what_you_will_learn("quality_gate")

    render_section_heading(
        "Use a delay slider and a threshold to see how `if/else` logic and a function create a repeatable SOP.",
    )
    controls_column, preview_column = st.columns([0.9, 1.1], gap="large")
    with controls_column:
        delay_days = st.slider("Delay days", min_value=0, max_value=15, value=6, step=1)
        threshold_days = st.slider("Safety stock threshold", min_value=1, max_value=10, value=5, step=1)
        safety_stock_alert = trigger_safety_stock(delay_days, threshold_days)
        render_plain_note(
            "This is the first point where Ain writes a rule instead of just storing information. That is why functions matter."
        )

    with preview_column:
        figure = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=delay_days,
                title={"text": "Delay days"},
                gauge={
                    "axis": {"range": [0, 15]},
                    "bar": {"color": ACCENT_COLOR if safety_stock_alert else TEXT_COLOR},
                    "steps": [
                        {"range": [0, threshold_days], "color": "rgba(30, 41, 59, 0.12)"},
                        {"range": [threshold_days, 15], "color": "rgba(249, 115, 22, 0.18)"},
                    ],
                    "threshold": {"line": {"color": ACCENT_COLOR, "width": 4}, "value": threshold_days},
                },
            )
        )
        figure.update_layout(template=PLOTLY_TEMPLATE, height=340, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(figure, width="stretch")
        if safety_stock_alert:
            st.error("Safety Stock Alert: delay days passed the threshold.")
        else:
            st.success("Shipment is still inside the safe operating threshold.")

    active_python_snippet = render_live_code_panel(
        "Live Code",
        quality_gate_live_code(
            delay_days=delay_days,
            threshold_days=threshold_days,
            safety_stock_alert=safety_stock_alert,
        ),
        key="quality-gate-live-code",
    )
    render_python_breakdown("How this works in Python", quality_gate_breakdown())

    render_section_heading("Vibe Explanation", "This is Ain's first decision engine.")
    st.markdown(
        (
            f"Right now the rule says: if `delay_days` is greater than **{threshold_days}**, trigger a safety stock alert. "
            f"With the slider at **{delay_days}**, the function returns **{safety_stock_alert}**."
        )
    )

    render_study_notes_panel("quality_gate", gemini_service)
    module_state = {
        "delay_days": delay_days,
        "threshold_days": threshold_days,
        "safety_stock_alert": safety_stock_alert,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("quality_gate", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("quality_gate")


if __name__ == "__main__":
    main()

