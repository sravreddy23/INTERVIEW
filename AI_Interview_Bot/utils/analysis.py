"""Answer analysis and scoring logic for interview responses."""

from __future__ import annotations

import json
import re
from typing import Any

from .config import ANALYSIS_RESPONSE_KEYS, CODING_MODES, DEFAULT_MODEL
from .google_ai import generate_json_text


def _ensure_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    score = payload.get("score", 0)
    try:
        score = round(float(score), 1)
    except Exception:
        score = 0.0

    confidence = str(payload.get("confidence", "Low")).title()
    return {
        "score": max(0.0, min(10.0, score)),
        "confidence": confidence,
        "technical_correctness": str(payload.get("technical_correctness", "Needs review")),
        "communication_quality": str(payload.get("communication_quality", "Needs review")),
        "strengths": _ensure_list(payload.get("strengths", [])),
        "weaknesses": _ensure_list(payload.get("weaknesses", [])),
        "improvements": _ensure_list(payload.get("improvements", [])),
        "sample_answer": str(payload.get("sample_answer", "")),
        "time_complexity": str(payload.get("time_complexity", "Not assessed")),
        "space_complexity": str(payload.get("space_complexity", "Not assessed")),
        "overall_feedback": str(payload.get("overall_feedback", "")),
    }


def _parse_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except Exception:
            return None


def _fallback_analysis(question: str, answer: str, mode: str, company: str, resume_skills: list[str], difficulty: int) -> dict[str, Any]:
    answer_text = answer.strip()
    word_count = len(answer_text.split())
    has_structure = any(marker in answer_text.lower() for marker in ["first", "second", "finally", "for example", "in summary"])
    has_complexity = bool(re.search(r"o\([^)]*\)", answer_text.lower()))
    has_examples = any(marker in answer_text.lower() for marker in ["example", "instance", "project", "built", "implemented"])
    technical_terms = sum(1 for token in ["complexity", "optimization", "sql", "index", "thread", "memory", "pointer", "recursion", "time", "space"] if token in answer_text.lower())
    resume_bonus = 0.4 if any(skill.lower() in answer_text.lower() for skill in resume_skills[:8]) else 0.0

    base_score = 3.0
    base_score += min(word_count / 45.0, 2.2)
    base_score += 1.2 if has_structure else 0.0
    base_score += 0.8 if has_examples else 0.0
    base_score += min(technical_terms * 0.4, 1.6)
    base_score += resume_bonus
    base_score += 0.5 if difficulty >= 3 and len(answer_text) > 120 else 0.0

    if mode in CODING_MODES:
        base_score += 0.6 if has_complexity else 0.0
        technical_correctness = "Looks directionally correct, but validate the algorithm and edge cases."
        time_complexity = "Mention explicit Big-O notation in the final answer."
        space_complexity = "Mention auxiliary space and data structures used."
    else:
        technical_correctness = "Technically plausible, but make the reasoning tighter and more specific."
        time_complexity = "Not assessed for this question."
        space_complexity = "Not assessed for this question."

    score = max(1.0, min(10.0, round(base_score, 1)))
    confidence = "High" if score >= 8 else "Medium" if score >= 5.5 else "Low"

    strengths = [
        "You provided a direct response." if answer_text else "You attempted the question.",
        "You showed some relevant terminology." if technical_terms else "You stayed on topic.",
    ]
    weaknesses = []
    if word_count < 35:
        weaknesses.append("The answer is quite short and lacks depth.")
    if not has_structure:
        weaknesses.append("Add a clearer structure such as problem, approach, and conclusion.")
    if mode in CODING_MODES and not has_complexity:
        weaknesses.append("State time and space complexity explicitly.")
    if not has_examples:
        weaknesses.append("A concrete example would make the answer stronger.")

    improvements = [
        "Lead with a concise summary, then support it with details.",
        "Add one concrete example or step-by-step explanation.",
    ]
    if mode in CODING_MODES:
        improvements.append("Mention the optimal approach, edge cases, and complexity trade-offs.")

    sample_answer = (
        "I would first clarify the constraints, then choose the most suitable approach, explain why it is optimal, "
        "walk through a small example, and finish with time and space complexity."
        if mode in CODING_MODES
        else "I would answer using the STAR format: situation, task, action, and result, while keeping the response focused and measurable."
    )

    return {
        "score": score,
        "confidence": confidence,
        "technical_correctness": technical_correctness,
        "communication_quality": "Clear enough, but it can be more concise, confident, and structured.",
        "strengths": strengths,
        "weaknesses": weaknesses,
        "improvements": improvements,
        "sample_answer": sample_answer,
        "time_complexity": time_complexity,
        "space_complexity": space_complexity,
        "overall_feedback": "A solid start. Tighten structure, add specifics, and finish with a stronger summary.",
    }


def build_analysis_prompt(question: str, answer: str, mode: str, company: str, resume_skills: list[str], difficulty: int) -> list[dict[str, str]]:
    skill_text = ", ".join(resume_skills[:10]) if resume_skills else "No resume skills extracted"
    system = (
        "You are a senior interviewer and answer evaluator. Score the candidate objectively and return strict JSON only. "
        "Be constructive, specific, and realistic. Do not include markdown, code fences, or extra commentary."
    )
    user = f"""
Interview mode: {mode}
Company style: {company}
Question difficulty: {difficulty}/5
Resume signals: {skill_text}
Question: {question}
Candidate answer: {answer}

Return a JSON object with these keys: {", ".join(ANALYSIS_RESPONSE_KEYS)}.
Rules:
- score must be a number from 0 to 10.
- confidence must be one of Low, Medium, High.
- strengths, weaknesses, and improvements must be arrays of short strings.
- If this is a coding question, include time_complexity and space_complexity.
- Make sample_answer noticeably better than the candidate answer, but keep it concise and interview-ready.
""".strip()
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def analyze_answer(
    *,
    client,
    question: str,
    answer: str,
    mode: str,
    company: str,
    resume_skills: list[str],
    difficulty: int,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    if client is not None:
        try:
            prompt_parts = build_analysis_prompt(question, answer, mode, company, resume_skills, difficulty)
            content = generate_json_text(client, model, "\n\n".join(part["content"] for part in prompt_parts), temperature=0.3) or "{}"
            parsed = _parse_json(content)
            if parsed:
                return _normalize_analysis(parsed)
        except Exception:
            pass

    return _fallback_analysis(question, answer, mode, company, resume_skills, difficulty)
