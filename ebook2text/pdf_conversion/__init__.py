from collections.abc import Generator
from pathlib import Path

from ebook2text.pdf_conversion.pdf_converter import PDFConverter
from ebook2text.pdf_conversion.pdf_image_extractor import PDFImageExtractor
from ebook2text.pdf_conversion.pdf_text_extractor import PDFTextExtractor

__all__ = [
    "PDFConverter",
    "PDFImageExtractor",
    "PDFTextExtractor",
    "convert_pdf",
    "initialize_pdf_converter",
]


def initialize_pdf_converter(file_path: Path, metadata: dict) -> PDFConverter:
    """
    Initializes a PDFConverter instance.

    Args:
        file_path (Path): The path to the PDF file to be read.
        metadata (dict): A dictionary containing metadata such as title and
            author information.
    Returns:
        PDFConverter: A PDFConverter instance.
    """
    image_extractor = PDFImageExtractor(file_path)
    text_extractor = PDFTextExtractor(image_extractor)
    return PDFConverter(file_path, metadata, text_extractor)


def convert_pdf(file_path: Path, metadata: dict) -> Generator[str, None, None]:
    """
    A convenience function that reads a PDF file and splits its content into
    chapters based on chapter boundaries.
    This function initializes a PDFConverter object with the provided file
    path and metadata. It then calls the 'parse_file' method of the
    PDFConverter instance to read each page of a PDF file and yield the parsed
    text as a string in a generator.
    Args:
        file_path (str): The path to the PDF file to be read.
        metadata (dict): A dictionary containing metadata such as title and
            author information.

    Yields:
        str: The parsed text of each page in the PDF file.
    """
    pdf_converter: PDFConverter = initialize_pdf_converter(file_path, metadata)

    yield from pdf_converter.parse_file()
