# NEBULOUS-CORE

NEBULOUS-CORE is a Streamlit learning dashboard and Python learning environment for Ain's Master's work in fuzzy-robust time series analysis for shipment logistics. It combines:

- Gemini RAG over local PDFs and CSVs in `/sources`
- Kimi `kimi-k2.5` as a Socratic tutor with Python-first explanations
- An orientation module plus a seven-stage apprentice-to-architect curriculum
- Live Python code blocks, syntax breakdown panels, and mixed math-plus-syntax quizzes

## Quick Start

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables:

```bash
export GEMINI_API_KEY="your-gemini-key"
export MOONSHOT_API_KEY="your-moonshot-key"
```

4. Run the app:

```bash
streamlit run app.py
```

For Ain's first session, open [FIRST_TIME_TUTORIAL.md](./FIRST_TIME_TUTORIAL.md), start with **Module 0: The Analyst's Toolbox**, and then move into **Module 1: The Storage Bins**.

## Local Source Library

Put your PDFs and CSVs in these folders:

```text
sources/shared
sources/toolbox
sources/storage_bins
sources/shipping_manifest
sources/quality_gate
sources/warehouse_manager
sources/intuition_engine
sources/quality_inspector
sources/future_predictor
```

Backward-compatible folders like `sources/fuzzy`, `sources/robust`, and `sources/forecast` are still recognized and mapped to the newer curriculum stages.

The dashboard keeps a local `manifest.json` to track file hashes, Gemini document IDs, and sync status.

## Shipment CSV Schema

Required columns:

- `shipment_date`
- `ordered_quantity`
- `received_quantity`
- `delay_days`

Optional columns:

- `war_disruption_index`
- `port_congestion_index`
- `supplier_risk_score`

If no valid shipment CSV is found, the app falls back to a built-in 90-day steel-coil demo dataset.

## Notes

- Missing API keys do not break the UI; the app shows setup instructions and continues with local math demos.
- Empty `/sources` folders are handled gracefully with plain-English guidance.
- Quiz progress is stored locally in `.app_storage/progress.json`.
- `streamlit-code-editor` is used when available so Ain can safely edit code snippets in a sandbox-style panel without changing the running model.
