from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import CERTIFICATION_LEVELS, MANIFEST_PATH, MODULE_SEQUENCE, PROGRESS_PATH, ensure_project_directories

LEGACY_STAGE_MAP = {
    "fuzzy": "intuition_engine",
    "robust": "quality_inspector",
    "forecast": "future_predictor",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_manifest() -> dict[str, Any]:
    return {
        "store": {
            "name": None,
            "display_name": "nebulous-core-sources",
        },
        "files": {},
        "last_synced_at": None,
        "status": "not_started",
        "message": "Waiting for first Gemini sync.",
    }


def default_progress() -> dict[str, Any]:
    return {
        "unlocked_module_index": 1,
        "completed_modules": [],
        "quiz_scores": {},
        "certification_level": CERTIFICATION_LEVELS[0],
        "last_updated": utc_now_iso(),
        "tutorial_shown": False,
    }


def load_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    ensure_project_directories()
    if not path.exists():
        save_json(path, fallback)
        return deepcopy(fallback)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        save_json(path, fallback)
        return deepcopy(fallback)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_project_directories()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def load_manifest() -> dict[str, Any]:
    return load_json(MANIFEST_PATH, default_manifest())


def save_manifest(manifest: dict[str, Any]) -> None:
    save_json(MANIFEST_PATH, manifest)


def load_progress() -> dict[str, Any]:
    return normalize_progress(load_json(PROGRESS_PATH, default_progress()))


def save_progress(progress: dict[str, Any]) -> None:
    progress = normalize_progress(progress)
    progress["last_updated"] = utc_now_iso()
    save_json(PROGRESS_PATH, progress)


def initialize_session_state(session_state: Any) -> None:
    progress = load_progress()
    manifest = load_manifest()
    session_state.setdefault("progress", progress)
    session_state.setdefault("manifest", manifest)
    session_state.setdefault("chat_messages", [])
    session_state.setdefault("tutor_input", "")
    session_state.setdefault("queued_tutor_prompt", None)
    session_state.setdefault("study_note_cache", {})
    session_state.setdefault("last_source_sync", manifest.get("last_synced_at"))
    session_state.setdefault("source_sync_bootstrapped", False)
    session_state.setdefault("source_sync_message", manifest.get("message"))
    session_state.setdefault("uploaded_csv_name", None)
    session_state.setdefault("uploaded_csv_bytes", None)
    session_state.setdefault("uploaded_dataset_status", "No uploaded dataset")
    session_state.setdefault("last_tutor_response", None)


def normalize_progress(progress: dict[str, Any]) -> dict[str, Any]:
    normalized = deepcopy(progress)
    completed_modules = set(normalized.get("completed_modules", []))

    mapped_legacy_modules = {LEGACY_STAGE_MAP[module] for module in completed_modules if module in LEGACY_STAGE_MAP}
    completed_modules.difference_update(set(LEGACY_STAGE_MAP.keys()))
    completed_modules.update(mapped_legacy_modules)

    furthest_stage_index = 0
    for legacy_target in mapped_legacy_modules:
        furthest_stage_index = max(furthest_stage_index, MODULE_SEQUENCE.index(legacy_target) + 1)
    for module_key in MODULE_SEQUENCE:
        if module_key in completed_modules:
            furthest_stage_index = max(furthest_stage_index, MODULE_SEQUENCE.index(module_key) + 1)
    if furthest_stage_index:
        completed_modules.update(MODULE_SEQUENCE[:furthest_stage_index])

    unlocked_index = 1
    for module_position, module_key in enumerate(MODULE_SEQUENCE, start=1):
        if module_key in completed_modules:
            unlocked_index = min(module_position + 1, len(MODULE_SEQUENCE))

    normalized["completed_modules"] = sorted(completed_modules)
    normalized["unlocked_module_index"] = max(1, unlocked_index)
    completed_stage_count = len([module_key for module_key in MODULE_SEQUENCE if module_key in completed_modules])
    certification_key = min(completed_stage_count, max(CERTIFICATION_LEVELS))
    normalized["certification_level"] = CERTIFICATION_LEVELS[certification_key]
    return normalized


def mark_module_completed(progress: dict[str, Any], module_key: str, score: int, passed: bool) -> dict[str, Any]:
    updated_progress = deepcopy(progress)
    updated_progress.setdefault("quiz_scores", {})
    updated_progress["quiz_scores"][module_key] = score
    completed_modules = set(updated_progress.get("completed_modules", []))
    if passed:
        completed_modules.add(module_key)
    updated_progress["completed_modules"] = sorted(completed_modules)
    updated_progress = normalize_progress(updated_progress)
    updated_progress["last_updated"] = utc_now_iso()
    return updated_progress
