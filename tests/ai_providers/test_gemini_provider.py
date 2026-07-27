import base64
import io

import pytest
from PIL import Image

from ebook2text.ai_providers._base import OCR_PROMPT
from ebook2text.ai_providers._gemini import GeminiOCR


def _image_base64(format: str = "PNG") -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color="white").save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@pytest.fixture
def provider(mocker):
    ocr = GeminiOCR(model="gemini-2.5-flash", api_key="gm-key")
    ocr._client = mocker.MagicMock()
    return ocr


def test_uses_gemini_api_key_env():
    assert GeminiOCR.api_key_env == "GEMINI_API_KEY"


def test_sends_prompt_and_decoded_image_parts(provider, mocker):
    provider._client.models.generate_content.return_value = mocker.MagicMock(
        text="Detected text"
    )
    encoded = _image_base64("JPEG")

    assert provider.perform_ocr([encoded]) == "Detected text"

    call = provider._client.models.generate_content.call_args
    assert call.kwargs["model"] == "gemini-2.5-flash"
    contents = call.kwargs["contents"]
    assert contents[0] == OCR_PROMPT
    part = contents[1]
    assert part.inline_data.mime_type == "image/jpeg"
    assert part.inline_data.data == base64.b64decode(encoded)
    assert call.kwargs["config"].max_output_tokens == 1000


def test_none_text_returns_empty_string(provider, mocker):
    provider._client.models.generate_content.return_value = mocker.MagicMock(
        text=None
    )
    assert provider.perform_ocr([_image_base64()]) == ""


def test_api_exception_returns_empty_string(provider):
    provider._client.models.generate_content.side_effect = RuntimeError("x")
    assert provider.perform_ocr([_image_base64()]) == ""


def test_factory_builds_gemini(monkeypatch):
    from ebook2text.ai_providers import get_ocr_provider

    monkeypatch.setattr(
        "ebook2text.ai_providers._factory.load_dotenv", lambda: None
    )
    monkeypatch.setenv("OCR_PROVIDER", "gemini")
    monkeypatch.setenv("OCR_MODEL", "gemini-2.5-flash")
    assert isinstance(get_ocr_provider(), GeminiOCR)
