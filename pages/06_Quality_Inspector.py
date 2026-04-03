from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import statsmodels.api as sm
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.kimi_tutor import KimiTutorService
from services.python_learning import robust_breakdown, robust_live_code
from services.storage import initialize_session_state
from services.ui import (
    bootstrap_app,
    configure_page,
    enforce_unlock,
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


def main() -> None:
    configure_page("NEBULOUS-CORE | Quality Inspector")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)
    enforce_unlock("quality_inspector")

    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("quality_inspector", kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]
    shipment_frame = dataset_bundle.dataframe.copy()

    bootstrap_app("quality_inspector")
    render_kpis(
        [
            ("Data Source", dataset_bundle.source_label, "This dataset feeds both OLS and robust fitting."),
            ("Detected Shock Days", str(int((shipment_frame["war_disruption_index"] > 0.8).sum())), "High-disruption shipment days in the visible sample."),
            ("Next Unlock", "Module 7", "Pass this sprint to unlock the future predictor."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("quality_inspector")

    render_section_heading(
        "Interactive Demo",
        "Switch robust mode on to see how Huber loss reduces the influence of war-related outliers.",
    )
    control_column, chart_column = st.columns([0.92, 1.35], gap="large")
    with control_column:
        engage_robust_mode = st.toggle("Engage Robust Mode", value=True)
        huber_threshold = st.slider("Huber threshold", min_value=1.0, max_value=3.0, value=1.35, step=0.05)
        render_plain_note(
            "A smaller Huber threshold makes the model skeptical of large residuals sooner, which usually lowers outlier influence faster."
        )

    x_index = np.arange(len(shipment_frame), dtype=float)
    design_matrix = sm.add_constant(
        np.column_stack([x_index, shipment_frame["war_disruption_index"].to_numpy(dtype=float)])
    )
    target = shipment_frame["received_quantity"].to_numpy(dtype=float)

    ols_result = sm.OLS(target, design_matrix).fit()
    robust_result = sm.RLM(target, design_matrix, M=sm.robust.norms.HuberT(t=huber_threshold)).fit()
    shipment_frame["ols_prediction"] = ols_result.predict(design_matrix)
    shipment_frame["robust_prediction"] = robust_result.predict(design_matrix)
    shipment_frame["robust_outlier_weight"] = robust_result.weights

    with chart_column:
        figure = go.Figure()
        baseline_mask = shipment_frame["shock_label"] == "Baseline shipment"
        shock_mask = ~baseline_mask
        figure.add_trace(
            go.Scatter(
                x=shipment_frame.loc[baseline_mask, "shipment_date"],
                y=shipment_frame.loc[baseline_mask, "received_quantity"],
                mode="markers",
                marker=dict(size=8, color="rgba(30, 41, 59, 0.58)"),
                name="Baseline shipment",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=shipment_frame.loc[shock_mask, "shipment_date"],
                y=shipment_frame.loc[shock_mask, "received_quantity"],
                mode="markers",
                marker=dict(size=11, color="rgba(249, 115, 22, 0.95)", symbol="diamond"),
                name="War-related outlier",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=shipment_frame["shipment_date"],
                y=shipment_frame["ols_prediction"],
                mode="lines",
                line=dict(color="rgba(30, 41, 59, 0.7)", width=2 if not engage_robust_mode else 1, dash="dash"),
                name="OLS fit",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=shipment_frame["shipment_date"],
                y=shipment_frame["robust_prediction"],
                mode="lines",
                line=dict(color=ACCENT_COLOR, width=4 if engage_robust_mode else 2),
                opacity=1.0 if engage_robust_mode else 0.45,
                name="Huber robust fit",
            )
        )
        figure.update_layout(
            template=PLOTLY_TEMPLATE,
            height=470,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Shipment date",
            yaxis_title="Received quantity",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
        )
        st.plotly_chart(figure, width="stretch")

    average_shock_weight = float(shipment_frame.loc[shock_mask, "robust_outlier_weight"].mean())
    active_python_snippet = render_live_code_panel(
        "Live Code",
        robust_live_code(
            huber_threshold=huber_threshold,
            engage_robust_mode=engage_robust_mode,
            average_shock_weight=average_shock_weight,
        ),
        key="robust-live-code",
    )
    render_python_breakdown(
        "How this works in Python",
        robust_breakdown(source_label=dataset_bundle.source_label),
    )

    render_section_heading(
        "Mathematical Visualization",
        "The weight map shows which observations the robust model trusts less when the shock spikes appear.",
    )
    render_formula(
        r"L_\delta(r) = \begin{cases}\frac{1}{2}r^2,& |r| \le \delta \\ \delta(|r|-\frac{1}{2}\delta),& |r|>\delta \end{cases}",
        caption="Huber loss behaves quadratically near zero and more linearly on extreme residuals.",
    )
    weight_figure = go.Figure()
    weight_figure.add_trace(
        go.Bar(
            x=shipment_frame["shipment_date"],
            y=shipment_frame["robust_outlier_weight"],
            marker_color=np.where(
                shipment_frame["war_disruption_index"] > 0.8,
                "rgba(249, 115, 22, 0.9)",
                "rgba(30, 41, 59, 0.7)",
            ),
            name="robust_outlier_weight",
        )
    )
    weight_figure.update_layout(
        template=PLOTLY_TEMPLATE,
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Shipment date",
        yaxis_title="Robust outlier weight",
        yaxis_range=[0, 1.05],
    )
    st.plotly_chart(weight_figure, width="stretch")

    active_model_label = "Huber robust fit" if engage_robust_mode else "OLS baseline fit"
    render_section_heading(
        "Vibe Explanation",
        "This is the business intuition behind the model switch.",
    )
    st.markdown(
        (
            f"Right now the dashboard is emphasizing **{active_model_label}**. The war-spike days have an average "
            f"`robust_outlier_weight` of **{average_shock_weight:.3f}**, which means the robust model is telling us those days are "
            f"real events worth noticing, but not events that should hijack the long-run shipment trend."
        )
    )

    render_study_notes_panel("quality_inspector", None)
    module_state = {
        "engage_robust_mode": engage_robust_mode,
        "huber_threshold": round(huber_threshold, 2),
        "average_robust_outlier_weight": round(average_shock_weight, 3),
        "ols_time_slope": round(float(ols_result.params[1]), 3),
        "robust_time_slope": round(float(robust_result.params[1]), 3),
        "dataset_source": dataset_bundle.source_label,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("quality_inspector", module_state, sidebar_payload, None, kimi_service)
    render_last_tutor_response()
    render_quiz("quality_inspector")


if __name__ == "__main__":
    main()
