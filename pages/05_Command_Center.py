from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.data import load_shipment_dataset
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.storage import initialize_session_state
from services.ui import (
    bootstrap_app,
    configure_page,
    handle_tutor_interaction,
    inject_styles,
    render_kpis,
    render_last_tutor_response,
    render_plain_note,
    render_quiz,
    render_section_heading,
    render_sidebar,
    render_study_notes_panel,
    render_what_you_will_learn,
)


def main() -> None:
    configure_page("NEBULOUS-CORE | The Command Center")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("command_center", gemini_service, kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]
    df = dataset_bundle.dataframe

    bootstrap_app("command_center")
    render_kpis(
        [
            ("Data Source", dataset_bundle.source_label, "The shipment feed powering your charts."),
            ("Certification", st.session_state["progress"]["certification_level"], "Your current learning sprint rank."),
            ("Next Unlock", "Module 6", "Pass this sprint to unlock the Fast Calculator."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("command_center")

    render_section_heading(
        "Chart Type Explorer",
        "Choose a chart type and configure its axes. Watch how the Plotly Python call changes as you adjust the controls.",
    )

    controls_col, chart_col = st.columns([0.9, 1.4], gap="large")
    with controls_col:
        chart_type = st.selectbox(
            "Chart type",
            ["Line — quantity over time", "Bar — delay by supplier", "Scatter — weight vs delay", "Histogram — delay distribution"],
            key="cc-chart-type",
        )
        color_scheme = st.color_picker("Accent colour", value="#F97316", key="cc-color")
        show_grid = st.toggle("Show gridlines", value=True, key="cc-grid")
        render_plain_note(
            "Plotly Express (px) is the fast-lane chart builder. Plotly Graph Objects (go) gives you full control over every single layer."
        )

    fig = go.Figure()
    live_code = ""

    if df is not None and not df.empty:
        import pandas as pd  # noqa: PLC0415

        if "Line" in chart_type and "shipment_date" in df.columns and "quantity_discrepancy" in df.columns:
            ts = df.dropna(subset=["shipment_date", "quantity_discrepancy"]).copy()
            ts["shipment_date"] = pd.to_datetime(ts["shipment_date"], errors="coerce")
            ts = ts.sort_values("shipment_date")
            fig = px.line(
                ts,
                x="shipment_date",
                y="quantity_discrepancy",
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=[color_scheme],
                labels={"shipment_date": "Shipment Date", "quantity_discrepancy": "Quantity Discrepancy"},
            )
            live_code = (
                'import plotly.express as px\n'
                'fig = px.line(\n'
                '    df,\n'
                '    x="shipment_date",\n'
                '    y="quantity_discrepancy",\n'
                f'    color_discrete_sequence=["{color_scheme}"],\n'
                ')\n'
                'fig.show()'
            )

        elif "Bar" in chart_type and "supplier_name" in df.columns and "delay_days" in df.columns:
            bar_data = df.groupby("supplier_name", as_index=False)["delay_days"].mean().nlargest(10, "delay_days")
            fig = px.bar(
                bar_data,
                x="supplier_name",
                y="delay_days",
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=[color_scheme],
                labels={"supplier_name": "Supplier", "delay_days": "Avg Delay Days"},
            )
            fig.update_layout(xaxis_tickangle=-35)
            live_code = (
                'bar_data = df.groupby("supplier_name")["delay_days"].mean().nlargest(10)\n'
                'fig = px.bar(\n'
                '    bar_data.reset_index(),\n'
                '    x="supplier_name",\n'
                '    y="delay_days",\n'
                f'    color_discrete_sequence=["{color_scheme}"],\n'
                ')\n'
                'fig.show()'
            )

        elif "Scatter" in chart_type and "coil_weight_tons" in df.columns and "delay_days" in df.columns:
            scatter_df = df.dropna(subset=["coil_weight_tons", "delay_days"])
            fig = px.scatter(
                scatter_df,
                x="coil_weight_tons",
                y="delay_days",
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=[color_scheme],
                opacity=0.7,
                labels={"coil_weight_tons": "Coil Weight (tons)", "delay_days": "Delay Days"},
            )
            live_code = (
                'fig = px.scatter(\n'
                '    df,\n'
                '    x="coil_weight_tons",\n'
                '    y="delay_days",\n'
                f'    color_discrete_sequence=["{color_scheme}"],\n'
                ')\n'
                'fig.show()'
            )

        else:  # Histogram
            col = "delay_days" if "delay_days" in df.columns else df.select_dtypes("number").columns[0]
            fig = px.histogram(
                df.dropna(subset=[col]),
                x=col,
                template=PLOTLY_TEMPLATE,
                color_discrete_sequence=[color_scheme],
                labels={col: col.replace("_", " ").title()},
                nbins=30,
            )
            live_code = (
                f'fig = px.histogram(df, x="{col}", nbins=30,\n'
                f'    color_discrete_sequence=["{color_scheme}"])\n'
                'fig.show()'
            )

        if not show_grid:
            fig.update_layout(xaxis_showgrid=False, yaxis_showgrid=False)

    else:
        fig.add_annotation(text="No data loaded", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font_size=18)
        live_code = "# Load a shipment CSV first\nimport plotly.express as px\nfig = px.line(df, x='shipment_date', y='quantity_discrepancy')\nfig.show()"

    with chart_col:
        st.plotly_chart(fig, width="stretch")

    render_section_heading("Live Python Code", "This is the exact Plotly call that drew the chart above.")
    st.code(live_code, language="python")

    render_section_heading(
        "How Plotly Works",
        "Plotly separates data from layout so Ain can layer multiple traces on the same axes.",
    )
    st.markdown(
        (
            "<div class='info-card'>"
            "<div class='card-label'>px vs go</div>"
            "<div class='card-copy'><code>plotly.express</code> is the one-liner shortcut — great for standard charts. "
            "<code>plotly.graph_objects</code> is the low-level API that lets you add individual traces, shapes, and annotations with full control.</div>"
            "</div>"
            "<div class='info-card'>"
            "<div class='card-label'>Templates</div>"
            "<div class='card-copy'>The <code>template=</code> argument swaps the entire colour scheme and gridline style. "
            "This dashboard uses <code>plotly_white</code> for a clean, publication-ready look.</div>"
            "</div>"
            "<div class='info-card'>"
            "<div class='card-label'>fig.show() vs st.plotly_chart()</div>"
            "<div class='card-copy'>In a script you call <code>fig.show()</code> to open the browser. "
            "In Streamlit you pass the figure to <code>st.plotly_chart(fig)</code> instead.</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    render_study_notes_panel("command_center", gemini_service)
    module_state = {
        "chart_type": chart_type,
        "color_scheme": color_scheme,
        "dataset_source": dataset_bundle.source_label,
        "live_code": live_code,
    }
    handle_tutor_interaction("command_center", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("command_center")


if __name__ == "__main__":
    main()
