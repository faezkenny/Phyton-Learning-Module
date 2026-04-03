from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import skfuzzy as fuzz
import streamlit as st

from services.config import PLOTLY_TEMPLATE, TEXT_COLOR, ACCENT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import fuzzy_breakdown, fuzzy_live_code
from services.storage import initialize_session_state
from services.ui import (
    bootstrap_app,
    configure_page,
    handle_tutor_interaction,
    inject_styles,
    render_formula,
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


def _build_fuzzy_curves(a: float, b: float, c: float, uncertainty_width: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    universe = np.linspace(0.0, max(14.0, c + 2.0), 500)
    base_curve = fuzz.trimf(universe, [a, b, c])
    upper_curve = fuzz.trimf(universe, [max(0.0, a - uncertainty_width), b, c + uncertainty_width])
    lower_left = max(0.0, min(b - 0.1, a + uncertainty_width * 0.45))
    lower_right = max(b + 0.1, c - uncertainty_width * 0.45)
    lower_curve = fuzz.trimf(universe, [lower_left, b, lower_right])
    return universe, base_curve, lower_curve, upper_curve


def main() -> None:
    configure_page("NEBULOUS-CORE | Intuition Engine")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("intuition_engine", gemini_service, kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]

    bootstrap_app("intuition_engine")
    render_kpis(
        [
            ("Data Source", dataset_bundle.source_label, "The shipment feed currently anchoring your examples."),
            ("Certification", st.session_state["progress"]["certification_level"], "Your current learning sprint rank."),
            ("Next Unlock", "Module 6", "Pass this sprint to unlock the quality inspector."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("intuition_engine")

    render_section_heading(
        "Interactive Demo",
        "Define what 'critical delay' means by shaping the triangular membership function with slider controls.",
    )
    controls_column, chart_column = st.columns([0.95, 1.35], gap="large")
    with controls_column:
        a = st.slider("Left foot a", min_value=0.0, max_value=8.0, value=1.5, step=0.1)
        b = st.slider("Peak b", min_value=max(0.2, a + 0.1), max_value=11.0, value=max(3.8, a + 0.1), step=0.1)
        c = st.slider("Right foot c", min_value=b + 0.1, max_value=14.0, value=max(b + 2.8, 7.8), step=0.1)
        current_delay_days = st.slider("Observed delay days", min_value=0.0, max_value=14.0, value=4.8, step=0.1)
        uncertainty_width = st.slider("Confidence cloud width", min_value=0.0, max_value=3.0, value=0.9, step=0.1)
        linguistic_label = st.text_input("Linguistic label", value="Critical Delay")
        render_plain_note(
            "Interpretation tip: a says when the concept begins, b is the strongest truth point, and c marks when the concept fades out."
        )

    universe, base_curve, lower_curve, upper_curve = _build_fuzzy_curves(a, b, c, uncertainty_width)
    membership_grade = float(fuzz.interp_membership(universe, base_curve, current_delay_days))
    with chart_column:
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=universe,
                y=upper_curve,
                mode="lines",
                line=dict(color="rgba(249, 115, 22, 0.0)", width=0),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        figure.add_trace(
            go.Scatter(
                x=universe,
                y=lower_curve,
                mode="lines",
                fill="tonexty",
                fillcolor="rgba(249, 115, 22, 0.18)",
                line=dict(color="rgba(249, 115, 22, 0.0)", width=0),
                name="Fuzzy confidence cloud",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=universe,
                y=base_curve,
                mode="lines",
                line=dict(color=ACCENT_COLOR, width=4),
                name=linguistic_label,
            )
        )
        figure.add_trace(
            go.Scatter(
                x=[current_delay_days],
                y=[membership_grade],
                mode="markers",
                marker=dict(size=12, color=TEXT_COLOR),
                name="Observed shipment",
            )
        )
        figure.add_vline(x=current_delay_days, line_dash="dash", line_color=TEXT_COLOR, opacity=0.5)
        figure.update_layout(
            template=PLOTLY_TEMPLATE,
            height=480,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Delay days",
            yaxis_title="Membership grade",
            yaxis_range=[0, 1.05],
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
        )
        st.plotly_chart(figure, width="stretch")

    active_python_snippet = render_live_code_panel(
        "Live Code",
        fuzzy_live_code(
            a=a,
            b=b,
            c=c,
            current_delay_days=current_delay_days,
            uncertainty_width=uncertainty_width,
            linguistic_label=linguistic_label,
            membership_grade=membership_grade,
        ),
        key="fuzzy-live-code",
    )
    render_python_breakdown(
        "How this works in Python",
        fuzzy_breakdown(source_label=dataset_bundle.source_label, linguistic_label=linguistic_label),
    )

    render_section_heading(
        "Mathematical Visualization",
        "See the symbolic rule next to the chart so the sliders map directly to the fuzzy math.",
    )
    render_formula(
        r"\mu_A(x) = \max\left(0, \min\left(\frac{x-a}{b-a}, \frac{c-x}{c-b}\right)\right)",
        caption="Triangular membership function for the active logistics label.",
    )
    st.markdown(
        (
            "<div class='info-card'>"
            f"<div class='card-label'>Current membership grade</div>"
            f"<div class='card-value'>{membership_grade:.3f}</div>"
            f"<div class='card-copy'>{linguistic_label} for a shipment delayed by {current_delay_days:.1f} days.</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    render_section_heading(
        "Vibe Explanation",
        "Use the plain-language intuition to connect the symbolic math to a real shipment conversation.",
    )
    st.markdown(
        (
            f"When Ain calls this scenario **{linguistic_label}**, she is really saying that delays near **{b:.1f} days** feel most representative "
            f"of the concept. The observed shipment at **{current_delay_days:.1f} days** currently belongs to that concept with a truth grade of "
            f"**{membership_grade:.3f}**. Widening the confidence cloud means the team is less certain about where the boundary of '{linguistic_label}' truly sits."
        )
    )

    render_study_notes_panel("intuition_engine", gemini_service)
    module_state = {
        "linguistic_label": linguistic_label,
        "a": round(a, 2),
        "b": round(b, 2),
        "c": round(c, 2),
        "current_delay_days": round(current_delay_days, 2),
        "uncertainty_width": round(uncertainty_width, 2),
        "membership_grade": round(membership_grade, 3),
        "dataset_source": dataset_bundle.source_label,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("intuition_engine", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("intuition_engine")


if __name__ == "__main__":
    main()
