import base64
import io

import pytest
from PIL import Image

from ebook2text.ai_providers._base import OCR_PROMPT
from ebook2text.ai_providers._openai import OpenAIOCR


def _image_base64(format: str = "PNG") -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color="white").save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _response_with(mocker, content):
    return mocker.MagicMock(
        choices=[mocker.MagicMock(message=mocker.MagicMock(content=content))]
    )


@pytest.fixture
def provider(mocker):
    ocr = OpenAIOCR(model="gpt-4o-mini", api_key="test-key")
    ocr._client = mocker.MagicMock()
    return ocr


class TestOpenAIWireShape:
    def test_sends_prompt_and_image_parts(self, provider, mocker):
        provider._client.chat.completions.create.return_value = _response_with(
            mocker, "Detected text"
        )
        result = provider.perform_ocr([_image_base64("JPEG")])

        assert result == "Detected text"
        call = provider._client.chat.completions.create.call_args
        assert call.kwargs["model"] == "gpt-4o-mini"
        assert call.kwargs["max_tokens"] == 1000
        messages = call.kwargs["messages"]
        assert len(messages) == 1
        content = messages[0]["content"]
        assert messages[0]["role"] == "user"
        assert content[0] == {"type": "text", "text": OCR_PROMPT}
        image_part = content[1]
        assert image_part["type"] == "image_url"
        assert image_part["image_url"]["detail"] == "low"
        assert image_part["image_url"]["url"].startswith(
            "data:image/jpeg;base64,"
        )

    def test_multiple_images_sent_in_one_message(self, provider, mocker):
        provider._client.chat.completions.create.return_value = _response_with(
            mocker, "text"
        )
        provider.perform_ocr([_image_base64(), _image_base64()])

        content = provider._client.chat.completions.create.call_args.kwargs[
            "messages"
        ][0]["content"]
        assert len(content) == 3

    def test_none_content_returns_empty_string(self, provider, mocker):
        provider._client.chat.completions.create.return_value = _response_with(
            mocker, None
        )
        assert provider.perform_ocr([_image_base64()]) == ""

    def test_refusal_retries_four_times(self, provider, mocker):
        provider._client.chat.completions.create.return_value = _response_with(
            mocker, "I'm sorry, I cannot"
        )
        assert provider.perform_ocr([_image_base64()]) == ""
        assert provider._client.chat.completions.create.call_count == 4

    def test_api_exception_returns_empty_string(self, provider):
        provider._client.chat.completions.create.side_effect = RuntimeError(
            "boom"
        )
        assert provider.perform_ocr([_image_base64()]) == ""


class TestOpenAIClientConstruction:
    def test_client_built_with_resolved_api_key(self, mocker):
        openai_class = mocker.patch("ebook2text.ai_providers._openai.OpenAI")
        provider = OpenAIOCR(model="gpt-4o-mini", api_key="explicit-key")
        provider._client
        openai_class.assert_called_once_with(api_key="explicit-key")
