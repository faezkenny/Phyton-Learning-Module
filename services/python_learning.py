from __future__ import annotations

from textwrap import dedent


def storage_bins_live_code(*, supplier_name: str, coil_weight: float, shipment_confirmed: bool) -> str:
    return dedent(
        f"""
        supplier_name = "{supplier_name}"
        coil_weight = {coil_weight:.2f}
        shipment_confirmed = {shipment_confirmed}

        print(type(supplier_name).__name__)       # str
        print(type(coil_weight).__name__)         # float
        print(type(shipment_confirmed).__name__)  # bool
        """
    ).strip()


def storage_bins_breakdown() -> list[dict[str, str]]:
    return [
        {
            "title": "Variables",
            "explanation": "A variable is like a labeled storage bin on the factory floor. The label tells Ain what the value means.",
            "code": 'supplier_name = "PT Steel Nusantara"\ncoil_weight = 18.75\nshipment_confirmed = True',
        },
        {
            "title": "Data Types",
            "explanation": "Python stores text, numbers, and yes/no decisions differently because each type does a different job.",
            "code": 'type("PT Steel Nusantara")\ntype(18.75)\ntype(True)',
        },
        {
            "title": "Logistics Meaning",
            "explanation": "Strings store names, floats store measured quantities, and booleans store operational status checks.",
            "code": 'supplier_name = "PT Meratus"\ncoil_weight = 21.4\nshipment_delayed = False',
        },
    ]


def shipping_manifest_live_code(*, coil_manifest: list[str], supplier_manifest: dict[str, float]) -> str:
    return dedent(
        f"""
        coil_manifest = {coil_manifest!r}
        supplier_manifest = {supplier_manifest!r}

        coil_manifest.append("COIL-NEW")
        supplier_manifest["PT Baru"] = 24.0
        """
    ).strip()


def shipping_manifest_breakdown() -> list[dict[str, str]]:
    return [
        {
            "title": "Lists",
            "explanation": "Lists are good when Ain just needs an ordered collection of shipment items like coil IDs.",
            "code": 'coil_manifest = ["COIL-101", "COIL-102", "COIL-103"]\ncoil_manifest.append("COIL-104")',
        },
        {
            "title": "Dictionaries",
            "explanation": "Dictionaries are useful when Ain wants a key and a value, like supplier name to quantity.",
            "code": 'supplier_manifest = {"PT Meratus": 42, "PT Cakra": 38}\nsupplier_manifest["PT Baru"] = 24',
        },
        {
            "title": "Factory Analogy",
            "explanation": "Use a list when you are counting boxes in order. Use a dictionary when you need a label on each box.",
            "code": 'first_coil = coil_manifest[0]\npt_meratus_quantity = supplier_manifest["PT Meratus"]',
        },
    ]


def quality_gate_live_code(*, delay_days: int, threshold_days: int, safety_stock_alert: bool) -> str:
    return dedent(
        f"""
        def trigger_safety_stock(delay_days: int, threshold_days: int = {threshold_days}) -> bool:
            if delay_days > threshold_days:
                return True
            return False

        delay_days = {delay_days}
        safety_stock_alert = trigger_safety_stock(delay_days)
        print(safety_stock_alert)  # {safety_stock_alert}
        """
    ).strip()


def quality_gate_breakdown() -> list[dict[str, str]]:
    return [
        {
            "title": "Conditionals",
            "explanation": "An `if/else` block is the quality gate: if a shipment is too late, trigger the alert; otherwise continue normally.",
            "code": 'if delay_days > 5:\n    alert = True\nelse:\n    alert = False',
        },
        {
            "title": "Functions",
            "explanation": "A function is a repeatable work order. Ain writes the rule once and can call it again on many shipments.",
            "code": 'def trigger_safety_stock(delay_days):\n    return delay_days > 5',
        },
        {
            "title": "Logistics Meaning",
            "explanation": "This is the point where Python stops being storage and starts making decisions that matter for operations.",
            "code": 'safety_stock_alert = trigger_safety_stock(delay_days=7)',
        },
    ]


def warehouse_manager_live_code(*, before_rows: int, after_rows: int) -> str:
    return dedent(
        f"""
        import pandas as pd

        shipment_frame = pd.read_csv("shipments.csv")
        shipment_frame["shipment_date"] = pd.to_datetime(shipment_frame["shipment_date"], errors="coerce")
        shipment_frame["delay_days"] = pd.to_numeric(shipment_frame["delay_days"], errors="coerce").fillna(0.0)
        shipment_frame = shipment_frame.drop_duplicates().sort_values("shipment_date").reset_index(drop=True)

        print("before", {before_rows})
        print("after", {after_rows})
        """
    ).strip()


