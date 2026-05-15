"""Optional voice helpers for text-to-speech and speech-to-text."""

from __future__ import annotations

from typing import Any


def tts_available() -> bool:
    try:
        import pyttsx3  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def stt_available() -> bool:
    try:
        import speech_recognition  # type: ignore  # noqa: F401

        return True
    except Exception:
        return False


def speak_text(text: str) -> bool:
    try:
        import pyttsx3  # type: ignore

        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception:
        return False


def transcribe_audio_file(audio_bytes: bytes) -> str:
    try:
        import io
        import speech_recognition as sr  # type: ignore

        recognizer = sr.Recognizer()
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio)
    except Exception:
        return ""
