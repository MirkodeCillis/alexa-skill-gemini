"""Text utilities for making Gemini responses TTS-friendly."""

import re


def strip_markdown_for_tts(text: str) -> str:
    """Remove markdown formatting so Alexa reads the text naturally.

    Removes: headers, bold/italic, bullets, numbered lists,
    code blocks, markdown links. Collapses excessive blank lines.
    """
    if text == "":
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
