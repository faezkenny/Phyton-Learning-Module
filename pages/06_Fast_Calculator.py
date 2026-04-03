from __future__ import annotations

import time

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.storage import initialize_session_state
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


def main() -> None:
    configure_page("NEBULOUS-CORE | The Fast Calculator")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)
    enforce_unlock("fast_calculator")

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("fast_calculator", gemini_service, kimi_service)

    bootstrap_app("fast_calculator")
    render_kpis(
        [
            ("Library", "NumPy", "The math engine behind every scientific Python library."),
            ("Certification", st.session_state["progress"]["certification_level"], "Your current learning sprint rank."),
            ("Next Unlock", "Module 7", "Pass this sprint to unlock the Intuition Engine."),
        ]
    )
    render_what_you_will_learn("fast_calculator")

    render_section_heading(
        "The Speed Race: Python Loop vs NumPy Array",
        "NumPy processes an entire column of values in one C-level instruction instead of looping in Python.",
    )

    controls_col, result_col = st.columns([1.0, 1.3], gap="large")
    with controls_col:
        n_coils = st.slider("Number of coils", min_value=100, max_value=100_000, value=10_000, step=100, key="fc-n")
        base_weight = st.slider("Base coil weight (tons)", min_value=5.0, max_value=30.0, value=18.75, step=0.25, key="fc-w")
        weight_std = st.slider("Weight variation (std dev)", min_value=0.1, max_value=5.0, value=1.2, step=0.1, key="fc-std")
        surcharge_pct = st.slider("Surcharge %", min_value=0.0, max_value=20.0, value=5.0, step=0.5, key="fc-sur")
        render_plain_note(
            "NumPy stores data in contiguous C arrays. Operations like `+`, `*`, `np.sum()` run at compiled C speed — far faster than a Python for-loop."
        )

    rng = np.random.default_rng(seed=42)
    weights = rng.normal(loc=base_weight, scale=weight_std, size=n_coils).clip(1.0)

    # Benchmark Python loop vs NumPy
    t0 = time.perf_counter()
    python_total = sum(w * (1 + surcharge_pct / 100) for w in weights.tolist())
    python_time_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    numpy_total = float(np.sum(weights * (1 + surcharge_pct / 100)))
    numpy_time_ms = (time.perf_counter() - t0) * 1000

    speedup = python_time_ms / max(numpy_time_ms, 0.001)

    with result_col:
        st.metric("Total billable weight (tons)", f"{numpy_total:,.1f}")
        col_a, col_b = st.columns(2)
        col_a.metric("Python loop", f"{python_time_ms:.2f} ms")
        col_b.metric("NumPy vectorised", f"{numpy_time_ms:.3f} ms", delta=f"{speedup:.0f}× faster", delta_color="inverse")

        # Distribution chart
        hist_counts, bin_edges = np.histogram(weights, bins=50)
        bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=bin_centers,
            y=hist_counts,
            marker_color=ACCENT_COLOR,
            name="Coil weight distribution",
        ))
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            height=280,
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="Weight (tons)",
            yaxis_title="Count",
        )
        st.plotly_chart(fig, use_container_width=True)

    live_code = f"""\
import numpy as np

# Generate {n_coils:,} synthetic coil weights
rng = np.random.default_rng(seed=42)
weights = rng.normal(loc={base_weight}, scale={weight_std}, size={n_coils}).clip(1.0)

# Vectorised surcharge calculation — no Python loop needed
surcharge = {surcharge_pct / 100:.4f}
billable_weights = weights * (1 + surcharge)

# Aggregate stats in a single call
total_weight   = np.sum(billable_weights)         # {numpy_total:,.1f} tons
mean_weight    = np.mean(billable_weights)        # {float(np.mean(weights * (1 + surcharge_pct / 100))):.2f} tons
std_weight     = np.std(billable_weights)         # {float(np.std(weights * (1 + surcharge_pct / 100))):.2f} tons
print(f"Total billable: {{total_weight:,.1f}} tons")
"""

    render_section_heading("Live Code", "This is the exact NumPy call powering the result above.")
    st.code(live_code, language="python")

    render_section_heading(
        "Core NumPy Concepts",
        "Three ideas explain 80% of how NumPy is used in data science.",
    )
    st.markdown(
        (
            "<div class='info-card'>"
            "<div class='card-label'>Arrays, not lists</div>"
            "<div class='card-copy'><code>np.array([...])</code> creates a typed, contiguous memory block. "
            "Maths on it runs in C, not Python — so <code>weights * 1.05</code> is thousands of times faster than a loop.</div>"
            "</div>"
            "<div class='info-card'>"
            "<div class='card-label'>Broadcasting</div>"
            "<div class='card-copy'>When you write <code>weights * (1 + surcharge)</code>, NumPy "
            "automatically applies the scalar to every element — no loop, no list comprehension needed.</div>"
            "</div>"
            "<div class='info-card'>"
            "<div class='card-label'>Aggregate functions</div>"
            "<div class='card-copy'><code>np.sum()</code>, <code>np.mean()</code>, <code>np.std()</code>, "
            "<code>np.percentile()</code> — these collapse an array to a single number in one instruction. "
            "Pandas and scikit-fuzzy call these same functions under the hood.</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    render_study_notes_panel("fast_calculator", gemini_service)
    module_state = {
        "n_coils": n_coils,
        "base_weight": base_weight,
        "surcharge_pct": surcharge_pct,
        "numpy_total": round(numpy_total, 1),
        "speedup": round(speedup, 1),
        "dataset_source": "synthetic",
    }
    handle_tutor_interaction("fast_calculator", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("fast_calculator")


if __name__ == "__main__":
    main()
