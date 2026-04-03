from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from .config import KIMI_MODEL, MOONSHOT_BASE_URL
from .content import SOCRATIC_SEEDS

# Allow override via environment variable for deployment flexibility
_KIMI_MODEL = os.getenv("KIMI_MODEL", KIMI_MODEL)


class KimiTutorService:
    def __init__(self, api_key: str | None = None, base_url: str = MOONSHOT_BASE_URL) -> None:
        self.api_key = api_key or os.getenv("MOONSHOT_API_KEY")
        self.base_url = base_url
        self._client = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self) -> OpenAI | None:
        if not self.available:
            return None
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def answer(
        self,
        module_key: str,
        user_prompt: str,
        module_state: dict[str, Any],
        grounded_notes: dict[str, Any],
        chat_history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not self.available:
            return {
                "ok": False,
                "message": "Set MOONSHOT_API_KEY to activate the Kimi Socratic tutor.",
                "content": None,
                "next_question": None,
                "assistant_message": None,
            }

        client = self._get_client()
        evidence_snippets = grounded_notes.get("citations", [])
        evidence_block = "\n\n".join(
            f"Source: {citation.get('source_path') or citation.get('title')}\nExcerpt: {citation.get('excerpt')}"
            for citation in evidence_snippets[:5]
        )
        answer_instructions = (
            "You are Ain's Socratic tutor for fuzzy-robust logistics mathematics and beginner Python literacy. "
            "Guide first, reveal second. Start by asking at least one short guiding question, then explain the concept "
            "using the live module state, the visible code behavior, and only the grounded evidence provided. "
            "Prioritize Python understanding: mention variables, DataFrames, function calls, column operations, indexing, loops, or conditionals whenever relevant. "
            "If Ain asks a math question, connect it back to how the Python code represents that math. "
            "Do not invent citations. If grounded evidence is missing, say so clearly and fall back to the visible math state and code state. "
            "End with a line that begins exactly with 'Next question:' followed by one concise, Python-friendly follow-up."
        )
        module_state_lines = "\n".join(f"- {key}: {value}" for key, value in module_state.items())
        grounded_answer = grounded_notes.get("answer") or "No Gemini study-note summary was available."

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": answer_instructions},
            {
                "role": "system",
                "content": (
                    f"Module: {module_key}\n"
                    f"Visible module state:\n{module_state_lines}\n\n"
                    f"Gemini study-note summary:\n{grounded_answer}\n\n"
                    f"Grounded evidence snippets:\n{evidence_block or 'No local evidence snippets were retrieved.'}"
                ),
            },
        ]
        for historical_message in chat_history[-8:]:
            clean_message = {k: v for k, v in historical_message.items() if k in {"role", "content", "reasoning_content"}}
            messages.append(clean_message)
        messages.append({"role": "user", "content": user_prompt})

        try:
            completion = client.chat.completions.create(
                model=_KIMI_MODEL,
                messages=messages,
                temperature=0.6,
                max_tokens=4096,
                extra_body={"thinking": {"type": "disabled"}},
            )
        except Exception:
            try:  # #10: Retry without non-standard extra_body on failure
                completion = client.chat.completions.create(
                    model=_KIMI_MODEL,
                    messages=messages,
                    temperature=0.6,
                    max_tokens=4096,
                )
            except Exception:
                return {
                    "ok": False,
                    "message": "The AI tutor is temporarily unavailable. Please try again shortly.",
                    "content": None,
                    "next_question": None,
                    "assistant_message": None,
                }
        message = completion.choices[0].message
        raw_content = message.content or ""
        next_question = self._extract_next_question(raw_content, module_key)
        content = self._strip_next_question(raw_content).strip()
        assistant_message = {
            "role": "assistant",
            "content": content,
            "next_question": next_question,
        }
        hidden_reasoning = getattr(message, "reasoning_content", None)
        if hidden_reasoning:
            assistant_message["reasoning_content"] = hidden_reasoning
        return {
            "ok": True,
            "message": "Kimi produced a grounded tutoring response.",
            "content": content,
            "next_question": next_question,
            "assistant_message": assistant_message,
        }

    def recommend_department(self, problem_text: str, department_descriptions: str) -> dict[str, Any]:
        if not self.available:
            return {
                "ok": False,
                "message": "Set MOONSHOT_API_KEY to activate the Kimi department recommender.",
                "content": None,
            }

        client = self._get_client()
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Ain's tool-first mentor. Choose exactly one library department from the provided catalog. "
                    "Respond in 3 short lines only:\n"
                    "Department: <Library>, <Factory Role>\n"
                    "Why: <one sentence tied to the student's problem>\n"
                    "Call: <one concise Python starter call>\n"
                    "Keep the answer practical and beginner-friendly."
                ),
            },
            {
                "role": "system",
                "content": f"Available departments:\n{department_descriptions}",
            },
            {"role": "user", "content": problem_text},
        ]

        try:
            completion = client.chat.completions.create(
                model=_KIMI_MODEL,
                messages=messages,
                temperature=0.6,
                max_tokens=500,
                extra_body={"thinking": {"type": "disabled"}},
            )
        except Exception:
            try:  # #10: Retry without non-standard extra_body on failure
                completion = client.chat.completions.create(
                    model=_KIMI_MODEL,
                    messages=messages,
                    temperature=0.6,
                    max_tokens=500,
                )
            except Exception:
                return {
                    "ok": False,
                    "message": "The department recommender is temporarily unavailable.",
                    "content": None,
                }

        message = completion.choices[0].message
        return {
            "ok": True,
            "message": "Kimi recommended the best-fit library department.",
            "content": message.content or "",
        }

    def default_seed_questions(self, module_key: str) -> list[str]:
        return SOCRATIC_SEEDS.get(module_key, SOCRATIC_SEEDS["home"])

    def _extract_next_question(self, raw_content: str, module_key: str) -> str:
        marker = "next question:"
        lower_content = raw_content.lower()
        if marker in lower_content:
            marker_index = lower_content.rfind(marker)
            return raw_content[marker_index + len(marker) :].strip()
        return self.default_seed_questions(module_key)[0]

    def _strip_next_question(self, raw_content: str) -> str:
        marker = "next question:"
        lower_content = raw_content.lower()
        if marker not in lower_content:
            return raw_content
        marker_index = lower_content.rfind(marker)
        return raw_content[:marker_index].rstrip()