def warehouse_manager_breakdown() -> list[dict[str, str]]:
    return [
        {
            "title": "DataFrames",
            "explanation": "A DataFrame is the warehouse ledger. Each row is one shipment and each column is one field Ain can clean or analyze.",
            "code": 'shipment_frame = pd.read_csv("shipments.csv")\nshipment_frame.head()',
        },
        {
            "title": "Cleaning Steps",
            "explanation": "The warehouse manager converts dates, fixes numeric columns, removes duplicates, and sorts the table into a reliable order.",
            "code": 'shipment_frame["shipment_date"] = pd.to_datetime(shipment_frame["shipment_date"])\nshipment_frame = shipment_frame.drop_duplicates()',
        },
        {
            "title": "Filtering",
            "explanation": "Once the table is clean, Ain can filter to only the rows she cares about, like delayed shipments or one supplier.",
            "code": 'late_shipments = shipment_frame[shipment_frame["delay_days"] > 5]',
        },
    ]


def fuzzy_live_code(
    *,
    a: float,
    b: float,
    c: float,
    current_delay_days: float,
    uncertainty_width: float,
    linguistic_label: str,
    membership_grade: float,
) -> str:
    return dedent(
        f"""
        import numpy as np
        import skfuzzy as fuzz

        linguistic_label = "{linguistic_label}"
        a = {a:.2f}
        b = {b:.2f}
        c = {c:.2f}
        current_delay_days = {current_delay_days:.2f}
        uncertainty_width = {uncertainty_width:.2f}

        delay_universe = np.linspace(0.0, 14.0, 500)
        membership_curve = fuzz.trimf(delay_universe, [a, b, c])
        confidence_curve = fuzz.trimf(
            delay_universe,
            [max(0.0, a - uncertainty_width), b, c + uncertainty_width],
        )
        membership_grade = fuzz.interp_membership(
            delay_universe,
            membership_curve,
            current_delay_days,
        )

        print(linguistic_label, round(membership_grade, 3))  # {membership_grade:.3f}
        """
    ).strip()


def fuzzy_breakdown(*, source_label: str, linguistic_label: str) -> list[dict[str, str]]:
    return [
        {
            "title": "DataFrames",
            "explanation": (
                "We still use a Pandas DataFrame to hold shipment records before fuzzy logic enters the picture. "
                f"In this app, the active shipment source is `{source_label}`, and columns like `delay_days` give us the numeric input for the fuzzy rule."
            ),
            "code": 'shipment_frame = pd.read_csv("shipments.csv")\ncurrent_delay_days = shipment_frame.loc[0, "delay_days"]',
        },
        {
            "title": "Loops / Conditionals",
            "explanation": (
                "Python often lets us avoid explicit loops by working with whole arrays at once. "
                "Here the fuzzy membership formula behaves like a conditional rule: values before `a` become 0, values near `b` rise toward 1, and values after `c` fall back to 0."
            ),
            "code": 'if current_delay_days < a:\n    membership_grade = 0.0\nelif current_delay_days == b:\n    membership_grade = 1.0\nelse:\n    membership_grade = fuzz.interp_membership(delay_universe, membership_curve, current_delay_days)',
        },
        {
            "title": "Library Calls",
            "explanation": (
                f"`fuzz.trimf()` from scikit-fuzzy builds the triangular curve for `{linguistic_label}`, and "
                "`fuzz.interp_membership()` asks where one observed value sits on that curve."
            ),
            "code": 'membership_curve = fuzz.trimf(delay_universe, [a, b, c])\nmembership_grade = fuzz.interp_membership(delay_universe, membership_curve, current_delay_days)',
        },
    ]


def robust_live_code(
    *,
    huber_threshold: float,
    engage_robust_mode: bool,
    average_shock_weight: float,
) -> str:
    return dedent(
        f"""
        import numpy as np
        import pandas as pd
        import statsmodels.api as sm

        shipment_frame = pd.read_csv("shipments.csv")
        shipment_frame["shock_label"] = np.where(
            shipment_frame["war_disruption_index"] > 0.8,
            "War-related outlier",
            "Baseline shipment",
        )

        x_index = np.arange(len(shipment_frame), dtype=float)
        design_matrix = sm.add_constant(
            np.column_stack([x_index, shipment_frame["war_disruption_index"].to_numpy(dtype=float)])
        )
        target = shipment_frame["received_quantity"].to_numpy(dtype=float)

        huber_threshold = {huber_threshold:.2f}
        ols_result = sm.OLS(target, design_matrix).fit()
        robust_result = sm.RLM(
            target,
            design_matrix,
            M=sm.robust.norms.HuberT(t=huber_threshold),
        ).fit()

        engage_robust_mode = {engage_robust_mode}
        active_prediction = robust_result.predict(design_matrix) if engage_robust_mode else ols_result.predict(design_matrix)
        shipment_frame["robust_outlier_weight"] = robust_result.weights
        print(round(shipment_frame.loc[shipment_frame["shock_label"] == "War-related outlier", "robust_outlier_weight"].mean(), 3))  # {average_shock_weight:.3f}
        """
    ).strip()


