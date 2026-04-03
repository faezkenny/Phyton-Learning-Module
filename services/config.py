from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT_DIR / "sources"
DATA_DIR = ROOT_DIR / "data"
PAGES_DIR = ROOT_DIR / "pages"
STORAGE_DIR = ROOT_DIR / ".app_storage"
MANIFEST_PATH = ROOT_DIR / "manifest.json"
PROGRESS_PATH = STORAGE_DIR / "progress.json"
STYLE_PATH = ROOT_DIR / "styles.css"
FIRST_TIME_TUTORIAL_PATH = ROOT_DIR / "FIRST_TIME_TUTORIAL.md"
STREAMLIT_CONFIG_PATH = ROOT_DIR / ".streamlit" / "config.toml"

BACKGROUND_COLOR = "#F8FAFC"
TEXT_COLOR = "#1E293B"
ACCENT_COLOR = "#F97316"
MUTED_TEXT_COLOR = "#64748B"
CARD_COLOR = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
PLOTLY_TEMPLATE = "plotly_white"

MODULE_SEQUENCE = [
    "storage_bins",
    "shipping_manifest",
    "quality_gate",
    "warehouse_manager",
    "command_center",
    "fast_calculator",
    "intuition_engine",
    "quality_inspector",
    "future_predictor",
]
MODULE_LABELS = {
    "home": "Mission Control",
    "toolbox": "The Analyst's Toolbox",
    "storage_bins": "Module 1: Storage Bins",
    "shipping_manifest": "Module 2: The Manifest",
    "quality_gate": "Module 3: The Quality Gate",
    "warehouse_manager": "Module 4: The Warehouse Manager",
    "command_center": "Module 5: The Command Center",
    "fast_calculator": "Module 6: The Fast Calculator",
    "intuition_engine": "Module 7: The Intuition Engine",
    "quality_inspector": "Module 8: The Quality Inspector",
    "future_predictor": "Module 9: The Future Predictor",
}
SOURCE_SUBDIRECTORIES = {
    "shared",
    "toolbox",
    "storage_bins",
    "shipping_manifest",
    "quality_gate",
    "warehouse_manager",
    "intuition_engine",
    "quality_inspector",
    "future_predictor",
    "fuzzy",
    "robust",
    "forecast",
}
SUPPORTED_SOURCE_SUFFIXES = {".pdf", ".csv", ".txt", ".md"}
REQUIRED_SHIPMENT_COLUMNS = {
    "shipment_date",
    "ordered_quantity",
    "received_quantity",
    "delay_days",
}
OPTIONAL_SHIPMENT_COLUMNS = {
    "war_disruption_index",
    "port_congestion_index",
    "supplier_risk_score",
}
CERTIFICATION_LEVELS = {
    0: "Level 0: Cadet",
    1: "Level 1: Storage Apprentice",
    2: "Level 2: Manifest Keeper",
    3: "Level 3: Gate Operator",
    4: "Level 4: Warehouse Analyst",
    5: "Level 5: Intuition Modeler",
    6: "Level 6: Robust Navigator",
    7: "Level 7: Fuzzy-Robust Architect",
}
GEMINI_MODEL = "gemini-2.5-pro"
KIMI_MODEL = "kimi-k2.5"
MOONSHOT_BASE_URL = "https://api.moonshot.ai/v1"


def ensure_project_directories() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    for subdirectory in SOURCE_SUBDIRECTORIES:
        (SOURCES_DIR / subdirectory).mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / ".streamlit").mkdir(parents=True, exist_ok=True)
