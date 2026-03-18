# Alexa Gemini Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete, production-ready multilingual Alexa Skill that proxies voice queries to Google Gemini with multi-turn session memory and live web search grounding.

**Architecture:** ASK SDK handlers in `src/alexa_gemini/handlers/` call `GeminiService` (in `src/alexa_gemini/services/gemini.py`) which wraps the `google-genai` client. Config is centralized in a frozen dataclass. The `lambda/` directory is the Alexa-hosted deployment target; `src/alexa_gemini/` is copied there by `build_lambda.sh` before upload.

**Tech Stack:** Python 3.11, ask-sdk-core, google-genai, python-dotenv, Poetry, pytest, ruff, mypy, python-semantic-release, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-03-18-alexa-gemini-assistant-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `pyproject.toml` | Create | Poetry config + all tool configs |
| `.gitignore` | Create | Exclude .env, caches, dist |
| `.env.example` | Create | Documented variable template (committed) |
| `.env` | Create | Local secrets (gitignored) |
| `CHANGELOG.md` | Create | Empty placeholder for semantic-release |
| `src/alexa_gemini/__init__.py` | Create | Package marker |
| `src/alexa_gemini/config.py` | Create | `Config` frozen dataclass + `load_config()` |
| `src/alexa_gemini/utils/__init__.py` | Create | Package marker |
| `src/alexa_gemini/utils/text.py` | Create | `strip_markdown_for_tts()` |
| `src/alexa_gemini/services/__init__.py` | Create | Package marker |
| `src/alexa_gemini/services/gemini.py` | Create | `GeminiService` |
| `src/alexa_gemini/handlers/__init__.py` | Create | Package marker |
| `src/alexa_gemini/handlers/launch.py` | Create | `LaunchRequestHandler` |
| `src/alexa_gemini/handlers/llm_intent.py` | Create | `LLMIntentHandler` |
| `src/alexa_gemini/handlers/help.py` | Create | `HelpIntentHandler` |
| `src/alexa_gemini/handlers/stop_cancel.py` | Create | `StopCancelIntentHandler` |
| `src/alexa_gemini/handlers/session_ended.py` | Create | `SessionEndedRequestHandler` |
| `lambda/lambda_function.py` | Create | Alexa entry point |
| `lambda/requirements.txt` | Create | Pinned flat deps (generated) |
| `tests/__init__.py` | Create | Package marker |
| `tests/conftest.py` | Create | Shared fixtures |
| `tests/test_config.py` | Create | Config tests |
| `tests/test_gemini_service.py` | Create | GeminiService tests |
| `tests/test_handlers.py` | Create | Handler tests |
| `interaction_model/en-US.json` | Create | English interaction model |
| `interaction_model/it-IT.json` | Create | Italian interaction model |
| `interaction_model/fr-FR.json` | Create | French interaction model |
| `interaction_model/de-DE.json` | Create | German interaction model |
| `interaction_model/es-ES.json` | Create | Spanish interaction model |
| `scripts/build_lambda.sh` | Create | Manual deploy prep script |
| `.github/workflows/ci.yml` | Create | CI/CD pipeline |
| `README.md` | Create | Full deploy guide |

---

## Task 1: Poetry project + pyproject.toml

**Files:**
- Create: `pyproject.toml`

- [ ] **Step 1: Init Poetry project non-interactively**

```bash
cd /path/to/alexa-skill-gemini
poetry init \
  --name alexa-gemini-assistant \
  --version 0.1.0 \
  --description "Multilingual Alexa Skill powered by Google Gemini" \
  --python "^3.11" \
  --no-interaction
```

- [ ] **Step 2: Add production dependencies**

```bash
poetry add ask-sdk-core google-genai python-dotenv
```

- [ ] **Step 3: Add dev dependencies**

```bash
poetry add --group dev pytest pytest-mock ruff mypy python-semantic-release
```

- [ ] **Step 4: Add tool configs to pyproject.toml**

Append to `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
select = ["E", "F", "I", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.semantic_release]
version_toml = ["pyproject.toml:tool.poetry.version"]
branch = "main"
changelog_file = "CHANGELOG.md"
build_command = ""
upload_to_pypi = false
commit_version_number = true
tag_format = "v{version}"

[tool.semantic_release.commit_parser_options]
allowed_tags = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "chore"]
minor_tags = ["feat"]
patch_tags = ["fix", "perf", "refactor"]
```

