from __future__ import annotations

from .config import MODULE_LABELS

MODULE_INTROS = {
    "home": {
        "eyebrow": "Academic Flight Simulator",
        "headline": "Shipping Disruption Simulator",
        "description": (
            "A local-first Python learning cockpit that guides Ain from basic storage bins and manifests "
            "all the way to fuzzy-robust time-series reasoning for industrial shipment logistics."
        ),
    },
    "toolbox": {
        "eyebrow": "Orientation",
        "headline": MODULE_LABELS["toolbox"],
        "description": (
            "Meet the factory departments first so Ain learns what each library does before diving into syntax or modeling."
        ),
    },
    "storage_bins": {
        "eyebrow": "Phase 1: Logistics Grammar",
        "headline": MODULE_LABELS["storage_bins"],
        "description": (
            "Learn how Python stores a supplier name, a coil weight, and a shipment status so Ain can reason about data one value at a time."
        ),
    },
    "shipping_manifest": {
        "eyebrow": "Phase 1: Logistics Grammar",
        "headline": MODULE_LABELS["shipping_manifest"],
        "description": (
            "Use lists and dictionaries like a shipping manifest so Ain can store multiple coils and label each one with useful attributes."
        ),
    },
    "quality_gate": {
        "eyebrow": "Phase 1: Logistics Grammar",
        "headline": MODULE_LABELS["quality_gate"],
        "description": (
            "Build simple decision rules with if/else logic and reusable work orders with Python functions."
        ),
    },
    "warehouse_manager": {
        "eyebrow": "Phase 2: Data Science Analyst",
        "headline": MODULE_LABELS["warehouse_manager"],
        "description": (
            "Turn a messy shipment sheet into a clean, filterable DataFrame so the rest of the thesis pipeline has reliable input."
        ),
    },
    "command_center": {
        "eyebrow": "Zone B: Department Managers",
        "headline": MODULE_LABELS["command_center"],
        "description": (
            "Build interactive 'Swiss-Fintech' charts from live shipment data using Plotly Express and Graph Objects."
        ),
    },
    "fast_calculator": {
        "eyebrow": "Zone B: Department Managers",
        "headline": MODULE_LABELS["fast_calculator"],
        "description": (
            "Process the total weight of thousands of coils in milliseconds using NumPy vectorised operations."
        ),
    },
    "intuition_engine": {
        "eyebrow": "Phase 2: Data Science Analyst",
        "headline": MODULE_LABELS["intuition_engine"],
        "description": (
            "Translate exact shipment values into fuzzy states and watch uncertainty become visible in the model."
        ),
    },
    "quality_inspector": {
        "eyebrow": "Phase 2: Data Science Analyst",
        "headline": MODULE_LABELS["quality_inspector"],
        "description": (
            "Use robust statistics to notice war spikes without letting them hijack the long-run shipment story."
        ),
    },
    "future_predictor": {
        "eyebrow": "Phase 2: Data Science Analyst",
        "headline": MODULE_LABELS["future_predictor"],
        "description": (
            "Forecast quantity discrepancy with ARIMA and scenario controls that mimic real logistics disruption."
        ),
    },
}

