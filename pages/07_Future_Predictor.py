from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from statsmodels.tsa.arima.model import ARIMA

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import forecast_breakdown, forecast_live_code
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
    sync_sources_if_needed,
)


def _fit_arima(series: pd.Series):
    candidate_orders = [(1, 1, 1), (2, 1, 1), (1, 0, 1), (1, 0, 0)]
    for order in candidate_orders:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fitted = ARIMA(series, order=order).fit()
            return fitted, order
        except Exception:
            continue
    raise ValueError("ARIMA could not fit the available discrepancy series.")


def main() -> None:
    configure_page("NEBULOUS-CORE | Future Predictor")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)
    enforce_unlock("future_predictor")

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sync_sources_if_needed(gemini_service)
    sidebar_payload = render_sidebar("future_predictor", gemini_service, kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]
    shipment_frame = dataset_bundle.dataframe.copy()

    bootstrap_app("future_predictor")
    render_kpis(
        [
            ("Data Source", dataset_bundle.source_label, "The history feeding the ARIMA forecast."),
            ("Observations", str(len(shipment_frame)), "Number of daily shipment points available to the model."),
            ("Certification", st.session_state["progress"]["certification_level"], "Your current end-of-course status."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("future_predictor")

    render_section_heading(
        "Interactive Demo",
        "Adjust the disruption scenario to see how quantity discrepancy could evolve over the forecast horizon.",
    )
    controls_column, chart_column = st.columns([0.92, 1.35], gap="large")
    with controls_column:
        forecast_horizon = st.slider("Forecast horizon (days)", min_value=7, max_value=30, value=14, step=1)
        discrepancy_multiplier = st.slider("Quantity discrepancy multiplier", min_value=0.8, max_value=1.6, value=1.1, step=0.05)
        delay_multiplier = st.slider("Delay stress multiplier", min_value=0.8, max_value=1.8, value=1.15, step=0.05)
        render_plain_note(
            "Scenario sliders alter the discrepancy signal the ARIMA model sees. Higher values simulate more severe mismatch between orders and receipts."
        )

    scenario_series = (
        shipment_frame["quantity_discrepancy"] * discrepancy_multiplier
        + shipment_frame["delay_days"] * (delay_multiplier - 1.0) * 3.0
    )
    scenario_series.index = shipment_frame["shipment_date"]
    arima_result, selected_order = _fit_arima(scenario_series)
    forecast_result = arima_result.get_forecast(steps=forecast_horizon)
    confidence_interval = forecast_result.conf_int()
    lower_band = confidence_interval.iloc[:, 0]
    upper_band = confidence_interval.iloc[:, 1]
    forecast_mean = forecast_result.predicted_mean
    forecast_index = pd.date_range(
        start=shipment_frame["shipment_date"].max() + pd.Timedelta(days=1),
        periods=forecast_horizon,
        freq="D",
    )
    forecast_mean.index = forecast_index
    lower_band.index = forecast_index
    upper_band.index = forecast_index

    with chart_column:
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=shipment_frame["shipment_date"],
                y=shipment_frame["quantity_discrepancy"],
                mode="lines",
                line=dict(color=TEXT_COLOR, width=2),
                name="Observed discrepancy",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=shipment_frame["shipment_date"],
                y=scenario_series,
                mode="lines",
                line=dict(color="rgba(249, 115, 22, 0.45)", width=2, dash="dot"),
                name="Scenario-adjusted signal",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=forecast_index,
                y=upper_band,
                mode="lines",
                line=dict(color="rgba(249, 115, 22, 0.0)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
        figure.add_trace(
            go.Scatter(
                x=forecast_index,
                y=lower_band,
                mode="lines",
                fill="tonexty",
                fillcolor="rgba(249, 115, 22, 0.16)",
                line=dict(color="rgba(249, 115, 22, 0.0)"),
                name="Forecast confidence cloud",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=forecast_index,
                y=forecast_mean,
                mode="lines+markers",
                line=dict(color=ACCENT_COLOR, width=4),
                marker=dict(size=6),
                name="ARIMA forecast",
            )
        )
        figure.update_layout(
            template=PLOTLY_TEMPLATE,
            height=470,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Shipment date",
            yaxis_title="Quantity discrepancy",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0),
        )
        st.plotly_chart(figure, width="stretch")

    active_python_snippet = render_live_code_panel(
        "Live Code",
        forecast_live_code(
            forecast_horizon=forecast_horizon,
            discrepancy_multiplier=discrepancy_multiplier,
            delay_multiplier=delay_multiplier,
            selected_order=selected_order,
            final_forecast_mean=float(forecast_mean.iloc[-1]),
        ),
        key="forecast-live-code",
    )
    render_python_breakdown(
        "How this works in Python",
        forecast_breakdown(source_label=dataset_bundle.source_label),
    )

    render_section_heading(
        "Mathematical Visualization",
        "The model notation and the confidence cloud explain what part is structural and what part is still uncertain.",
    )
    render_formula(
        r"\phi(B)(1-B)^d y_t = c + \theta(B)\epsilon_t",
        caption="ARIMA uses autoregressive structure, differencing, and moving-average shocks to model discrepancy over time.",
    )
    render_plain_note(
        f"Selected order: ARIMA{selected_order}. Final-day mean forecast: {forecast_mean.iloc[-1]:.2f} quantity units."
    )

    render_section_heading(
        "Vibe Explanation",
        "Translate the forecast line into a logistics narrative Ain can defend in a thesis meeting.",
    )
    st.markdown(
        (
            f"With the discrepancy multiplier at **{discrepancy_multiplier:.2f}** and delay stress at **{delay_multiplier:.2f}**, the model sees a stronger "
            f"mismatch between ordered and received coil volume. The orange forecast line shows the expected path, while the confidence cloud reminds Ain that "
            f"future disruptions still carry uncertainty even when the direction of risk is becoming clearer."
        )
    )

    render_study_notes_panel("future_predictor", gemini_service)
    module_state = {
        "forecast_horizon_days": forecast_horizon,
        "discrepancy_multiplier": round(discrepancy_multiplier, 2),
        "delay_multiplier": round(delay_multiplier, 2),
        "selected_arima_order": selected_order,
        "latest_quantity_discrepancy": round(float(shipment_frame["quantity_discrepancy"].iloc[-1]), 2),
        "final_forecast_mean": round(float(forecast_mean.iloc[-1]), 2),
        "dataset_source": dataset_bundle.source_label,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("future_predictor", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("future_predictor")


if __name__ == "__main__":
    main()
