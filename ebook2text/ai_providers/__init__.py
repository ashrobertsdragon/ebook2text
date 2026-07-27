"""AI provider implementations for OCR of ebook images."""

from ebook2text.ai_providers._base import (
    BaseOCRProvider,
    OCRProvider,
    SourceImage,
)
from ebook2text.ai_providers._factory import get_ocr_provider

__all__ = [
    "BaseOCRProvider",
    "OCRProvider",
    "SourceImage",
    "get_ocr_provider",
]
