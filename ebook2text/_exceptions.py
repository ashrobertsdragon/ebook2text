class ImageSizeError(Exception):
    """
    Custom exception class for image size-related errors.
    """

    pass


class ImageTooSmallError(ImageSizeError):
    """
    Custom exception class for handling errors related to an image being too
    small.
    """

    pass


class ImageTooLargeError(ImageSizeError):
    """
    Custom exception class for handling errors related to an image being too
    large.
    """

    pass


class NoResponseError(Exception):
    pass


class EbookConversionError(Exception):
    pass


class EpubConversionError(EbookConversionError):
    pass


class PDFConversionError(EbookConversionError):
    pass


class DocxConversionError(EbookConversionError):
    pass


class TextConversionError(EbookConversionError):
    pass


class OCRProviderError(EbookConversionError):
    """Base class for errors raised by AI OCR providers."""

    pass


class UnsupportedProviderError(OCRProviderError):
    """Raised when an unknown OCR provider name is requested."""

    pass


class MissingDependencyError(OCRProviderError):
    """Raised when a provider's SDK is not installed."""

    pass


class MissingConfigurationError(OCRProviderError):
    """Raised when required provider configuration is absent."""

    pass
