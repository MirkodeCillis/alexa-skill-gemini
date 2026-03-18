"""Unit tests for GeminiService — all google-genai calls are mocked."""

from unittest.mock import MagicMock, patch

from alexa_gemini.config import Config
from alexa_gemini.services.gemini import FALLBACK_TEXT, MAX_HISTORY_TURNS, GeminiService

FAKE_CONFIG = Config(gemini_api_key="fake-key", gemini_model="gemini-2.5-flash")


def _make_service() -> tuple[GeminiService, MagicMock]:
    """Return (service, mock_client) with google.genai.Client patched."""
    with patch("alexa_gemini.services.gemini.genai.Client") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        svc = GeminiService(FAKE_CONFIG)
    svc._client = mock_client  # keep reference for assertions
    return svc, mock_client


def test_history_truncated_before_user_message_appended() -> None:
    svc, mock_client = _make_service()
    # Build history longer than MAX_HISTORY_TURNS * 2
    long_history = [
        {"role": "user" if i % 2 == 0 else "model", "parts": [{"text": f"msg{i}"}]}
        for i in range(MAX_HISTORY_TURNS * 2 + 6)
    ]
    mock_response = MagicMock()
    mock_response.text = "answer"
    mock_client.models.generate_content.return_value = mock_response

    _, updated = svc.chat("new question", long_history)

    call_args = mock_client.models.generate_content.call_args
    contents_sent = call_args.kwargs["contents"]
    # contents = truncated history (20) + user message (1) = 21
    assert len(contents_sent) == MAX_HISTORY_TURNS * 2 + 1


def test_user_message_appended_to_contents() -> None:
    svc, mock_client = _make_service()
    mock_response = MagicMock()
    mock_response.text = "answer"
    mock_client.models.generate_content.return_value = mock_response

    svc.chat("hello", [])

    contents = mock_client.models.generate_content.call_args.kwargs["contents"]
    assert contents[-1] == {"role": "user", "parts": [{"text": "hello"}]}


def test_model_reply_appended_to_returned_history() -> None:
    svc, mock_client = _make_service()
    mock_response = MagicMock()
    mock_response.text = "**bold answer**"
    mock_client.models.generate_content.return_value = mock_response

    _, updated = svc.chat("hi", [])

    # Last entry should be model reply with markdown stripped
    assert updated[-1]["role"] == "model"
    assert updated[-1]["parts"][0]["text"] == "bold answer"


def test_markdown_stripped_from_response() -> None:
    svc, mock_client = _make_service()
    mock_response = MagicMock()
    mock_response.text = "## Title\n- item one\n**strong**"
    mock_client.models.generate_content.return_value = mock_response

    text, _ = svc.chat("q", [])

    assert "##" not in text
    assert "**" not in text
    assert "-" not in text


def test_fallback_on_api_error() -> None:
    from google.genai import errors  # type: ignore[import]
    svc, mock_client = _make_service()
    mock_client.models.generate_content.side_effect = errors.APIError.__new__(errors.APIError)

    text, history = svc.chat("q", [{"role": "user", "parts": [{"text": "prev"}]}])

    assert text == FALLBACK_TEXT
    assert history == [{"role": "user", "parts": [{"text": "prev"}]}]


def test_fallback_on_generic_exception() -> None:
    svc, mock_client = _make_service()
    mock_client.models.generate_content.side_effect = RuntimeError("oops")

    text, history = svc.chat("q", [])

    assert text == FALLBACK_TEXT
    assert history == []


def test_fallback_when_response_text_is_none() -> None:
    svc, mock_client = _make_service()
    mock_response = MagicMock()
    mock_response.text = None
    mock_client.models.generate_content.return_value = mock_response

    text, history = svc.chat("q", [])

    assert text == FALLBACK_TEXT
    assert history == []


def test_history_not_modified_on_fallback() -> None:
    svc, mock_client = _make_service()
    mock_client.models.generate_content.side_effect = RuntimeError("oops")
    original = [{"role": "user", "parts": [{"text": "prev"}]}]

    _, returned_history = svc.chat("q", original)

    assert returned_history is original
