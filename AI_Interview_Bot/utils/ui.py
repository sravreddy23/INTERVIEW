"""Visual styling and small UI helpers for a polished Streamlit experience."""

from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
            --bg: #0B1020;
            --panel: rgba(17, 25, 46, 0.92);
            --panel-strong: #131C33;
            --border: rgba(145, 164, 255, 0.16);
            --text: #F5F7FB;
            --muted: #9BA8D0;
            --accent: #7C9CFF;
            --accent-2: #38D7B5;
            --danger: #FF7A90;
            --warning: #FFCD70;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: var(--text);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(124, 156, 255, 0.16), transparent 28%),
                radial-gradient(circle at top right, rgba(56, 215, 181, 0.12), transparent 24%),
                linear-gradient(180deg, #0B1020 0%, #09101D 100%);
        }

        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 2.5rem;
        }

        .hero-wrap {
            background: linear-gradient(135deg, rgba(124,156,255,0.16), rgba(56,215,181,0.10));
            border: 1px solid var(--border);
            padding: 1.5rem 1.6rem;
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
            position: relative;
            overflow: hidden;
            animation: fadeUp 650ms ease-out both;
        }

        .hero-wrap::after {
            content: "";
            position: absolute;
            inset: -40% -20% auto auto;
            width: 280px;
            height: 280px;
            background: radial-gradient(circle, rgba(124,156,255,0.22), transparent 68%);
            filter: blur(10px);
        }

        .hero-kicker {
            color: var(--accent-2);
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: clamp(2rem, 4vw, 3.5rem);
            line-height: 1.03;
            margin: 0;
        }

        .hero-subtitle {
            color: var(--muted);
            margin-top: 0.7rem;
            font-size: 1.0rem;
            max-width: 62ch;
        }

        .glass-card {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1rem 1rem 1.1rem 1rem;
            box-shadow: 0 16px 45px rgba(0,0,0,0.22);
        }

        .section-heading {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.2rem;
            margin: 0 0 0.3rem 0;
        }

        .section-subtitle {
            color: var(--muted);
            margin: 0;
            font-size: 0.92rem;
        }

        .chat-bubble {
            border: 1px solid var(--border);
            background: rgba(19, 28, 51, 0.9);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.8rem;
        }

        .chat-bubble.user {
            border-color: rgba(56, 215, 181, 0.28);
            background: rgba(20, 46, 43, 0.72);
        }

        .chat-bubble.assistant {
            border-color: rgba(124, 156, 255, 0.28);
            background: rgba(18, 26, 48, 0.86);
        }

        .mini-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.34rem 0.68rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            color: var(--text);
            font-size: 0.82rem;
            margin: 0 0.3rem 0.35rem 0;
        }

        .metric-card {
            border-radius: 18px;
            padding: 0.95rem 1rem;
            border: 1px solid var(--border);
            background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.02));
        }

        .pulse {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-2);
            box-shadow: 0 0 0 rgba(56, 215, 181, 0.4);
            animation: pulse 2s infinite;
            margin-right: 0.45rem;
        }

        div[data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(13, 18, 34, 0.98), rgba(16, 23, 42, 0.96));
            border-right: 1px solid var(--border);
        }

        button[kind="primary"] {
            background: linear-gradient(135deg, var(--accent), #8b6cff) !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 700 !important;
            box-shadow: 0 12px 30px rgba(124, 156, 255, 0.28) !important;
        }

        button[kind="secondary"] {
            border-radius: 12px !important;
            border: 1px solid var(--border) !important;
        }

        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: rgba(255,255,255,0.03) !important;
        }

        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(56, 215, 181, 0.4); }
            70% { box-shadow: 0 0 0 12px rgba(56, 215, 181, 0); }
            100% { box-shadow: 0 0 0 0 rgba(56, 215, 181, 0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-kicker">InterviewAI</div>
            <h1 class="hero-title">{title}</h1>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="glass-card" style="margin-bottom: 0.9rem;">
            <div class="section-heading">{title}</div>
            <p class="section-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
