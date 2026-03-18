"""Unit tests for Alexa handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from tests.conftest import make_handler_input

if TYPE_CHECKING:
    from alexa_gemini.handlers.llm_intent import LLMIntentHandler


# ---------------------------------------------------------------------------
# LLMIntentHandler
# ---------------------------------------------------------------------------

class TestLLMIntentHandler:
    def _get_handler(self) -> LLMIntentHandler:
        from alexa_gemini.handlers.llm_intent import LLMIntentHandler
        return LLMIntentHandler()

    def test_can_handle_llm_intent(self, llm_input: MagicMock) -> None:
        handler = self._get_handler()
        assert handler.can_handle(llm_input) is True

    def test_cannot_handle_other_intent(self) -> None:
        handler = self._get_handler()
        other = make_handler_input(intent_name="AMAZON.HelpIntent")
        assert handler.can_handle(other) is False

    def test_empty_slot_returns_reprompt_no_gemini_call(
        self, empty_slot_input: MagicMock
    ) -> None:
        handler = self._get_handler()
        with patch("alexa_gemini.handlers.llm_intent.GeminiService") as mock_svc_cls:
            handler.handle(empty_slot_input)
            mock_svc_cls.assert_not_called()
        empty_slot_input.response_builder.speak.assert_called_once()
        EXPECTED_REPROMPT = (
            "Sorry, I didn't catch that. What would you like to ask? "
            "— Scusa, non ho capito. Cosa vorresti chiedere?"
        )
        speech = empty_slot_input.response_builder.speak.call_args[0][0]
        assert speech == EXPECTED_REPROMPT

    def test_question_slot_passed_to_gemini(
        self, llm_input: MagicMock, mock_gemini_service: MagicMock
    ) -> None:
        handler = self._get_handler()
        handler.handle(llm_input)
        mock_gemini_service.chat.assert_called_once()
        call_args = mock_gemini_service.chat.call_args
        assert call_args[0][0] == "what is the weather"
        assert call_args[0][1] == []  # history initialized to empty list

    def test_history_initialized_to_empty_list(
        self, mock_gemini_service: MagicMock
    ) -> None:
        handler = self._get_handler()
        hi = make_handler_input(
            intent_name="LLMIntent",
            slots={"question": "hello"},
            session_attributes={},  # no history key
        )
        handler.handle(hi)
        call_args = mock_gemini_service.chat.call_args
        assert call_args[0][1] == []

    def test_updated_history_written_to_session(
        self, llm_input: MagicMock, mock_gemini_service: MagicMock
    ) -> None:
        handler = self._get_handler()
        new_history = [{"role": "user", "parts": [{"text": "q"}]}]
        mock_gemini_service.chat.return_value = ("answer", new_history)
        handler.handle(llm_input)
        assert llm_input.attributes_manager.session_attributes["history"] == new_history

    def test_returns_non_empty_speech(
        self, llm_input: MagicMock, mock_gemini_service: MagicMock
    ) -> None:
        handler = self._get_handler()
        mock_gemini_service.chat.return_value = ("Here is your answer", [])
        handler.handle(llm_input)
        llm_input.response_builder.speak.assert_called_once_with("Here is your answer")

    def test_should_not_end_session(
        self, llm_input: MagicMock, mock_gemini_service: MagicMock
    ) -> None:
        handler = self._get_handler()
        handler.handle(llm_input)
        llm_input.response_builder.set_should_end_session.assert_called_once_with(False)


# ---------------------------------------------------------------------------
# strip_markdown_for_tts edge case
# ---------------------------------------------------------------------------

def test_strip_markdown_empty_string() -> None:
    from alexa_gemini.utils.text import strip_markdown_for_tts
    assert strip_markdown_for_tts("") == ""


# ---------------------------------------------------------------------------
# LaunchRequestHandler
# ---------------------------------------------------------------------------

def test_launch_can_handle(launch_input: MagicMock) -> None:
    from alexa_gemini.handlers.launch import LaunchRequestHandler
    assert LaunchRequestHandler().can_handle(launch_input) is True


def test_launch_returns_speech(launch_input: MagicMock) -> None:
    from alexa_gemini.handlers.launch import WELCOME, LaunchRequestHandler
    LaunchRequestHandler().handle(launch_input)
    launch_input.response_builder.speak.assert_called_once_with(WELCOME)


# ---------------------------------------------------------------------------
# HelpIntentHandler
# ---------------------------------------------------------------------------

def test_help_can_handle(help_input: MagicMock) -> None:
    from alexa_gemini.handlers.help import HelpIntentHandler
    assert HelpIntentHandler().can_handle(help_input) is True


def test_help_does_not_end_session(help_input: MagicMock) -> None:
    from alexa_gemini.handlers.help import HelpIntentHandler
    HelpIntentHandler().handle(help_input)
    help_input.response_builder.set_should_end_session.assert_called_once_with(False)


# ---------------------------------------------------------------------------
# StopCancelIntentHandler
# ---------------------------------------------------------------------------

def test_stop_can_handle(stop_input: MagicMock) -> None:
    from alexa_gemini.handlers.stop_cancel import StopCancelIntentHandler
    assert StopCancelIntentHandler().can_handle(stop_input) is True


def test_cancel_can_handle(cancel_input: MagicMock) -> None:
    from alexa_gemini.handlers.stop_cancel import StopCancelIntentHandler
    assert StopCancelIntentHandler().can_handle(cancel_input) is True


def test_stop_clears_history(stop_input: MagicMock) -> None:
    from alexa_gemini.handlers.stop_cancel import StopCancelIntentHandler
    stop_input.attributes_manager.session_attributes = {"history": [{"role": "user"}]}
    StopCancelIntentHandler().handle(stop_input)
    assert stop_input.attributes_manager.session_attributes.get("history") in (None, [])
