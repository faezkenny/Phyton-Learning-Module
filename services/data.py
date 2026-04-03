from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .config import DATA_DIR, REQUIRED_SHIPMENT_COLUMNS, SOURCES_DIR


@dataclass
class DatasetBundle:
    dataframe: pd.DataFrame
    source_label: str
    source_path: str | None
    warnings: list[str]


def enrich_shipment_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    enriched = dataframe.copy()
    enriched["shipment_date"] = pd.to_datetime(enriched["shipment_date"])
    enriched = enriched.sort_values("shipment_date").reset_index(drop=True)
    enriched["ordered_quantity"] = pd.to_numeric(enriched["ordered_quantity"], errors="coerce")
    enriched["received_quantity"] = pd.to_numeric(enriched["received_quantity"], errors="coerce")
    enriched["delay_days"] = pd.to_numeric(enriched["delay_days"], errors="coerce")
    nan_delay_count = enriched["delay_days"].isna().sum()
    if nan_delay_count > 0:  # Fix #7: warn instead of silently filling
        import streamlit as _st
        try:
            _st.warning(f"{nan_delay_count} rows have missing delay_days and were filled with 0. Fuzzy and Huber models may be affected.")
        except Exception:
            pass  # safety guard if called outside Streamlit context
    enriched["delay_days"] = enriched["delay_days"].fillna(0.0)

    if "war_disruption_index" not in enriched:
        enriched["war_disruption_index"] = np.clip(enriched["delay_days"] / 10.0, 0.0, 1.0)
    if "port_congestion_index" not in enriched:
        rolling_delay = enriched["delay_days"].rolling(window=5, min_periods=1).mean()
        enriched["port_congestion_index"] = np.clip(rolling_delay / 8.0, 0.0, 1.0)
    if "supplier_risk_score" not in enriched:
        discrepancy_ratio = (
            (enriched["ordered_quantity"] - enriched["received_quantity"])
            / enriched["ordered_quantity"].replace(0, np.nan)
        ).fillna(0.0)
        enriched["supplier_risk_score"] = np.clip(0.45 + discrepancy_ratio, 0.0, 1.0)

    enriched["quantity_discrepancy"] = enriched["ordered_quantity"] - enriched["received_quantity"]
    enriched["fulfillment_ratio"] = (
        enriched["received_quantity"] / enriched["ordered_quantity"].replace(0, np.nan)
    ).fillna(0.0)
    enriched["shipment_volatility"] = (
        enriched["quantity_discrepancy"].rolling(window=7, min_periods=2).std().fillna(0.0)
    )
    enriched["delay_severity"] = np.clip(enriched["delay_days"] / 10.0, 0.0, 1.0)
    enriched["shock_label"] = np.where(
        enriched["war_disruption_index"] > 0.7,
        "War-related outlier",
        "Baseline shipment",
    )
    return enriched


