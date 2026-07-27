import pytest

from ebook2text._exceptions import (
    MissingConfigurationError,
    UnsupportedProviderError,
)
from ebook2text.ai_providers import get_ocr_provider
from ebook2text.ai_providers._openai import OpenAIOCR


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.setattr(
        "ebook2text.ai_providers._factory.load_dotenv", lambda: None
    )
    for var in ("OCR_PROVIDER", "OCR_MODEL", "OCR_MAX_TOKENS", "OPENAI_MODEL"):
        monkeypatch.delenv(var, raising=False)


class TestProviderSelection:
    def test_defaults_to_openai(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "gpt-4o-mini")
        assert isinstance(get_ocr_provider(), OpenAIOCR)

    def test_env_var_selects_provider(self, monkeypatch):
        monkeypatch.setenv("OCR_PROVIDER", "openai")
        monkeypatch.setenv("OCR_MODEL", "gpt-4o-mini")
        assert isinstance(get_ocr_provider(), OpenAIOCR)

    def test_argument_overrides_env(self, monkeypatch):
        monkeypatch.setenv("OCR_PROVIDER", "bogus-provider")
        monkeypatch.setenv("OCR_MODEL", "gpt-4o-mini")
        assert isinstance(get_ocr_provider(provider="openai"), OpenAIOCR)

    def test_provider_name_is_case_insensitive(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "gpt-4o-mini")
        assert isinstance(get_ocr_provider(provider="OpenAI"), OpenAIOCR)

    def test_unknown_provider_raises(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "some-model")
        with pytest.raises(UnsupportedProviderError, match="bogus"):
            get_ocr_provider(provider="bogus")


class TestModelResolution:
    def test_model_argument_wins(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "env-model")
        provider = get_ocr_provider(model="arg-model")
        assert provider.model == "arg-model"

    def test_ocr_model_env_used(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "env-model")
        assert get_ocr_provider().model == "env-model"

    def test_falls_back_to_openai_model_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_MODEL", "legacy-model")
        assert get_ocr_provider().model == "legacy-model"

    def test_missing_model_raises(self):
        with pytest.raises(MissingConfigurationError, match="OCR_MODEL"):
            get_ocr_provider()


class TestMaxTokens:
    def test_default_is_1000(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "m")
        assert get_ocr_provider().max_tokens == 1000

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "m")
        monkeypatch.setenv("OCR_MAX_TOKENS", "250")
        assert get_ocr_provider().max_tokens == 250

    def test_argument_wins(self, monkeypatch):
        monkeypatch.setenv("OCR_MODEL", "m")
        monkeypatch.setenv("OCR_MAX_TOKENS", "250")
        assert get_ocr_provider(max_tokens=500).max_tokens == 500
