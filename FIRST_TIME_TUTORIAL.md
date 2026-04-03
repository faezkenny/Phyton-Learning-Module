# First-Time Tutorial

This guide is for Ain's first session inside NEBULOUS-CORE.

## 1. Open the dashboard

Run:

```bash
streamlit run app.py
```

If the API keys are not ready yet, that is okay. The dashboard still works with demo data and safe fallback states.

## 2. Start with Module 0

Open **Module 0: The Analyst's Toolbox** first.

That module is the lowest-stress entry point because it teaches:

- which library does which job
- when to call Pandas, Plotly, Scikit-Fuzzy, NumPy, or Statsmodels
- how the thesis workflow moves from raw data to final chart

Do not worry about memorizing code yet. The goal is just to learn which department to call.

## 3. Decide whether to use demo data or real files

You have two safe options:

- Use the built-in 90-day steel-coil demo dataset
- Add your own PDFs and CSVs into `sources/`

Recommended source folders:

```text
sources/shared
sources/toolbox
sources/fuzzy
sources/robust
sources/forecast
```

If no files are added yet, the app will not crash. It will explain what is missing in plain English.

## 4. Use the sidebar like a study copilot

The sidebar has three main jobs:

- upload an optional shipment CSV
- refresh the Gemini source index
- ask Kimi questions about the current lesson

Good first questions:

- "Which library should I call if my shipment file is messy?"
- "Why did this chart move when I changed the slider?"
- "What Python function is doing this part?"

## 5. Move through the learning order

The recommended sequence is:

1. Module 0: learn the tool departments
2. Module 1: Storage Bins
3. Module 2: Shipping Manifest
4. Module 3: Quality Gate
5. Module 4: Warehouse Manager
6. Module 5: Intuition Engine
7. Module 6: Quality Inspector
8. Module 7: Future Predictor

Each quiz unlocks the next sprint.

## 6. How to use the Python learning panels

Each lesson has:

- a live code block that mirrors the visible controls
- a sandbox editor for safe edits
- a "How this works in Python" section

Use them like this:

1. change one slider
2. watch the chart move
3. look at the live code block
4. ask Kimi why the variable changed

That loop is more important than memorizing syntax.

## 7. If something looks wrong

Check these first:

- `GEMINI_API_KEY` and `MOONSHOT_API_KEY` are set if you want live AI features
- your CSV has `shipment_date`, `ordered_quantity`, `received_quantity`, and `delay_days`
- your PDFs and CSVs are inside the correct `sources/` folders

If the AI tools are unavailable, the dashboard should still let you learn with local math demos.

## 8. What success looks like

By the end of a first session, Ain should be able to say:

- "Pandas is for cleaning shipment data."
- "Plotly is for interactive charts."
- "Scikit-Fuzzy is for linguistic risk logic."
- "Statsmodels is for robust regression and forecasting."
- "I do not need to memorize everything; I just need to know which tool to call."
