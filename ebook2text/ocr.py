"""Image encoding helpers and deprecated OCR entry point."""

import base64
import warnings

from ebook2text.ai_providers import get_ocr_provider


def encode_image_bytes(image_bytes: bytes) -> str:
    """Encode opened image as base64 string from bytes."""
    return base64.b64encode(image_bytes).decode("utf-8")


def encode_image_file(image_path: str) -> str:
    """Encode image as base64 string with file path."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def run_ocr(base64_images: list[str]) -> str:
    """
    Perform OCR on a list of base64-encoded images.

    Deprecated: construct a provider with
    ebook2text.ai_providers.get_ocr_provider and call perform_ocr instead.
    """
    warnings.warn(
        "run_ocr is deprecated; use "
        "ebook2text.ai_providers.get_ocr_provider().perform_ocr instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return get_ocr_provider().perform_ocr(base64_images)