def generate_synthetic_shipments(num_days: int = 90, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    shipment_date = pd.date_range(end=pd.Timestamp.today().normalize(), periods=num_days, freq="D")
    time_index = np.arange(num_days)
    ordered_quantity = 112 + 0.22 * time_index + 9 * np.sin(time_index / 6.0) + rng.normal(0, 3, num_days)
    ordered_quantity = np.round(np.clip(ordered_quantity, 92, None), 2)

    war_disruption_index = np.clip(0.22 + 0.12 * np.sin(time_index / 10.0) + rng.normal(0, 0.05, num_days), 0, 1)
    port_congestion_index = np.clip(0.35 + 0.18 * np.cos(time_index / 9.0) + rng.normal(0, 0.04, num_days), 0, 1)
    supplier_risk_score = np.clip(0.4 + 0.2 * np.sin(time_index / 14.0) + rng.normal(0, 0.03, num_days), 0, 1)

    outlier_positions = np.array([19, 46, 67])
    war_disruption_index[outlier_positions] = np.array([0.96, 0.99, 0.93])
    port_congestion_index[outlier_positions] = np.array([0.74, 0.81, 0.77])

    discrepancy_ratio = 0.06 + 0.18 * war_disruption_index + 0.07 * port_congestion_index
    received_quantity = ordered_quantity * (1.0 - discrepancy_ratio) + rng.normal(0, 2.6, num_days)
    received_quantity[outlier_positions] = ordered_quantity[outlier_positions] * np.array([0.63, 0.54, 0.58])
    received_quantity = np.round(np.clip(received_quantity, 30, None), 2)

    delay_days = 0.9 + 2.7 * war_disruption_index + 1.4 * port_congestion_index + rng.normal(0, 0.7, num_days)
    delay_days[outlier_positions] += np.array([3.5, 4.3, 4.0])
    delay_days = np.round(np.clip(delay_days, 0, None), 2)

    synthetic = pd.DataFrame(
        {
            "shipment_date": shipment_date,
            "ordered_quantity": ordered_quantity,
            "received_quantity": received_quantity,
            "delay_days": delay_days,
            "war_disruption_index": np.round(war_disruption_index, 3),
            "port_congestion_index": np.round(port_congestion_index, 3),
            "supplier_risk_score": np.round(supplier_risk_score, 3),
        }
    )
    return enrich_shipment_data(synthetic)


def validate_shipment_dataframe(dataframe: pd.DataFrame) -> tuple[bool, str | None]:
    missing_columns = REQUIRED_SHIPMENT_COLUMNS - set(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        return False, f"Missing required columns: {missing}"
    return True, None


def _read_csv(csv_bytes: bytes | None = None, path: Path | None = None) -> pd.DataFrame:
    if csv_bytes is not None:
        return pd.read_csv(io.BytesIO(csv_bytes))
    if path is None:
        raise ValueError("A path or CSV bytes payload is required.")
    return pd.read_csv(path)


def discover_local_csv_paths() -> Iterable[Path]:
    seen_paths: set[Path] = set()
    # Fix #6: consolidated rglob to avoid duplicate discovery
    for path in [*DATA_DIR.glob("*.csv"), *SOURCES_DIR.rglob("*.csv")]:
        if path.is_file() and path not in seen_paths:
            seen_paths.add(path)
            yield path


def load_shipment_dataset(uploaded_csv_bytes: bytes | None = None, uploaded_name: str | None = None) -> DatasetBundle:
    warnings: list[str] = []

    if uploaded_csv_bytes is not None:
        try:
            uploaded_dataframe = _read_csv(csv_bytes=uploaded_csv_bytes)
            is_valid, validation_message = validate_shipment_dataframe(uploaded_dataframe)
            if is_valid:
                return DatasetBundle(
                    dataframe=enrich_shipment_data(uploaded_dataframe),
                    source_label=f"Uploaded CSV: {uploaded_name or 'session-upload.csv'}",
                    source_path=uploaded_name,
                    warnings=warnings,
                )
            warnings.append(f"Uploaded CSV ignored. {validation_message}")
        except Exception as exc:  # pragma: no cover - user supplied files are unpredictable
            warnings.append(f"Uploaded CSV could not be read: {exc}")

    for candidate_path in discover_local_csv_paths():
        try:
            local_dataframe = _read_csv(path=candidate_path)
            is_valid, validation_message = validate_shipment_dataframe(local_dataframe)
            if not is_valid:
                warnings.append(f"{candidate_path.name} skipped. {validation_message}")
                continue
            return DatasetBundle(
                dataframe=enrich_shipment_data(local_dataframe),
                source_label=f"Local CSV: {candidate_path.name}",
                source_path=str(candidate_path),
                warnings=warnings,
            )
        except Exception as exc:  # pragma: no cover - local files can still be malformed
            warnings.append(f"{candidate_path.name} skipped. Could not read CSV: {exc}")

    warnings.append(
        "No valid shipment CSV was found in data/ or sources/. Using the built-in 90-day steel-coil demo dataset."
    )
    return DatasetBundle(
        dataframe=generate_synthetic_shipments(),
        source_label="Synthetic 90-day demo dataset",
        source_path=None,
        warnings=warnings,
    )

