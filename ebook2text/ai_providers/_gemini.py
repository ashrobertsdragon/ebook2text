"""Google Gemini OCR provider."""

import base64
from functools import cached_property
from typing import Any

from ebook2text.ai_providers._base import (
    OCR_PROMPT,
    BaseOCRProvider,
    SourceImage,
    import_provider_sdk,
)


class GeminiOCR(BaseOCRProvider):
    """OCR provider backed by the Google Gemini API."""

    api_key_env = "GEMINI_API_KEY"

    @cached_property
    def _genai(self) -> Any:
        """Import the google-genai SDK lazily."""
        return import_provider_sdk("google.genai", "gemini")

    @cached_property
    def _client(self) -> Any:
        """Lazily construct the Gemini client."""
        return self._genai.Client(api_key=self._resolve_api_key())

    def _request(self, images: list[SourceImage]) -> str:
        """Send one generate_content request with prompt and image parts."""
        types = self._genai.types
        parts = [
            types.Part.from_bytes(
                data=base64.b64decode(image.base64_data),
                mime_type=image.media_type,
            )
            for image in images
        ]
        response = self._client.models.generate_content(
            model=self.model,
            contents=[OCR_PROMPT, *parts],
            config=types.GenerateContentConfig(
                max_output_tokens=self.max_tokens
            ),
        )
        return response.text or ""
