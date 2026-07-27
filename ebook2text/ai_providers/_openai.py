"""OpenAI OCR provider."""

from functools import cached_property
from typing import cast

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from ebook2text.ai_providers._base import (
    OCR_PROMPT,
    BaseOCRProvider,
    SourceImage,
)


class OpenAIOCR(BaseOCRProvider):
    """OCR provider backed by the OpenAI chat completions API."""

    api_key_env = "OPENAI_API_KEY"

    @cached_property
    def _client(self) -> OpenAI:
        """Lazily construct the OpenAI client."""
        return OpenAI(api_key=self._resolve_api_key())

    def _request(self, images: list[SourceImage]) -> str:
        """Send one chat completion request with prompt and image parts."""
        content: list[dict] = [
            {"type": "text", "text": OCR_PROMPT},
            *(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": (
                            f"data:{image.media_type};base64,"
                            f"{image.base64_data}"
                        ),
                        "detail": "low",
                    },
                }
                for image in images
            ),
        ]
        messages = cast(
            list[ChatCompletionMessageParam],
            [{"role": "user", "content": content}],
        )
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
        )
        if not response.choices:
            return ""
        return response.choices[0].message.content or ""
