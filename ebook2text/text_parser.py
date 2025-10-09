from collections.abc import Generator
from pathlib import Path

from ebook2text._exceptions import TextConversionError
from ebook2text._logger import logger
from ebook2text.chapter_check import is_chapter
from ebook2text.text_utilities import clean_text, desmarten_text


class TextParser:
    def __init__(self, file_path: Path):
        self.file_path: Path = file_path
        self._chapter_separator: str = "***"

    def read_line(self) -> Generator[str, None, None]:
        try:
            with self.file_path.open("r", encoding="utf-8") as f:
                yield from f
        except (OSError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file: {e}")
            raise TextConversionError from e

    def parse_file(self) -> Generator[str, None, None]:
        """
        Parses the book lines, replacing chapter headers with asterisks and
        applying text standardization.

        Yields a line-by-line of the processed book content as a string.
        """
        for line in self.read_line():
            parsed_line = (
                self._chapter_separator
                if is_chapter(line)
                else desmarten_text(line)
            )

            yield clean_text(parsed_line)

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
        cleaned_content = self._clean_before_write(content, output_path)
        with output_path.open("a", encoding="utf-8") as f:
            f.write(cleaned_content + "\n")

    def return_string(self, generator: Generator[str, None, None]) -> str:
        """
        Return the parsed text as a string.

        Args:
            generator (Generator[str, None, None]): The content generator
                that yields the text. This is usually the `parse_file` method.

        Returns:
            str: The parsed text as a single string.
        """
        return "\n".join(line for line in generator if line.strip()).lstrip(
            self._chapter_separator
        )
