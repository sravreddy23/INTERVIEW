"""Interview question generation with AI and high-quality fallback logic."""

from __future__ import annotations

import json
import random
import re
from typing import Any

from .config import COMPANY_STYLE_HINTS, CODING_MODES, DEFAULT_MODEL, MODE_TOPIC_HINTS, LLM_RESPONSE_KEYS
from .google_ai import generate_json_text

QUESTION_BANK = {
    "HR Interview": [
        {"question": "Tell me about yourself and what brought you to this interview.", "focus_area": "intro"},
        {"question": "Describe a time you handled a disagreement in a team.", "focus_area": "teamwork"},
        {"question": "What are your strengths and what is one weakness you are actively improving?", "focus_area": "self-awareness"},
        {"question": "Why should we hire you over other candidates?", "focus_area": "motivation"},
        {"question": "Tell me about a challenge you faced and how you resolved it.", "focus_area": "problem solving"},
    ],
    "Python": [
        {"question": "Explain the difference between a list, tuple, set, and dictionary in Python.", "focus_area": "basics"},
        {"question": "What is list comprehension and when would you use it?", "focus_area": "syntax"},
        {"question": "How does Python memory management work at a high level?", "focus_area": "runtime"},
        {"question": "How would you handle exceptions in production code?", "focus_area": "robustness"},
        {"question": "Write a function to detect duplicates in a list efficiently.", "focus_area": "coding"},
    ],
    "DBMS": [
        {"question": "What is normalization and why is it important?", "focus_area": "normalization"},
        {"question": "Explain the difference between INNER JOIN, LEFT JOIN, and RIGHT JOIN.", "focus_area": "sql"},
        {"question": "What is a transaction and what does ACID mean?", "focus_area": "transactions"},
        {"question": "How do indexes improve query performance, and what is the trade-off?", "focus_area": "optimization"},
        {"question": "Design a SQL query to identify the second highest salary in a table.", "focus_area": "coding"},
    ],
    "DSA": [
        {"question": "Compare arrays, linked lists, stacks, and queues with use cases.", "focus_area": "basics"},
        {"question": "Explain recursion and common pitfalls when using it.", "focus_area": "recursion"},
        {"question": "How would you choose between BFS and DFS for a problem?", "focus_area": "graphs"},
        {"question": "What makes a sorting algorithm stable, and why does it matter?", "focus_area": "sorting"},
        {"question": "Solve a two-sum style problem and explain the optimal approach.", "focus_area": "coding"},
    ],
    "Operating Systems": [
        {"question": "What is the difference between a process and a thread?", "focus_area": "processes"},
        {"question": "Explain CPU scheduling and describe a common scheduling algorithm.", "focus_area": "scheduling"},
        {"question": "What causes deadlock, and how can it be prevented?", "focus_area": "deadlocks"},
        {"question": "How does virtual memory work?", "focus_area": "memory"},
        {"question": "How would you diagnose high CPU usage in an application?", "focus_area": "practical"},
    ],
    "Computer Networks": [
        {"question": "Walk me through the OSI model and its layers.", "focus_area": "basics"},
        {"question": "What is the difference between TCP and UDP?", "focus_area": "transport"},
        {"question": "How does DNS resolution work?", "focus_area": "dns"},
        {"question": "Explain HTTP methods and common status codes.", "focus_area": "web"},
        {"question": "How would you troubleshoot a slow network request?", "focus_area": "practical"},
    ],
    "Aptitude": [
        {"question": "A train travels 120 km in 2 hours. What is its average speed?", "focus_area": "speed"},
        {"question": "If the price increases by 20% and then decreases by 20%, what is the net effect?", "focus_area": "percentages"},
        {"question": "A worker can finish a job in 8 days. How much work is done in 3 days?", "focus_area": "ratio"},
        {"question": "Explain how you would solve a probability question with two coin tosses.", "focus_area": "probability"},
        {"question": "A company has 60% male and 40% female employees. If 25% of males and 50% of females attend training, what percentage attends overall?", "focus_area": "logic"},
    ],
    "Behavioral Interview": [
        {"question": "Tell me about a time you had to learn something quickly.", "focus_area": "learning"},
        {"question": "Describe a situation where you took ownership without being asked.", "focus_area": "ownership"},
        {"question": "Tell me about a failure and what you learned from it.", "focus_area": "growth"},
        {"question": "How do you handle pressure and conflicting deadlines?", "focus_area": "resilience"},
        {"question": "Describe a time you improved a process or workflow.", "focus_area": "impact"},
    ],
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


def _difficulty_label(difficulty: int) -> str:
    difficulty = max(1, min(5, difficulty))
    return {1: "warm-up", 2: "foundational", 3: "intermediate", 4: "advanced", 5: "very challenging"}[difficulty]


def _company_prefix(company: str) -> str:
    if company == "Neutral / Standard":
        return ""
    return f"{company} style: {COMPANY_STYLE_HINTS.get(company, 'professional and focused')}. "


def _question_bank_for_mode(mode: str) -> list[dict[str, str]]:
    return QUESTION_BANK.get(mode, QUESTION_BANK["HR Interview"])


def _is_coding_question(mode: str, latest_analysis: dict[str, Any] | None) -> bool:
    if mode in CODING_MODES:
        return True
    if latest_analysis and any(token in str(latest_analysis.get("overall_feedback", "")).lower() for token in ["complexity", "optimization", "algorithm"]):
        return True
    return False


def _build_prompt(mode: str, company: str, resume_skills: list[str], difficulty: int, history: list[dict[str, str]], latest_analysis: dict[str, Any] | None) -> str:
    skill_text = ", ".join(resume_skills[:10]) if resume_skills else "No extracted resume skills"
    feedback_text = ""
    if latest_analysis:
        feedback_text = (
            f"Previous score: {latest_analysis.get('score', 0)}/10. "
            f"Weaknesses: {', '.join(latest_analysis.get('weaknesses', [])[:3])}. "
            f"Improvements: {', '.join(latest_analysis.get('improvements', [])[:3])}."
        )

    company_style = COMPANY_STYLE_HINTS.get(company, "professional and realistic")
    topic_hint = MODE_TOPIC_HINTS.get(mode, "core interview skills")
    history_text = "\n".join(f"Q: {item.get('question', '')}\nA: {item.get('answer', '')}" for item in history[-4:]) or "No prior turns."
    weakness_text = ", ".join(latest_analysis.get("weaknesses", [])[:3]) if latest_analysis else "None"
    strength_text = ", ".join(latest_analysis.get("strengths", [])[:3]) if latest_analysis else "None"

    return (
        "You are InterviewAI, a professional, realistic, and concise interviewer. "
        "Ask exactly one question at a time. Keep the tone natural, slightly challenging, and adaptive. "
        "Never provide explanations unless the user has already answered and you are generating a follow-up question. "
        "When possible, vary phrasing to sound like a real interviewer. Return strict JSON only.\n\n"
        f"Interview mode: {mode}\n"
        f"Company style: {company} ({company_style})\n"
        f"Target topic: {topic_hint}\n"
        f"Skill signals from resume: {skill_text}\n"
        f"Current difficulty: {difficulty}/5 ({_difficulty_label(difficulty)})\n"
        f"Context from last answer: {feedback_text or 'No previous answer yet.'}\n"
        f"Recent history:\n{history_text}\n\n"
        f"Latest strengths: {strength_text}\n"
        f"Latest weaknesses: {weakness_text}\n\n"
        "Generate the next best interviewer question. If the candidate just answered poorly, ask a sharper follow-up focused on the weakness. "
        "If the candidate answered strongly, increase difficulty slightly and probe deeper. "
        "The question must feel like a real interview question, not a generic prompt.\n\n"
        "Required JSON keys: question, difficulty, is_follow_up, focus_area, reason, expected_answer_signals."
    )


def _fallback_question(mode: str, company: str, difficulty: int, resume_skills: list[str], latest_analysis: dict[str, Any] | None) -> dict[str, Any]:
    bank = _question_bank_for_mode(mode)
    best_skill = resume_skills[0] if resume_skills else None
    weakness = None
    if latest_analysis and latest_analysis.get("weaknesses"):
        weakness = latest_analysis["weaknesses"][0]

    if weakness:
        follow_up_text = f"Can you go deeper on this weakness: {weakness}?"
        focus_area = "follow-up"
    elif best_skill and random.random() > 0.45:
        follow_up_text = f"How would you apply your experience with {best_skill} in a real interview scenario?"
        focus_area = best_skill
    else:
        chosen = random.choice(bank)
        follow_up_text = chosen["question"]
        focus_area = chosen["focus_area"]

    if company != "Neutral / Standard":
        follow_up_text = f"{follow_up_text} {company} style follow-up: keep the answer crisp, specific, and outcome-driven."

    if difficulty >= 4 and _is_coding_question(mode, latest_analysis):
        follow_up_text = f"{follow_up_text} Also talk through complexity, edge cases, and trade-offs."

    return {
        "question": follow_up_text,
        "difficulty": max(1, min(5, difficulty)),
        "is_follow_up": bool(weakness),
        "focus_area": focus_area,
        "reason": "Fallback question generated locally because the AI model is unavailable.",
        "expected_answer_signals": ["clear reasoning", "specific examples", "structured response"],
    }


def _normalize_payload(payload: dict[str, Any], difficulty: int) -> dict[str, Any]:
    question = str(payload.get("question", "")).strip()
    if not question.endswith("?"):
        question = question.rstrip(".") + "?"
    return {
        "question": question,
        "difficulty": int(payload.get("difficulty", difficulty)),
        "is_follow_up": bool(payload.get("is_follow_up", False)),
        "focus_area": str(payload.get("focus_area", "general")),
        "reason": str(payload.get("reason", "")),
        "expected_answer_signals": payload.get("expected_answer_signals", ["clear reasoning"]),
    }


def generate_question(
    *,
    client,
    mode: str,
    company: str,
    difficulty: int,
    history: list[dict[str, str]],
    resume_skills: list[str],
    latest_analysis: dict[str, Any] | None,
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    if client is not None:
        try:
            prompt = _build_prompt(mode, company, resume_skills, difficulty, history, latest_analysis)
            content = generate_json_text(client, model, prompt, temperature=0.7) or "{}"
            parsed = _parse_json(content)
            if parsed:
                return _normalize_payload(parsed, difficulty)
        except Exception:
            pass

    return _fallback_question(mode, company, difficulty, resume_skills, latest_analysis)


def suggest_next_difficulty(current_difficulty: int, analysis_score: float) -> int:
    if analysis_score >= 8.0:
        return min(5, current_difficulty + 1)
    if analysis_score <= 4.5:
        return max(1, current_difficulty - 1)
    return max(1, min(5, current_difficulty))
