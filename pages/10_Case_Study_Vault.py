from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.storage import initialize_session_state
from services.ui import (
    bootstrap_app,
    configure_page,
    handle_tutor_interaction,
    inject_styles,
    render_formula,
    render_kpis,
    render_last_tutor_response,
    render_plain_note,
    render_quiz,
    render_section_heading,
    render_sidebar,
    render_study_notes_panel,
    render_what_you_will_learn,
)


# ── Case study registry ──────────────────────────────────────────────────────
CASE_STUDIES = {
    "🚢 Global Logistics Oracle": {
        "industry": "Steel Coil Shipping",
        "thesis_link": "Direct",
        "fuzzy_inputs": ["Port Congestion", "Quantity Discrepancy"],
        "fuzzy_output": "Shipment Risk Level",
        "description": (
            "Steel coils are shipped from Indonesian mills to buyers across Asia and the Middle East. "
            "When port congestion spikes and quantity discrepancy turns severe, the Fuzzy model classifies "
            "the shipment as a High Risk Outlier — the same logic Ain uses in her thesis."
        ),
        "rule": "If Port Congestion is HIGH and Quantity Discrepancy is SEVERE → Risk Level is CRITICAL",
        "robust_note": (
            "The Huber Regressor is applied after fuzzy classification to estimate the realistic arrival date window. "
            "It ignores war-spike outliers (disruption index > 0.8) so the prediction is not pulled toward extreme events."
        ),
    },
    "📈 Stock Market Sentiment": {
        "industry": "Bursa Malaysia / Global Tech",
        "thesis_link": "Benchmark",
        "fuzzy_inputs": ["Bullish/Bearish Sentiment", "Volume Trend"],
        "fuzzy_output": "Next-day price direction vibe",
        "description": (
            "Traders do not know whether the next day is bullish or bearish — they know the 'vibe.' "
            "Fuzzy Time Series captures this linguistic uncertainty better than a hard threshold like 'if price > X.'"
        ),
        "rule": "If Sentiment is BULLISH and Volume is HIGH → Direction Confidence is STRONG UP",
        "robust_note": (
            "Black swan events (Covid crash, flash crashes) act like war-spike outliers. A Robust regressor "
            "downweights these so the trend estimate is not driven by a single month of panic."
        ),
    },
    "🏭 Automotive Demand Forecasting": {
        "industry": "Perodua-style Raw Material Buffer",
        "thesis_link": "Benchmark",
        "fuzzy_inputs": ["Market Demand Signal", "Lead Time Variability"],
        "fuzzy_output": "Buffer Stock Recommendation",
        "description": (
            "Automotive manufacturers must decide buffer stock weeks before demand materialises. "
            "FTS translates soft signals like 'low demand' into concrete safety stock targets "
            "without waiting for a confirmed sales number."
        ),
        "rule": "If Demand is LOW and Lead Time is HIGH → Buffer Stock recommendation is CONSERVATIVE INCREASE",
        "robust_note": (
            "Demand shocks (chip shortage, model launches) are treated as outliers. "
            "The Robust regressor keeps the baseline forecast stable even when one quarter is anomalous."
        ),
    },
    "🌦️ Weather & Port Operations": {
        "industry": "Port Environmental Risk",
        "thesis_link": "Benchmark",
        "fuzzy_inputs": ["Temperature Band", "Sea State"],
        "fuzzy_output": "Loading Window Risk",
        "description": (
            "Port crane operations slow or halt based on environmental conditions. "
            "FTS captures 'moderate sea state' linguistically rather than demanding a single threshold "
            "in wave height centimetres — because port operators already think in these terms."
        ),
        "rule": "If Temperature is HOT and Sea State is MODERATE → Loading Window Risk is ELEVATED",
        "robust_note": (
            "Typhoon seasons create extreme readings that skew historical models. "
            "The Huber Regressor keeps the baseline loading rate accurate outside typhoon weeks."
        ),
    },
}

VIVA_PROS = [
    ("Human-Readable Rules", "Unlike deep learning black boxes, Ain can show her professors the exact logic: 'If port congestion is High AND discrepancy is Severe, the model flags Critical Risk.' It is logic the examiners can trace back to first principles."),
    ("Uncertainty Management", "Standard regression breaks during a shipping war because the shock magnitudes were never in the training data. FTS bends — it was designed for vague, overlapping categories where hard thresholds fail."),
    ("Linguistic Grounding", "Domain experts already speak in 'low', 'medium', 'high'. FTS inherits that vocabulary directly instead of forcing a translation between expert intuition and numeric thresholds."),
]

