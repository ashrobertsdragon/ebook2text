"""Shared OCR provider contract, prompt, and image preparation helpers."""

import base64
import importlib
import io
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import ModuleType
from typing import ClassVar, Protocol, runtime_checkable

from PIL import Image

from ebook2text import logger
from ebook2text._exceptions import (
    MissingConfigurationError,
    MissingDependencyError,
    NoResponseError,
    OCRProviderError,
)

OCR_PROMPT: str = (
    "Please provide the text in these images as a single "
    "combined statement with spaces as appropriate "
    "without any commentary. Use your judgment on whether"
    " consecutive images are a single word or multiple "
    "words. If there is no text in the image, or it is "
    "unreadable, respond with 'No text found'"
)

REFUSAL_MARKERS: list[str] = [
    "I'm sorry",
    "I apologize",
    "I cannot",
    "text-based",
]

DEFAULT_MAX_TOKENS: int = 1000
MAX_RETRIES: int = 3

_MAGIC_SIGNATURES: dict[str, bytes] = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "image/gif": b"GIF8",
}


@runtime_checkable
class OCRProvider(Protocol):
    """Structural contract for OCR providers accepted by converters."""

    def perform_ocr(self, base64_images: list[str]) -> str:
        """Extract text from a list of base64-encoded images."""
        ...


@dataclass(frozen=True)
class SourceImage:
    """A base64-encoded image with its detected media type."""

    base64_data: str
    media_type: str


def clean_response(answer: str) -> str:
    """Map 'No text found' and refusal responses to an empty string."""
    if answer == "No text found":
        return ""
    if _is_refusal(answer):
        return ""
    return answer


def _is_refusal(answer: str) -> bool:
    """Check whether a response contains a known refusal marker."""
    return any(marker in answer for marker in REFUSAL_MARKERS)


def detect_media_type(base64_image: str) -> str | None:
    """Detect the image media type from base64-encoded magic bytes."""
    header = base64.b64decode(base64_image[:24])
    for media_type, signature in _MAGIC_SIGNATURES.items():
        if header.startswith(signature):
            return media_type
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def prepare_image(base64_image: str) -> SourceImage:
    """Build a SourceImage, transcoding unsupported formats to PNG."""
    media_type = detect_media_type(base64_image)
    if media_type is not None:
        return SourceImage(base64_image, media_type)
    decoded = base64.b64decode(base64_image)
    buffer = io.BytesIO()
    Image.open(io.BytesIO(decoded)).save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return SourceImage(encoded, "image/png")


def import_provider_sdk(module: str, extra: str) -> ModuleType:
    """Import a provider SDK, raising a helpful error if not installed."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise MissingDependencyError(
            f"The '{extra}' extra is required for this OCR provider. "
            f"Install it with: pip install ebook2text[{extra}]"
        ) from exc


class BaseOCRProvider(ABC):
    """Template for OCR providers: shared retry, refusal, and error logic."""

    api_key_env: ClassVar[str]

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        """Store configuration; SDK clients are constructed lazily."""
        self.model = model
        self.max_tokens = max_tokens
        self._api_key = api_key

    def _resolve_api_key(self) -> str:
        """Return the configured API key or raise naming the env var."""
        key = self._api_key or os.getenv(self.api_key_env)
        if not key:
            raise MissingConfigurationError(
                f"Set the {self.api_key_env} environment variable or pass "
                "api_key to the provider."
            )
        return key

    @abstractmethod
    def _request(self, images: list[SourceImage]) -> str:
        """Make one provider API call and return the raw response text."""

    def perform_ocr(self, base64_images: list[str]) -> str:
        """
        Perform OCR on a list of base64-encoded images.

        Refusals are retried up to MAX_RETRIES times; unrecoverable API
        errors are logged and mapped to an empty string. Configuration and
        dependency errors propagate so misconfiguration is not silent.
        """
        if not base64_images:
            logger.info("No images to OCR")
            return ""
        try:
            images = [prepare_image(image) for image in base64_images]
            for _ in range(MAX_RETRIES + 1):
                answer = self._request(images)
                if not answer:
                    raise NoResponseError("No response found")
                if not _is_refusal(answer):
                    return clean_response(answer)
                logger.error(f"OCR provider refusal: {answer}")
            raise NoResponseError(f"OCR provider refused: {answer}")
        except OCRProviderError:
            raise
        except Exception as e:
            logger.exception("An error occurred %s", str(e))
            return ""
