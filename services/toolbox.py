from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolboxDepartment:
    key: str
    name: str
    icon: str
    factory_role: str
    thesis_reason: str
    starter_call: str
    keywords: tuple[str, ...]


TOOLBOX_DEPARTMENTS: dict[str, ToolboxDepartment] = {
    "pandas": ToolboxDepartment(
        key="pandas",
        name="Pandas",
        icon="WH",
        factory_role="The Warehouse Manager",
        thesis_reason="Sorting, cleaning, filtering, and reshaping raw shipment CSV files before modeling starts.",
        starter_call='pd.read_csv("shipments.csv")',
        keywords=("csv", "excel", "clean", "filter", "missing", "table", "rows", "columns", "dataframe", "merge"),
    ),
    "numpy": ToolboxDepartment(
        key="numpy",
        name="NumPy",
        icon="PE",
        factory_role="The Precision Engineer",
        thesis_reason="Handling arrays, vector math, averages, and fast numeric transformations for coil-weight calculations.",
        starter_call="np.array([112.0, 108.5, 115.2])",
        keywords=("array", "matrix", "vector", "math", "average", "weights", "numeric", "calculation"),
    ),
    "plotly": ToolboxDepartment(
        key="plotly",
        name="Plotly",
        icon="CC",
        factory_role="The Command Center",
        thesis_reason="Turning shipment tables into interactive charts for thesis storytelling and exploration.",
        starter_call='px.line(shipment_frame, x="shipment_date", y="quantity_discrepancy")',
        keywords=("graph", "chart", "visual", "plot", "dashboard", "interactive", "presentation"),
    ),
    "scikit-fuzzy": ToolboxDepartment(
        key="scikit-fuzzy",
        name="Scikit-Fuzzy",
        icon="IS",
        factory_role="The Intuition Specialist",
        thesis_reason="Converting crisp numbers like delay days into linguistic states such as Arriving Soon or Critical Delay.",
        starter_call="fuzz.trimf(delay_universe, [a, b, c])",
        keywords=("fuzzy", "membership", "linguistic", "delay", "soon", "critical", "uncertainty", "truth"),
    ),
    "statsmodels": ToolboxDepartment(
        key="statsmodels",
        name="Statsmodels",
        icon="QI",
        factory_role="The Quality Inspector",
        thesis_reason="Finding trends, checking outliers, and keeping forecasts robust when war spikes or port strikes hit the data.",
        starter_call="sm.RLM(target, design_matrix, M=sm.robust.norms.HuberT()).fit()",
        keywords=("outlier", "spike", "regression", "forecast", "trend", "robust", "arima", "steady", "port strike"),
    ),
}


def heuristic_tool_recommendation(problem_text: str) -> dict[str, str]:
    lowered_problem = problem_text.lower().strip()
    if not lowered_problem:
        department = TOOLBOX_DEPARTMENTS["pandas"]
        return {
            "tool_key": department.key,
            "library": department.name,
            "factory_role": department.factory_role,
            "starter_call": department.starter_call,
            "why": "Most analysis workflows begin by loading and cleaning the shipment data first.",
        }

    best_department = TOOLBOX_DEPARTMENTS["pandas"]
    best_score = -1
    for department in TOOLBOX_DEPARTMENTS.values():
        score = sum(1 for keyword in department.keywords if keyword in lowered_problem)
        if score > best_score:
            best_score = score
            best_department = department

    return {
        "tool_key": best_department.key,
        "library": best_department.name,
        "factory_role": best_department.factory_role,
        "starter_call": best_department.starter_call,
        "why": best_department.thesis_reason,
    }