MODULE_LEARNING_OBJECTIVES: dict[str, list[str]] = {
    "toolbox": [
        "Recognise the role of each core Python library in the shipment analytics workflow",
        "Identify which library to call for cleaning, maths, visualisation, and modelling",
        "Run a live test-drive demo for Pandas, NumPy, Plotly, Scikit-Fuzzy, and Statsmodels",
        "Use the tool recommender to route a logistics problem to the right department",
    ],
    "storage_bins": [
        "Understand why Python uses different types for text, numbers, and flags",
        "Store a supplier name, coil weight, and shipment status as the correct Python types",
        "Inspect variable types with `type()` and connect them to real logistics values",
        "Read live Python code that updates as you change the input controls",
    ],
    "shipping_manifest": [
        "Store a collection of shipment coils using a Python list",
        "Label each coil with attributes using a Python dictionary",
        "Add, update, and access items in both lists and dictionaries",
        "Explain when a list is better than a dictionary for shipment data",
    ],
    "quality_gate": [
        "Write an `if/else` decision rule that triggers a safety stock alert",
        "Package a reusable logistics rule inside a Python function",
        "Trace how Python chooses between branches based on delay values",
        "Call a custom function and interpret its return value in context",
    ],
    "warehouse_manager": [
        "Load a raw shipment CSV into a Pandas DataFrame with `pd.read_csv()`",
        "Clean messy data by stripping whitespace, converting types, and dropping duplicates",
        "Filter rows by condition and sort by date to build a reliable pipeline input",
        "Explain why each cleaning step matters for the models that come later",
    ],
    "command_center": [
        "Import Plotly Express as px and Plotly Graph Objects as go",
        "Choose the correct chart type for time-series, categorical, and distribution data",
        "Customise colours, labels, and templates with keyword arguments",
        "Pass a Plotly figure to Streamlit using st.plotly_chart()",
    ],
    "fast_calculator": [
        "Understand why NumPy arrays run faster than Python loops",
        "Apply broadcasting to calculate a surcharge across 10 000 coil weights in one line",
        "Use np.sum(), np.mean(), and np.std() to aggregate an entire column instantly",
        "Benchmark a Python loop against a NumPy vectorised operation",
    ],
    "intuition_engine": [
        "Shape a triangular fuzzy membership function using three parameters a, b, and c",
        "Interpret the membership grade of an observed shipment delay as a truth score",
        "Visualise the fuzzy confidence cloud and understand what widening it means",
        "Call `fuzz.trimf()` and `fuzz.interp_membership()` with the correct arguments",
    ],
    "quality_inspector": [
        "Compare OLS and Huber robust regression on the same noisy shipment data",
        "Understand why Huber regression downweights extreme outliers instead of removing them",
        "Label war-disruption spikes using `np.where()` and robust outlier weights",
        "Fit a Huber model with `sm.RLM()` and extract its predicted trend line",
    ],
    "future_predictor": [
        "Convert a Pandas date column into a proper time-series index",
        "Fit an ARIMA model to quantity discrepancy and generate a 14-day forecast",
        "Apply scenario sliders to simulate port strikes and demand surges",
        "Interpret confidence bands as a measure of model uncertainty around future estimates",
    ],
}

SOCRATIC_SEEDS = {

    "home": [
        "Which stage should Ain focus on first if she feels nervous about coding?",
        "How do the early grammar modules support the later fuzzy and robust modules?",
        "Which local source would help explain the curriculum more clearly?",
    ],
    "toolbox": [
        "Which library should I call first if my shipment file is messy?",
        "What starter function should I remember for charts versus cleaning?",
        "If I see an outlier spike, which department should I call and why?",
    ],
    "storage_bins": [
        "Why is a supplier name stored differently from a coil weight?",
        "What breaks if I store delay days as text instead of a number?",
        "How would Python know whether a shipment is confirmed or not?",
    ],
    "shipping_manifest": [
        "When should Ain use a list instead of a dictionary for shipment data?",
        "Why is a supplier name a good dictionary key?",
        "How does adding a new coil to the manifest change the Python object?",
    ],
    "quality_gate": [
        "What condition should trigger a safety stock alert in this lesson?",
        "Why is a function useful if Ain repeats the same logistics rule often?",
        "How does Python choose between the if and else branch here?",
    ],
    "warehouse_manager": [
        "Which Pandas step cleans the data before analysis begins?",
        "What would happen if Ain forgot to convert dates into datetimes?",
        "Why does filtering rows feel like asking the warehouse manager for only the relevant boxes?",
    ],
    "command_center": [
        "Which Plotly function would Ain call to draw a line chart comparing delay days over time?",
        "What is the difference between plotly.express and plotly.graph_objects?",
        "How does changing the template argument change the chart appearance?",
    ],
    "fast_calculator": [
        "Why is np.sum(weights) faster than sum(weights) for 10 000 values?",
        "What does broadcasting mean in NumPy and how does it apply to a surcharge calculation?",
        "How would Ain change the code to calculate the median weight instead of the mean?",
    ],
    "intuition_engine": [
        "How do I change the color of this membership chart in Python?",
        "What happens in the code if I move the peak b to the right?",
        "Why does `fuzz.interp_membership()` act like a function using my slider values?",
    ],
    "quality_inspector": [
        "What happens if I change the CSV column name for `war_disruption_index`?",
        "How do I call a Huber regressor in `statsmodels`?",
        "Why does `np.where()` replace a Python loop here?",
    ],
    "future_predictor": [
        "How does Pandas turn `shipment_date` into a real time-series index?",
        "What changes in Python if I extend the forecast horizon from 14 to 30 days?",
        "Why does the ARIMA helper loop through several model orders?",
    ],
}

