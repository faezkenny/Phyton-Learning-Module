from __future__ import annotations

from pathlib import Path

import streamlit as st

from services.config import FIRST_TIME_TUTORIAL_PATH, MODULE_LABELS, MODULE_SEQUENCE, SOURCES_DIR, ensure_project_directories
from services.kimi_tutor import KimiTutorService
from services.storage import initialize_session_state, load_manifest, save_progress
from services.ui import (
    bootstrap_app,
    configure_page,
    handle_tutor_interaction,
    inject_styles,
    render_kpis,
    render_last_tutor_response,
    render_plain_note,
    render_section_heading,
    render_sidebar,
    render_study_notes_panel,
)


def render_learning_sprint_card(module_key: str, description: str, unlocked: bool) -> None:
    destination = {
        "storage_bins": "pages/01_Storage_Bins.py",
        "shipping_manifest": "pages/02_Shipping_Manifest.py",
        "quality_gate": "pages/03_Quality_Gate.py",
        "warehouse_manager": "pages/04_Warehouse_Manager.py",
        "intuition_engine": "pages/05_Intuition_Engine.py",
        "quality_inspector": "pages/06_Quality_Inspector.py",
        "future_predictor": "pages/07_Future_Predictor.py",
    }[module_key]
    status_text = "Unlocked" if unlocked else "Locked"
    st.markdown(
        (
            "<div class='info-card'>"
            f"<div class='card-label'>{status_text}</div>"
            f"<div class='card-value'>{MODULE_LABELS[module_key]}</div>"
            f"<div class='card-copy'>{description}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    st.page_link(destination, label=f"Open {MODULE_LABELS[module_key]}", icon=":material/arrow_forward:")


@st.dialog("First-Time Guide", width="large")
def render_first_time_tutorial(progress: dict, source_count: int) -> None:
    st.markdown(
        "Welcome aboard the Academic Flight Simulator! This dashboard is built for interactive learning. Here is how to navigate:"
    )
    tutorial_steps = [
        (
            "1",
            "Follow The Curriculum",
            "Use the left sidebar to navigate. Start at Module 1. Complete the quiz at the bottom of each page to unlock the next level.",
        ),
        (
            "2",
            "Interactive Python",
            "Inside each module, adjust the sliders. Watch how the charts and the 'Live Python Code' change automatically as you interact.",
        ),
        (
            "3",
            "Ain's AI Copilot",
            "Stuck? Click the floating orange Chat Button (💬) at the bottom right to open the AI Socratic Tutor. It will explain exactly what the Python code is doing.",
        ),
        (
            "4",
            "Learn by Doing",
            "Don't worry about memorizing syntax. Ask the AI 'Why did this chart move when I adjusted the slider?' and use the 'Suggested Questions' to guide your learning.",
        ),
    ]
    tutorial_columns = st.columns(4, gap="medium")
    for column, (step_number, title, description) in zip(tutorial_columns, tutorial_steps):
        with column:
            st.markdown(
                (
                    "<div class='tutorial-card'>"
                    f"<div class='tutorial-step'>{step_number}</div>"
                    f"<div class='card-value'>{title}</div>"
                    f"<div class='card-copy'>{description}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

    start_column, status_column = st.columns([0.75, 1.25], gap="large")
    with start_column:
        st.page_link(
            "pages/01_Storage_Bins.py",
            label="Start Module 1",
            icon=":material/play_circle:",
        )
    with status_column:
        if source_count == 0:
            render_plain_note(
                "You are currently using the built-in demo dataset. Perfect for your first flight! You can upload your own optionally via the sidebar."
            )
        elif not progress.get("completed_modules"):
            render_plain_note(
                f"{source_count} custom documents are indexed! The Copilot will use your own PDFs and CSVs to answer your questions during this syllabus."
            )

    st.divider()
    if not st.session_state["progress"].get("tutorial_shown", False):
        if st.button("Got It, Let's Start! 🚀", type="primary"):
            st.session_state["progress"]["tutorial_shown"] = True
            save_progress(st.session_state["progress"])
            st.rerun()


def main() -> None:
    configure_page("NEBULOUS-CORE | Mission Control")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("home", kimi_service)

    bootstrap_app("home")

    import json as _json
    _kb_path = Path(__file__).parent / "knowledge_base.json"
    if _kb_path.exists():
        try:
            with _kb_path.open("r", encoding="utf-8") as _kb_file:
                _kb = _json.load(_kb_file)
            st.markdown("<h2 class='section-title'>Fuzzy Logic Masterclass (NotebookLM Extraction)</h2>", unsafe_allow_html=True)
            _fuzzy_module = _kb["curriculum"]["intuition_engine"]
            st.latex(_fuzzy_module["math_latex"])
            st.info(f"Thesis Insight: {_fuzzy_module['viva_point']}")
        except Exception:
            pass  # Knowledge base unavailable — silently skip the panel


    progress = st.session_state["progress"]
    dataset_bundle = sidebar_payload["dataset_bundle"]
    render_kpis(
        [
            ("Certification", progress["certification_level"], "Your current dashboard mastery tier."),
            ("Modules", f"{progress.get('unlocked_module_index', 1)} / 7", "Stages unlocked so far."),
            ("Data Feed", dataset_bundle.source_label, "The shipment dataset currently powering the live demos."),
        ]
    )

    for warning in dataset_bundle.warnings:
        st.info(warning)

    left_column, right_column = st.columns([1.3, 0.9], gap="large")
    with left_column:
        if not progress.get("tutorial_shown", False):
            render_first_time_tutorial(progress, 0)

        if st.button("🗺️ Open Navigation Guide"):
            render_first_time_tutorial(progress, 0)

        render_section_heading(
            "Curriculum Path",
            "Seven stages from basic Python variables all the way to ARIMA forecasting. Complete each quiz to unlock the next stage and raise your certification level.",
        )
        render_plain_note(
            "Start with Module 1 and work through each stage in order. The Analyst Toolbox is available after Module 3 as a practical reference for the tools used in later stages."
        )
        sprint_descriptions = {
            "storage_bins": "Variables and types for single shipment facts like supplier name, coil weight, and confirmation status.",
            "shipping_manifest": "Lists and dictionaries for storing several coils and their attributes like a logistics manifest.",
            "quality_gate": "If/else logic and functions for repeatable safety-stock rules and shipping SOPs.",
            "warehouse_manager": "Pandas loading, cleaning, and filtering of raw shipment tables.",
            "intuition_engine": "Interactive fuzzy membership controls with a confidence cloud and symbolic math.",
            "quality_inspector": "OLS versus Huber-weighted robust fitting on noisy steel-coil shipment data.",
            "future_predictor": "ARIMA forecasting over quantity discrepancy with disruption scenario sliders.",
        }
        for module_key in MODULE_SEQUENCE:
            unlocked = progress.get("unlocked_module_index", 1) >= MODULE_SEQUENCE.index(module_key) + 1
            render_learning_sprint_card(module_key, sprint_descriptions[module_key], unlocked)

        render_section_heading(
            "Tutor Workflow",
            "Use the AI Copilot in the sidebar to ask questions about the Python code and the models on each page. The tutor uses Socratic reasoning to guide you through concepts step by step.",
        )
        render_plain_note(
            "Click the 💬 button or use the sidebar Ask box. Try asking: 'Why did the chart change when I moved the slider?' or 'Explain the Python loop on this page.'"
        )

    with right_column:
        render_section_heading(
            "Architecture At A Glance",
            "The dashboard is intentionally split into retrieval, reasoning, and live math so Ain can see both the evidence and the model behavior.",
        )
        st.markdown(
            (
                "<div class='info-card'>"
                "<div class='card-label'>Gemini RAG</div>"
                "<div class='card-copy'>Indexes local PDFs and CSVs from /sources, keeps them in sync through manifest hashing, and returns cited evidence snippets.</div>"
                "</div>"
                "<div class='info-card'>"
                "<div class='card-label'>Kimi k2.5</div>"
                "<div class='card-copy'>Acts as a Socratic tutor that reasons over the visible formulas, chart state, and Gemini evidence without exposing raw reasoning traces.</div>"
                "</div>"
                "<div class='info-card'>"
                "<div class='card-label'>Learning Engine</div>"
                "<div class='card-copy'>Streamlit pages, Plotly white-theme visuals, live code blocks, syntax breakdowns, quizzes, and local progress persistence keep the experience portfolio-ready and beginner-friendly.</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        render_section_heading(
            "Research Sources",
            "All reference documents, papers, and reports used to build this dashboard are indexed in the NotebookLM notebook.",
        )
        st.markdown(
            (
                "<div class='info-card'>"
                "<div class='card-label'>📚 NotebookLM Notebook</div>"
                "<div class='card-copy'>36 research documents — academic papers on fuzzy logic, robust regression, ARIMA forecasting, Python data science, and steel logistics — indexed and searchable.</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.link_button(
            "🔗 Open Research Notebook",
            url="https://notebooklm.google.com/notebook/8f8d78ee-75f3-4306-a89f-911a6924c79e",
            use_container_width=True,
        )

    render_study_notes_panel("home", None)

    module_state = {
        "certification_level": progress["certification_level"],
        "unlocked_module_index": progress["unlocked_module_index"],
        "indexed_source_files": 0,
        "dataset_source": dataset_bundle.source_label,
    }
    handle_tutor_interaction("home", module_state, sidebar_payload, None, kimi_service)
    render_last_tutor_response()


def __boot__() -> None:
    pg = st.navigation([
        st.Page(main, title="Home", icon="🏠", default=True),
        st.Page("pages/01_Storage_Bins.py", title="Module 1: Storage bins"),
        st.Page("pages/02_Shipping_Manifest.py", title="Module 2: Shipping Manifest"),
        st.Page("pages/03_Quality_Gate.py", title="Module 3: Quality Gate"),
        st.Page("pages/00_Analysts_Toolbox.py", title="Analyst Toolbox"),
        st.Page("pages/04_Warehouse_Manager.py", title="Module 4: Warehouse Manager"),
        st.Page("pages/05_Intuition_Engine.py", title="Module 5: Intuition Engine"),
        st.Page("pages/06_Quality_Inspector.py", title="Module 6: Quality Inspector"),
        st.Page("pages/07_Future_Predictor.py", title="Module 7: Future Predictor"),
    ])
    pg.run()


__boot__()
