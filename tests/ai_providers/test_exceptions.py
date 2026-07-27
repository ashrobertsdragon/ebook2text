import pytest

from ebook2text._exceptions import (
    EbookConversionError,
    MissingConfigurationError,
    MissingDependencyError,
    OCRProviderError,
    UnsupportedProviderError,
)


@pytest.mark.parametrize(
    "exception_class",
    [
        UnsupportedProviderError,
        MissingDependencyError,
        MissingConfigurationError,
    ],
)
def test_provider_errors_subclass_ocr_provider_error(exception_class):
    assert issubclass(exception_class, OCRProviderError)


def test_ocr_provider_error_subclasses_ebook_conversion_error():
    assert issubclass(OCRProviderError, EbookConversionError)


def test_provider_error_carries_message():
    error = MissingDependencyError("pip install ebook2text[gemini]")
    assert "ebook2text[gemini]" in str(error)
