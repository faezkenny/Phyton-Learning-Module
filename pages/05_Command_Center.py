from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import command_center_breakdown, command_center_live_code
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

CHART_GUIDES = {
    "Line — quantity over time": {
        "headline": "Trend Story",
        "question": "How does quantity discrepancy move across shipment dates?",
        "why": "Use a line when time is the main actor and Ain wants to read direction, rhythm, and momentum.",
    },
    "Bar — delay by supplier": {
        "headline": "Supplier Comparison",
        "question": "Which suppliers create the highest average delay burden?",
        "why": "Use a bar chart when Ain is comparing categories side by side instead of following a time path.",
    },
    "Scatter — weight vs delay": {
        "headline": "Relationship Finder",
        "question": "Do heavier coils arrive with longer delays, especially during disruption spikes?",
        "why": "Use a scatter plot when Ain wants to see whether two numeric variables move together or form clusters.",
    },
    "Histogram — delay distribution": {
        "headline": "Shape of the Delays",
        "question": "Are most delays small with a few large spikes, or is the whole system broadly unstable?",
        "why": "Use a histogram when Ain cares about distribution shape rather than one-to-one comparisons.",
    },
}


def main() -> None:
    configure_page("NEBULOUS-CORE | The Command Center")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("command_center", gemini_service, kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]
    shipment_frame = dataset_bundle.dataframe.copy()

    bootstrap_app("command_center")
    render_kpis(
        [
            ("Focus", "Plotly", "This stage teaches Ain how to turn tables into clear interactive visuals."),
            ("Factory Role", "Command Center", "Choose the right visual control panel for the logistics question."),
            ("Next Unlock", "Module 6", "Pass this sprint to unlock the Fast Calculator."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("command_center")

    render_section_heading(
        "Chart Recipe Builder",
        "Choose the visual question first, then let Python build the right Plotly figure for that job.",
    )
    controls_col, chart_col = st.columns([0.92, 1.08], gap="large")
    with controls_col:
        chart_type = st.selectbox(
            "Chart type",
            list(CHART_GUIDES),
            key="cc-chart-type",
        )
        color_scheme = st.color_picker("Accent colour", value=ACCENT_COLOR, key="cc-color")
        show_grid = st.toggle("Show gridlines", value=True, key="cc-grid")
        overlay_moving_average = False
        if chart_type.startswith("Line"):
            overlay_moving_average = st.toggle("Overlay 7-day moving average", value=True, key="cc-moving-average")
        guide = CHART_GUIDES[chart_type]
        st.markdown(
            (
                "<div class='info-card'>"
                f"<div class='card-label'>{guide['headline']}</div>"
                f"<div class='card-copy'><strong>Question:</strong> {guide['question']}</div>"
                f"<div class='card-copy' style='margin-top:0.45rem;'>{guide['why']}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        render_plain_note(
            "Think like an analyst, not a decorator. Ain should choose the chart based on the question she wants the thesis graph to answer."
        )

    figure = go.Figure()
    preview_frame = pd.DataFrame()
    chart_story = ""

    if chart_type.startswith("Line"):
        preview_frame = shipment_frame[["shipment_date", "ordered_quantity", "received_quantity", "quantity_discrepancy"]].copy()
        preview_frame["shipment_date"] = pd.to_datetime(preview_frame["shipment_date"], errors="coerce")
        preview_frame = preview_frame.dropna(subset=["shipment_date"]).sort_values("shipment_date")
        preview_frame["seven_day_average"] = preview_frame["quantity_discrepancy"].rolling(window=7, min_periods=1).mean()
        figure = px.line(
            preview_frame,
            x="shipment_date",
            y="quantity_discrepancy",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[color_scheme],
            labels={"shipment_date": "Shipment Date", "quantity_discrepancy": "Quantity Discrepancy"},
        )
        if overlay_moving_average:
            figure.add_scatter(
                x=preview_frame["shipment_date"],
                y=preview_frame["seven_day_average"],
                mode="lines",
                name="7-day moving average",
                line=dict(color=TEXT_COLOR, width=2, dash="dash"),
            )
        chart_story = (
            "The line chart answers a time-series question: it shows when shipment discrepancy rises, falls, or settles into a pattern. "
            "The moving average softens day-to-day noise so Ain can explain the underlying operational drift."
        )
    elif chart_type.startswith("Bar"):
        preview_frame = (
            shipment_frame.groupby("supplier_name", as_index=False)
            .agg(
                average_delay_days=("delay_days", "mean"),
                average_discrepancy=("quantity_discrepancy", "mean"),
                shipment_count=("supplier_name", "size"),
            )
            .sort_values("average_delay_days", ascending=False)
            .head(5)
        )
        figure = px.bar(
            preview_frame,
            x="supplier_name",
            y="average_delay_days",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[color_scheme],
            labels={"supplier_name": "Supplier", "average_delay_days": "Average Delay Days"},
            hover_data={"average_discrepancy": ":.2f", "shipment_count": True},
        )
        figure.update_layout(xaxis_tickangle=-28)
        chart_story = (
            "The bar chart is a ranking view. It helps Ain compare suppliers side by side and quickly spot which partner contributes the largest average delay burden."
        )
    elif chart_type.startswith("Scatter"):
        preview_frame = shipment_frame[
            ["coil_weight_tons", "delay_days", "quantity_discrepancy", "shock_label", "supplier_name"]
        ].dropna()
        figure = px.scatter(
            preview_frame,
            x="coil_weight_tons",
            y="delay_days",
            color="shock_label",
            size="quantity_discrepancy",
            template=PLOTLY_TEMPLATE,
            color_discrete_map={
                "Baseline shipment": color_scheme,
                "War-related outlier": TEXT_COLOR,
            },
            labels={"coil_weight_tons": "Coil Weight (tons)", "delay_days": "Delay Days"},
            hover_data={"supplier_name": True, "quantity_discrepancy": ":.2f"},
        )
        chart_story = (
            "The scatter plot looks for relationship patterns. It lets Ain ask whether heavier coils drift into longer delays and whether war-related outliers form a separate cluster."
        )
    else:
        preview_frame = shipment_frame[["delay_days", "war_disruption_index", "quantity_discrepancy"]].copy()
        figure = px.histogram(
            preview_frame,
            x="delay_days",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[color_scheme],
            labels={"delay_days": "Delay Days"},
            nbins=24,
        )
        chart_story = (
            "The histogram focuses on shape. Ain can see whether delays are concentrated near normal operations or spread out with a heavy right tail caused by disruption spikes."
        )

    if not show_grid:
        figure.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)
    figure.update_layout(height=460, margin=dict(l=20, r=20, t=20, b=20))

    with chart_col:
        st.plotly_chart(figure, width="stretch")
        with st.expander("Data behind this chart"):
            st.dataframe(preview_frame.head(10), width="stretch", hide_index=True)

    active_python_snippet = render_live_code_panel(
        "Live Code",
        command_center_live_code(
            chart_type=chart_type,
            color_scheme=color_scheme,
            show_grid=show_grid,
            overlay_moving_average=overlay_moving_average,
        ),
        key="command-center-live-code",
    )
    render_python_breakdown("How this works in Python", command_center_breakdown(chart_type=chart_type))

    render_section_heading(
        "Mathematical Mapping",
        "Even a chart module should remind Ain what quantity the picture is built from.",
    )
    render_formula(
        r"\text{Quantity Discrepancy}_t = \text{Ordered Quantity}_t - \text{Received Quantity}_t",
        caption="This is the core operational gap that several charts in this module visualize.",
    )
    if chart_type.startswith("Line") and overlay_moving_average:
        render_formula(
            r"\text{7-Day Average}_t = \frac{1}{7}\sum_{i=0}^{6} \text{Quantity Discrepancy}_{t-i}",
            caption="The dashed line smooths local noise so the bigger operational pattern is easier to explain.",
        )

    render_section_heading(
        "Vibe Explanation",
        "This is where Ain learns to justify a chart choice, not just generate one.",
    )
    st.markdown(chart_story)
    render_plain_note(
        "A good thesis figure is really an argument. Ain should be able to say why this chart type was chosen and what decision signal it reveals."
    )

    render_study_notes_panel("command_center", gemini_service)
    module_state = {
        "chart_type": chart_type,
        "color_scheme": color_scheme,
        "show_grid": show_grid,
        "overlay_moving_average": overlay_moving_average,
        "dataset_source": dataset_bundle.source_label,
        "chart_story": chart_story,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("command_center", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("command_center")


if __name__ == "__main__":
    main()
