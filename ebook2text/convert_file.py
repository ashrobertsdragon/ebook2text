from pathlib import Path

from ebook2text.docx_conversion import DocxConverter, initialize_docx_converter
from ebook2text.epub_conversion import EpubConverter, initialize_epub_converter
from ebook2text.pdf_conversion import PDFConverter, initialize_pdf_converter
from ebook2text.text_parser import TextParser


def _initialize_converter(
    file_path: Path, metadata: dict, extension: str
) -> DocxConverter | EpubConverter | PDFConverter | TextParser:
    """
    Initialize the appropriate converter based on the file extension.

    Args:
        file_path (Path): The path to the book file.
        metadata (dict): Dictionary with title and author name.
        extension (str): The file extension of the book file.

    Returns:
        Union[DocxConverter, EpubConverter, PDFConverter, TextParser]: The
            initialized converter.

    Raises:
        ValueError: If the file type is not supported.
    """
    if extension == ".epub":
        return initialize_epub_converter(file_path, metadata)
    elif extension == ".pdf":
        return initialize_pdf_converter(file_path, metadata)
    elif extension == ".docx":
        return initialize_docx_converter(file_path, metadata)
    elif extension in {".txt", ".text"}:
        return TextParser(file_path)
    raise ValueError(f"Unsupported file type: {extension}")


def _parse_file_path(file_path: Path) -> Path:
    """Create the text file name from the book file name."""
    folder = file_path.parent
    book_name = (
        file_path.stem.replace(" ", "_").replace("-", "_").replace(".", "_")
    )
    almost_path = folder / book_name
    return almost_path.with_suffix(".txt")


def convert_file(
    file_path: Path,
    metadata: dict,
    *,
    save_file: bool = True,
    save_path: Path | None = None,
) -> str | None:
    """
    Converts a book to a text file with 3 asterisks for chapter breaks
    Args:
        file_path: Path to the book file.
        metadata: Dictionary with title and author name.
        save_file: Boolean to save the file or not.
        save_path: (Optional) Path to save the file to.

    Returns:
        None if save_file is False, else returns the parsed text as a string.

    Raises:
        ValueError: If the file type is not supported (inherited from
            _initialize_converter).
    """
    extension = file_path.suffix.lower()
    converter = _initialize_converter(file_path, metadata, extension)
    if not save_file:
        return converter.return_string(converter.parse_file())

    save_path = save_path or _parse_file_path(file_path)
    for content in converter.parse_file():
        if content:
            converter.write_text(content, save_path)
    return None
