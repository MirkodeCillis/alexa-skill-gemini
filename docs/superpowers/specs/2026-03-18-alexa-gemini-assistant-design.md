# Alexa Gemini Assistant — Design Spec

**Date:** 2026-03-18
**Project:** alexa-skill-gemini
**Status:** Approved (v2 — post-review)

---

## 1. Overview

An Amazon Alexa Skill that acts as a conversational voice assistant powered by Google Gemini. Users invoke the skill and ask free-form questions in any supported language; Gemini replies in the same language, optionally grounding answers with live web search. Conversation history is maintained across turns within a single Alexa session.

**Tech stack:** ASK SDK (Python), Google Gemini 2.5 Flash (`google-genai` SDK), Poetry, python-semantic-release, GitHub Actions, Alexa-hosted Python runtime (Python 3.11).

---

## 2. Architecture

```
Alexa Voice Service
      ↓  (JSON request)
lambda/lambda_function.py          ← entry point; loads .env, registers handlers
      ↓
ask_sdk_core.SkillBuilder          ← routes requests to the correct handler
      ↓
src/alexa_gemini/handlers/         ← one handler per intent/lifecycle event
  launch.py                        ← welcome message
  llm_intent.py                    ← core chat loop (LLMIntent)
  help.py                          ← usage instructions
  stop_cancel.py                   ← goodbye + history clear
  session_ended.py                 ← cleanup
      ↓
src/alexa_gemini/services/
  gemini.py  (GeminiService)       ← wraps google-genai, manages history, calls Gemini
      ↓
src/alexa_gemini/config.py         ← frozen Config dataclass loaded from os.environ
src/alexa_gemini/utils/text.py     ← strip_markdown_for_tts()
```

**Alexa-hosted deployment note:** The Alexa-hosted runtime adds only `lambda/` to `sys.path`. The `src/alexa_gemini/` package must be copied into `lambda/alexa_gemini/` before deployment. `scripts/build_lambda.sh` handles this (see Section 8). For local development, `src/` is added to `PYTHONPATH` via `[tool.pytest.ini_options] pythonpath = ["src"]` in `pyproject.toml`.

---

## 3. Components

### 3.1 Config (`src/alexa_gemini/config.py`)

- Frozen dataclass with fields: `gemini_api_key: str`, `gemini_model: str`.
- `load_config()` reads `GEMINI_API_KEY` and `GEMINI_MODEL` from `os.environ`.
- Raises `EnvironmentError` with a clear bilingual message if `GEMINI_API_KEY` is empty or missing.
- Default for `GEMINI_MODEL`: `gemini-2.5-flash`.
- All `os.environ` access is centralized here; no direct `os.environ` calls elsewhere.

### 3.2 GeminiService (`src/alexa_gemini/services/gemini.py`)

- Constructor accepts `Config`, instantiates `google.genai.Client(api_key=config.gemini_api_key)`, stores `config.gemini_model` as `self.model`.

- **System instruction** (a module-level constant string, passed at every API call via `GenerateContentConfig`):
  > "You are a concise voice assistant integrated with Amazon Alexa. Always detect the language of the user's message and reply in the same language. Keep all responses short and suitable for text-to-speech output: no markdown, no bullet points, no symbols, no numbered lists. If the user asks about current events, recent news, or real-time information, use the web search tool to find an accurate answer."

- `chat(question: str, history: list[dict]) -> tuple[str, list[dict]]`:
  1. **Truncates** the incoming history to the last `MAX_HISTORY_TURNS * 2` messages first (default `MAX_HISTORY_TURNS = 10`, i.e. keep at most 20 messages). This prevents the Alexa session attribute payload from exceeding the ~24 KB response size limit.
  2. Appends `{"role": "user", "parts": [{"text": question}]}` to the truncated copy (now at most 21 messages before the call; after the model reply is appended in step 7, stored history stabilises at ≤22 messages — well within the payload limit).
  3. Builds a `GenerateContentConfig` with:
     ```python
     from google.genai.types import GenerateContentConfig, Tool, GoogleSearch
     cfg = GenerateContentConfig(
         system_instruction=SYSTEM_INSTRUCTION,
         tools=[Tool(google_search=GoogleSearch())],
     )
     ```
  4. Calls:
     ```python
     response = self.client.models.generate_content(
         model=self.model,
         contents=history_copy,   # list of {"role": ..., "parts": [...]} dicts
         config=cfg,
     )
     ```
  5. Extracts text: `text = response.text`. If `response.text` is `None` or empty (e.g. tool-only turn, safety block), returns the bilingual fallback string and the **original** (pre-call) history unchanged.
  6. Strips markdown via `strip_markdown_for_tts(text)`.
  7. Appends `{"role": "model", "parts": [{"text": cleaned_text}]}` to the truncated history copy.
  8. Returns `(cleaned_text, updated_history)`.

