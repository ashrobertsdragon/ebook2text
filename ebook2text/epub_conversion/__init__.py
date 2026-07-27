from collections.abc import Generator
from pathlib import Path

from ebook2text.ai_providers import OCRProvider
from ebook2text.epub_conversion.epub_converter import EpubConverter
from ebook2text.epub_conversion.epub_text_extractor import EpubTextExtractor

__all__ = [
    "EpubConverter",
    "EpubTextExtractor",
    "convert_epub",
    "initialize_epub_converter",
]


def initialize_epub_converter(
    file_path: Path,
    metadata: dict,
    ocr_provider: OCRProvider | None = None,
) -> EpubConverter:
    text_extractor = EpubTextExtractor(ocr_provider=ocr_provider)
    return EpubConverter(file_path, metadata, text_extractor)


def convert_epub(
    file_path: Path,
    metadata: dict,
    ocr_provider: OCRProvider | None = None,
) -> Generator[str, None, None]:
    """
    A convenience function that reads an EPUB file and splits it into
    chapters.

    Args:
        file_path (str): The path to the EPUB file to be read.
        metadata (dict): A dictionary containing metadata such as title and
            author information.
        ocr_provider (OCRProvider | None): Optional OCR provider; defaults
            to the environment-configured provider.

    Returns:
        str: The cleaned text of the chapters separated by '***'.
    """
    epub_converter = initialize_epub_converter(
        file_path, metadata, ocr_provider
    )

    yield from epub_converter.parse_file()
