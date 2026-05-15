"""InterviewAI - a modern AI interview practice chatbot built with Streamlit."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from utils.analysis import analyze_answer
from utils.auth import login, signup
from utils.config import (
    APP_NAME,
    APP_SUBTITLE,
    COMPANY_OPTIONS,
    DEFAULT_MAX_TURNS,
    DEFAULT_MODEL,
    DEFAULT_TIMER_SECONDS,
    INTERVIEW_MODES,
)
from utils.interview_engine import generate_question, suggest_next_difficulty
from utils.google_ai import get_google_client
from utils.resume import build_resume_summary, extract_pdf_text, extract_skills
from utils.storage import (
    authenticate_user,
    fetch_dashboard_stats,
    fetch_interview_turns,
    get_latest_resume_profile,
    initialize_database,
    save_interview_turn,
    save_resume_profile,
)
from utils.ui import inject_custom_css, render_hero, render_section
from utils.voice import speak_text, stt_available, tts_available

load_dotenv()
initialize_database()

st.set_page_config(page_title=APP_NAME, page_icon="🎯", layout="wide", initial_sidebar_state="expanded")
inject_custom_css()


# -----------------------------------------------------------------------------
# Session bootstrap
# -----------------------------------------------------------------------------

def init_state() -> None:
    defaults = {
        "authenticated": False,
        "user": None,
        "active_page": "Dashboard",
        "pending_mode": "HR Interview",
        "pending_company": "Neutral / Standard",
        "pending_difficulty": 2,
        "active_mode": "HR Interview",
        "active_company": "Neutral / Standard",
        "active_difficulty": 2,
        "max_turns": DEFAULT_MAX_TURNS,
        "session_id": str(uuid.uuid4()),
        "interview_started": False,
        "interview_completed": False,
        "turn_index": 0,
        "question_count": 0,
        "current_question_data": None,
        "current_question_text": "",
        "chat_messages": [],
        "turn_history": [],
        "last_analysis": None,
        "resume_text": "",
        "resume_skills": [],
        "resume_file_name": "",
        "start_time": None,
        "selected_model": os.getenv("GOOGLE_MODEL", DEFAULT_MODEL),
        "voice_enabled": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


# -----------------------------------------------------------------------------
# AI client and session helpers
# -----------------------------------------------------------------------------

client = get_google_client()


def reset_interview_state() -> None:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.interview_started = True
    st.session_state.interview_completed = False
    st.session_state.turn_index = 0
    st.session_state.question_count = 0
    st.session_state.current_question_data = None
    st.session_state.current_question_text = ""
    st.session_state.chat_messages = []
    st.session_state.turn_history = []
    st.session_state.last_analysis = None
    st.session_state.start_time = time.time()


def get_resume_context(user_id: int) -> tuple[str, list[str]]:
    stored = get_latest_resume_profile(user_id)
    if stored:
        st.session_state.resume_text = stored["extracted_text"]
        st.session_state.resume_skills = stored["extracted_skills"]
        st.session_state.resume_file_name = stored["file_name"]
    return st.session_state.resume_text, list(st.session_state.resume_skills)


def start_question_cycle() -> None:
    resume_skills = list(st.session_state.resume_skills)
    question_payload = generate_question(
        client=client,
        mode=st.session_state.active_mode,
        company=st.session_state.active_company,
        difficulty=st.session_state.active_difficulty,
        history=st.session_state.turn_history,
        resume_skills=resume_skills,
        latest_analysis=st.session_state.last_analysis,
        model=st.session_state.selected_model,
    )
    st.session_state.current_question_data = question_payload
    st.session_state.current_question_text = question_payload["question"]
    st.session_state.question_count += 1
    st.session_state.chat_messages.append(
        {
            "role": "assistant",
            "content": question_payload["question"],
            "kind": "question",
            "meta": question_payload,
        }
    )


def begin_new_session() -> None:
    st.session_state.active_mode = st.session_state.pending_mode
    st.session_state.active_company = st.session_state.pending_company
    st.session_state.active_difficulty = st.session_state.pending_difficulty
    if st.session_state.user:
        get_resume_context(st.session_state.user["id"])
    reset_interview_state()
    start_question_cycle()


def maybe_render_chat_history() -> None:
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            if message.get("kind") == "analysis":
                st.markdown(message["content"])
            else:
                st.markdown(message["content"])


def interview_progress() -> float:
    if st.session_state.max_turns <= 0:
        return 0.0
    return min(1.0, st.session_state.turn_index / float(st.session_state.max_turns))


def elapsed_seconds() -> int:
    if not st.session_state.start_time:
        return 0
    return int(time.time() - float(st.session_state.start_time))


def current_timer_text() -> str:
    elapsed = elapsed_seconds()
    remaining = max(0, DEFAULT_TIMER_SECONDS - elapsed)
    return f"{elapsed // 60:02d}:{elapsed % 60:02d} elapsed | {remaining // 60:02d}:{remaining % 60:02d} left"


# -----------------------------------------------------------------------------
# Authentication screen
# -----------------------------------------------------------------------------

def render_auth_screen() -> None:
    render_hero(
        "Practice realistic interviews with AI",
        "A polished chatbot that asks one question at a time, scores your answers, adapts difficulty, and tracks your progress across sessions.",
    )

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        render_section("What you get", "Hackathon-ready features designed for students and job seekers.")
        st.markdown(
            """
            <div class="glass-card">
                <div class="mini-pill">Dark professional UI</div>
                <div class="mini-pill">Company-style interviews</div>
                <div class="mini-pill">Resume-aware questioning</div>
                <div class="mini-pill">Answer scoring and feedback</div>
                <div class="mini-pill">Dashboard analytics</div>
                <div class="mini-pill">Optional voice hooks</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        st.info("If you do not set a Google AI key, the app still runs in a local demo mode with deterministic interview logic.")

    with right:
        render_section("Login or sign up", "Authentication is local and stored in SQLite.")
        login_tab, signup_tab = st.tabs(["Login", "Sign up"])

        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                login_username = st.text_input("Username", placeholder="yourname")
                login_password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    user = login(login_username, login_password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = dict(user)
                        st.success("Logged in successfully.")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with signup_tab:
            with st.form("signup_form", clear_on_submit=False):
                signup_username = st.text_input("Choose a username")
                signup_password = st.text_input("Choose a password", type="password")
                confirm_password = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create account", use_container_width=True)
                if submitted:
                    if signup_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        ok, error = signup(signup_username, signup_password)
                        if ok:
                            user = authenticate_user(signup_username, signup_password)
                            st.session_state.authenticated = True
                            st.session_state.user = dict(user) if user else None
                            st.success("Account created and logged in.")
                            st.rerun()
                        else:
                            st.error(error or "Unable to create account.")


# -----------------------------------------------------------------------------
# Sidebar navigation and controls
# -----------------------------------------------------------------------------

def render_sidebar() -> None:
    user = st.session_state.user or {}
    with st.sidebar:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="hero-kicker">Signed in as</div>
                <div class="section-heading">{user.get('username', 'Guest')}</div>
                <p class="section-subtitle">InterviewAI local workspace</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")
        navigation = st.radio(
            "Navigation",
            ["Dashboard", "Practice Interview", "Resume Insights", "Settings"],
            index=["Dashboard", "Practice Interview", "Resume Insights", "Settings"].index(st.session_state.active_page)
            if st.session_state.active_page in ["Dashboard", "Practice Interview", "Resume Insights", "Settings"]
            else 0,
        )
        st.session_state.active_page = navigation

        st.divider()
        st.markdown("### Interview Setup")
        st.session_state.pending_mode = st.selectbox("Interview mode", INTERVIEW_MODES, index=INTERVIEW_MODES.index(st.session_state.pending_mode))
        st.session_state.pending_company = st.selectbox("Company style", COMPANY_OPTIONS, index=COMPANY_OPTIONS.index(st.session_state.pending_company))
        st.session_state.pending_difficulty = st.slider("Starting difficulty", 1, 5, int(st.session_state.pending_difficulty))
        st.session_state.max_turns = st.slider("Target turns", 5, 15, int(st.session_state.max_turns))

        st.divider()
        st.markdown("### Resume Status")
        if st.session_state.resume_skills:
            st.success(f"{len(st.session_state.resume_skills)} skills detected")
            st.caption(", ".join(st.session_state.resume_skills[:6]))
        else:
            st.caption("Upload a PDF resume to personalize the interview.")

        st.divider()
        if st.button("Start new interview", use_container_width=True):
            begin_new_session()
            st.session_state.active_page = "Practice Interview"
            st.rerun()

        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.chat_messages = []
            st.session_state.turn_history = []
            st.session_state.current_question_data = None
            st.session_state.current_question_text = ""
            st.session_state.interview_started = False
            st.session_state.interview_completed = False
            st.session_state.start_time = None
            st.rerun()


# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------

def render_dashboard() -> None:
    render_hero(
        "Performance dashboard",
        "Track scores, review trends, and see how your interview performance improves over time.",
    )
    user = st.session_state.user
    stats = fetch_dashboard_stats(user["id"])

    cols = st.columns(4)
    metrics = [
        ("Avg score", f"{stats['avg_score']}/10"),
        ("Best score", f"{stats['best_score']}/10"),
        ("Total answers", str(stats['total_turns'])),
        ("Avg response time", f"{stats['avg_time']}s"),
    ]
    for col, (label, value) in zip(cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="hero-kicker">{label}</div>
                    <div class="section-heading">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        render_section("Score trend", "Latest scores captured from your interview sessions.")
        if stats["trend_scores"]:
            trend_df = pd.DataFrame(
                {
                    "timestamp": pd.to_datetime(stats["trend_timestamps"]),
                    "score": stats["trend_scores"],
                }
            )
            st.line_chart(trend_df.set_index("timestamp")["score"])
        else:
            st.info("No interview history yet. Start a practice session to generate analytics.")

    with right:
        render_section("Latest snapshot", "Most recent recorded answer.")
        if stats["total_turns"]:
            st.metric("Latest score", f"{stats['latest_score']}/10")
            st.caption(f"{stats['latest_mode']} | {stats['latest_company']}")
        else:
            st.caption("Your latest score will appear here after your first answer.")

    st.write("")
    render_section("Recent turns", "Review the last few scored answers and feedback.")
    turns = fetch_interview_turns(user["id"], limit=8)
    if turns:
        table_rows = []
        for turn in turns:
            table_rows.append(
                {
                    "Time": turn["created_at"].replace("T", " ")[:19],
                    "Mode": turn["mode"],
                    "Company": turn["company"],
                    "Score": turn["score"],
                    "Confidence": turn["confidence"],
                    "Question": turn["question"][:90] + ("..." if len(turn["question"]) > 90 else ""),
                }
            )
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No saved turns yet.")


# -----------------------------------------------------------------------------
# Resume insights
# -----------------------------------------------------------------------------

def render_resume_page() -> None:
    render_hero(
        "Resume insights",
        "Upload a PDF resume so InterviewAI can extract skills and personalize the next interview session.",
    )
    user = st.session_state.user
    upload = st.file_uploader("Upload PDF resume", type=["pdf"])
    if upload is not None:
        extracted_text = extract_pdf_text(upload)
        skills = extract_skills(extracted_text)
        st.session_state.resume_text = extracted_text
        st.session_state.resume_skills = skills
        st.session_state.resume_file_name = upload.name
        save_resume_profile(user_id=user["id"], file_name=upload.name, extracted_text=extracted_text, extracted_skills=skills)
        st.success("Resume uploaded and parsed.")

    if st.session_state.resume_file_name:
        st.caption(f"Current resume: {st.session_state.resume_file_name}")

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        render_section("Extracted skills", "These skills are used to personalize interview questions.")
        if st.session_state.resume_skills:
            chips = "".join(f'<span class="mini-pill">{skill}</span>' for skill in st.session_state.resume_skills)
            st.markdown(f"<div class='glass-card'>{chips}</div>", unsafe_allow_html=True)
        else:
            st.info("Upload a PDF resume to see extracted skills here.")

    with right:
        render_section("Resume summary", "A concise summary inserted into the interview prompt.")
        if st.session_state.resume_text:
            st.text_area("Parsed resume preview", st.session_state.resume_text[:3000], height=280)
            st.caption(build_resume_summary(st.session_state.resume_text, st.session_state.resume_skills))
        else:
            st.info("No resume parsed yet.")


# -----------------------------------------------------------------------------
# Practice interview flow
# -----------------------------------------------------------------------------

def render_question_card() -> None:
    question_data = st.session_state.current_question_data or {}
    question_text = question_data.get("question", "")
    if not question_text:
        return

    focus_area = question_data.get("focus_area", "general")
    difficulty = question_data.get("difficulty", st.session_state.active_difficulty)
    follow_up = "Yes" if question_data.get("is_follow_up") else "No"

    st.markdown(
        f"""
        <div class="glass-card">
            <div class="hero-kicker">Current question</div>
            <div class="section-heading">{question_text}</div>
            <p class="section-subtitle">Focus: {focus_area} | Difficulty: {difficulty}/5 | Follow-up: {follow_up}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analysis_block(analysis: dict[str, Any]) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Score", f"{analysis['score']}/10")
    c2.metric("Confidence", analysis["confidence"])
    c3.metric("Communication", analysis["communication_quality"][:28])

    left, right = st.columns([1, 1], gap="large")
    with left:
        st.markdown("#### Strengths")
        for item in analysis.get("strengths", []):
            st.write(f"- {item}")
        st.markdown("#### Weaknesses")
        for item in analysis.get("weaknesses", []):
            st.write(f"- {item}")
    with right:
        st.markdown("#### Improvements")
        for item in analysis.get("improvements", []):
            st.write(f"- {item}")
        st.markdown("#### Sample answer")
        st.write(analysis.get("sample_answer", ""))
        st.caption(f"Time complexity: {analysis.get('time_complexity', 'Not assessed')}")
        st.caption(f"Space complexity: {analysis.get('space_complexity', 'Not assessed')}")
        st.caption(f"Technical correctness: {analysis.get('technical_correctness', '')}")


def maybe_finish_interview() -> bool:
    if st.session_state.turn_index >= st.session_state.max_turns:
        st.session_state.interview_completed = True
        return True
    if elapsed_seconds() >= DEFAULT_TIMER_SECONDS:
        st.session_state.interview_completed = True
        return True
    return False


def render_practice_page() -> None:
    render_hero(
        "Practice interview",
        "Answer one question at a time while the interviewer adapts to your performance in real time.",
    )

    if not st.session_state.interview_started:
        render_section("Ready when you are", "Start a fresh interview session using the sidebar controls.")
        st.info("Pick a mode, choose a company style, and click Start new interview from the sidebar.")
        return

    if st.session_state.interview_completed:
        render_section("Interview completed", "Review your performance and start a new session when you are ready.")
        if st.session_state.last_analysis:
            render_analysis_block(st.session_state.last_analysis)
        st.success("Session finished. Use the sidebar to launch another interview.")
        return

    render_section("Live session", "The interviewer asks one question at a time and adapts after every answer.")
    progress = interview_progress()
    st.progress(progress)
    st.caption(f"Turn {st.session_state.turn_index + 1} of {st.session_state.max_turns} | {current_timer_text()}")

    maybe_render_chat_history()
    render_question_card()

    if st.session_state.current_question_data and tts_available():
        voice_col, status_col = st.columns([0.25, 0.75])
        with voice_col:
            if st.button("Speak question", use_container_width=True):
                speak_text(st.session_state.current_question_text)
        with status_col:
            st.caption("Optional voice support is available because a text-to-speech backend was detected.")

    user_answer = st.chat_input("Type your answer and press Enter")
    if user_answer and st.session_state.current_question_data:
        question_text = st.session_state.current_question_text
        st.session_state.chat_messages.append({"role": "user", "content": user_answer, "kind": "answer"})
        st.session_state.turn_history.append({"question": question_text, "answer": user_answer})

        with st.spinner("Analyzing your response and preparing the next question..."):
            resume_text, resume_skills = get_resume_context(st.session_state.user["id"])
            analysis = analyze_answer(
                client=client,
                question=question_text,
                answer=user_answer,
                mode=st.session_state.active_mode,
                company=st.session_state.active_company,
                resume_skills=resume_skills,
                difficulty=int(st.session_state.current_question_data.get("difficulty", st.session_state.active_difficulty)),
                model=st.session_state.selected_model,
            )
            st.session_state.last_analysis = analysis
            st.session_state.chat_messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"**Score:** {analysis['score']}/10 | **Confidence:** {analysis['confidence']}\n\n"
                        f"**Strengths:** {', '.join(analysis.get('strengths', [])[:3])}\n\n"
                        f"**Improvements:** {', '.join(analysis.get('improvements', [])[:3])}"
                    ),
                    "kind": "analysis",
                }
            )
            save_interview_turn(
                user_id=st.session_state.user["id"],
                session_id=st.session_state.session_id,
                turn_index=st.session_state.turn_index,
                mode=st.session_state.active_mode,
                company=st.session_state.active_company,
                difficulty=int(st.session_state.current_question_data.get("difficulty", st.session_state.active_difficulty)),
                question=question_text,
                answer=user_answer,
                analysis=analysis,
                elapsed_seconds=elapsed_seconds(),
            )
            st.session_state.turn_index += 1
            st.session_state.active_difficulty = suggest_next_difficulty(
                int(st.session_state.current_question_data.get("difficulty", st.session_state.active_difficulty)),
                float(analysis.get("score", 0)),
            )
            st.session_state.current_question_data = None
            st.session_state.current_question_text = ""

            if maybe_finish_interview():
                st.session_state.interview_completed = True
            else:
                start_question_cycle()

        st.rerun()


# -----------------------------------------------------------------------------
# Settings and optional voice hooks
# -----------------------------------------------------------------------------

def render_settings_page() -> None:
    render_hero(
        "Settings",
        "Adjust the model, inspect runtime status, and view optional voice capabilities.",
    )

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        render_section("Runtime", "Current app and model state.")
        st.write(f"**Gemini model:** {st.session_state.selected_model}")
        st.write(f"**Google AI API configured:** {'Yes' if client else 'No - demo mode active'}")
        st.write(f"**Voice TTS available:** {'Yes' if tts_available() else 'No'}")
        st.write(f"**Voice STT available:** {'Yes' if stt_available() else 'No'}")
        if st.button("Reset current interview", use_container_width=True):
            reset_interview_state()
            st.session_state.interview_started = False
            st.session_state.interview_completed = False
            st.success("Current interview reset.")

    with right:
        render_section("Optional voice AI", "Voice support is intentionally optional so the app stays deployment-friendly.")
        st.info(
            "If you want local text-to-speech or speech-to-text, install pyttsx3 and SpeechRecognition. The app will detect them automatically."
        )
        st.caption("MongoDB is left as an environment toggle for future integration; local SQLite is the default database.")


# -----------------------------------------------------------------------------
# Main app entrypoint
# -----------------------------------------------------------------------------

def main() -> None:
    if not st.session_state.authenticated:
        render_auth_screen()
        return

    if st.session_state.user:
        get_resume_context(st.session_state.user["id"])

    render_sidebar()

    if st.session_state.active_page == "Dashboard":
        render_dashboard()
    elif st.session_state.active_page == "Practice Interview":
        render_practice_page()
    elif st.session_state.active_page == "Resume Insights":
        render_resume_page()
    else:
        render_settings_page()


if __name__ == "__main__":
    main()