- **Error handling:** Catch `google.genai.errors.APIError` (import: `from google.genai import errors`) and generic `Exception`. Log the error, return bilingual fallback and original history unchanged. No re-raise.

- **Bilingual fallback string** (used for all error/empty-response cases):
  `"I'm sorry, something went wrong. — Mi dispiace, si è verificato un errore."`

### 3.3 strip_markdown_for_tts (`src/alexa_gemini/utils/text.py`)

Removes from text:
- Headers (`#`, `##`, `###` at line start)
- Bold/italic (`**`, `*`, `__`, `_` wrapping)
- Bullet lines (`- `, `* `, `• ` at line start)
- Numbered list prefixes (`1. `, `2. `, …)
- Inline and block code (backtick fences)
- Markdown links `[text](url)` → keeps only `text`
- Collapses 3+ consecutive newlines to one

### 3.4 Handlers

All handlers call `load_config()` and instantiate `GeminiService` inside `handle()` (not at module level). This is intentional: on Alexa-hosted, the Lambda container is reused across warm-start invocations, but the env vars are guaranteed to be set before any handler is called. Instantiating per-request avoids issues with import-time ordering when `load_dotenv()` may not yet have run. The performance overhead is acceptable for a voice skill.

History is read/written via `handler_input.attributes_manager.session_attributes["history"]`, initialized to `[]` if absent.

| Handler | Intent / Event | `should_end_session` | Behavior |
|---|---|---|---|
| `LaunchRequestHandler` | `LaunchRequest` | `False` | Bilingual welcome |
| `LLMIntentHandler` | `LLMIntent` | `False` | Extract slot → validate → call `GeminiService.chat()` → save history → return response |
| `HelpIntentHandler` | `AMAZON.HelpIntent` | `False` | Bilingual usage instructions; session stays open |
| `StopCancelIntentHandler` | `AMAZON.StopIntent`, `AMAZON.CancelIntent` | `True` | Goodbye message, clears history from session attributes |
| `SessionEndedRequestHandler` | `SessionEndedRequest` | N/A (no response) | Clears history |

**Empty slot handling in `LLMIntentHandler`:** If `slots.get("question")` is absent or its `.value` is empty/whitespace, do not call `GeminiService`; instead return a reprompt: `"Sorry, I didn't catch that. What would you like to ask? — Scusa, non ho capito. Cosa vorresti chiedere?"` with `should_end_session=False`.

### 3.5 Interaction Models

Five locale files in `interaction_model/`:

| Locale | File | Invocation name |
|---|---|---|
| English (US) | `en-US.json` | `chat with gemini` |
| Italian | `it-IT.json` | `chatta con gemini` |
| French | `fr-FR.json` | `discute avec gemini` |
| German | `de-DE.json` | `chatte mit gemini` |
| Spanish (ES) | `es-ES.json` | `habla con gemini` |

Each model includes:
- `LLMIntent` with `question` slot of type `AMAZON.SearchQuery` — marked **optional** (no dialog management); the handler validates the slot value as described in 3.4.
- ≥10 sample utterances in the locale's language.
- Built-in intents: `AMAZON.HelpIntent`, `AMAZON.CancelIntent`, `AMAZON.StopIntent`.

### 3.6 lambda/ (deployment target)

- `lambda_function.py`: calls `load_dotenv()` first, then imports and registers all handlers.
- `requirements.txt`: pinned flat deps generated by `poetry export --without-hashes --without dev`.
- `lambda/alexa_gemini/`: copy of `src/alexa_gemini/` placed here by `build_lambda.sh` before upload to the Alexa Developer Console.

---

## 4. Data Flow (per turn)

```
1. User speaks → Alexa sends IntentRequest (LLMIntent, slot: question)
2. LLMIntentHandler.handle():
   a. Read history from session_attributes (default [])
   b. Validate question slot — if empty: reprompt and return
   c. Call GeminiService.chat(question, history)
      i.   Truncate history copy to last MAX_HISTORY_TURNS*2 messages
      ii.  Append user message to truncated copy
      iii. Call Gemini API with full history copy + google_search tool + system_instruction
      iv.  Check response.text: if None/empty → return fallback + original history
      v.   Strip markdown from response text
      vi.  Append model message to history copy
      vii. Return (cleaned_text, updated_history)
   d. Write updated_history back to session_attributes
   e. Return Alexa response with cleaned text, should_end_session=False
3. Alexa speaks the response, session stays open
```

---

## 5. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Google AI Studio API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model identifier |

- `.env.example`: committed, documents all variables.
- `.env`: gitignored, pre-filled for local dev.
- `load_dotenv()` is called once at the top of `lambda_function.py`; silently no-ops on Alexa-hosted where `.env` is not present.
- `pyproject.toml` specifies `python = "^3.11"` — must remain in sync with the Alexa-hosted Python 3.11 runtime.

---

## 6. Testing

