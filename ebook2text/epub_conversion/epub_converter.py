from collections.abc import Generator
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub
from ebooklib.epub import EpubException

from ebook2text import logger
from ebook2text._exceptions import EpubConversionError
from ebook2text._types import EpubBook, EpubItem, ResultSet, Tag
from ebook2text.chapter_check import NOT_CHAPTER, is_chapter, is_not_chapter
from ebook2text.epub_conversion.epub_text_extractor import EpubTextExtractor
from ebook2text.text_utilities import desmarten_text


class EpubConverter:
    """
    Converts EPUB files to text and splits chapters.

    Args:
        file_path (str): The path to the EPUB file to be read.
        metadata (dict): A dictionary containing metadata such as title and
            author information.

    Attributes:
        epub_book (EpubBook): The EpubBook object representing the EPUB file.
        metadata (dict): A dictionary containing metadata such as title and
            author information.
        text_extractor (EpubTextExtractor): An instance of EpubTextExtractor
            for extracting text from the EPUB file.
        _chapter_separator (str): The separator used to separate chapters.
        max_lines_to_check (int): The maximum number of lines to check for
            chapter boundaries.

    Methods:
        _read_file(file_path): Reads an EPUB file using Ebooklib package.
        _get_items(): Yields items in the Epub file.
        _process_chapter_text(item): Extracts text from a chapter item.
        _clean_text(text): Cleans the extracted text.
        parse_file(): Splits the EPUB file into chapters and returns the
            cleaned text.
        write_text(content, file_path): Writes the parsed text to a file.
        return_string(generator): Returns the parsed text as a string.
    """

    def __init__(
        self,
        file_path: Path,
        metadata: dict,
        text_extractor: EpubTextExtractor,
    ) -> None:
        self.epub_book: EpubBook = self._read_file(file_path)
        self.metadata = metadata
        self.text_extractor = text_extractor
        self._chapter_separator = "\n***\n"
        self.max_lines_to_check = 6

    def _read_file(self, file_path: Path) -> EpubBook:
        """Reads Epub file from the file path using Ebooklib package"""
        try:
            return epub.read_epub(file_path, options={"ignore_ncx": True})
        except EpubException as e:
            logger.error(f"Error reading EPUB file: {e}")
            raise EpubConversionError from e

    def _get_items(self) -> Generator[EpubItem, None, None]:
        """Yields 'items' in the Epub file."""
        try:
            yield from self.epub_book.get_items()
        except EpubException as e:
            logger.error(f"Error reading EPUB file: {e}")
            raise EpubConversionError from e

    def _process_chapter_text(self, item: EpubItem) -> str:
        """
        Extracts text from a chapter item.

        Args:
            item: ebooklib item representing a chapter.

        Returns:
            str: String containing the text of the chapter.
        """
        text_elements = ["p", "img", "h1", "h2", "h3", "h4", "h5", "h6"]
        soup = BeautifulSoup(item.content, "html.parser")
        elements: ResultSet[Tag] = soup.find_all(text_elements)

        for i, element in enumerate(elements[: self.max_lines_to_check]):
            text = self.text_extractor.extract_text(element, self.epub_book)
            if any(word in NOT_CHAPTER for word in text.split()):
                return ""
            elif is_chapter(text):
                starting_line = i + 1
                return "\n".join(
                    tag.get_text().strip()
                    for tag in elements[starting_line:]
                    if tag != "img"
                )
        return ""

    def clean_text(self, text: str) -> str:
        """
        Removes smart punctuation from text
        """
        return desmarten_text(text)

    def parse_file(self) -> Generator[str, None, None]:
        """
        Split the EPUB file into chapters and return the cleaned text.

        Returns:
            str: The cleaned text of the chapters separated by the chapter
                separator.
        """
        for item in self._get_items():
            if (
                item.get_type() == ebooklib.ITEM_DOCUMENT
                and not is_not_chapter(item.file_name.lower(), self.metadata)
            ):
                if chapter_text := self._process_chapter_text(item):
                    yield self.clean_text(chapter_text)

    def _clean_before_write(self, text: str, output_path: Path) -> str:
        """
        Strips the chapter separator from the text if the file does not exist.

        Args:
            text (str): The text to be cleaned.
            output_path (Path): The path to the output file.

        Returns:
            str: The text with the leading chapter separator stripped.

        Note:
            This method is used to strip the leading chapter separator
            before writing to a file.
        """
        return (
            text
            if output_path.exists()
            else text.lstrip(self._chapter_separator)
        )

    def write_text(self, content: str, output_path: Path) -> None:
        """
        Write the parsed text to a file.

        Args:
            output (str): The parsed text to be written to the file.
            file_path (Path): The path to the output file.
        """
        cleaned_content = self._clean_before_write(content, output_path)
        with output_path.open("a", encoding="utf-8") as f:
            f.write(self._chapter_separator + cleaned_content)

    def return_string(self, generator: Generator[str, None, None]) -> str:
        """
        Return the parsed text as a string.

        Args:
            generator (Generator[str, None, None]): The content generator
                that yields the text. This is usually the `parse_file` method.

        Returns:
            str: The parsed text as a single string.
        """
        return f"{self._chapter_separator}".join(generator)
