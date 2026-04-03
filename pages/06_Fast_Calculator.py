from __future__ import annotations

import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.config import ACCENT_COLOR, PLOTLY_TEMPLATE, TEXT_COLOR, ensure_project_directories
from services.gemini_rag import GeminiRAGService
from services.kimi_tutor import KimiTutorService
from services.python_learning import fast_calculator_breakdown, fast_calculator_live_code
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


def main() -> None:
    configure_page("NEBULOUS-CORE | The Fast Calculator")
    inject_styles()
    ensure_project_directories()
    initialize_session_state(st.session_state)

    gemini_service = GeminiRAGService()
    kimi_service = KimiTutorService()
    sidebar_payload = render_sidebar("fast_calculator", gemini_service, kimi_service)

    bootstrap_app("fast_calculator")
    render_kpis(
        [
            ("Focus", "NumPy", "This stage teaches Ain how Python handles heavy numerical workloads efficiently."),
            ("Factory Role", "Fast Calculator", "Turn one logistics formula into a whole-column calculation."),
            ("Next Unlock", "Module 7", "Pass this sprint to unlock the Intuition Engine."),
        ]
    )
    render_what_you_will_learn("fast_calculator")

    render_section_heading(
        "The Speed Race: Python Loop vs NumPy Array",
        "NumPy handles the whole shipment batch in one vectorised pass, while a Python loop touches every value one by one.",
    )

    controls_col, result_col = st.columns([0.92, 1.08], gap="large")
    with controls_col:
        n_coils = st.slider("Number of coils", min_value=100, max_value=100_000, value=10_000, step=100, key="fc-n")
        base_weight = st.slider("Base coil weight (tons)", min_value=5.0, max_value=30.0, value=18.75, step=0.25, key="fc-w")
        weight_std = st.slider("Weight variation (std dev)", min_value=0.1, max_value=5.0, value=1.2, step=0.1, key="fc-std")
        surcharge_pct = st.slider("Surcharge %", min_value=0.0, max_value=20.0, value=5.0, step=0.5, key="fc-sur")
        render_plain_note(
            "This is the kitchen-scale moment: NumPy is the tool Ain calls when she needs precise maths across thousands of values, not one value at a time."
        )

    rng = np.random.default_rng(seed=42)
    weights = rng.normal(loc=base_weight, scale=weight_std, size=n_coils).clip(1.0)
    surcharge_multiplier = 1 + surcharge_pct / 100
    billable_weights = weights * surcharge_multiplier

    t0 = time.perf_counter()
    python_total = sum(weight * surcharge_multiplier for weight in weights.tolist())
    python_time_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    numpy_total = float(np.sum(billable_weights))
    numpy_time_ms = (time.perf_counter() - t0) * 1000

    mean_weight = float(np.mean(billable_weights))
    std_weight = float(np.std(billable_weights))
    speedup = python_time_ms / max(numpy_time_ms, 0.001)

    sample_frame = pd.DataFrame(
        {
            "coil_weight_tons": np.round(weights[:8], 2),
            "billable_weight_tons": np.round(billable_weights[:8], 2),
        }
    )
    sample_frame["surcharge_added_tons"] = np.round(
        sample_frame["billable_weight_tons"] - sample_frame["coil_weight_tons"],
        2,
    )

    with result_col:
        st.metric("Total billable weight (tons)", f"{numpy_total:,.1f}")
        metric_col_a, metric_col_b = st.columns(2)
        metric_col_a.metric("Python loop", f"{python_time_ms:.2f} ms")
        metric_col_b.metric("NumPy vectorised", f"{numpy_time_ms:.3f} ms", delta=f"{speedup:.0f}x faster", delta_color="inverse")

        preview_tabs = st.tabs(["Speed Race", "Weight Distribution", "Sample Rows"])
        with preview_tabs[0]:
            race_figure = go.Figure()
            race_figure.add_trace(
                go.Bar(
                    x=["Python loop", "NumPy vectorised"],
                    y=[python_time_ms, numpy_time_ms],
                    marker_color=[TEXT_COLOR, ACCENT_COLOR],
                    text=[f"{python_time_ms:.2f} ms", f"{numpy_time_ms:.3f} ms"],
                    textposition="outside",
                )
            )
            race_figure.update_layout(
                template=PLOTLY_TEMPLATE,
                height=290,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Calculation method",
                yaxis_title="Execution time (ms)",
                showlegend=False,
            )
            st.plotly_chart(race_figure, width="stretch")
        with preview_tabs[1]:
            hist_counts, bin_edges = np.histogram(weights, bins=36)
            bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
            dist_figure = go.Figure()
            dist_figure.add_trace(
                go.Bar(
                    x=bin_centers,
                    y=hist_counts,
                    marker_color=ACCENT_COLOR,
                    name="Coil weight distribution",
                )
            )
            dist_figure.update_layout(
                template=PLOTLY_TEMPLATE,
                height=290,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Weight (tons)",
                yaxis_title="Count",
            )
            st.plotly_chart(dist_figure, width="stretch")
        with preview_tabs[2]:
            st.dataframe(sample_frame, width="stretch", hide_index=True)

    active_python_snippet = render_live_code_panel(
        "Live Code",
        fast_calculator_live_code(
            n_coils=n_coils,
            base_weight=base_weight,
            weight_std=weight_std,
            surcharge_pct=surcharge_pct,
            numpy_total=numpy_total,
            mean_weight=mean_weight,
            std_weight=std_weight,
        ),
        key="fast-calculator-live-code",
    )
    render_python_breakdown("How this works in Python", fast_calculator_breakdown())

    render_section_heading(
        "Mathematical Visualization",
        "The NumPy code is just the symbolic logistics formula applied to an entire array at once.",
    )
    render_formula(
        r"\mathbf{billable\_weights} = \mathbf{weights} \times (1 + s)",
        caption="Broadcasting applies the surcharge scalar s to every coil weight in one vectorised step.",
    )
    render_formula(
        r"\text{speedup} = \frac{t_{\mathrm{python}}}{t_{\mathrm{numpy}}}",
        caption="This ratio turns the benchmark into a simple learning signal: larger values mean the vectorised path is winning harder.",
    )

    render_section_heading(
        "Vibe Explanation",
        "This is the moment Ain stops thinking one row at a time and starts thinking in arrays.",
    )
    st.markdown(
        (
            f"For **{n_coils:,}** coils, both methods reach almost the same total, but NumPy does the job in **{numpy_time_ms:.3f} ms** instead of "
            f"**{python_time_ms:.2f} ms**. That is why data science code prefers arrays: one formula can act across an entire shipment batch without a slow Python loop."
        )
    )
    render_plain_note(
        "If Ain can explain broadcasting in plain English, she has crossed an important line from beginner syntax into real analytical thinking."
    )

    render_study_notes_panel("fast_calculator", gemini_service)
    module_state = {
        "n_coils": n_coils,
        "base_weight": base_weight,
        "weight_std": weight_std,
        "surcharge_pct": surcharge_pct,
        "numpy_total": round(numpy_total, 1),
        "python_total": round(python_total, 1),
        "speedup": round(speedup, 1),
        "active_python_snippet": active_python_snippet,
    }
    handle_tutor_interaction("fast_calculator", module_state, sidebar_payload, gemini_service, kimi_service)
    render_last_tutor_response()
    render_quiz("fast_calculator")


if __name__ == "__main__":
    main()
