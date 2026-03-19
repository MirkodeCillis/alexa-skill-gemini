"""Shared test fixtures."""

from typing import Any, Callable
from unittest.mock import MagicMock

import pytest
from ask_sdk_model import IntentRequest  # type: ignore[attr-defined]


def make_handler_input(
    intent_name: str | None = None,
    slots: dict[str, str | None] | None = None,
    session_attributes: dict[str, Any] | None = None,
    is_intent: bool = True,
) -> MagicMock:
    """Build a mock HandlerInput for the given intent and slots."""
    handler_input = MagicMock()

    # Request type
    if is_intent and intent_name:
        handler_input.request_envelope.request.object_type = "IntentRequest"
        handler_input.request_envelope.request.__class__ = IntentRequest
        intent = MagicMock()
        intent.name = intent_name

        # Build slots mock
        slot_map: dict[str, MagicMock] = {}
        for slot_name, slot_val in (slots or {}).items():
            slot_mock = MagicMock()
            slot_mock.value = slot_val
            slot_map[slot_name] = slot_mock
        intent.slots = slot_map
        handler_input.request_envelope.request.intent = intent
    else:
        handler_input.request_envelope.request.object_type = intent_name or "LaunchRequest"

    # Session attributes
    attrs = session_attributes if session_attributes is not None else {}
    handler_input.attributes_manager.session_attributes = attrs

    # Response builder
    response_builder = MagicMock()
    response_builder.speak.return_value = response_builder
    response_builder.ask.return_value = response_builder
    response_builder.set_should_end_session.return_value = response_builder
    response_builder.response = MagicMock()
    handler_input.response_builder = response_builder

    return handler_input


@pytest.fixture
def launch_input() -> MagicMock:
    return make_handler_input(intent_name="LaunchRequest", is_intent=False)


@pytest.fixture
def llm_input() -> MagicMock:
    return make_handler_input(
        intent_name="LLMIntent",
        slots={"question": "what is the weather"},
    )


@pytest.fixture
def empty_slot_input() -> MagicMock:
    return make_handler_input(
        intent_name="LLMIntent",
        slots={"question": ""},
    )


@pytest.fixture
def help_input() -> MagicMock:
    return make_handler_input(intent_name="AMAZON.HelpIntent")


@pytest.fixture
def stop_input() -> MagicMock:
    return make_handler_input(intent_name="AMAZON.StopIntent")


@pytest.fixture
def cancel_input() -> MagicMock:
    return make_handler_input(intent_name="AMAZON.CancelIntent")


@pytest.fixture
def mock_handler_input() -> Callable[[str | None, dict[str, str | None] | None, dict[str, Any] | None, bool], MagicMock]:
    """Factory fixture: returns make_handler_input for use in tests."""
    return make_handler_input


@pytest.fixture
def mock_gemini_service(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch GeminiService everywhere it's imported and return the mock."""
    mock_svc = MagicMock()
    mock_svc.chat.return_value = ("answer", [])
    monkeypatch.setattr("alexa_gemini.handlers.llm_intent.load_config", lambda: MagicMock())
    monkeypatch.setattr("alexa_gemini.handlers.llm_intent.GeminiService", lambda _: mock_svc)
    return mock_svc