- [ ] **Step 5: Verify install works**

```bash
poetry install
```

Expected: resolves and installs without errors.

---

## Task 2: .gitignore, .env files, CHANGELOG.md

**Files:**
- Create: `.gitignore`, `.env.example`, `.env`, `CHANGELOG.md`

- [ ] **Step 1: Create .gitignore**

```
.env
__pycache__/
*.pyc
.mypy_cache/
.pytest_cache/
dist/
.venv/
lambda/alexa_gemini/
```

Note: `lambda/alexa_gemini/` is gitignored because it is generated by `build_lambda.sh`.

- [ ] **Step 2: Create .env.example**

```bash
# Get your API key at: https://aistudio.google.com → Get API key → Create API key
GEMINI_API_KEY=

# Gemini model to use. Options (free tier):
#   gemini-2.5-flash       — 10 RPM, 250 RPD  — recommended default
#   gemini-2.5-flash-lite  — 15 RPM, 1000 RPD — best for high-volume free use
#   gemini-2.5-pro         — 5 RPM,  50 RPD   — complex reasoning, very low free quota
GEMINI_MODEL=gemini-2.5-flash
```

- [ ] **Step 3: Create .env (local dev — never committed)**

```bash
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

- [ ] **Step 4: Create empty CHANGELOG.md**

```markdown
# Changelog
```

- [ ] **Step 5: Verify .env is gitignored**

```bash
git check-ignore -v .env
```

Expected: `.gitignore:1:.env   .env`

---

## Task 3: Config module (TDD)

**Files:**
- Create: `src/alexa_gemini/__init__.py`
- Create: `src/alexa_gemini/config.py`
- Create: `tests/__init__.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Create package markers**

`src/alexa_gemini/__init__.py`:
```python
"""Alexa Gemini assistant package."""
```

`tests/__init__.py`: empty file.

- [ ] **Step 2: Write failing tests**

`tests/test_config.py`:
```python
import os
import pytest
from alexa_gemini.config import Config, load_config


def test_load_config_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-pro")
    cfg = load_config()
    assert cfg.gemini_api_key == "test-key"
    assert cfg.gemini_model == "gemini-2.5-pro"


def test_load_config_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    cfg = load_config()
    assert cfg.gemini_model == "gemini-2.5-flash"


def test_load_config_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        load_config()


def test_load_config_empty_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "   ")
    with pytest.raises(EnvironmentError, match="GEMINI_API_KEY"):
        load_config()


def test_config_is_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    cfg = load_config()
    with pytest.raises(Exception):
        cfg.gemini_api_key = "other"  # type: ignore[misc]
```

- [ ] **Step 3: Run tests — confirm they fail**

```bash
poetry run pytest tests/test_config.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `config` doesn't exist yet.

- [ ] **Step 4: Implement config.py**

`src/alexa_gemini/config.py`:
```python
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
        raise EnvironmentError(
            "GEMINI_API_KEY is not set.\n"
            "  Local development: copy .env.example to .env and fill in the key.\n"
            "  Alexa-hosted: go to Developer Console > Code tab > Environment Variables."
        )
    return Config(
        gemini_api_key=api_key,
        gemini_model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip(),
    )
```

- [ ] **Step 5: Run tests — confirm they pass**

```bash
poetry run pytest tests/test_config.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add src/alexa_gemini/__init__.py src/alexa_gemini/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add Config dataclass and load_config()"
```

---

## Task 4: strip_markdown_for_tts utility (TDD)

**Files:**
- Create: `src/alexa_gemini/utils/__init__.py`
- Create: `src/alexa_gemini/utils/text.py`
- Test: `tests/test_handlers.py` (add `strip_markdown_for_tts` test at the end — see Task 9)

- [ ] **Step 1: Create package marker**

`src/alexa_gemini/utils/__init__.py`:
```python
"""Utility helpers."""
```

- [ ] **Step 2: Implement strip_markdown_for_tts**

`src/alexa_gemini/utils/text.py`:
```python
"""Text utilities for making Gemini responses TTS-friendly."""

import re


