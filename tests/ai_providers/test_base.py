import base64
import io

import pytest
from PIL import Image

from ebook2text._exceptions import MissingConfigurationError
from ebook2text.ai_providers._base import (
    BaseOCRProvider,
    SourceImage,
    clean_response,
    detect_media_type,
    import_provider_sdk,
    prepare_image,
)


def _encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _image_base64(format: str) -> str:
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), color="white").save(buffer, format=format)
    return _encode(buffer.getvalue())


class RecordingProvider(BaseOCRProvider):
    api_key_env = "FAKE_OCR_API_KEY"

    def __init__(self, responses: list[str], **kwargs):
        super().__init__(model="fake-model", **kwargs)
        self.responses = responses
        self.calls: list[list[SourceImage]] = []

    def _request(self, images: list[SourceImage]) -> str:
        self.calls.append(images)
        return self.responses[
            min(len(self.calls) - 1, len(self.responses) - 1)
        ]


class TestCleanResponse:
    def test_passes_through_normal_text(self):
        assert clean_response("Chapter One") == "Chapter One"

    def test_strips_no_text_found(self):
        assert clean_response("No text found") == ""

    def test_strips_refusals(self):
        assert clean_response("I'm sorry, I cannot help with that") == ""


class TestDetectMediaType:
    def test_detects_png(self):
        assert detect_media_type(_image_base64("PNG")) == "image/png"

    def test_detects_jpeg(self):
        assert detect_media_type(_image_base64("JPEG")) == "image/jpeg"

    def test_detects_gif(self):
        assert detect_media_type(_image_base64("GIF")) == "image/gif"

    def test_detects_webp(self):
        assert detect_media_type(_image_base64("WEBP")) == "image/webp"

    def test_unknown_format_returns_none(self):
        assert detect_media_type(_encode(b"not an image at all")) is None


class TestPrepareImage:
    def test_known_format_passes_through(self):
        encoded = _image_base64("JPEG")
        image = prepare_image(encoded)
        assert image == SourceImage(encoded, "image/jpeg")

    def test_unknown_format_transcoded_to_png(self):
        image = prepare_image(_image_base64("BMP"))
        assert image.media_type == "image/png"
        decoded = base64.b64decode(image.base64_data)
        assert Image.open(io.BytesIO(decoded)).format == "PNG"


class TestPerformOcr:
    def test_empty_image_list_returns_empty_string(self):
        provider = RecordingProvider(responses=["should not be called"])
        assert provider.perform_ocr([]) == ""
        assert provider.calls == []

    def test_returns_recognized_text(self):
        provider = RecordingProvider(responses=["Chapter One"])
        assert provider.perform_ocr([_image_base64("PNG")]) == "Chapter One"
        assert len(provider.calls) == 1

    def test_passes_prepared_images_to_request(self):
        provider = RecordingProvider(responses=["text"])
        provider.perform_ocr([_image_base64("JPEG")])
        assert provider.calls[0][0].media_type == "image/jpeg"

    def test_no_text_found_returns_empty_without_retry(self):
        provider = RecordingProvider(responses=["No text found"])
        assert provider.perform_ocr([_image_base64("PNG")]) == ""
        assert len(provider.calls) == 1

    def test_refusal_retries_then_returns_empty(self):
        provider = RecordingProvider(responses=["I'm sorry, I cannot"])
        assert provider.perform_ocr([_image_base64("PNG")]) == ""
        assert len(provider.calls) == 4

    def test_refusal_then_success_returns_text(self):
        provider = RecordingProvider(
            responses=["I cannot do that", "Real text"]
        )
        assert provider.perform_ocr([_image_base64("PNG")]) == "Real text"
        assert len(provider.calls) == 2

    def test_empty_response_returns_empty_string(self):
        provider = RecordingProvider(responses=[""])
        assert provider.perform_ocr([_image_base64("PNG")]) == ""

    def test_undecodable_image_swallowed(self):
        provider = RecordingProvider(responses=["unreachable"])
        assert provider.perform_ocr([_encode(b"not an image at all")]) == ""
        assert provider.calls == []

    def test_unexpected_exception_swallowed(self):
        class ExplodingProvider(RecordingProvider):
            def _request(self, images):
                raise RuntimeError("network down")

        provider = ExplodingProvider(responses=[])
        assert provider.perform_ocr([_image_base64("PNG")]) == ""

    def test_configuration_error_propagates(self):
        class UnconfiguredProvider(RecordingProvider):
            def _request(self, images):
                self._resolve_api_key()
                return "unreachable"

        provider = UnconfiguredProvider(responses=[])
        with pytest.raises(MissingConfigurationError):
            provider.perform_ocr([_image_base64("PNG")])


class TestResolveApiKey:
    def test_explicit_key_wins(self, monkeypatch):
        monkeypatch.setenv("FAKE_OCR_API_KEY", "env-key")
        provider = RecordingProvider(responses=[], api_key="explicit-key")
        assert provider._resolve_api_key() == "explicit-key"

    def test_env_key_used_when_no_explicit_key(self, monkeypatch):
        monkeypatch.setenv("FAKE_OCR_API_KEY", "env-key")
        provider = RecordingProvider(responses=[])
        assert provider._resolve_api_key() == "env-key"

    def test_missing_key_raises_naming_env_var(self, monkeypatch):
        monkeypatch.delenv("FAKE_OCR_API_KEY", raising=False)
        provider = RecordingProvider(responses=[])
        with pytest.raises(
            MissingConfigurationError, match="FAKE_OCR_API_KEY"
        ):
            provider._resolve_api_key()


class TestImportProviderSdk:
    def test_imports_installed_module(self):
        assert import_provider_sdk("base64", "irrelevant").b64encode

    def test_missing_module_raises_naming_extra(self):
        from ebook2text._exceptions import MissingDependencyError

        with pytest.raises(
            MissingDependencyError, match=r"ebook2text\[gemini\]"
        ):
            import_provider_sdk("nonexistent_sdk_module", "gemini")
