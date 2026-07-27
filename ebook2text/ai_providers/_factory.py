"""Factory for constructing OCR providers from arguments or environment."""

import os

from dotenv import load_dotenv

from ebook2text._exceptions import (
    MissingConfigurationError,
    UnsupportedProviderError,
)
from ebook2text.ai_providers._base import (
    DEFAULT_MAX_TOKENS,
    BaseOCRProvider,
    OCRProvider,
)

SUPPORTED_PROVIDERS = ("openai", "openrouter", "gemini", "anthropic")


def _provider_class(name: str) -> type[BaseOCRProvider]:
    """Resolve a provider name to its class, importing lazily."""
    match name:
        case "openai":
            from ebook2text.ai_providers._openai import OpenAIOCR

            return OpenAIOCR
        case "openrouter":
            from ebook2text.ai_providers._openrouter import OpenRouterOCR

            return OpenRouterOCR
        case "gemini":
            from ebook2text.ai_providers._gemini import GeminiOCR

            return GeminiOCR
        case "anthropic":
            from ebook2text.ai_providers._anthropic import AnthropicOCR

            return AnthropicOCR
        case _:
            raise UnsupportedProviderError(
                f"Unknown OCR provider '{name}'. Supported providers: "
                f"{', '.join(SUPPORTED_PROVIDERS)}"
            )


def get_ocr_provider(
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
) -> OCRProvider:
    """
    Build an OCR provider from arguments, falling back to environment
    variables OCR_PROVIDER, OCR_MODEL (or legacy OPENAI_MODEL), and
    OCR_MAX_TOKENS.
    """
    load_dotenv()
    default_name: str = os.getenv("OCR_PROVIDER") or "openai"
    name = (provider or default_name).lower()
    resolved_model = (
        model or os.getenv("OCR_MODEL") or os.getenv("OPENAI_MODEL")
    )
    if resolved_model is None:
        raise MissingConfigurationError(
            "Set the OCR_MODEL environment variable or pass model=..."
        )
    resolved_max_tokens = max_tokens or int(
        os.getenv("OCR_MAX_TOKENS", str(DEFAULT_MAX_TOKENS))
    )
    provider_class = _provider_class(name)
    return provider_class(model=resolved_model, max_tokens=resolved_max_tokens)