def strip_markdown_for_tts(text: str) -> str:
    """Remove markdown formatting so Alexa reads the text naturally.

    Removes: headers, bold/italic, bullets, numbered lists,
    code blocks, markdown links. Collapses excessive blank lines.
    """
    if not text:
        return text

    # Remove fenced code blocks (```...```)
    text = re.sub(r"```[\s\S]*?```", "", text)

    # Remove inline code (`...`)
    text = re.sub(r"`[^`]+`", "", text)

    # Remove markdown links [text](url) → keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove headers (# ## ### at line start)
    text = re.sub(r"^#{1,3}\s+", "", text, flags=re.MULTILINE)

    # Remove bold and italic (**text**, *text*, __text__, _text_)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove bullet lines (- , * , • at line start)
    text = re.sub(r"^[-*•]\s+", "", text, flags=re.MULTILINE)

    # Remove numbered list prefixes (1. 2. etc. at line start)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)

    # Collapse 3+ consecutive newlines to a single newline
    text = re.sub(r"\n{3,}", "\n", text)

    return text.strip()
```

- [ ] **Step 3: Quick smoke test in the REPL to verify**

```bash
poetry run python -c "
from alexa_gemini.utils.text import strip_markdown_for_tts
print(strip_markdown_for_tts('## Hello\n**bold** and *italic*\n- bullet\n1. item\n[link](http://x.com)'))
"
```

Expected output: `Hello\nbold and italic\nbullet\nitem\nlink`

- [ ] **Step 4: Commit**

```bash
git add src/alexa_gemini/utils/__init__.py src/alexa_gemini/utils/text.py
git commit -m "feat: add strip_markdown_for_tts utility"
```

---

## Task 5: GeminiService (TDD)

**Files:**
- Create: `src/alexa_gemini/services/__init__.py`
- Create: `src/alexa_gemini/services/gemini.py`
- Test: `tests/test_gemini_service.py`

- [ ] **Step 1: Create package marker**

`src/alexa_gemini/services/__init__.py`:
```python
"""Service layer."""
```

- [ ] **Step 2: Write failing tests**

`tests/test_gemini_service.py`:
```python
"""Unit tests for GeminiService — all google-genai calls are mocked."""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest

from alexa_gemini.config import Config
from alexa_gemini.services.gemini import GeminiService, MAX_HISTORY_TURNS, FALLBACK_TEXT


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
    mock_client.models.generate_content.side_effect = errors.APIError("boom")  # type: ignore[attr-defined]

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
```

- [ ] **Step 3: Run tests — confirm they fail**

```bash
poetry run pytest tests/test_gemini_service.py -v
```

Expected: `ModuleNotFoundError` for `alexa_gemini.services.gemini`.

- [ ] **Step 4: Implement GeminiService**

`src/alexa_gemini/services/gemini.py`:
```python
"""GeminiService — wraps google-genai, manages conversation history."""

import logging
from typing import Any

import google.genai as genai  # type: ignore[import]
from google.genai import errors  # type: ignore[import]
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool  # type: ignore[import]

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
```

- [ ] **Step 5: Run tests — confirm they pass**

```bash
poetry run pytest tests/test_gemini_service.py -v
```

Expected: 8 passed.

- [ ] **Step 6: Commit**

```bash
git add src/alexa_gemini/services/__init__.py src/alexa_gemini/services/gemini.py tests/test_gemini_service.py
git commit -m "feat: add GeminiService with history management and error handling"
```

---

## Task 6: Alexa handlers (TDD)

**Files:**
- Create: `src/alexa_gemini/handlers/__init__.py`
- Create: `src/alexa_gemini/handlers/launch.py`
- Create: `src/alexa_gemini/handlers/llm_intent.py`
- Create: `src/alexa_gemini/handlers/help.py`
- Create: `src/alexa_gemini/handlers/stop_cancel.py`
- Create: `src/alexa_gemini/handlers/session_ended.py`
- Create: `tests/conftest.py`
- Test: `tests/test_handlers.py`

- [ ] **Step 1: Create handler package marker**

`src/alexa_gemini/handlers/__init__.py`:
```python
"""Alexa request handlers."""
```

- [ ] **Step 2: Write conftest.py fixtures**

`tests/conftest.py`:
```python
"""Shared test fixtures."""

from typing import Any
from unittest.mock import MagicMock

import pytest


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
```

- [ ] **Step 3: Write failing handler tests**

`tests/test_handlers.py`:
```python
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
```

- [ ] **Step 4: Run tests — confirm they fail**

```bash
poetry run pytest tests/test_handlers.py -v
```

Expected: `ModuleNotFoundError` for the handler modules.

- [ ] **Step 5: Implement handlers**

`src/alexa_gemini/handlers/launch.py`:
```python
"""LaunchRequestHandler — greets the user and opens the session."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

WELCOME = (
    "Hello! I'm your Gemini-powered assistant. Ask me anything! "
    "— Ciao! Sono il tuo assistente Gemini. Chiedimi pure!"
)


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_request_type
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak(WELCOME)
            .set_should_end_session(False)
            .response
        )
```

`src/alexa_gemini/handlers/llm_intent.py`:
```python
"""LLMIntentHandler — core chat loop."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

