"""Resume parsing and skill extraction helpers."""

from __future__ import annotations

import io
import re
from collections import Counter
from typing import Any

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

from .config import SKILL_KEYWORDS


def extract_pdf_text(uploaded_file) -> str:
    """Extract plain text from a Streamlit PDF upload."""

    if uploaded_file is None:
        return ""

    if PdfReader is None:
        return ""

    reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    return "\n".join(pages).strip()


def extract_skills(text: str, limit: int = 12) -> list[str]:
    """Detect likely skills from resume text using keyword matching."""

    normalized = re.sub(r"\s+", " ", text.lower())
    matches: Counter[str] = Counter()

    for label, keywords in SKILL_KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                matches[label] += 1

    if not matches:
        fallback_keywords = re.findall(r"\b[a-zA-Z][a-zA-Z+.#/-]{2,}\b", normalized)
        return sorted({word for word in fallback_keywords[:limit]})

    ranked = [skill for skill, _ in matches.most_common(limit)]
    return ranked


def build_resume_summary(text: str, skills: list[str]) -> str:
    """Generate a compact resume summary for the interview prompt."""

    clean_text = re.sub(r"\s+", " ", text).strip()
    if not clean_text:
        return "Resume text unavailable."
    excerpt = clean_text[:900]
    skill_text = ", ".join(skills[:8]) if skills else "No obvious skills detected"
    return f"Detected skills: {skill_text}. Resume excerpt: {excerpt}"
