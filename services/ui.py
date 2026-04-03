from __future__ import annotations

import html as _html
from pathlib import Path
from typing import Any

import streamlit as st

from .config import MODULE_LABELS, MODULE_SEQUENCE, STYLE_PATH, TEXT_COLOR
from .content import MODULE_INTROS, MODULE_LEARNING_OBJECTIVES, QUIZ_CONTENT
from .data import load_shipment_dataset
from .storage import load_manifest, load_progress, mark_module_completed, save_progress

MODULE_UNLOCK_INDEX = {"toolbox": 4}  # requires quality_gate (index 3) completion
MODULE_UNLOCK_INDEX.update({module_key: index for index, module_key in enumerate(MODULE_SEQUENCE, start=1)})

try:
    from code_editor import code_editor
except Exception:  # pragma: no cover - optional component
    code_editor = None


def configure_page(page_title: str) -> None:
    st.set_page_config(
        page_title=page_title,
        page_icon=":material/flight_takeoff:",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_styles() -> None:
    if STYLE_PATH.exists():
        css = STYLE_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def bootstrap_app(module_key: str) -> None:
    intro = MODULE_INTROS[module_key]
    st.markdown(f"<p class='eyebrow'>{intro['eyebrow']}</p>", unsafe_allow_html=True)
    st.markdown(f"<h1 class='hero-title'>{intro['headline']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='hero-copy'>{intro['description']}</p>", unsafe_allow_html=True)


def render_kpis(kpis: list[tuple[str, str, str]]) -> None:
    columns = st.columns(len(kpis))
    for column, (label, value, description) in zip(columns, kpis):
        safe_label = _html.escape(str(label))
        safe_value = _html.escape(str(value))
        safe_description = _html.escape(str(description))
        column.markdown(
            (
                "<div class='info-card'>"
                f"<div class='card-label'>{safe_label}</div>"
                f"<div class='card-value'>{safe_value}</div>"
                f"<div class='card-copy'>{safe_description}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def enforce_unlock(module_key: str) -> None:
    progress = st.session_state.get("progress") or load_progress()
    required_index = MODULE_UNLOCK_INDEX[module_key]
    unlocked_index = progress.get("unlocked_module_index", 1)
    if unlocked_index < required_index:
        previous_module = MODULE_SEQUENCE[required_index - 2]
        st.warning(
            f"This sprint is locked. Complete {MODULE_LABELS[previous_module]} and pass its quiz to unlock this page."
        )
        st.stop()


def sync_sources_if_needed(gemini_service) -> None:
    if st.session_state.get("source_sync_bootstrapped"):
        return
    manifest = load_manifest()
    # #2: Only auto-sync on cold boot if manifest is absent (no store yet).
    # Otherwise let users trigger manually to avoid blocking cold boot.
    has_store = bool(manifest.get("store", {}).get("name"))
    if not has_store:
        result = gemini_service.sync_sources(force=False)
    else:
        result = type("_R", (), {"message": manifest.get("message", "Sources loaded from manifest.")})()  # type: ignore[misc]
    st.session_state["manifest"] = load_manifest()
    st.session_state["last_source_sync"] = st.session_state["manifest"].get("last_synced_at")
    st.session_state["source_sync_message"] = getattr(result, "message", "")
    st.session_state["source_sync_bootstrapped"] = True


def render_sidebar(module_key: str, gemini_service, kimi_service) -> dict[str, Any]:
    sidebar_payload: dict[str, Any] = {}
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>Ain's Copilot</div>", unsafe_allow_html=True)
        st.caption("Ask questions about the Python code and data models on each page. The Kimi AI tutor will guide you using the Socratic method.")

        uploaded_file = st.file_uploader(
            "Optional shipment CSV",
            type=["csv"],
            key="shared_csv_uploader",
            help="If you upload a valid shipment CSV, the pages will use it instead of the synthetic demo dataset.",
        )
        _MAX_CSV_BYTES = 5 * 1024 * 1024  # 5 MB #5
        if uploaded_file is not None:
            if uploaded_file.size > _MAX_CSV_BYTES:
                st.warning(f"CSV too large ({uploaded_file.size // 1024} KB). Maximum size is 5 MB.")
            else:
                st.session_state["uploaded_csv_name"] = uploaded_file.name
                st.session_state["uploaded_csv_bytes"] = uploaded_file.getvalue()
                st.session_state["uploaded_dataset_status"] = f"Using uploaded CSV: {uploaded_file.name}"
        if st.session_state.get("uploaded_csv_name"):
            st.success(st.session_state["uploaded_dataset_status"])
            if st.button("Clear uploaded CSV", width="stretch"):
                st.session_state["uploaded_csv_name"] = None
                st.session_state["uploaded_csv_bytes"] = None
                st.session_state["uploaded_dataset_status"] = "No uploaded dataset"
                st.rerun()

        st.markdown("### 📚 Research Sources")
        st.link_button(
            "Open NotebookLM Notebook",
            url="https://notebooklm.google.com/notebook/8f8d78ee-75f3-4306-a89f-911a6924c79e",
            use_container_width=True,
        )
        st.caption("36 papers on fuzzy logic, robust regression, forecasting, and Python.")

    sidebar_payload["dataset_bundle"] = load_shipment_dataset(
        uploaded_csv_bytes=st.session_state.get("uploaded_csv_bytes"),
        uploaded_name=st.session_state.get("uploaded_csv_name"),
    )

    with st.popover("💬", use_container_width=False):
        st.markdown("### Socratic Tutor")
        if not kimi_service.available:
            st.info("Add `MOONSHOT_API_KEY` to activate the Kimi tutor.")
        if not gemini_service.available:
            st.info("Add `GEMINI_API_KEY` to enable Gemini grounded evidence in the chatbot.")

        col_title, col_clear = st.columns([3, 1])
        with col_clear:
            if st.button("Clear", key=f"clear-chat-{module_key}", help="Clear conversation history"):
                st.session_state["chat_messages"] = []
                st.session_state["last_tutor_response"] = None
                st.rerun()

        for message in st.session_state.get("chat_messages", [])[-8:]:
            role = "user" if message.get("role") == "user" else "assistant"
            with st.chat_message(role):
                st.markdown(message.get("content", ""))
                citations = message.get("citations") or []
                if citations:
                    st.caption("Sources: " + " | ".join(Path(citation.get("source_path", "local-source")).name for citation in citations[:3]))

        sidebar_payload["spinner_container"] = st.container()

        st.caption("Suggested questions:")
        for suggestion in kimi_service.default_seed_questions(module_key)[:3]:
            if st.button(suggestion, key=f"{module_key}-{suggestion}", use_container_width=True):
                sidebar_payload["submitted_prompt"] = suggestion

        chat_input = st.chat_input("Ask Kimi + Gemini...", key=f"chat-input-{module_key}")
        if chat_input:
            sidebar_payload["submitted_prompt"] = chat_input.strip()

        queued_prompt = st.session_state.get("queued_tutor_prompt")
        if queued_prompt and not sidebar_payload.get("submitted_prompt"):
            sidebar_payload["submitted_prompt"] = queued_prompt
            st.session_state["queued_tutor_prompt"] = None

    return sidebar_payload


def render_study_notes_panel(module_key: str, gemini_service) -> None:
    st.markdown("### NotebookLM-Style Study Notes")
    cache_key = f"study-notes-{module_key}"
    if st.button("Generate grounded study notes", key=f"study-notes-button-{module_key}"):
        st.session_state["study_note_cache"][cache_key] = gemini_service.build_study_notes(module_key)

    note_bundle = st.session_state["study_note_cache"].get(cache_key)
    if note_bundle is None:
        st.info("Generate notes to summarize the local sources for this sprint.")
        return
    if not note_bundle.get("ok"):
        st.warning(note_bundle.get("message"))
        return

    st.markdown(
        (
            "<div class='study-card'>"
            f"{note_bundle.get('answer', 'No notes were returned.')}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    citations = note_bundle.get("citations") or []
    if citations:
        st.caption("Grounded in: " + " | ".join(Path(citation.get("source_path", "local-source")).name for citation in citations[:4]))


def handle_tutor_interaction(
    module_key: str,
    module_state: dict[str, Any],
    sidebar_payload: dict[str, Any],
    gemini_service,
    kimi_service,
) -> None:
    submitted_prompt = sidebar_payload.get("submitted_prompt")
    if not submitted_prompt:
        return

    prior_history = list(st.session_state.get("chat_messages", []))
    
    def process_tutor():
        g_notes = gemini_service.retrieve_grounded_notes(
            query=submitted_prompt,
            module_key=module_key,
            prompt_prefix="Retrieve the most relevant local evidence for Ain's question. Keep the answer concise and citation-friendly.",
        )
        t_resp = kimi_service.answer(
            module_key=module_key,
            user_prompt=submitted_prompt,
            module_state=module_state,
            grounded_notes=g_notes,
            chat_history=prior_history,
        )
        return g_notes, t_resp

    spinner_container = sidebar_payload.get("spinner_container")
    
    if spinner_container is not None:
        with spinner_container:
            with st.chat_message("user"):
                st.markdown(submitted_prompt)
            with st.chat_message("assistant"):
                with st.spinner("Kimi and Gemini are analyzing the dashboard..."):
                    grounded_notes, tutor_response = process_tutor()
    else:
        with st.spinner("Kimi and Gemini are analyzing the dashboard..."):
            grounded_notes, tutor_response = process_tutor()
            
    st.session_state["chat_messages"].append({"role": "user", "content": submitted_prompt})

    if not tutor_response.get("ok"):
        st.session_state["last_tutor_response"] = tutor_response
        st.rerun()
        return

    assistant_message = tutor_response["assistant_message"]
    assistant_message["citations"] = grounded_notes.get("citations", [])
    st.session_state["chat_messages"].append(assistant_message)
    st.session_state["last_tutor_response"] = {
        "content": tutor_response["content"],
        "next_question": tutor_response["next_question"],
        "citations": grounded_notes.get("citations", []),
    }
    st.rerun()


def render_last_tutor_response() -> None:
    response = st.session_state.get("last_tutor_response")
    if not response:
        return
    if response.get("content") is None:
        st.warning(response.get("message"))
        return
    render_section_heading("Socratic Tutor Response")
    st.markdown(
        (
            "<div class='tutor-card'>"
            f"{response['content']}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    if response.get("next_question"):
        st.caption(f"Suggested next question: {response['next_question']}")
        if st.button("Ask suggested next question", key="ask-next-question"):
            st.session_state["queued_tutor_prompt"] = response["next_question"]
            st.rerun()
    citations = response.get("citations") or []
    if citations:
        st.caption("Evidence used: " + " | ".join(Path(citation.get("source_path", "local-source")).name for citation in citations[:4]))


def render_quiz(module_key: str, passing_score: int = 3) -> None:
    render_section_heading("Knowledge Check")
    quiz_items = QUIZ_CONTENT[module_key]
    total_questions = len(quiz_items)
    st.caption(f"{total_questions} questions · pass {passing_score}/{total_questions} to unlock the next sprint.")
    prior_score = st.session_state.get("progress", {}).get("quiz_scores", {}).get(module_key)
    if prior_score is not None:
        st.progress(min(prior_score / total_questions, 1.0), text=f"Last attempt: {prior_score}/{total_questions}")
    with st.form(f"quiz-form-{module_key}"):
        answers = []
        for index, item in enumerate(quiz_items, start=1):
            answers.append(
                st.radio(
                    f"{index}. [{item['category']}] {item['prompt']}",
                    options=item["options"],
                    index=None,
                    key=f"{module_key}-quiz-{index}",
                )
            )
        submitted = st.form_submit_button("Check answers and unlock next sprint")

    if not submitted:
        return

    score = 0
    required_questions_passed = True
    missed_required_prompts: list[str] = []
    for answer, quiz_item in zip(answers, QUIZ_CONTENT[module_key]):
        if answer == quiz_item["answer"]:
            score += 1
        elif quiz_item.get("required_for_unlock"):
            required_questions_passed = False
            missed_required_prompts.append(quiz_item["prompt"])
    passed = score >= passing_score and required_questions_passed
    progress = st.session_state.get("progress") or load_progress()
    updated_progress = mark_module_completed(progress, module_key, score, passed)
    st.session_state["progress"] = updated_progress
    save_progress(updated_progress)

    if passed:
        st.success(
            f"Level unlocked. You scored {score}/{len(QUIZ_CONTENT[module_key])}. "
            f"Current certification: {updated_progress['certification_level']}."
        )
    else:
        if missed_required_prompts:
            st.warning(
                f"You scored {score}/{len(QUIZ_CONTENT[module_key])}, but a required Python unlock question is still missing. "
                "Review the live code block and the key library call for this lesson, then try again."
            )
        else:
            st.warning(f"You scored {score}/{len(QUIZ_CONTENT[module_key])}. Review the module and try again.")


def render_dataset_status(dataset_bundle) -> None:
    st.markdown(
        (
            "<div class='sidebar-card'>"
            f"<strong>Data source:</strong> {dataset_bundle.source_label}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
    for warning in dataset_bundle.warnings:
        st.info(warning)


def render_section_heading(title: str, description: str | None = None) -> None:
    st.markdown(f"<h2 class='section-title'>{title}</h2>", unsafe_allow_html=True)
    if description:
        st.markdown(f"<p class='section-copy'>{description}</p>", unsafe_allow_html=True)


def render_formula(formula_latex: str, caption: str | None = None) -> None:
    st.latex(formula_latex)
    if caption:
        st.caption(caption)


def render_plain_note(message: str) -> None:
    st.markdown(
        (
            "<div class='info-card'>"
            f"<div class='card-copy' style='color:{TEXT_COLOR}'>{message}</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_what_you_will_learn(module_key: str) -> None:
    objectives = MODULE_LEARNING_OBJECTIVES.get(module_key, [])
    if not objectives:
        return
    items_html = "".join(
        f"<div style='display:flex;align-items:flex-start;gap:0.6rem;margin-bottom:0.55rem;'>"
        f"<span style='color:var(--accent);font-size:1.1rem;line-height:1.6;'>✓</span>"
        f"<span style='color:var(--text);line-height:1.6;'>{obj}</span>"
        f"</div>"
        for obj in objectives
    )
    st.markdown(
        (
            "<div class='info-card'>"
            "<div class='card-label' style='margin-bottom:0.8rem;'>What you will learn</div>"
            f"{items_html}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_live_code_panel(title: str, code_text: str, key: str) -> str:
    st.markdown(f"### {title}")
    st.code(code_text, language="python")
    st.caption("This snippet updates live as the controls change so Ain can connect the UI state to real Python variables.")

    if code_editor is None:
        st.info("Install `streamlit-code-editor` to unlock an editable sandbox here. For now, the live snippet is read-only.")
        return code_text

    sandbox_key = f"{key}-sandbox"
    st.caption("Sandbox mode: edit the snippet below to explore syntax safely. Edits do not change the running dashboard.")
    response_dict = code_editor(
        code_text,
        lang="python",
        theme="default",
        allow_reset=True,
        response_mode=["blur", "debounce"],
        key=sandbox_key,
        options={"wrap": True, "showLineNumbers": True},
        height=320,
    )
    edited_text = code_text
    if isinstance(response_dict, dict) and response_dict.get("text"):
        edited_text = response_dict["text"]
    return edited_text


def render_python_breakdown(title: str, sections: list[dict[str, str]]) -> None:
    with st.expander(title):
        for section in sections:
            st.markdown(f"**{section['title']}**")
            st.markdown(section["explanation"])
            st.code(section["code"], language="python")