All external calls (`google.genai.Client`, Alexa `HandlerInput`) are mocked.

**`tests/conftest.py`** provides shared fixtures:
- `mock_handler_input(intent_name, slots)` — returns a mock `HandlerInput` with configurable intent name, slots dict, and an empty `session_attributes` dict.
- `mock_gemini_service` — a `MagicMock` replacing `GeminiService` that returns a configurable `(response_text, updated_history)` tuple.

| Test file | Test cases |
|---|---|
| `test_config.py` | Load success with both vars set; `EnvironmentError` when `GEMINI_API_KEY` empty; `EnvironmentError` when `GEMINI_API_KEY` absent; default model `gemini-2.5-flash` when `GEMINI_MODEL` not set |
| `test_gemini_service.py` | History truncated to `MAX_HISTORY_TURNS*2` before user message appended; user message appended after truncation; model reply appended after successful call; `strip_markdown_for_tts` applied to raw response; bilingual fallback on `APIError`; bilingual fallback on generic `Exception`; bilingual fallback when `response.text` is `None`; history not modified when fallback is returned |
| `test_handlers.py` | `LLMIntentHandler.can_handle()` True for `LLMIntent`; empty `question` slot returns reprompt without calling `GeminiService`; `question` slot extracted correctly; history initialized to `[]` when absent; `GeminiService.chat()` called with correct args; updated history written back to session attributes; non-empty speech output returned; `should_end_session=False`; `strip_markdown_for_tts("")` returns `""` |

---

## 7. CI/CD

**lint-and-test** (every push/PR):
```
checkout → setup Python 3.11 → pip install poetry → poetry install
→ ruff check src tests → mypy src → pytest --tb=short
```

**release** (push to **`main` branch only**, needs lint-and-test):
```
on: push
branches: [main]
```
```
checkout (fetch-depth: 0) → pip install poetry python-semantic-release
→ semantic-release version → semantic-release publish
```
Env: `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}`. The `branches: [main]` filter in the `on: push` trigger is mandatory — without it, any push to any branch could trigger a release.

Python version in CI (3.11) must match Alexa-hosted runtime. If the Alexa runtime is upgraded, update both `pyproject.toml` and `.github/workflows/ci.yml`.

---

## 8. build_lambda.sh

`scripts/build_lambda.sh` is used for manual deployment preparation. Steps must execute in this exact order:

1. **Remove stale copy:** `rm -rf lambda/alexa_gemini/` — prevents stale files from a previous build.
2. **Copy source:** `cp -r src/alexa_gemini lambda/alexa_gemini/` — places the package where the Alexa-hosted runtime can find it.
3. **Install deps:** `pip install -r lambda/requirements.txt --target lambda/` — installs pinned production deps into `lambda/`. **This step must run after step 2** to avoid any dep installing over the freshly copied package.
4. Prints a summary of what was copied.

Note: Poetry 1.8+ requires the `poetry-plugin-export` plugin for `poetry export` to work. Install it once with: `pip install poetry-plugin-export`. The README documents this prerequisite.

This script is **not** run by CI (CI tests against `src/` directly via `PYTHONPATH`). It is run manually before uploading code to the Alexa Developer Console Code tab, or can be automated in a deploy job in the future.

---

## 9. Versioning Strategy

- Tool: `python-semantic-release`, driven by Conventional Commits on `main`.
- Initial commit: `chore: initial project scaffold` → version stays at `0.1.0`.
- Final commit: `feat!: complete alexa gemini assistant` → triggers MAJOR bump → `1.0.0` on first CI run.
- Changelog auto-generated in `CHANGELOG.md`.
- `version_toml = ["pyproject.toml:tool.poetry.version"]` tracks version in `pyproject.toml`.

---

## 10. Project Structure

```
alexa-skill-gemini/
├── lambda/
│   ├── lambda_function.py        ← Alexa entry point
│   ├── alexa_gemini/             ← copied from src/ by build_lambda.sh
│   └── requirements.txt          ← pinned flat deps for Alexa-hosted runtime
├── src/
│   └── alexa_gemini/
│       ├── __init__.py
│       ├── config.py
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── launch.py
│       │   ├── llm_intent.py
│       │   ├── help.py
│       │   ├── stop_cancel.py
│       │   └── session_ended.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── gemini.py
│       └── utils/
│           ├── __init__.py
│           └── text.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_gemini_service.py
│   └── test_handlers.py
├── interaction_model/
│   ├── en-US.json
│   ├── it-IT.json
│   ├── fr-FR.json
│   ├── de-DE.json
│   └── es-ES.json
├── scripts/
│   └── build_lambda.sh
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   └── superpowers/specs/
│       └── 2026-03-18-alexa-gemini-assistant-design.md
├── .env.example
├── .env
├── .gitignore
├── pyproject.toml
├── CHANGELOG.md
└── README.md
```
