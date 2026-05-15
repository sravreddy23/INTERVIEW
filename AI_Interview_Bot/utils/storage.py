"""Local persistence for users, resume profiles, and interview history."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH, DATA_DIR


def _ensure_parent_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_connection():
    _ensure_parent_dirs()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the lightweight SQLite schema used by the app."""

    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS resume_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                extracted_skills TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS interview_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                mode TEXT NOT NULL,
                company TEXT NOT NULL,
                difficulty INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                score REAL NOT NULL,
                confidence TEXT NOT NULL,
                technical_correctness TEXT NOT NULL,
                communication_quality TEXT NOT NULL,
                strengths TEXT NOT NULL,
                weaknesses TEXT NOT NULL,
                improvements TEXT NOT NULL,
                sample_answer TEXT NOT NULL,
                time_complexity TEXT NOT NULL,
                space_complexity TEXT NOT NULL,
                overall_feedback TEXT NOT NULL,
                elapsed_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )


def _pbkdf2(password: str, salt: bytes) -> str:
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return derived.hex()


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    return salt.hex(), _pbkdf2(password, salt)


def create_user(username: str, password: str) -> tuple[bool, str | None]:
    username = username.strip().lower()
    if not username or not password:
        return False, "Username and password are required."

    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            return False, "That username already exists."

        salt, password_hash = hash_password(password)
        connection.execute(
            """
            INSERT INTO users (username, password_salt, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, salt, password_hash, datetime.utcnow().isoformat()),
        )
    return True, None


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    username = username.strip().lower()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return None

        salt = bytes.fromhex(row["password_salt"])
        candidate_hash = _pbkdf2(password, salt)
        if not hmac.compare_digest(candidate_hash, row["password_hash"]):
            return None
        return dict(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def save_resume_profile(user_id: int, file_name: str, extracted_text: str, extracted_skills: list[str]) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO resume_profiles (user_id, file_name, extracted_text, extracted_skills, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file_name,
                extracted_text,
                json.dumps(extracted_skills),
                datetime.utcnow().isoformat(),
            ),
        )


def get_latest_resume_profile(user_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM resume_profiles
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["extracted_skills"] = json.loads(result["extracted_skills"])
        return result


def save_interview_turn(
    *,
    user_id: int,
    session_id: str,
    turn_index: int,
    mode: str,
    company: str,
    difficulty: int,
    question: str,
    answer: str,
    analysis: dict[str, Any],
    elapsed_seconds: int,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO interview_turns (
                user_id, session_id, turn_index, mode, company, difficulty,
                question, answer, score, confidence, technical_correctness,
                communication_quality, strengths, weaknesses, improvements,
                sample_answer, time_complexity, space_complexity, overall_feedback,
                elapsed_seconds, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                session_id,
                turn_index,
                mode,
                company,
                difficulty,
                question,
                answer,
                float(analysis.get("score", 0)),
                analysis.get("confidence", "Low"),
                analysis.get("technical_correctness", "Not assessed"),
                analysis.get("communication_quality", "Not assessed"),
                json.dumps(analysis.get("strengths", [])),
                json.dumps(analysis.get("weaknesses", [])),
                json.dumps(analysis.get("improvements", [])),
                analysis.get("sample_answer", ""),
                analysis.get("time_complexity", "Not assessed"),
                analysis.get("space_complexity", "Not assessed"),
                analysis.get("overall_feedback", ""),
                elapsed_seconds,
                datetime.utcnow().isoformat(),
            ),
        )


def fetch_interview_turns(user_id: int, limit: int = 100) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT * FROM interview_turns
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        turns: list[dict[str, Any]] = []
        for row in rows:
            turn = dict(row)
            turn["strengths"] = json.loads(turn["strengths"])
            turn["weaknesses"] = json.loads(turn["weaknesses"])
            turn["improvements"] = json.loads(turn["improvements"])
            turns.append(turn)
        return turns


def fetch_dashboard_stats(user_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_turns,
                AVG(score) AS avg_score,
                MAX(score) AS best_score,
                MIN(score) AS lowest_score,
                AVG(elapsed_seconds) AS avg_time
            FROM interview_turns
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        latest = connection.execute(
            """
            SELECT score, created_at, mode, company
            FROM interview_turns
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()

        recent = connection.execute(
            """
            SELECT score, created_at
            FROM interview_turns
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (user_id,),
        ).fetchall()

    scores = [float(item["score"]) for item in recent][::-1]
    timestamps = [item["created_at"] for item in recent][::-1]
    return {
        "total_turns": int(row["total_turns"] or 0),
        "avg_score": round(float(row["avg_score"] or 0), 2),
        "best_score": round(float(row["best_score"] or 0), 2),
        "lowest_score": round(float(row["lowest_score"] or 0), 2),
        "avg_time": round(float(row["avg_time"] or 0), 1),
        "latest_score": round(float(latest["score"]), 2) if latest else 0.0,
        "latest_mode": latest["mode"] if latest else "",
        "latest_company": latest["company"] if latest else "",
        "trend_scores": scores,
        "trend_timestamps": timestamps,
    }
