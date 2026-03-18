import pytest

from alexa_gemini.config import load_config


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