VIVA_CONS = [
    ("Data Quality Requirement", "FTS needs at least 60–90 days of clean, consistently formatted shipment records. If Ain's CSV has missing delay_days rows, the membership curves shift incorrectly."),
    ("Computational Weight for Large Datasets", "Centroid defuzzification sums over the whole output universe for every prediction. For 1,000+ coil rows this is fast on modern hardware, but it is worth noting the Ryzen 3080 Ti rig's advantage when batch-processing historical data."),
    ("Membership Design Sensitivity", "Changing the triangular vertex positions (a, b, c) changes every classification result. Ain must justify her membership boundaries in the Methodology chapter, not just choose them by feel."),
]


def _render_centroid_explorer() -> float:
    """Interactive defuzzification centroid visualiser. Returns the selected centroid x*."""
    st.markdown(
        "<div class='info-card'>"
        "<div class='card-label'>Vibe Coder Exercise — The Market Strategist</div>"
        "<div class='card-copy'>"
        "Scenario: Steel prices are <strong>Bullish</strong> but Shipping Lead Time is <strong>High.</strong> "
        "Move the slider to set where the defuzzified output (the Centroid) should land on the combined fuzzy output curve."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    universe = np.linspace(0, 10, 500)

    # Two conflicting rule output curves
    # Rule A: Bullish → output "optimistic" (peaked around 7.5)
    mu_a = np.maximum(0, 1 - np.abs(universe - 7.5) / 2.5)
    # Rule B: High lead time → output "cautious" (peaked around 3.5)
    mu_b = np.maximum(0, 1 - np.abs(universe - 3.5) / 2.5)
    # Aggregate (union)
    mu_agg = np.maximum(mu_a, mu_b)

    # True centroid
    true_centroid = float(np.sum(universe * mu_agg) / np.sum(mu_agg))

    user_centroid = st.slider(
        "Place the Centroid marker (x*)",
        min_value=0.0,
        max_value=10.0,
        value=5.5,
        step=0.1,
        key="vault-centroid",
        help="Drag until your instinct says the 'centre of mass' of the shaded area is correct.",
    )

    error = abs(user_centroid - true_centroid)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=universe, y=mu_agg, fill="tozeroy",
        fillcolor=f"rgba(249,115,22,0.18)", line=dict(color=ACCENT_COLOR, width=2),
        name="Aggregated fuzzy output",
    ))
    fig.add_vline(x=true_centroid, line_color=TEXT_COLOR, line_dash="dot", line_width=1.5, annotation_text=f"True x* = {true_centroid:.2f}")
    fig.add_vline(x=user_centroid, line_color=ACCENT_COLOR, line_dash="solid", line_width=2.5, annotation_text=f"Your marker = {user_centroid:.1f}")
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=280,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis_title="Output universe (risk index)",
        yaxis_title="μ(x)",
        showlegend=False,
    )
    st.plotly_chart(fig, width="stretch")

    if error <= 0.5:
        st.success(f"✅ Excellent! You placed x* = {user_centroid:.1f} (true centroid = {true_centroid:.2f}). You understand the centre-of-mass intuition.")
    elif error <= 1.5:
        st.info(f"Close — you placed {user_centroid:.1f}, true centroid is {true_centroid:.2f}. Think of it as the balance point of the whole shaded area, not just the tallest peak.")
    else:
        st.warning(f"Your marker ({user_centroid:.1f}) is {error:.1f} units from the true centroid ({true_centroid:.2f}). Look at the full shaded area and find where it would balance on a fulcrum.")

    return user_centroid


