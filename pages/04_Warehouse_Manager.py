from __future__ import annotations

import pandas as pd
import streamlit as st

from services.config import ensure_project_directories
from services.data import load_shipment_dataset
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import warehouse_manager_breakdown, warehouse_manager_live_code
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


def build_messy_table(shipment_frame: pd.DataFrame) -> pd.DataFrame:
    messy_frame = shipment_frame.head(6)[["shipment_date", "ordered_quantity", "received_quantity", "delay_days"]].copy()
    messy_frame["shipment_date"] = messy_frame["shipment_date"].dt.strftime(" %d-%m-%Y ")
    messy_frame["ordered_quantity"] = messy_frame["ordered_quantity"].map(lambda value: f" {value:.1f} ")
    messy_frame["received_quantity"] = messy_frame["received_quantity"].map(lambda value: f"{value:.1f} tons")
    messy_frame.loc[messy_frame.index[2], "delay_days"] = None
    return pd.concat([messy_frame, messy_frame.iloc[[1]]], ignore_index=True)


def clean_table(messy_frame: pd.DataFrame) -> pd.DataFrame:
    cleaned_frame = messy_frame.copy()
    cleaned_frame["shipment_date"] = pd.to_datetime(cleaned_frame["shipment_date"].str.strip(), format="%d-%m-%Y", errors="coerce")
    cleaned_frame["ordered_quantity"] = pd.to_numeric(cleaned_frame["ordered_quantity"].str.strip(), errors="coerce")
    cleaned_frame["received_quantity"] = pd.to_numeric(
        cleaned_frame["received_quantity"].str.replace(" tons", "", regex=False),
        errors="coerce",
    )
    cleaned_frame["delay_days"] = pd.to_numeric(cleaned_frame["delay_days"], errors="coerce").fillna(0.0)
    cleaned_frame = cleaned_frame.drop_duplicates().sort_values("shipment_date").reset_index(drop=True)
    return cleaned_frame


def main() -> None:
    configure_page("NEBULOUS-CORE | Warehouse Manager")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("warehouse_manager", gemini_service, kimi_service)
    dataset_bundle = sidebar_payload["dataset_bundle"]
    shipment_frame = dataset_bundle.dataframe.copy()

    bootstrap_app("warehouse_manager")
    render_kpis(
        [
            ("Focus", "Pandas", "This stage turns raw shipment rows into a clean DataFrame."),
            ("Factory Role", "Warehouse Manager", "Clean, sort, and filter before anything advanced happens."),
            ("Next Unlock", "Module 5", "Pass this quiz to unlock the fuzzy intuition engine."),
        ]
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)
    render_what_you_will_learn("warehouse_manager")

    render_section_heading(
        "Messy Data Cleaner",
        "One click turns a broken shipment table into something the rest of the thesis pipeline can actually trust.",
    )
    messy_frame = build_messy_table(shipment_frame)
    cleaned_frame = clean_table(messy_frame)
    left_column, right_column = st.columns(2, gap="large")
    left_column.markdown("**Before cleaning**")
    left_column.dataframe(messy_frame, width="stretch", hide_index=True)
    right_column.markdown("**After Pandas cleaning**")
    right_column.dataframe(cleaned_frame, width="stretch", hide_index=True)
    render_plain_note(
        "This is the difference between raw paperwork and a clean warehouse ledger. Pandas is the department that makes the table trustworthy."
    )

    active_python_snippet = render_live_code_panel(
        "Live Code",
        warehouse_manager_live_code(before_rows=len(messy_frame), after_rows=len(cleaned_frame)),
        key="warehouse-manager-live-code",
    )
    render_python_breakdown("How this works in Python", warehouse_manager_breakdown())

    render_section_heading("Vibe Explanation", "This is where Ain moves from Python grammar to real analyst work.")
    st.markdown(
        (
            f"The messy table started with **{len(messy_frame)}** rows and the cleaned DataFrame ended with **{len(cleaned_frame)}** rows. "
            "Pandas removed the duplicate, converted dates, repaired numeric fields, and put the shipment records into a reliable order."
        )
    )

    render_study_notes_panel("warehouse_manager", gemini_service)
    module_state = {
        "messy_rows": len(messy_frame),
        "clean_rows": len(cleaned_frame),
        "dataset_source": dataset_bundle.source_label,
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("warehouse_manager", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("warehouse_manager")


if __name__ == "__main__":
    main()
