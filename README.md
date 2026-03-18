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
