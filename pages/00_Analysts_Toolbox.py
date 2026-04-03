from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import skfuzzy as fuzz
import statsmodels.api as sm
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.storage import initialize_session_state
from services.toolbox import TOOLBOX_DEPARTMENTS, heuristic_tool_recommendation
from services.ui import (
    bootstrap_app,
    configure_page,
    enforce_unlock,
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


def _render_department_cards() -> str:
    selected_tool = st.session_state.get("active_toolbox_tool", "pandas")
    card_columns = st.columns(5, gap="medium")
    for column, department in zip(card_columns, TOOLBOX_DEPARTMENTS.values()):
        with column:
            st.markdown(
                (
                    "<div class='tool-card'>"
                    f"<div class='tool-icon'>{department.icon}</div>"
                    f"<div class='card-label'>{department.factory_role}</div>"
                    f"<div class='card-value'>{department.name}</div>"
                    f"<div class='card-copy'>{department.thesis_reason}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            if st.button(f"Test Drive {department.name}", key=f"tool-card-{department.key}", width="stretch"):
                st.session_state["active_toolbox_tool"] = department.key
                selected_tool = department.key
    return selected_tool


def _build_pandas_demo(shipment_frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    messy_frame = shipment_frame.head(5)[["shipment_date", "ordered_quantity", "received_quantity", "delay_days"]].copy()
    messy_frame["shipment_date"] = messy_frame["shipment_date"].dt.strftime(" %Y/%m/%d ")
    messy_frame["ordered_quantity"] = messy_frame["ordered_quantity"].map(lambda value: f" {value:.1f} ")
    messy_frame["received_quantity"] = messy_frame["received_quantity"].map(lambda value: f"{value:.1f} tons")
    messy_frame.loc[messy_frame.index[1], "delay_days"] = None
    messy_frame = pd.concat([messy_frame, messy_frame.iloc[[2]]], ignore_index=True)

    cleaned_frame = messy_frame.copy()
    cleaned_frame["shipment_date"] = pd.to_datetime(cleaned_frame["shipment_date"].str.strip(), format="%Y/%m/%d", errors="coerce")
    cleaned_frame["ordered_quantity"] = pd.to_numeric(cleaned_frame["ordered_quantity"].str.strip(), errors="coerce")
    cleaned_frame["received_quantity"] = pd.to_numeric(
        cleaned_frame["received_quantity"].str.replace(" tons", "", regex=False),
        errors="coerce",
    )
    cleaned_frame["delay_days"] = pd.to_numeric(cleaned_frame["delay_days"], errors="coerce").fillna(0.0)
    cleaned_frame = cleaned_frame.drop_duplicates().sort_values("shipment_date").reset_index(drop=True)
    return messy_frame, cleaned_frame


def _render_active_department_demo(active_tool: str, shipment_frame: pd.DataFrame) -> None:
    department = TOOLBOX_DEPARTMENTS[active_tool]
    render_section_heading(
        f"{department.name} Test Drive",
        f"{department.factory_role} in action. Focus on the job this library performs for Ain's thesis workflow.",
    )
    st.code(department.starter_call, language="python")
    st.caption("Starter call to remember. Ain does not need to memorize the full library, just the right department to call.")

    if active_tool == "pandas":
        messy_frame, cleaned_frame = _build_pandas_demo(shipment_frame)
        left_column, right_column = st.columns(2, gap="large")
        left_column.markdown("**Incoming messy shipment table**")
        left_column.dataframe(messy_frame, width="stretch", hide_index=True)
        right_column.markdown("**Cleaned with Pandas**")
        right_column.dataframe(cleaned_frame, width="stretch", hide_index=True)
        render_plain_note(
            "Pandas is the first call because it takes raw, messy shipment rows and turns them into something the rest of the factory can trust."
        )
        return

    if active_tool == "numpy":
        weight_matrix = shipment_frame["received_quantity"].head(6).to_numpy(dtype=float).reshape(2, 3)
        metric_columns = st.columns(3)
        metric_columns[0].metric("Array mean", f"{weight_matrix.mean():.2f}")
        metric_columns[1].metric("Array std", f"{weight_matrix.std():.2f}")
        metric_columns[2].metric("Total weight", f"{weight_matrix.sum():.2f}")
        st.dataframe(pd.DataFrame(weight_matrix, columns=["Batch A", "Batch B", "Batch C"]), width="stretch")
        render_plain_note(
            "NumPy is the precision engineer because it treats shipment numbers like a fast matrix of values instead of a slow row-by-row calculation."
        )
        return

    if active_tool == "plotly":
        summary_frame = shipment_frame.tail(8)[["shipment_date", "quantity_discrepancy"]].copy()
        left_column, right_column = st.columns([0.85, 1.15], gap="large")
        left_column.markdown("**Static table before the glow-up**")
        left_column.dataframe(summary_frame, width="stretch", hide_index=True)
        figure = px.line(
            summary_frame,
            x="shipment_date",
            y="quantity_discrepancy",
            markers=True,
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[ACCENT_COLOR],
        )
        figure.update_layout(height=330, margin=dict(l=20, r=20, t=20, b=20))
        right_column.markdown("**Interactive Plotly chart after the glow-up**")
        right_column.plotly_chart(figure, width="stretch")
        render_plain_note(
            "Plotly is the command center because it turns a dry table into an explorable chart Ain can show to a supervisor or thesis panel."
        )
        return

    if active_tool == "scikit-fuzzy":
        delay_universe = np.linspace(0, 12, 300)
        arriving_soon_curve = fuzz.trimf(delay_universe, [0, 1.5, 4])
        critical_delay_curve = fuzz.trimf(delay_universe, [3, 6, 10])
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=delay_universe, y=arriving_soon_curve, mode="lines", name="Arriving Soon", line=dict(color=TEXT_COLOR, width=3)))
        figure.add_trace(go.Scatter(x=delay_universe, y=critical_delay_curve, mode="lines", name="Critical Delay", line=dict(color=ACCENT_COLOR, width=4)))
        figure.update_layout(template=PLOTLY_TEMPLATE, height=330, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Delay days", yaxis_title="Membership grade")
        st.plotly_chart(figure, width="stretch")
        render_plain_note(
            "Scikit-Fuzzy is the intuition specialist because it helps Ain turn exact numbers like 4.2 days into human labels like 'arriving soon' or 'critical delay'."
        )
        return

    x_index = np.arange(18, dtype=float)
    observed_series = shipment_frame["received_quantity"].head(18).to_numpy(dtype=float).copy()
    observed_series[-1] += 28
    design_matrix = sm.add_constant(x_index)
    ols_result = sm.OLS(observed_series, design_matrix).fit()
    robust_result = sm.RLM(observed_series, design_matrix, M=sm.robust.norms.HuberT(t=1.35)).fit()
    figure = go.Figure()
    figure.add_trace(go.Scatter(x=x_index, y=observed_series, mode="markers", name="Observed shipments", marker=dict(size=9, color="rgba(30, 41, 59, 0.55)")))
    figure.add_trace(go.Scatter(x=x_index, y=ols_result.predict(design_matrix), mode="lines", name="OLS trend", line=dict(color=TEXT_COLOR, dash="dash")))
    figure.add_trace(go.Scatter(x=x_index, y=robust_result.predict(design_matrix), mode="lines", name="Robust trend", line=dict(color=ACCENT_COLOR, width=4)))
    figure.update_layout(template=PLOTLY_TEMPLATE, height=330, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Shipment sequence", yaxis_title="Received quantity")
    st.plotly_chart(figure, width="stretch")
    render_plain_note(
        "Statsmodels is the quality inspector because it notices the spike but still helps Ain keep the underlying trend steady with robust regression."
    )


def _render_workflow_map() -> None:
    workflow_frame = pd.DataFrame(
        {
            "Department": ["Pandas", "Scikit-Fuzzy", "Statsmodels", "Plotly"],
            "Start": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]),
            "Finish": pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"]),
            "Role": ["Clean Data", "Add Logic", "Check Trends", "Show Results"],
        }
    )
    figure = px.timeline(
        workflow_frame,
        x_start="Start",
        x_end="Finish",
        y="Department",
        color="Department",
        text="Role",
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=["#CBD5E1", "#FDBA74", "#FB923C", "#F97316"],
    )
    figure.update_yaxes(autorange="reversed")
    figure.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
    st.plotly_chart(figure, width="stretch")
    st.caption("NumPy acts like the precision engineer underneath the full workflow, supporting math across each stage.")


def _department_catalog_text() -> str:
    lines = []
    for department in TOOLBOX_DEPARTMENTS.values():
        lines.append(
            f"- {department.name} | {department.factory_role} | Use for: {department.thesis_reason} | Starter call: {department.starter_call}"
        )
    return "\n".join(lines)


def _render_tool_recommender(kimi_service: KimiTutorService) -> dict[str, str] | None:
    st.markdown("### Which Module Do I Need?")
    st.caption("Describe the problem in plain English. Kimi will route Ain to the right department and give one starter call.")
    with st.form("toolbox-recommender-form"):
        problem_text = st.text_input(
            "Example: My coil weights are in a messy Excel file and I need to clean them first.",
            key="toolbox-problem-text",
        )
        submitted = st.form_submit_button("Call the Expert", type="primary")

    if not submitted:
        return st.session_state.get("toolbox_recommendation")

    if kimi_service.available:
        kimi_result = kimi_service.recommend_department(problem_text, _department_catalog_text())
        if kimi_result.get("ok"):
            recommendation = {
                "mode": "kimi",
                "content": kimi_result["content"],
            }
            st.session_state["toolbox_recommendation"] = recommendation
            return recommendation
        st.warning(kimi_result.get("message"))

    heuristic = heuristic_tool_recommendation(problem_text)
    recommendation = {
        "mode": "heuristic",
        "content": (
            f"Department: {heuristic['library']}, {heuristic['factory_role']}\n"
            f"Why: {heuristic['why']}\n"
            f"Call: {heuristic['starter_call']}"
        ),
    }
    st.session_state["toolbox_recommendation"] = recommendation
    return recommendation


def main() -> None:
    configure_page("NEBULOUS-CORE | Analyst Toolbox")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)
    enforce_unlock("toolbox")

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("toolbox", gemini_service, kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]
    shipment_frame = dataset_bundle.dataframe.copy()

    bootstrap_app("toolbox")
    render_kpis(
        [
            ("Departments", "5", "The core libraries Ain will call during her thesis workflow."),
            ("Role", "Practical Reference", "Available after Module 3 as a hands-on tool reference for the later curriculum stages."),
            ("Data Source", dataset_bundle.source_label, "The same dataset can feed the toolbox demos."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("toolbox")

    render_section_heading(
        "Factory Floor",
        "Think of each library as a department in a car factory. Ain only needs to know who to call and when.",
    )
    active_tool = _render_department_cards()
    _render_active_department_demo(active_tool, shipment_frame)

    render_section_heading(
        "Workflow Map",
        "Ain's thesis workflow usually starts with cleaning, adds logic, checks trends, and ends with presentation-quality charts.",
    )
    _render_workflow_map()

    recommendation = _render_tool_recommender(kimi_service)
    if recommendation:
        st.markdown(
            (
                "<div class='tutor-card'>"
                f"{recommendation['content']}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        if recommendation["mode"] == "heuristic":
            st.caption("Kimi was unavailable, so the app used a built-in department router as a safe fallback.")

    render_plain_note(
        "Recipe analogy: the ingredients are raw CSV rows, Python is the chef, and the kitchen tools are Pandas, NumPy, Plotly, Scikit-Fuzzy, and Statsmodels."
    )

    render_study_notes_panel("toolbox", gemini_service)
    module_state = {
        "active_department": TOOLBOX_DEPARTMENTS[active_tool].name,
        "active_role": TOOLBOX_DEPARTMENTS[active_tool].factory_role,
        "starter_call": TOOLBOX_DEPARTMENTS[active_tool].starter_call,
        "dataset_source": dataset_bundle.source_label,
        "tool_recommendation": recommendation["content"] if recommendation else "No department recommendation requested yet.",
    }
    handle_tutor_interaction("toolbox", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("toolbox")


if __name__ == "__main__":
    main()
