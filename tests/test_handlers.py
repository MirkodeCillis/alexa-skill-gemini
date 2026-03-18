"""Unit tests for Alexa handlers."""

from unittest.mock import MagicMock, patch
import pytest

from tests.conftest import make_handler_input


# ---------------------------------------------------------------------------
# LLMIntentHandler
# ---------------------------------------------------------------------------

class TestLLMIntentHandler:
    def _get_handler(self) -> object:
        from alexa_gemini.handlers.llm_intent import LLMIntentHandler
        return LLMIntentHandler()

    def test_can_handle_llm_intent(self, llm_input: MagicMock) -> None:
        handler = self._get_handler()
        assert handler.can_handle(llm_input) is True  # type: ignore[union-attr]

    def test_cannot_handle_other_intent(self) -> None:
        handler = self._get_handler()
        other = make_handler_input(intent_name="AMAZON.HelpIntent")
        assert handler.can_handle(other) is False  # type: ignore[union-attr]

    def test_empty_slot_returns_reprompt_no_gemini_call(
        self, empty_slot_input: MagicMock
    ) -> None:
        handler = self._get_handler()
        with patch("alexa_gemini.handlers.llm_intent.GeminiService") as mock_svc_cls:
            handler.handle(empty_slot_input)  # type: ignore[union-attr]
            mock_svc_cls.assert_not_called()
        empty_slot_input.response_builder.speak.assert_called_once()
        speech = empty_slot_input.response_builder.speak.call_args[0][0]
        assert len(speech) > 0

    def test_question_slot_passed_to_gemini(self, llm_input: MagicMock) -> None:
        handler = self._get_handler()
        with (
            patch("alexa_gemini.handlers.llm_intent.load_config"),
            patch("alexa_gemini.handlers.llm_intent.GeminiService") as mock_svc_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.chat.return_value = ("answer", [])
            mock_svc_cls.return_value = mock_svc

            handler.handle(llm_input)  # type: ignore[union-attr]

            mock_svc.chat.assert_called_once()
            call_args = mock_svc.chat.call_args
            assert call_args[0][0] == "what is the weather"

    def test_history_initialized_to_empty_list(self) -> None:
        handler = self._get_handler()
        hi = make_handler_input(
            intent_name="LLMIntent",
            slots={"question": "hello"},
            session_attributes={},  # no history key
        )
        with (
            patch("alexa_gemini.handlers.llm_intent.load_config"),
            patch("alexa_gemini.handlers.llm_intent.GeminiService") as mock_svc_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.chat.return_value = ("answer", [])
            mock_svc_cls.return_value = mock_svc

            handler.handle(hi)  # type: ignore[union-attr]

            call_args = mock_svc.chat.call_args
            assert call_args[0][1] == []

    def test_updated_history_written_to_session(self, llm_input: MagicMock) -> None:
        handler = self._get_handler()
        new_history = [{"role": "user", "parts": [{"text": "q"}]}]
        with (
            patch("alexa_gemini.handlers.llm_intent.load_config"),
            patch("alexa_gemini.handlers.llm_intent.GeminiService") as mock_svc_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.chat.return_value = ("answer", new_history)
            mock_svc_cls.return_value = mock_svc

            handler.handle(llm_input)  # type: ignore[union-attr]

        assert llm_input.attributes_manager.session_attributes["history"] == new_history

    def test_returns_non_empty_speech(self, llm_input: MagicMock) -> None:
        handler = self._get_handler()
        with (
            patch("alexa_gemini.handlers.llm_intent.load_config"),
            patch("alexa_gemini.handlers.llm_intent.GeminiService") as mock_svc_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.chat.return_value = ("Here is your answer", [])
            mock_svc_cls.return_value = mock_svc

            handler.handle(llm_input)  # type: ignore[union-attr]

        llm_input.response_builder.speak.assert_called_once_with("Here is your answer")

    def test_should_not_end_session(self, llm_input: MagicMock) -> None:
        handler = self._get_handler()
        with (
            patch("alexa_gemini.handlers.llm_intent.load_config"),
            patch("alexa_gemini.handlers.llm_intent.GeminiService") as mock_svc_cls,
        ):
            mock_svc = MagicMock()
            mock_svc.chat.return_value = ("ok", [])
            mock_svc_cls.return_value = mock_svc
            handler.handle(llm_input)  # type: ignore[union-attr]

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
    from alexa_gemini.handlers.launch import LaunchRequestHandler
    LaunchRequestHandler().handle(launch_input)
    launch_input.response_builder.speak.assert_called_once()
    speech = launch_input.response_builder.speak.call_args[0][0]
    assert len(speech) > 0


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


def test_stop_clears_history(stop_input: MagicMock) -> None:
    from alexa_gemini.handlers.stop_cancel import StopCancelIntentHandler
    stop_input.attributes_manager.session_attributes = {"history": [{"role": "user"}]}
    StopCancelIntentHandler().handle(stop_input)
    assert stop_input.attributes_manager.session_attributes.get("history") in (None, [])
