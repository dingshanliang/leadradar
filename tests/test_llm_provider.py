from leadradar.config import Settings
from leadradar.llm.extraction import MockLLMProvider, OpenAICompatibleLLMProvider, get_llm_provider


def test_get_llm_provider_defaults_to_mock(monkeypatch):
    monkeypatch.setattr(
        "leadradar.config.get_settings",
        lambda: Settings(llm_provider="mock"),
    )
    provider = get_llm_provider()
    assert isinstance(provider, MockLLMProvider)


def test_get_llm_provider_uses_openai_when_configured(monkeypatch):
    monkeypatch.setattr(
        "leadradar.config.get_settings",
        lambda: Settings(
            llm_provider="openai_compatible",
            llm_api_key="sk-test",
            llm_base_url="https://api.example.com/v1",
            llm_model="gpt-4o-mini",
        ),
    )
    provider = get_llm_provider()
    assert isinstance(provider, OpenAICompatibleLLMProvider)
