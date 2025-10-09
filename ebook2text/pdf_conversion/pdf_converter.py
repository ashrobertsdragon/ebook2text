import re
from collections.abc import Generator
from pathlib import Path

from pdfminer.high_level import extract_pages
from pdfminer.pdfparser import PDFSyntaxError

from ebook2text import logger
from ebook2text._exceptions import PDFConversionError
from ebook2text._types import LTPage
from ebook2text.pdf_conversion._enums import LineAction, LineType
from ebook2text.pdf_conversion.pdf_line_logic import check_line, compare_lines
from ebook2text.pdf_conversion.pdf_text_extractor import PDFTextExtractor
from ebook2text.text_utilities import desmarten_text


class PDFConverter:
    """
    PDFConverter class for converting PDF files to text and images.

    This class provides methods for extracting text and images from PDF files.
    It includes functions for processing PDF layout elements, extracting
    images in base64 format, running OCR on images, splitting text into
    paragraphs, and checking for chapter boundaries.

    Args:
        file_path (str): Path to the PDF file.
        metadata (dict): Dictionary with title and author name.
    """

    SENTENCE_PUNCTUATION: tuple = (".", "!", "?", '."', '!"', '?"')

    def __init__(
        self, file_path: Path, metadata: dict, text_extractor: PDFTextExtractor
    ):
        self.pages: Generator[LTPage, None, None] = self._read_file(file_path)
        self.metadata = metadata
        self._text_extractor = text_extractor

        self._max_lines_to_check = 6
        self._chapter_separator = "***\n"

        self._page: list[str] = []

    def _read_file(self, file_path: Path) -> Generator[LTPage, None, None]:
        """
        Read the PDF file using PDFMiner.Six extract_pages function.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            List[LTPage]: List of page objects.
        """
        try:
            yield from extract_pages(file_path, maxpages=25)
        except (PDFSyntaxError, OSError) as e:
            logger.error(f"Error reading PDF file: {e}")
            raise PDFConversionError from e

    def _ends_with_punctuation(self, text: str) -> bool:
        """Checks if text ends with sentence punctuation"""
        return text.rstrip().endswith(self.SENTENCE_PUNCTUATION)

    def _is_title_page(self, page_lines: list[str]) -> bool:
        """
        Determines if title page by comparing page length to threshold.
        """
        return len(page_lines) < self._max_lines_to_check

    @staticmethod
    def _split_line(line: str) -> list[str]:
        """Split the line at newline characters."""
        return line.split("\n")

    @staticmethod
    def _remove_smart_punctuation(text: str) -> str:
        """
        Remove smart punctuation from the given text.

        Args:
            text (str): The text to have smart punctuation removed.

        Returns:
            str: The text with smart punctuation removed.
        """
        return desmarten_text(text)

    def _add_line_to_page(self, line: str) -> None:
        """Adds a line to the current page."""
        self._page.append(line.rstrip() + "\n") if self._ends_with_punctuation(
            line
        ) else self._page.append(line)

    def _process_page_text(self, page_lines: list[str], metadata: dict) -> str:
        """
        Process the text of a page.

        Args:
            page_lines (list[str]): The lines of the page.
            metadata (dict): The metadata dictionary.

        Returns:
            str: The processed text of the page.

        Note:
            Due to limitations of the PDF specification, we can't assume that
            a newline is a new paragraph, a new page, a new chapter, or just a
            new line.
        """
        checked: int = 0
        index: int = 0
        previous_line_value: LineType = LineType.UNINITIALIZED
        last_action: LineAction = LineAction.UNINITIALIZED

        while index < len(page_lines):
            split_lines = self._split_line(page_lines[index])
            if len(split_lines) > 1:
                page_lines[index : index + 1] = split_lines

            line = page_lines[index].strip("\r\n").lstrip()
            index += 1
            if not line:
                continue

            if checked < self._max_lines_to_check:
                checked += 1
                line_value: LineType = check_line(line, metadata)
                action = compare_lines(
                    previous_line=previous_line_value,
                    current_line=line_value,
                    last_action=last_action,
                )
                last_action = action
                previous_line_value = line_value

                if action == LineAction.RETURN_EMPTY:
                    return ""
                elif action in (LineAction.FIRST_LINE, LineAction.CONTINUE):
                    continue
                elif action == LineAction.ADD_SEPARATOR:
                    self._page.append(self._chapter_separator)
            self._add_line_to_page(line)
        # after all lines run through `split_line`
        return "".join(self._page)

    @staticmethod
    def _remove_extra_whitespace(text: str) -> str:
        """Remove extra whitespace from the given text."""
        text = re.sub(r"\n+", "\n", text)
        return re.sub(r"[ ]{2,}", " ", text)

    def parse_file(self) -> Generator[str, None, None]:
        """
        Parse the PDF file and return the parsed text.

        Yields:
            str: The parsed text of the PDF file.
        """
        for page in self.pages:
            page_text = self._process_page_text(
                self._text_extractor.extract_text(page), self.metadata
            )
            self._page = []
            clean_text = self._remove_smart_punctuation(page_text)
            yield self._remove_extra_whitespace(clean_text)

    def _clean_before_write(self, text: str, output_path: Path) -> str:
        """
        Strips the chapter separator from the text if the file does not exist.

        Args:
            text (str): The text to be cleaned.
            output_path (Path): The path to the output file.

        Returns:
            str: The cleaned text.

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
        if not content.strip():
            return
        cleaned_content = self._clean_before_write(content, output_path)
        with output_path.open("a", encoding="utf-8") as f:
            f.write(cleaned_content)

    def return_string(self, generator: Generator[str, None, None]) -> str:
        """
        Return the parsed text as a string.

        Args:
            generator (Generator[str, None, None]): The content generator
                that yields the text. This is usually the `parse_file` method.

        Returns:
            str: The parsed text as a single string.
        """
        return "".join(line for line in generator if line.strip()).lstrip(
            self._chapter_separator
        )