from alexa_gemini.config import load_config
from alexa_gemini.services.gemini import GeminiService

REPROMPT = (
    "Sorry, I didn't catch that. What would you like to ask? "
    "— Scusa, non ho capito. Cosa vorresti chiedere?"
)


class LLMIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("LLMIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots
        question_slot = slots.get("question") if slots else None
        question = (question_slot.value or "").strip() if question_slot else ""

        if not question:
            return (
                handler_input.response_builder
                .speak(REPROMPT)
                .set_should_end_session(False)
                .response
            )

        session_attrs = handler_input.attributes_manager.session_attributes
        history = session_attrs.get("history", [])

        config = load_config()
        service = GeminiService(config)
        response_text, updated_history = service.chat(question, history)

        session_attrs["history"] = updated_history

        return (
            handler_input.response_builder
            .speak(response_text)
            .set_should_end_session(False)
            .response
        )
```

`src/alexa_gemini/handlers/help.py`:
```python
"""HelpIntentHandler."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

HELP_TEXT = (
    "Just ask me anything — current events, general knowledge, or any question you have. "
    "Say 'stop' to end. "
    "— Chiedimi qualsiasi cosa: notizie, curiosità o qualsiasi domanda. "
    "Di' 'stop' per uscire."
)


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak(HELP_TEXT)
            .set_should_end_session(False)
            .response
        )
```

`src/alexa_gemini/handlers/stop_cancel.py`:
```python
"""StopCancelIntentHandler — ends the session gracefully."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

GOODBYE = "Goodbye! — Arrivederci!"


class StopCancelIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name
        return is_intent_name("AMAZON.StopIntent")(handler_input) or is_intent_name(
            "AMAZON.CancelIntent"
        )(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        session_attrs = handler_input.attributes_manager.session_attributes
        session_attrs["history"] = []
        return (
            handler_input.response_builder
            .speak(GOODBYE)
            .set_should_end_session(True)
            .response
        )
```

`src/alexa_gemini/handlers/session_ended.py`:
```python
"""SessionEndedRequestHandler — cleans up when the session closes."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_request_type
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        session_attrs = handler_input.attributes_manager.session_attributes
        session_attrs["history"] = []
        return handler_input.response_builder.response
```

- [ ] **Step 6: Run all tests — confirm they pass**

```bash
poetry run pytest -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/alexa_gemini/handlers/ tests/conftest.py tests/test_handlers.py
git commit -m "feat: add Alexa request handlers"
```

---

## Task 7: lambda/ entry point + requirements.txt

**Files:**
- Create: `lambda/lambda_function.py`
- Create: `lambda/requirements.txt`

- [ ] **Step 1: Create lambda_function.py**

`lambda/lambda_function.py`:
```python
from dotenv import load_dotenv

load_dotenv()  # loads .env if present (local dev); no-op on Alexa-hosted

from ask_sdk_core.skill_builder import SkillBuilder

from alexa_gemini.handlers.help import HelpIntentHandler
from alexa_gemini.handlers.launch import LaunchRequestHandler
from alexa_gemini.handlers.llm_intent import LLMIntentHandler
from alexa_gemini.handlers.session_ended import SessionEndedRequestHandler
from alexa_gemini.handlers.stop_cancel import StopCancelIntentHandler

sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(LLMIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(StopCancelIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

handler = sb.lambda_handler()
```

- [ ] **Step 2: Generate requirements.txt**

```bash
pip install poetry-plugin-export 2>/dev/null || true
poetry export --without-hashes --without dev -f requirements.txt \
  --output lambda/requirements.txt
```

- [ ] **Step 3: Verify requirements.txt is non-empty**

```bash
cat lambda/requirements.txt
```

Expected: several pinned packages including `ask-sdk-core`, `google-genai`, `python-dotenv`.

- [ ] **Step 4: Commit**

```bash
git add lambda/lambda_function.py lambda/requirements.txt
git commit -m "feat: add lambda entry point and pinned requirements"
```

---

## Task 8: Interaction models (5 locales)

**Files:**
- Create: `interaction_model/en-US.json`
- Create: `interaction_model/it-IT.json`
- Create: `interaction_model/fr-FR.json`
- Create: `interaction_model/de-DE.json`
- Create: `interaction_model/es-ES.json`

- [ ] **Step 1: Create en-US.json**

`interaction_model/en-US.json`:
```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "chat with gemini",
      "intents": [
        {
          "name": "LLMIntent",
          "slots": [
            { "name": "question", "type": "AMAZON.SearchQuery" }
          ],
          "samples": [
            "{question}",
            "ask {question}",
            "tell me {question}",
            "I want to know {question}",
            "can you tell me {question}",
            "what is {question}",
            "search for {question}",
            "look up {question}",
            "find out {question}",
            "I have a question {question}",
            "please answer {question}"
          ]
        },
        { "name": "AMAZON.HelpIntent", "samples": [] },
        { "name": "AMAZON.CancelIntent", "samples": [] },
        { "name": "AMAZON.StopIntent", "samples": [] }
      ],
      "types": []
    }
  }
}
```

- [ ] **Step 2: Create it-IT.json**

`interaction_model/it-IT.json`:
```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "chatta con gemini",
      "intents": [
        {
          "name": "LLMIntent",
          "slots": [
            { "name": "question", "type": "AMAZON.SearchQuery" }
          ],
          "samples": [
            "{question}",
            "chiedi {question}",
            "dimmi {question}",
            "voglio sapere {question}",
            "puoi dirmi {question}",
            "cos'è {question}",
            "cerca {question}",
            "trovami {question}",
            "ho una domanda {question}",
            "rispondimi su {question}",
            "spiegami {question}"
          ]
        },
        { "name": "AMAZON.HelpIntent", "samples": [] },
        { "name": "AMAZON.CancelIntent", "samples": [] },
        { "name": "AMAZON.StopIntent", "samples": [] }
      ],
      "types": []
    }
  }
}
```

- [ ] **Step 3: Create fr-FR.json**

`interaction_model/fr-FR.json`:
```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "discute avec gemini",
      "intents": [
        {
          "name": "LLMIntent",
          "slots": [
            { "name": "question", "type": "AMAZON.SearchQuery" }
          ],
          "samples": [
            "{question}",
            "demande {question}",
            "dis-moi {question}",
            "je veux savoir {question}",
            "peux-tu me dire {question}",
            "qu'est-ce que {question}",
            "cherche {question}",
            "trouve {question}",
            "j'ai une question {question}",
            "réponds à {question}",
            "explique-moi {question}"
          ]
        },
        { "name": "AMAZON.HelpIntent", "samples": [] },
        { "name": "AMAZON.CancelIntent", "samples": [] },
        { "name": "AMAZON.StopIntent", "samples": [] }
      ],
      "types": []
    }
  }
}
```

- [ ] **Step 4: Create de-DE.json**

`interaction_model/de-DE.json`:
```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "chatte mit gemini",
      "intents": [
        {
          "name": "LLMIntent",
          "slots": [
            { "name": "question", "type": "AMAZON.SearchQuery" }
          ],
          "samples": [
            "{question}",
            "frage {question}",
            "sag mir {question}",
            "ich möchte wissen {question}",
            "kannst du mir sagen {question}",
            "was ist {question}",
            "suche nach {question}",
            "finde heraus {question}",
            "ich habe eine Frage {question}",
            "beantworte {question}",
            "erkläre mir {question}"
          ]
        },
        { "name": "AMAZON.HelpIntent", "samples": [] },
        { "name": "AMAZON.CancelIntent", "samples": [] },
        { "name": "AMAZON.StopIntent", "samples": [] }
      ],
      "types": []
    }
  }
}
```

- [ ] **Step 5: Create es-ES.json**

`interaction_model/es-ES.json`:
```json
{
  "interactionModel": {
    "languageModel": {
      "invocationName": "habla con gemini",
      "intents": [
        {
          "name": "LLMIntent",
          "slots": [
            { "name": "question", "type": "AMAZON.SearchQuery" }
          ],
          "samples": [
            "{question}",
            "pregunta {question}",
            "dime {question}",
            "quiero saber {question}",
            "puedes decirme {question}",
            "qué es {question}",
            "busca {question}",
            "encuentra {question}",
            "tengo una pregunta {question}",
            "respóndeme sobre {question}",
            "explícame {question}"
          ]
        },
        { "name": "AMAZON.HelpIntent", "samples": [] },
        { "name": "AMAZON.CancelIntent", "samples": [] },
        { "name": "AMAZON.StopIntent", "samples": [] }
      ],
      "types": []
    }
  }
}
```

- [ ] **Step 6: Validate all JSON files parse without error**

```bash
for f in interaction_model/*.json; do python -m json.tool "$f" > /dev/null && echo "OK: $f"; done
```

Expected: `OK: interaction_model/de-DE.json` … for each file.

- [ ] **Step 7: Commit**

```bash
git add interaction_model/
git commit -m "feat: add Alexa interaction models for 5 locales"
```

---

## Task 9: build_lambda.sh + CI workflow

**Files:**
- Create: `scripts/build_lambda.sh`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create build_lambda.sh**

`scripts/build_lambda.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

echo "==> Step 1: Remove stale lambda/alexa_gemini/"
rm -rf "$ROOT/lambda/alexa_gemini"

echo "==> Step 2: Copy src/alexa_gemini -> lambda/alexa_gemini/"
cp -r "$ROOT/src/alexa_gemini" "$ROOT/lambda/alexa_gemini"

echo "==> Step 3: Install pinned deps into lambda/"
pip install -r "$ROOT/lambda/requirements.txt" --target "$ROOT/lambda" --quiet

echo "==> Done. lambda/ is ready for upload to the Alexa Developer Console."
```

```bash
chmod +x scripts/build_lambda.sh
```

- [ ] **Step 2: Create ci.yml**

`   .github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
  pull_request:

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install poetry
      - run: poetry install
      - run: poetry run ruff check src tests
      - run: poetry run mypy src
      - run: poetry run pytest --tb=short

  release:
    runs-on: ubuntu-latest
    needs: lint-and-test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install poetry python-semantic-release
      - run: semantic-release version
      - run: semantic-release publish
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 3: Commit**

```bash
git add scripts/build_lambda.sh .github/
git commit -m "chore: add build_lambda.sh and GitHub Actions CI workflow"
```

---

## Task 10: README.md

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README**

`README.md` — full content:

````markdown
# Alexa Gemini Assistant

A multilingual Amazon Alexa Skill that uses Google Gemini as its AI backend. Ask anything — Gemini responds in your language, with optional live web search grounding for current events.

**Tech stack:** Amazon Alexa Skills Kit (ASK SDK), Google Gemini 2.5 Flash, Python 3.11, Poetry.

---

## Prerequisites

- Python 3.11+
- Poetry: `pip install poetry`
- A Google account (for AI Studio API key)
- An Amazon Developer account (free at https://developer.amazon.com)

---

## Local Setup

```bash
git clone <repo-url>
cd alexa-skill-gemini
poetry install
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY
```

---

## Getting a Gemini API Key

1. Go to https://aistudio.google.com
2. Click **Get API key** in the left sidebar
3. Click **Create API key in new project**
4. Copy the generated key
5. Paste it as the value of `GEMINI_API_KEY` in your `.env` file

---

## Switching the Gemini Model

- **Locally:** change `GEMINI_MODEL` in `.env`
- **On Alexa-hosted:** update the `GEMINI_MODEL` Environment Variable in the Code tab and redeploy

| Model                 | RPM | RPD  | Best for                        |
|-----------------------|-----|------|---------------------------------|
| gemini-2.5-flash      | 10  | 250  | Default — balanced quality/cost |
| gemini-2.5-flash-lite | 15  | 1000 | High-volume personal use        |
| gemini-2.5-pro        | 5   | 50   | Complex reasoning (low quota)   |

---

## Deploying to Alexa Developer Console

1. Go to https://developer.amazon.com/alexa/console/ask and sign in
2. Click **Create Skill** → enter a skill name → select **Other** → **Custom** → **Alexa-hosted (Python)** → choose a hosting region → click **Create Skill**
3. **Build tab → Invocation**: set the invocation name (e.g. `chat with gemini`)
4. **Build tab → JSON Editor**: paste the content of `interaction_model/en-US.json`; switch locale to `it-IT` and paste `it-IT.json` (repeat for other locales as needed)
5. Click **Save Model** then **Build Model** and wait for the build to complete
6. **Code tab**: before uploading, run `scripts/build_lambda.sh` to prepare the `lambda/` folder (requires `pip install poetry-plugin-export` once). Then replace each file in the console editor with the corresponding file from `lambda/`
7. **Code tab → Environment Variables** (gear/settings icon):
   - Add `GEMINI_API_KEY` → paste your key from Google AI Studio
   - Add `GEMINI_MODEL` → e.g. `gemini-2.5-flash`
   - Click **Save**
8. Click **Deploy** and wait for deployment to finish
9. **Test tab**: set toggle to **Development** → type or say your invocation phrase to test end-to-end

---

## Running Tests Locally

```bash
poetry run pytest --tb=short       # run all tests
poetry run ruff check src tests    # lint
poetry run mypy src                # type checking
```

---

## Versioning (Conventional Commits)

This project uses `python-semantic-release` driven by Conventional Commits on `main`.

| Commit prefix | Version bump        | Example                              |
|---------------|---------------------|--------------------------------------|
| `feat:`       | MINOR (0.1.0→0.2.0) | `feat: add Calendar intent`          |
| `fix:`        | PATCH (0.1.0→0.1.1) | `fix: handle empty question slot`    |
| `feat!:`      | MAJOR (0.1.0→1.0.0) | `feat!: redesign session management` |
| `docs:`       | none                | `docs: update README`                |
| `chore:`      | none                | `chore: update dependencies`         |

Releases are created automatically on push to `main` via GitHub Actions.

---

## Project Structure

```
alexa-skill-gemini/
├── lambda/
│   ├── lambda_function.py        ← Alexa entry point
│   ├── alexa_gemini/             ← copied from src/ by build_lambda.sh (gitignored)
│   └── requirements.txt          ← pinned flat deps for Alexa-hosted runtime
├── src/
│   └── alexa_gemini/
│       ├── config.py             ← Config dataclass, all env var access
│       ├── handlers/             ← one handler per intent/lifecycle event
│       ├── services/gemini.py    ← GeminiService, history management
│       └── utils/text.py         ← strip_markdown_for_tts()
├── tests/                        ← pytest test suite
├── interaction_model/            ← Alexa interaction models (5 locales)
├── scripts/build_lambda.sh       ← manual deploy prep
├── .github/workflows/ci.yml      ← lint + test + semantic-release
├── .env.example                  ← committed variable template
├── pyproject.toml                ← Poetry + all tool configs
└── README.md
```
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with full deploy guide"
```

---

## Task 11: Run full verification + initial commit + final commit

- [ ] **Step 1: Run full test suite**

```bash
poetry run pytest --tb=short
```

Expected: all tests pass.

- [ ] **Step 2: Run linter**

```bash
poetry run ruff check src tests
```

Expected: no errors.

- [ ] **Step 3: Run type checker**

```bash
poetry run mypy src
```

Expected: `Success: no issues found`.

- [ ] **Step 4: Verify .env is gitignored**

```bash
git status
```

Confirm `.env` does not appear as a tracked file.

- [ ] **Step 5: Verify .env.example is staged/tracked**

```bash
git ls-files .env.example
```

Expected: `.env.example`

- [ ] **Step 6: Stage all remaining files and create initial commit**

```bash
git add .
git status  # review what's staged — confirm .env is NOT included
git commit -m "chore: initial project scaffold"
```

- [ ] **Step 7: Create the final breaking-change commit to trigger 1.0.0**

```bash
git commit --allow-empty -m "feat!: complete alexa gemini assistant"
```

This empty commit triggers `python-semantic-release` to bump the version to `1.0.0` on the next push to `main`.

---

## Final Checklist

After all tasks are done, verify:

- [ ] `poetry install` — no errors
- [ ] `poetry run pytest` — all tests pass
- [ ] `poetry run ruff check src tests` — no errors
- [ ] `poetry run mypy src` — no errors
- [ ] `.env` is NOT tracked by git (`git ls-files .env` returns nothing)
- [ ] `.env.example` IS tracked (`git ls-files .env.example` returns `.env.example`)
- [ ] `lambda/requirements.txt` is present and non-empty
- [ ] `Config` raises `EnvironmentError` when `GEMINI_API_KEY` is missing (covered by tests)
- [ ] `gemini-2.5-flash` is the default model (covered by tests)
- [ ] All 5 `interaction_model/*.json` files are valid JSON
- [ ] `README.md` contains the Alexa Developer Console deploy guide
- [ ] Two commits exist: `chore: initial project scaffold` and `feat!: complete alexa gemini assistant`
