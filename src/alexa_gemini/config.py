"""Centralized runtime configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Runtime configuration.

    Set values locally in .env (copied from .env.example).
    On Alexa-hosted, set them in the Developer Console: Code tab > Environment Variables.
    """

    gemini_api_key: str
    gemini_model: str


def load_config() -> Config:
    """Load and validate configuration from environment variables.

    Raises:
        EnvironmentError: if GEMINI_API_KEY is missing or empty.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise OSError(
            "GEMINI_API_KEY is not set.\n"
            "  Local development: copy .env.example to .env and fill in the key.\n"
            "  Alexa-hosted: go to Developer Console > Code tab > Environment Variables."
        )
    return Config(
        gemini_api_key=api_key,
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip(),
    )