def robust_breakdown(*, source_label: str) -> list[dict[str, str]]:
    return [
        {
            "title": "DataFrames",
            "explanation": (
                f"We load the shipment CSV into a Pandas DataFrame from `{source_label}` so each row represents one dated shipment record. "
                "That makes it easy to create new columns like `shock_label` and `robust_outlier_weight`."
            ),
            "code": 'shipment_frame = pd.read_csv("shipments.csv")\nshipment_frame["shock_label"] = np.where(shipment_frame["war_disruption_index"] > 0.8, "War-related outlier", "Baseline shipment")',
        },
        {
            "title": "Loops / Conditionals",
            "explanation": (
                "Instead of writing a Python `for` loop over every row, NumPy and Pandas apply the disruption rule to the whole column at once. "
                "The `np.where()` call is a vectorized conditional: if disruption is above 0.8, mark it as a war-related outlier."
            ),
            "code": 'shipment_frame["shock_label"] = np.where(shipment_frame["war_disruption_index"] > 0.8, "War-related outlier", "Baseline shipment")',
        },
        {
            "title": "Library Calls",
            "explanation": (
                "`sm.OLS(...).fit()` gives the baseline regression, while `sm.RLM(..., M=sm.robust.norms.HuberT(...)).fit()` "
                "switches to a robust model that downweights extreme residuals."
            ),
            "code": 'ols_result = sm.OLS(target, design_matrix).fit()\nrobust_result = sm.RLM(target, design_matrix, M=sm.robust.norms.HuberT(t=huber_threshold)).fit()',
        },
    ]


def forecast_live_code(
    *,
    forecast_horizon: int,
    discrepancy_multiplier: float,
    delay_multiplier: float,
    selected_order: tuple[int, int, int],
    final_forecast_mean: float,
) -> str:
    return dedent(
        f"""
        import pandas as pd
        from statsmodels.tsa.arima.model import ARIMA

        shipment_frame = pd.read_csv("shipments.csv")
        shipment_frame["shipment_date"] = pd.to_datetime(shipment_frame["shipment_date"])
        shipment_frame["quantity_discrepancy"] = (
            shipment_frame["ordered_quantity"] - shipment_frame["received_quantity"]
        )

        discrepancy_multiplier = {discrepancy_multiplier:.2f}
        delay_multiplier = {delay_multiplier:.2f}
        scenario_series = (
            shipment_frame["quantity_discrepancy"] * discrepancy_multiplier
            + shipment_frame["delay_days"] * (delay_multiplier - 1.0) * 3.0
        )
        scenario_series.index = shipment_frame["shipment_date"]

        model = ARIMA(scenario_series, order={selected_order}).fit()
        forecast = model.get_forecast(steps={forecast_horizon})
        forecast_mean = forecast.predicted_mean
        print(round(float(forecast_mean.iloc[-1]), 2))  # {final_forecast_mean:.2f}
        """
    ).strip()


def forecast_breakdown(*, source_label: str) -> list[dict[str, str]]:
    return [
        {
            "title": "DataFrames",
            "explanation": (
                f"Pandas is doing the heavy lifting again. We load `{source_label}`, convert `shipment_date` into real datetimes, "
                "and build a `quantity_discrepancy` column that the forecast model can learn from."
            ),
            "code": 'shipment_frame = pd.read_csv("shipments.csv")\nshipment_frame["shipment_date"] = pd.to_datetime(shipment_frame["shipment_date"])\nshipment_frame["quantity_discrepancy"] = shipment_frame["ordered_quantity"] - shipment_frame["received_quantity"]',
        },
        {
            "title": "Loops / Conditionals",
            "explanation": (
                "The ARIMA helper in this app uses a Python loop to try several model orders until one fits cleanly. "
                "That is a beginner-friendly pattern: loop through candidates, try a model, and stop when one works."
            ),
            "code": 'candidate_orders = [(1, 1, 1), (2, 1, 1), (1, 0, 1)]\nfor order in candidate_orders:\n    try:\n        fitted_model = ARIMA(series, order=order).fit()\n        break\n    except Exception:\n        continue',
        },
        {
            "title": "Library Calls",
            "explanation": (
                "`ARIMA(...).fit()` trains the time-series model, and `get_forecast()` returns both the forecast mean and the uncertainty bands."
            ),
            "code": 'model = ARIMA(scenario_series, order=(1, 1, 1)).fit()\nforecast = model.get_forecast(steps=14)\nconfidence_interval = forecast.conf_int()',
        },
    ]
