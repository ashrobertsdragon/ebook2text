"""Anthropic Claude OCR provider."""

from functools import cached_property
from typing import Any

from ebook2text.ai_providers._base import (
    OCR_PROMPT,
    BaseOCRProvider,
    SourceImage,
    import_provider_sdk,
)


class AnthropicOCR(BaseOCRProvider):
    """OCR provider backed by the Anthropic Messages API."""

    api_key_env = "ANTHROPIC_API_KEY"

    @cached_property
    def _client(self) -> Any:
        """Lazily construct the Anthropic client."""
        anthropic = import_provider_sdk("anthropic", "anthropic")
        return anthropic.Anthropic(api_key=self._resolve_api_key())

    def _request(self, images: list[SourceImage]) -> str:
        """Send one messages request with image blocks and the OCR prompt."""
        content = [
            *(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image.media_type,
                        "data": image.base64_data,
                    },
                }
                for image in images
            ),
            {"type": "text", "text": OCR_PROMPT},
        ]
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        if response.stop_reason == "refusal":
            return ""
        return "".join(
            block.text for block in response.content if block.type == "text"
        )
