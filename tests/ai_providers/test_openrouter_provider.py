from ebook2text.ai_providers._openai import OpenAIOCR
from ebook2text.ai_providers._openrouter import OpenRouterOCR


def test_is_openai_subclass():
    assert issubclass(OpenRouterOCR, OpenAIOCR)


def test_uses_openrouter_api_key_env():
    assert OpenRouterOCR.api_key_env == "OPENROUTER_API_KEY"


def test_client_built_with_openrouter_base_url(mocker):
    openai_class = mocker.patch("ebook2text.ai_providers._openrouter.OpenAI")
    provider = OpenRouterOCR(
        model="anthropic/claude-sonnet-4.5", api_key="or-key"
    )
    provider._client
    openai_class.assert_called_once_with(
        api_key="or-key", base_url="https://openrouter.ai/api/v1"
    )


def test_factory_builds_openrouter(monkeypatch):
    from ebook2text.ai_providers import get_ocr_provider

    monkeypatch.setattr(
        "ebook2text.ai_providers._factory.load_dotenv", lambda: None
    )
    monkeypatch.setenv("OCR_PROVIDER", "openrouter")
    monkeypatch.setenv("OCR_MODEL", "google/gemini-2.5-flash")
    assert isinstance(get_ocr_provider(), OpenRouterOCR)