QUIZ_CONTENT = {
    "toolbox": [
        {
            "category": "Tool Knowledge",
            "prompt": "Your shipment spike came from a port strike, but you want a steady trend that is less hijacked by that spike. Which department should you call?",
            "options": [
                "Statsmodels / Robust Regression",
                "Plotly / Interactive Charts",
                "Scikit-Fuzzy / Membership Functions",
            ],
            "answer": "Statsmodels / Robust Regression",
        },
        {
            "category": "Tool Knowledge",
            "prompt": "Which library is the Warehouse Manager that loads and cleans raw shipment CSV files?",
            "options": ["Pandas", "NumPy", "Plotly"],
            "answer": "Pandas",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which starter call would you use to load a shipment CSV into a DataFrame?",
            "options": [
                'pd.read_csv("shipments.csv")',
                'np.read_table("shipments.csv")',
                'px.load_csv("shipments.csv")',
            ],
            "answer": 'pd.read_csv("shipments.csv")',
        },
        {
            "category": "Python Syntax",
            "prompt": "If Ain wants an interactive chart from a DataFrame, which call shape is closest to the right department?",
            "options": [
                'px.line(shipment_frame, x="shipment_date", y="quantity_discrepancy")',
                'pd.line(shipment_frame, "shipment_date", "quantity_discrepancy")',
                'sm.line(shipment_frame, x="shipment_date", y="quantity_discrepancy")',
            ],
            "answer": 'px.line(shipment_frame, x="shipment_date", y="quantity_discrepancy")',
        },
    ],
    "storage_bins": [
        {
            "category": "Logistics Concept",
            "prompt": "Which Python type best fits a supplier name like `PT Steel Nusantara`?",
            "options": ["String", "Float", "Boolean"],
            "answer": "String",
        },
        {
            "category": "Logistics Concept",
            "prompt": "Which type best matches a coil weight such as `18.75` tons?",
            "options": ["Dictionary", "Float", "Boolean"],
            "answer": "Float",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which line stores a shipment-confirmed flag as a Boolean?",
            "options": [
                "shipment_confirmed = True",
                'shipment_confirmed = "True"',
                "shipment_confirmed = 1.0",
            ],
            "answer": "shipment_confirmed = True",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which function lets Ain inspect the type of a Python value?",
            "options": ["type(value)", "shape(value)", "value.type()"],
            "answer": "type(value)",
        },
    ],
    "shipping_manifest": [
        {
            "category": "Logistics Concept",
            "prompt": "Which structure is best for storing several coil IDs in order?",
            "options": ["List", "Dictionary", "Boolean"],
            "answer": "List",
        },
        {
            "category": "Logistics Concept",
            "prompt": "Which structure is best for linking a supplier name to a shipment quantity?",
            "options": ["Dictionary", "Float", "Tuple of booleans"],
            "answer": "Dictionary",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which line correctly adds a new coil ID to a Python list named `coil_manifest`?",
            "options": [
                'coil_manifest.append("COIL-107")',
                'coil_manifest.add("COIL-107")',
                'coil_manifest["COIL-107"] = True',
            ],
            "answer": 'coil_manifest.append("COIL-107")',
        },
        {
            "category": "Python Syntax",
            "prompt": "Which line correctly stores a supplier quantity in a dictionary?",
            "options": [
                'supplier_manifest["PT Meratus"] = 42',
                'supplier_manifest.append("PT Meratus", 42)',
                'supplier_manifest = ["PT Meratus": 42]',
            ],
            "answer": 'supplier_manifest["PT Meratus"] = 42',
        },
    ],
    "quality_gate": [
        {
            "category": "Logistics Concept",
            "prompt": "If delay days are greater than 5 in this module, what should happen?",
            "options": [
                "Trigger a safety stock alert",
                "Delete the shipment row",
                "Convert the delay into a string",
            ],
            "answer": "Trigger a safety stock alert",
        },
        {
            "category": "Logistics Concept",
            "prompt": "Why is a function useful for a safety stock rule?",
            "options": [
                "It stores many rows like a DataFrame",
                "It lets Ain reuse the same decision logic",
                "It draws charts automatically",
            ],
            "answer": "It lets Ain reuse the same decision logic",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which line begins a Python function definition?",
            "options": [
                "def safety_stock_alert(delay_days):",
                "function safety_stock_alert(delay_days):",
                "alert safety_stock_alert(delay_days):",
            ],
            "answer": "def safety_stock_alert(delay_days):",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which condition correctly checks whether delay days exceed 5?",
            "options": ["if delay_days > 5:", "if delay_days = 5:", "if greater(delay_days, 5)"],
            "answer": "if delay_days > 5:",
        },
    ],
    "warehouse_manager": [
        {
            "category": "Logistics Concept",
            "prompt": "What is the Warehouse Manager's main job in Ain's thesis workflow?",
            "options": [
                "Load, clean, and filter shipment tables",
                "Create fuzzy membership functions",
                "Ignore outliers with Huber loss",
            ],
            "answer": "Load, clean, and filter shipment tables",
        },
        {
            "category": "Logistics Concept",
            "prompt": "Why should duplicate shipment rows usually be removed before analysis?",
            "options": [
                "They can distort counts and totals",
                "They make Plotly orange by default",
                "They turn numbers into strings",
            ],
            "answer": "They can distort counts and totals",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which Pandas call loads a CSV file into a DataFrame?",
            "options": [
                'pd.read_csv("shipments.csv")',
                'pd.load_frame("shipments.csv")',
                'np.read_csv("shipments.csv")',
            ],
            "answer": 'pd.read_csv("shipments.csv")',
        },
        {
            "category": "Python Syntax",
            "prompt": "Which Pandas call is commonly used to remove duplicate rows?",
            "options": [
                "shipment_frame.drop_duplicates()",
                "shipment_frame.remove_copies()",
                "shipment_frame.unique_rows()",
            ],
            "answer": "shipment_frame.drop_duplicates()",
        },
    ],
    "command_center": [
        {
            "category": "Logistics Concept",
            "prompt": "Which chart type is best for showing how quantity discrepancy changes over time?",
            "options": ["Line chart", "Bar chart", "Scatter plot"],
            "answer": "Line chart",
        },
        {
            "category": "Logistics Concept",
            "prompt": "When should Ain use plotly.graph_objects instead of plotly.express?",
            "options": [
                "To fully control individual traces, shapes, and annotations",
                "To load data from a CSV file faster",
                "To replace NumPy in numerical calculations",
            ],
            "answer": "To fully control individual traces, shapes, and annotations",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which call draws an interactive line chart from a DataFrame in Plotly Express?",
            "options": [
                'px.line(df, x="shipment_date", y="quantity_discrepancy")',
                'go.Line(df, x="shipment_date", y="quantity_discrepancy")',
                'df.plot(x="shipment_date", y="quantity_discrepancy")',
            ],
            "answer": 'px.line(df, x="shipment_date", y="quantity_discrepancy")',
        },
        {
            "category": "Python Syntax",
            "prompt": "How do you display a Plotly figure inside a Streamlit app?",
            "options": ["st.plotly_chart(fig)", "fig.show()", "st.chart(fig)"],
            "answer": "st.plotly_chart(fig)",
        },
    ],
    "fast_calculator": [
        {
            "category": "Logistics Concept",
            "prompt": "Why does NumPy beat a Python loop for calculating total coil weight across 10 000 entries?",
            "options": [
                "It runs the operation in compiled C-level code on a contiguous memory block",
                "It automatically uses more CPU cores",
                "It skips values that are zero to save time",
            ],
            "answer": "It runs the operation in compiled C-level code on a contiguous memory block",
        },
        {
            "category": "Logistics Concept",
            "prompt": "What is broadcasting in NumPy?",
            "options": [
                "Applying a scalar operation to every element of an array without writing a loop",
                "Sending data to multiple servers simultaneously",
                "Converting a Python list to a NumPy array",
            ],
            "answer": "Applying a scalar operation to every element of an array without writing a loop",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which NumPy call calculates the total weight across all coils?",
            "options": ["np.sum(weights)", "np.total(weights)", "weights.sum_all()"],
            "answer": "np.sum(weights)",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which line applies a 5% surcharge to every coil weight using broadcasting?",
            "options": [
                "billable = weights * 1.05",
                "billable = [w * 1.05 for w in weights]",
                "billable = np.loop(weights, lambda w: w * 1.05)",
            ],
            "answer": "billable = weights * 1.05",
        },
    ],
    "intuition_engine": [
        {
            "category": "Logistics Math",
            "prompt": "If a shipment day lands exactly at the peak parameter b, what is the triangular membership grade?",
            "options": ["0.0", "0.5", "1.0"],
            "answer": "1.0",
        },
        {
            "category": "Logistics Math",
            "prompt": "What does widening the fuzzy confidence cloud primarily represent?",
            "options": [
                "More historical observations",
                "More uncertainty around the linguistic definition",
                "A steeper deterministic rule",
            ],
            "answer": "More uncertainty around the linguistic definition",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which scikit-fuzzy call creates the triangular membership curve from `a`, `b`, and `c`?",
            "options": [
                "fuzz.trimf(delay_universe, [a, b, c])",
                "fuzz.interp_membership(delay_universe, [a, b, c])",
                "fuzz.triangle(delay_universe, a, b, c)",
            ],
            "answer": "fuzz.trimf(delay_universe, [a, b, c])",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which function reads the membership grade of one observed delay value from the curve?",
            "options": [
                "fuzz.interp_membership(delay_universe, membership_curve, current_delay_days)",
                "fuzz.read_grade(current_delay_days)",
                "membership_curve.grade(current_delay_days)",
            ],
            "answer": "fuzz.interp_membership(delay_universe, membership_curve, current_delay_days)",
        },
    ],
    "quality_inspector": [
        {
            "category": "Logistics Math",
            "prompt": "Why does Huber regression react less aggressively to extreme war-spike outliers?",
            "options": [
                "It removes those points from the dataset",
                "It treats large residuals more linearly than OLS",
                "It increases the squared penalty on extreme points",
            ],
            "answer": "It treats large residuals more linearly than OLS",
        },
        {
            "category": "Logistics Math",
            "prompt": "If a point gets a low robust_outlier_weight, what should you infer?",
            "options": [
                "The point has high leverage in the robust fit",
                "The point is being downweighted as less trustworthy",
                "The point should be duplicated in the dataset",
            ],
            "answer": "The point is being downweighted as less trustworthy",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which `statsmodels` call correctly fits a Huber-style robust regression?",
            "options": [
                "sm.RLM(target, design_matrix, M=sm.robust.norms.HuberT(t=1.35)).fit()",
                'sm.OLS(target, design_matrix).fit("huber")',
                "sm.Huber(target, design_matrix).train()",
            ],
            "answer": "sm.RLM(target, design_matrix, M=sm.robust.norms.HuberT(t=1.35)).fit()",
            "required_for_unlock": True,
        },
        {
            "category": "Python Syntax",
            "prompt": "Which line most directly creates a column-wise conditional label without writing a Python `for` loop?",
            "options": [
                'shipment_frame["shock_label"] = np.where(shipment_frame["war_disruption_index"] > 0.8, "War-related outlier", "Baseline shipment")',
                'for row in shipment_frame: row["shock_label"] = "War-related outlier"',
                'shipment_frame.if war_disruption_index > 0.8 then "War-related outlier"',
            ],
            "answer": 'shipment_frame["shock_label"] = np.where(shipment_frame["war_disruption_index"] > 0.8, "War-related outlier", "Baseline shipment")',
        },
    ],
    "future_predictor": [
        {
            "category": "Logistics Math",
            "prompt": "In this dashboard, quantity discrepancy is defined as:",
            "options": [
                "received_quantity - ordered_quantity",
                "ordered_quantity - received_quantity",
                "delay_days / ordered_quantity",
            ],
            "answer": "ordered_quantity - received_quantity",
        },
        {
            "category": "Logistics Math",
            "prompt": "What do the shaded forecast bands communicate?",
            "options": [
                "Guaranteed shipment values",
                "The model's uncertainty around future estimates",
                "A robust regression weight map",
            ],
            "answer": "The model's uncertainty around future estimates",
        },
        {
            "category": "Python Syntax",
            "prompt": "Which Pandas line turns the shipment date column into real datetime values for time-series work?",
            "options": [
                'shipment_frame["shipment_date"] = pd.to_datetime(shipment_frame["shipment_date"])',
                'shipment_frame["shipment_date"] = pd.read_datetime("shipment_date")',
                'shipment_frame.to_time_series("shipment_date")',
            ],
            "answer": 'shipment_frame["shipment_date"] = pd.to_datetime(shipment_frame["shipment_date"])',
        },
        {
            "category": "Python Syntax",
            "prompt": "Which `statsmodels` call fits the ARIMA model used in this module?",
            "options": [
                "ARIMA.fit(scenario_series, order=(1, 1, 1))",
                "ARIMA(scenario_series, order=(1, 1, 1)).fit()",
                "scenario_series.fit_arima(order=(1, 1, 1))",
            ],
            "answer": "ARIMA(scenario_series, order=(1, 1, 1)).fit()",
        },
    ],
}
