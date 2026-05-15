"""Authentication helpers used by the Streamlit app."""

from __future__ import annotations

from .storage import authenticate_user, create_user


def signup(username: str, password: str) -> tuple[bool, str | None]:
    return create_user(username, password)


def login(username: str, password: str):
    return authenticate_user(username, password)