def _render_scenario_simulator(dataset_bundle) -> dict:
    """Fuzzy scenario simulator for the anchor logistics case study."""
    import skfuzzy as fuzz  # noqa: PLC0415

    universe = np.linspace(0, 1, 500)

    congestion_level = st.slider("Port Congestion (0 = Clear, 1 = Gridlocked)", 0.0, 1.0, 0.72, 0.01, key="vault-congestion")
    discrepancy_level = st.slider("Quantity Discrepancy (0 = Exact, 1 = Total Loss)", 0.0, 1.0, 0.61, 0.01, key="vault-discrepancy")

    # Membership functions
    mu_low_cong = fuzz.trimf(universe, [0.0, 0.0, 0.45])
    mu_mid_cong = fuzz.trimf(universe, [0.3, 0.5, 0.7])
    mu_high_cong = fuzz.trimf(universe, [0.55, 1.0, 1.0])

    mu_min_disc = fuzz.trimf(universe, [0.0, 0.0, 0.4])
    mu_notic_disc = fuzz.trimf(universe, [0.25, 0.5, 0.75])
    mu_sev_disc = fuzz.trimf(universe, [0.6, 1.0, 1.0])

    cong_high = float(fuzz.interp_membership(universe, mu_high_cong, congestion_level))
    disc_sev = float(fuzz.interp_membership(universe, mu_sev_disc, discrepancy_level))
    cong_mid = float(fuzz.interp_membership(universe, mu_mid_cong, congestion_level))
    disc_notic = float(fuzz.interp_membership(universe, mu_notic_disc, discrepancy_level))
    cong_low = float(fuzz.interp_membership(universe, mu_low_cong, congestion_level))
    disc_min = float(fuzz.interp_membership(universe, mu_min_disc, discrepancy_level))

    rule_critical = min(cong_high, disc_sev)
    rule_elevated = min(cong_mid, disc_notic)
    rule_normal = min(cong_low, disc_min)

    risk_universe = np.linspace(0, 1, 500)
    mu_normal_out = fuzz.trimf(risk_universe, [0.0, 0.0, 0.35])
    mu_elevated_out = fuzz.trimf(risk_universe, [0.2, 0.5, 0.8])
    mu_critical_out = fuzz.trimf(risk_universe, [0.65, 1.0, 1.0])

    aggregated = np.maximum(
        np.maximum(
            np.fmin(rule_normal, mu_normal_out),
            np.fmin(rule_elevated, mu_elevated_out),
        ),
        np.fmin(rule_critical, mu_critical_out),
    )

    centroid = float(np.sum(risk_universe * aggregated) / max(np.sum(aggregated), 1e-9))

    if centroid >= 0.65:
        risk_label, risk_color = "🔴 CRITICAL RISK", "#EF4444"
    elif centroid >= 0.4:
        risk_label, risk_color = "🟡 ELEVATED RISK", "#F59E0B"
    else:
        risk_label, risk_color = "🟢 NORMAL OPERATIONS", "#22C55E"

    col_a, col_b = st.columns(2)
    col_a.metric("Fuzzy Risk Index (x*)", f"{centroid:.3f}")
    col_b.metric("Classification", risk_label)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=risk_universe, y=aggregated, fill="tozeroy",
        fillcolor="rgba(249,115,22,0.15)", line=dict(color=ACCENT_COLOR), name="Aggregated output"))
    fig.add_vline(x=centroid, line_color=risk_color, line_width=2.5, line_dash="solid",
        annotation_text=f"x* = {centroid:.3f}")
    fig.update_layout(template=PLOTLY_TEMPLATE, height=240,
        margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Risk Index Universe", yaxis_title="μ(x)", showlegend=False)
    st.plotly_chart(fig, width="stretch")

    return {
        "congestion_level": congestion_level,
        "discrepancy_level": discrepancy_level,
        "risk_index": round(centroid, 3),
        "risk_label": risk_label,
        "rule_critical_activation": round(rule_critical, 3),
    }


def main() -> None:
    configure_page("NEBULOUS-CORE | The Case Study Vault")
    inject_styles()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("case_study_vault", gemini_service, kimi_service)

    bootstrap_app("case_study_vault")
    render_kpis(
        [
            ("Focus", "Applied FTS", "Where abstract fuzzy logic hits real industrial data."),
            ("Factory Role", "Case Study Vault", "Ain switches from Learning Mode to Consultant Mode."),
            ("Stage", "Thesis Grounding", "These four scenarios anchor the math to real decisions."),
        ]
    )

    render_what_you_will_learn("case_study_vault")

    # ── Case Study Cards ─────────────────────────────────────────────────────
    render_section_heading(
        "The Four Case Studies",
        "Same Fuzzy Time Series logic — four different industries. Ain should be able to explain why the same tool works for all of them.",
    )

    selected_case = st.selectbox(
        "Choose a case study",
        list(CASE_STUDIES.keys()),
        key="vault-case-select",
    )
    case = CASE_STUDIES[selected_case]

    col_info, col_rule = st.columns([1.1, 0.9], gap="large")
    with col_info:
        badges = " ".join(
            f"<span style='background:#F1F5F9;border:1px solid #E2E8F0;border-radius:6px;padding:2px 8px;font-size:0.78rem;margin-right:4px;'>{inp}</span>"
            for inp in case["fuzzy_inputs"]
        )
        st.markdown(
            (
                "<div class='info-card'>"
                f"<div class='card-label'>{case['industry']} — {case['thesis_link']}</div>"
                f"<div class='card-value' style='font-size:1rem;'>{case['description']}</div>"
                f"<div class='card-copy' style='margin-top:0.6rem;'><strong>Fuzzy Inputs:</strong> {badges}</div>"
                f"<div class='card-copy' style='margin-top:0.3rem;'><strong>Output:</strong> {case['fuzzy_output']}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    with col_rule:
        st.markdown(
            (
                "<div class='info-card'>"
                "<div class='card-label'>Fuzzy Rule</div>"
                f"<div class='card-copy' style='font-family:monospace;font-size:0.88rem;line-height:1.55;'>{case['rule']}</div>"
                "</div>"
                "<div class='info-card'>"
                "<div class='card-label'>Robust Regression Role</div>"
                f"<div class='card-copy'>{case['robust_note']}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    # ── Live Simulator (anchor case only) ────────────────────────────────────
    if selected_case.startswith("🚢"):
        render_section_heading(
            "Scenario Simulator",
            "Move the sliders to see how the fuzzy engine classifies your shipment in real time.",
        )
        try:
            sim_state = _render_scenario_simulator(sidebar_payload["dataset_bundle"])
        except ImportError:
            st.info("Install `scikit-fuzzy` to activate the live simulator.")
            sim_state = {}
        render_formula(
            r"\text{Risk Index} = x^* = \frac{\int \mu_{\text{agg}}(x) \cdot x \, dx}{\int \mu_{\text{agg}}(x) \, dx}",
            caption="The centroid defuzzification formula collapses the aggregated membership curve into a single crisp risk score.",
        )
    else:
        sim_state = {}

    # ── Industry Benchmarks Table ────────────────────────────────────────────
    render_section_heading(
        "Multi-Industry Benchmarks at a Glance",
        "Ain can use this table in her thesis to show that FTS is a universal analytical language, not a niche logistics trick.",
    )
    table_md = (
        "| Application | Fuzzy Input | Goal |\n"
        "|:---|:---|:---|\n"
        "| **Steel Coil Shipping** | Port Congestion / Quantity Discrepancy | Flag High Risk Outlier shipments |\n"
        "| **Stock Market** | Bullish / Bearish Sentiment | Predict 'vibe' of Bursa Malaysia or global tech |\n"
        "| **Automotive Demand** | Low / Medium / High Market Signal | Optimise buffer stock for raw materials |\n"
        "| **Weather & Port Ops** | Cold / Moderate / Hot + Sea State | Model uncertainty that affects loading windows |\n"
    )
    st.markdown(table_md)

    # ── Centroid Explorer ────────────────────────────────────────────────────
    render_section_heading(
        "Vibe Coder Exercise — Place the Centroid",
        "Ain must understand defuzzification before she can explain it. Drag the slider; the chart will tell you how accurate your intuition is.",
    )
    user_centroid = _render_centroid_explorer()
    render_formula(
        r"x^* = \frac{\int \mu_A(x) \cdot x \, dx}{\int \mu_A(x) \, dx}",
        caption="The centroid (centre of mass) of the aggregated membership area is the defuzzified crisp output.",
    )

    # ── Viva Defense Corner ───────────────────────────────────────────────────
    render_section_heading(
        "Thesis Defense Corner",
        "Ain's professors will probe these exact points. Master the argument before the Viva.",
    )

    col_pro, col_con = st.columns(2, gap="large")
    with col_pro:
        st.markdown("#### ✅ Why FTS Wins Here")
        for title, explanation in VIVA_PROS:
            st.markdown(
                (
                    "<div class='info-card'>"
                    f"<div class='card-label'>{title}</div>"
                    f"<div class='card-copy'>{explanation}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
    with col_con:
        st.markdown("#### ⚠️ Where We Must Be Careful")
        for title, explanation in VIVA_CONS:
            st.markdown(
                (
                    "<div class='info-card'>"
                    f"<div class='card-label'>{title}</div>"
                    f"<div class='card-copy'>{explanation}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

    render_plain_note(
        "The pro/con table is not a weakness list — it is a sign that Ain understands the model deeply enough to know its limits. That is exactly what examiners want to see."
    )

    render_study_notes_panel("case_study_vault", gemini_service)
    render_quiz("case_study_vault")

    module_state = {
        "selected_case_study": selected_case,
        "user_centroid_estimate": round(user_centroid, 2),
        **sim_state,
    }
    handle_tutor_interaction("case_study_vault", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()


if __name__ == "__main__":
    main()
