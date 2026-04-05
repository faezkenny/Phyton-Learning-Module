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
            "Steel coils move from Indonesian mills to buyers across Asia and the Middle East. "
            "When port congestion spikes and discrepancy turns severe, the fuzzy engine flags the shipment Critical Risk. "
            "This is the same rule structure Ain runs in her thesis."
        ),
        "rule": "If Port Congestion is HIGH and Quantity Discrepancy is SEVERE → Risk Level is CRITICAL",
        "robust_note": (
            "The Huber Regressor estimates the realistic arrival window after fuzzy classification. "
            "It ignores war-spike days (disruption index > 0.8) so one bad week does not pull the whole forecast off course."
        ),
    },
    "📈 Stock Market Sentiment": {
        "industry": "Bursa Malaysia / Global Tech",
        "thesis_link": "Benchmark",
        "fuzzy_inputs": ["Bullish/Bearish Sentiment", "Volume Trend"],
        "fuzzy_output": "Next-day direction confidence",
        "description": (
            "Traders do not know if tomorrow is bullish — they know the vibe. "
            "FTS captures that vagueness better than a hard threshold like 'if price > X, buy.' "
            "The same membership curve that maps delay days to risk can map market sentiment to direction confidence."
        ),
        "rule": "If Sentiment is BULLISH and Volume is HIGH → Direction Confidence is STRONG UP",
        "robust_note": (
            "Flash crashes and Covid months act like war-spike outliers. "
            "A Robust Regressor downweights those months so the baseline trend is not driven by one panic quarter."
        ),
    },
    "🏭 Automotive Demand Forecasting": {
        "industry": "Perodua-style Raw Material Buffer",
        "thesis_link": "Benchmark",
        "fuzzy_inputs": ["Market Demand Signal", "Lead Time Variability"],
        "fuzzy_output": "Buffer Stock Target",
        "description": (
            "Automotive plants must lock in buffer stock weeks before demand confirms. "
            "FTS turns soft signals like 'low demand' into a concrete safety stock number "
            "without waiting for a confirmed sales figure."
        ),
        "rule": "If Demand is LOW and Lead Time is HIGH → Buffer Stock is CONSERVATIVE INCREASE",
        "robust_note": (
            "Chip shortages and model launches punch anomalous quarters into the data. "
            "The Robust Regressor keeps the baseline forecast stable outside those spikes."
        ),
    },
    "🌦️ Weather & Port Operations": {
        "industry": "Port Environmental Risk",
        "thesis_link": "Benchmark",
        "fuzzy_inputs": ["Temperature Band", "Sea State"],
        "fuzzy_output": "Loading Window Risk",
        "description": (
            "Port crane operators already think in 'moderate sea state' — not wave height in centimetres. "
            "FTS borrows that vocabulary directly so the rule reads the same way the operator thinks it."
        ),
        "rule": "If Temperature is HOT and Sea State is MODERATE → Loading Window Risk is ELEVATED",
        "robust_note": (
            "Typhoon months push extreme readings into the historical data. "
            "The Huber Regressor keeps the baseline loading rate accurate outside typhoon season."
        ),
    },
}

VIVA_PROS = [
    ("The rules are readable", "Ain can show her examiners the exact logic: if congestion is High and discrepancy is Severe, the model flags Critical Risk. Standard regression cannot do that — it just returns a number with no explanation of why."),
    ("It bends where others snap", "Standard regression breaks during a shipping war because those spike magnitudes were never in the training data. FTS handles the vague, overlapping categories the war created — it was built for exactly this kind of mess."),
    ("It borrows the expert's vocabulary", "Port operators already say 'moderate sea state.' Automotive planners already say 'low demand.' FTS uses those words directly instead of forcing a translation between intuition and threshold numbers."),
]

VIVA_CONS = [
    ("The data has to be clean first", "FTS needs at least 60–90 days of consistent records. Missing delay_days rows shift the membership curves incorrectly. The Warehouse Manager module (Module 4) is the fix for this problem before FTS enters."),
    ("Centroid defuzzification is not free", "Summing over the whole output universe for every prediction costs compute time. It is fast enough on normal hardware, but worth naming clearly when Ain defends why a Ryzen 3080 Ti rig was used for batch processing the historical dataset."),
    ("The membership boundaries need defending", "Changing the triangle vertices a, b, c changes every classification result. Ain must justify those choices in the Methodology chapter — not just state that they felt right."),
]


def _render_centroid_explorer() -> float:
    """Interactive defuzzification centroid visualiser. Returns the selected centroid x*."""
    st.markdown(
        "<div class='info-card'>"
        "<div class='card-label'>Sprint Exercise — Place the Centroid</div>"
        "<div class='card-copy'>"
        "Scenario: Steel prices are <strong>Bullish</strong> but Shipping Lead Time is <strong>High.</strong> "
        "Two conflicting fuzzy rules activate at the same time. "
        "Drag the slider to where you think the defuzzified output should land."
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
        "Where is the balance point? (x*)",
        min_value=0.0,
        max_value=10.0,
        value=5.5,
        step=0.1,
        key="vault-centroid",
        help="Think centre of mass — not the tallest peak, but where the whole shaded area would balance on a fulcrum.",
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
        st.success(f"✅ Right. x* = {user_centroid:.1f} — true centroid is {true_centroid:.2f}. That is the centre-of-mass intuition working correctly.")
    elif error <= 1.5:
        st.info(f"Close — you placed {user_centroid:.1f}, true centroid is {true_centroid:.2f}. The whole shaded area needs to balance, not just the tallest peak.")
    else:
        st.warning(f"Off by {error:.1f} units. The true centroid is {true_centroid:.2f}. Look at the full shaded region and find where a fulcrum would hold it level.")

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
        "Same fuzzy rule structure, four different industries. Pick one and read the logic card.",
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
            "Move the sliders to see how the fuzzy engine classifies the shipment in real time.",
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
        "Four Industries, One Rule Structure",
        "Ain can use this table in her thesis to show FTS is not a logistics trick — it is a language for vague decisions.",
    )
    table_md = (
        "| Application | Fuzzy Input | Goal |\n"
        "|:---|:---|:---|\n"
        "| **Steel Coil Shipping** | Port Congestion / Quantity Discrepancy | Flag Critical Risk shipments |\n"
        "| **Stock Market** | Bullish / Bearish Sentiment | Read the direction vibe of Bursa Malaysia or global tech |\n"
        "| **Automotive Demand** | Low / Medium / High Market Signal | Set buffer stock before demand confirms |\n"
        "| **Weather & Port Ops** | Temperature Band / Sea State | Score the loading window risk before cranes move |\n"
    )
    st.markdown(table_md)

    # ── Centroid Explorer ────────────────────────────────────────────────────
    render_section_heading(
        "Place the Centroid",
        "Two conflicting rules activate at the same time. See where Ain's instinct lands versus the actual centre of mass.",
    )
    user_centroid = _render_centroid_explorer()
    render_formula(
        r"x^* = \frac{\int \mu_A(x) \cdot x \, dx}{\int \mu_A(x) \, dx}",
        caption="The centroid (centre of mass) of the aggregated membership area is the defuzzified crisp output.",
    )

    # ── Viva Defense Corner ───────────────────────────────────────────────────
    render_section_heading(
        "Thesis Defense Corner",
        "Three wins and three watch-outs. Ain's examiners will probe both sides.",
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
        "Knowing the limits is not a weakness in the Viva — it is proof that Ain understands the model deeply enough to deploy it safely."
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
