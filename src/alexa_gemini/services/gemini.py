"""GeminiService — wraps google-genai, manages conversation history."""

import logging
from typing import Any

import google.genai as genai
from google.genai import errors
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

from alexa_gemini.config import Config
from alexa_gemini.utils.text import strip_markdown_for_tts

logger = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 10  # keep last N user+model pairs (= N*2 messages)

FALLBACK_TEXT = (
    "I'm sorry, something went wrong. — Mi dispiace, si è verificato un errore."
)

SYSTEM_INSTRUCTION = (
    "You are a concise voice assistant integrated with Amazon Alexa. "
    "Always detect the language of the user's message and reply in the same language. "
    "Keep all responses short and suitable for text-to-speech output: no markdown, "
    "no bullet points, no symbols, no numbered lists. "
    "If the user asks about current events, recent news, or real-time information, "
    "use the web search tool to find an accurate answer."
)


class GeminiService:
    """Wraps the google-genai client and manages per-session conversation history."""

    def __init__(self, config: Config) -> None:
        self._client = genai.Client(api_key=config.gemini_api_key)
        self._model = config.gemini_model

    def chat(
        self, question: str, history: list[dict[str, Any]]
    ) -> tuple[str, list[dict[str, Any]]]:
        """Send a question to Gemini and return (response_text, updated_history).

        Args:
            question: The user's question text.
            history: Existing conversation history in Gemini format.

        Returns:
            Tuple of (cleaned response text, updated history list).
            On any error, returns (FALLBACK_TEXT, original history).
        """
        try:
            # Truncate history first, then append user message
            history_copy = history[-(MAX_HISTORY_TURNS * 2):]
            history_copy = history_copy + [
                {"role": "user", "parts": [{"text": question}]}
            ]

            cfg = GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[Tool(google_search=GoogleSearch())],
            )

            response = self._client.models.generate_content(
                model=self._model,
                contents=history_copy,
                config=cfg,
            )

            if not response.text:
                logger.warning("Gemini returned empty response text")
                return FALLBACK_TEXT, history

            cleaned = strip_markdown_for_tts(response.text)
            history_copy = history_copy + [
                {"role": "model", "parts": [{"text": cleaned}]}
            ]
            return cleaned, history_copy

        except errors.APIError as exc:
            logger.error("Gemini APIError: %s", exc)
            return FALLBACK_TEXT, history
        except Exception as exc:
            logger.error("Unexpected error calling Gemini: %s", exc)
            return FALLBACK_TEXT, history
