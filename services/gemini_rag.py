"""Gemini RAG service — grounded evidence retrieval for the Socratic tutor."""
from __future__ import annotations

import hashlib
import mimetypes
import os
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import GEMINI_MODEL, SOURCES_DIR, SUPPORTED_SOURCE_SUFFIXES
from .storage import load_manifest, save_manifest, utc_now_iso

# Allow override via environment variable for deployment flexibility (#3)
_GEMINI_MODEL = os.getenv("GEMINI_MODEL", GEMINI_MODEL)


@dataclass
class SourceFileRecord:
    relative_path: str
    absolute_path: Path
    module_tag: str
    mime_type: str
    sha256: str


@dataclass
class SyncResult:
    ok: bool
    status: str
    message: str
    store_name: str | None
    tracked_files: int
    uploaded_files: int
    deleted_files: int


class GeminiRAGService:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if not self.available:
            return None
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _metadata_items(self, record: SourceFileRecord) -> list[dict[str, Any]]:
        return [
            {"key": "module", "string_value": record.module_tag},
            {"key": "source_path", "string_value": record.relative_path},
            {"key": "sha256", "string_value": record.sha256},
            {"key": "file_type", "string_value": record.mime_type},
        ]

    def scan_sources(self) -> list[SourceFileRecord]:
        if not SOURCES_DIR.exists():
            return []

        source_records: list[SourceFileRecord] = []
        for path in sorted(SOURCES_DIR.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in SUPPORTED_SOURCE_SUFFIXES:
                continue
            relative_path = path.relative_to(SOURCES_DIR.parent).as_posix()
            path_parts = path.relative_to(SOURCES_DIR).parts
            module_tag = "shared"
            if len(path_parts) > 1:
                raw_module_tag = path_parts[0]
                module_aliases = {
                    "fuzzy": "intuition_engine",
                    "robust": "quality_inspector",
                    "forecast": "future_predictor",
                }
                if raw_module_tag in {
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
                }:
                    module_tag = module_aliases.get(raw_module_tag, raw_module_tag)
            mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            source_records.append(
                SourceFileRecord(
                    relative_path=relative_path,
                    absolute_path=path,
                    module_tag=module_tag,
                    mime_type=mime_type,
                    sha256=self._sha256_for_path(path),
                )
            )
        return source_records

    def sync_sources(self, force: bool = False) -> SyncResult:
        manifest = load_manifest()
        source_records = self.scan_sources()

        if not self.available:
            manifest["status"] = "missing_api_key"
            manifest["message"] = "Set GEMINI_API_KEY to enable citation-backed local retrieval."
            save_manifest(manifest)
            return SyncResult(False, manifest["status"], manifest["message"], None, len(source_records), 0, 0)

        if not source_records:
            manifest["status"] = "empty_sources"
            manifest["message"] = (
                "The /sources folder is empty. Add PDFs or CSVs to sources/shared and any module folder "
                "such as sources/storage_bins, sources/warehouse_manager, or sources/intuition_engine to enable retrieval."
            )
            save_manifest(manifest)
            return SyncResult(True, manifest["status"], manifest["message"], manifest["store"]["name"], 0, 0, 0)

        client = self._get_client()
        store_name = manifest.get("store", {}).get("name")
        if not store_name:
            store = client.file_search_stores.create(config={"display_name": "nebulous-core-sources"})
            store_name = store.name
            manifest["store"] = {"name": store_name, "display_name": getattr(store, "display_name", "nebulous-core-sources")}

        existing_documents = self._list_documents(store_name)
        tracked_files = manifest.setdefault("files", {})
        current_paths = {record.relative_path for record in source_records}
        uploaded_files = 0
        deleted_files = 0

        for stale_path in list(tracked_files):
            if stale_path in current_paths:
                continue
            stale_document_name = tracked_files[stale_path].get("document_name")
            if stale_document_name:
                self._delete_document(stale_document_name)
                deleted_files += 1
            tracked_files.pop(stale_path, None)

        for record in source_records:
            existing_entry = tracked_files.get(record.relative_path, {})
            existing_document_name = existing_entry.get("document_name")
            existing_sha = existing_entry.get("sha256")

            if (
                not force
                and existing_document_name
                and existing_sha == record.sha256
                and existing_document_name in existing_documents
            ):
                continue

            if existing_document_name:
                self._delete_document(existing_document_name)
                deleted_files += 1

            raw_display_name = Path(record.relative_path).name
            ascii_display_name = unicodedata.normalize("NFKD", raw_display_name).encode("ascii", "ignore").decode("ascii")
            operation = client.file_search_stores.upload_to_file_search_store(
                file=str(record.absolute_path),
                file_search_store_name=store_name,
                config={
                    "display_name": ascii_display_name or raw_display_name[:80],
                    "custom_metadata": self._metadata_items(record),
                },
            )
            self._wait_for_operation(client, operation)
            uploaded_files += 1

        refreshed_documents = self._list_documents(store_name)
        for record in source_records:
            matched_document = self._match_document(refreshed_documents, record.relative_path, record.sha256)
            tracked_files[record.relative_path] = {
                "sha256": record.sha256,
                "module": record.module_tag,
                "mime_type": record.mime_type,
                "document_name": matched_document.get("name") if matched_document else None,
                "display_name": matched_document.get("display_name") if matched_document else record.absolute_path.name,
                "indexed_at": utc_now_iso(),
            }

        manifest["status"] = "ready"
        manifest["message"] = f"Gemini RAG is ready. {len(source_records)} source files indexed."
        manifest["last_synced_at"] = utc_now_iso()
        save_manifest(manifest)
        return SyncResult(True, "ready", manifest["message"], store_name, len(source_records), uploaded_files, deleted_files)

    def retrieve_grounded_notes(self, query: str, module_key: str, prompt_prefix: str | None = None) -> dict[str, Any]:
        manifest = load_manifest()
        store_name = manifest.get("store", {}).get("name")
        if not self.available:
            return {
                "ok": False,
                "message": "Gemini RAG is unavailable. Add GEMINI_API_KEY to enable local source retrieval.",
                "answer": None,
                "citations": [],
            }
        if not store_name:
            return {
                "ok": False,
                "message": "No Gemini file-search store exists yet. Add source files and run sync first.",
                "answer": None,
                "citations": [],
            }

        client = self._get_client()
        from google.genai import types

        metadata_filter = None
        if module_key in {
            "toolbox",
            "storage_bins",
            "shipping_manifest",
            "quality_gate",
            "warehouse_manager",
            "intuition_engine",
            "quality_inspector",
            "future_predictor",
        }:
            metadata_filter = f'module="{module_key}" OR module="shared"'

        contents = query if not prompt_prefix else f"{prompt_prefix}\n\nUser task: {query}"
        response = client.models.generate_content(
            model=_GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        file_search=types.FileSearch(
                            file_search_store_names=[store_name],
                            metadata_filter=metadata_filter,
                        )
                    )
                ]
            ),
        )

        answer_text = getattr(response, "text", "") or ""
        citations = self._normalize_citations(response)
        return {
            "ok": True,
            "message": "Retrieved grounded notes from local sources.",
            "answer": answer_text,
            "citations": citations,
        }

    def build_study_notes(self, module_key: str) -> dict[str, Any]:
        module_descriptions = {
            "toolbox": "Summarize the local source material that explains the roles of Pandas, NumPy, Plotly, Scikit-Fuzzy, and Statsmodels in logistics analytics.",
            "storage_bins": "Summarize local source material that explains variables, data types, and simple Python storage concepts using logistics examples.",
            "shipping_manifest": "Summarize local source material that explains Python lists and dictionaries for shipment records and manifest data.",
            "quality_gate": "Summarize local source material that explains if/else logic and Python functions for logistics decision rules.",
            "warehouse_manager": "Summarize local source material that explains Pandas data loading, cleaning, and filtering for shipment tables.",
            "intuition_engine": "Summarize the local source material that explains fuzzy membership functions for shipment risk.",
            "quality_inspector": "Summarize the local source material that explains robust regression, Huber loss, and outlier resistance in logistics datasets.",
            "future_predictor": "Summarize the local source material that explains ARIMA forecasting and quantity discrepancy in shipment operations.",
            "home": "Summarize the most important concepts from the local source library for this dashboard.",
        }
        prompt_prefix = (
            "You are a study-notes generator. Write concise NotebookLM-style notes with 3 short sections: "
            "Key idea, why it matters for logistics, and one caution."
        )
        return self.retrieve_grounded_notes(module_descriptions[module_key], module_key, prompt_prefix=prompt_prefix)

    def _wait_for_operation(self, client, operation) -> None:
        while not operation.done:
            time.sleep(2)
            operation = client.operations.get(operation)

    def _delete_document(self, document_name: str) -> None:
        client = self._get_client()
        if not client:
            return
        try:
            client.file_search_stores.documents.delete(name=document_name, config={"force": True})
        except TypeError:
            client.file_search_stores.documents.delete(name=document_name)
        except Exception:
            return

    def _list_documents(self, store_name: str) -> dict[str, dict[str, Any]]:
        client = self._get_client()
        if not client:
            return {}

        documents: dict[str, dict[str, Any]] = {}
        try:
            for document in client.file_search_stores.documents.list(parent=store_name):
                metadata = {}
                for item in getattr(document, "custom_metadata", []) or []:
                    metadata[item.key] = getattr(item, "string_value", None) or getattr(item, "numeric_value", None)
                documents[document.name] = {
                    "name": document.name,
                    "display_name": getattr(document, "display_name", None),
                    "mime_type": getattr(document, "mime_type", None),
                    "metadata": metadata,
                }
        except Exception:
            return {}
        return documents

    def _match_document(self, documents: dict[str, dict[str, Any]], relative_path: str, sha256: str) -> dict[str, Any] | None:
        for document in documents.values():
            metadata = document.get("metadata", {})
            if metadata.get("source_path") == relative_path and metadata.get("sha256") == sha256:
                return document
        return None

    def _normalize_citations(self, response) -> list[dict[str, Any]]:
        candidates = getattr(response, "candidates", []) or []
        if not candidates:
            return []
        grounding_metadata = getattr(candidates[0], "grounding_metadata", None)
        if grounding_metadata is None:
            return []

        citations: list[dict[str, Any]] = []
        for chunk in getattr(grounding_metadata, "grounding_chunks", []) or []:
            retrieved_context = getattr(chunk, "retrieved_context", None)
            if not retrieved_context:
                continue
            custom_metadata = {}
            for item in getattr(retrieved_context, "custom_metadata", []) or []:
                custom_metadata[item.key] = getattr(item, "string_value", None) or getattr(item, "numeric_value", None)
            citations.append(
                {
                    "title": getattr(retrieved_context, "title", None) or Path(custom_metadata.get("source_path", "local-source")).name,
                    "source_path": custom_metadata.get("source_path"),
                    "module": custom_metadata.get("module"),
                    "excerpt": getattr(retrieved_context, "text", "")[:320],
                    "uri": getattr(retrieved_context, "uri", None),
                }
            )
        return citations

    @staticmethod
    def _sha256_for_path(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
