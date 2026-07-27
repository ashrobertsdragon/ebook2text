"""OpenRouter OCR provider, wire-compatible with the OpenAI API."""

from functools import cached_property

from openai import OpenAI

from ebook2text.ai_providers._openai import OpenAIOCR


class OpenRouterOCR(OpenAIOCR):
    """OCR provider routing requests through OpenRouter."""

    api_key_env = "OPENROUTER_API_KEY"
    BASE_URL = "https://openrouter.ai/api/v1"

    @cached_property
    def _client(self) -> OpenAI:
        """Lazily construct an OpenAI client pointed at OpenRouter."""
        return OpenAI(api_key=self._resolve_api_key(), base_url=self.BASE_URL)
