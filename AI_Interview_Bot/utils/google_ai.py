"""Google Gemini client helpers used by InterviewAI."""

from __future__ import annotations

import os
from typing import Any

try:
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore
except Exception:  # pragma: no cover - dependency may be absent in local demo mode
    genai = None
    types = None


def get_google_client() -> Any | None:
    api_key = (
        os.getenv("GOOGLE_API_KEY", "").strip()
        or os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_AI_API_KEY", "").strip()
    )
    if not api_key or genai is None:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def generate_json_text(client: Any | None, model: str, prompt: str, temperature: float) -> str | None:
    if client is None or types is None:
        return None
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                response_mime_type="application/json",
            ),
        )
        return getattr(response, "text", None)
    except Exception:
        return None