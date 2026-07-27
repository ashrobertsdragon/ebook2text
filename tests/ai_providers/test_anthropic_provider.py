import base64
import io

import pytest
from PIL import Image

from ebook2text.ai_providers._anthropic import AnthropicOCR
from ebook2text.ai_providers._base import OCR_PROMPT


def _image_base64(format: str = "PNG") -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color="white").save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _response_with(mocker, blocks, stop_reason="end_turn"):
    return mocker.MagicMock(content=blocks, stop_reason=stop_reason)


def _text_block(mocker, text):
    return mocker.MagicMock(type="text", text=text)


@pytest.fixture
def provider(mocker):
    ocr = AnthropicOCR(model="claude-haiku-4-5", api_key="ant-key")
    ocr._client = mocker.MagicMock()
    return ocr


def test_uses_anthropic_api_key_env():
    assert AnthropicOCR.api_key_env == "ANTHROPIC_API_KEY"


def test_sends_image_blocks_with_detected_media_type(provider, mocker):
    provider._client.messages.create.return_value = _response_with(
        mocker, [_text_block(mocker, "Detected text")]
    )
    encoded = _image_base64("JPEG")

    assert provider.perform_ocr([encoded]) == "Detected text"

    call = provider._client.messages.create.call_args
    assert call.kwargs["model"] == "claude-haiku-4-5"
    assert call.kwargs["max_tokens"] == 1000
    content = call.kwargs["messages"][0]["content"]
    image_block = content[0]
    assert image_block["type"] == "image"
    assert image_block["source"]["type"] == "base64"
    assert image_block["source"]["media_type"] == "image/jpeg"
    assert image_block["source"]["data"] == encoded
    assert content[-1] == {"type": "text", "text": OCR_PROMPT}


def test_refusal_stop_reason_returns_empty(provider, mocker):
    provider._client.messages.create.return_value = _response_with(
        mocker,
        [_text_block(mocker, "should not be read")],
        stop_reason="refusal",
    )
    assert provider.perform_ocr([_image_base64()]) == ""


def test_joins_only_text_blocks(provider, mocker):
    blocks = [
        mocker.MagicMock(type="thinking", thinking="hmm"),
        _text_block(mocker, "Part one. "),
        _text_block(mocker, "Part two."),
    ]
    provider._client.messages.create.return_value = _response_with(
        mocker, blocks
    )
    assert provider.perform_ocr([_image_base64()]) == "Part one. Part two."


def test_api_exception_returns_empty_string(provider):
    provider._client.messages.create.side_effect = RuntimeError("boom")
    assert provider.perform_ocr([_image_base64()]) == ""


def test_factory_builds_anthropic(monkeypatch):
    from ebook2text.ai_providers import get_ocr_provider

    monkeypatch.setattr(
        "ebook2text.ai_providers._factory.load_dotenv", lambda: None
    )
    monkeypatch.setenv("OCR_PROVIDER", "anthropic")
    monkeypatch.setenv("OCR_MODEL", "claude-haiku-4-5")
    assert isinstance(get_ocr_provider(), AnthropicOCR)
