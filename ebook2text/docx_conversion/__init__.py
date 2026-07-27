from collections.abc import Generator
from pathlib import Path

from ebook2text.ai_providers import OCRProvider
from ebook2text.docx_conversion.docx_converter import DocxConverter
from ebook2text.docx_conversion.docx_image_extractor import DocxImageExtractor
from ebook2text.docx_conversion.docx_text_extractor import DocxTextExtractor

__all__ = [
    "DocxConverter",
    "DocxImageExtractor",
    "DocxTextExtractor",
    "convert_docx",
    "initialize_docx_converter",
]


def initialize_docx_converter(
    file_path: Path,
    metadata: dict,
    ocr_provider: OCRProvider | None = None,
) -> DocxConverter:
    image_extractor = DocxImageExtractor()
    text_extractor = DocxTextExtractor(
        image_extractor, ocr_provider=ocr_provider
    )
    return DocxConverter(file_path, metadata, text_extractor)


def convert_docx(
    file_path: Path,
    metadata: dict,
    ocr_provider: OCRProvider | None = None,
) -> Generator[str, None, None]:
    """
    A convenience function that reads the contents of a DOCX file and returns
    the processed text.

    Args:
        file_path (str): The path to the DOCX file.
        metadata (dict): Metadata about the document.
        ocr_provider (OCRProvider | None): Optional OCR provider; defaults
            to the environment-configured provider.

    Returns:
        str: The processed text of the DOCX file formatted into chapters.
    """

    docx_converter = initialize_docx_converter(
        file_path, metadata, ocr_provider
    )

    yield from docx_converter.parse_file()
