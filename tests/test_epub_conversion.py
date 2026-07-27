import pytest
from bs4 import BeautifulSoup

from ebook2text.epub_conversion import EpubConverter, EpubTextExtractor


@pytest.fixture
def epub_file(test_files_dir):
    return str(test_files_dir / "test_epub.epub")


@pytest.fixture
def epub_file_with_image(test_files_dir):
    return str(test_files_dir / "test_epub_with_image.epub")


@pytest.fixture
def sample_element_with_text():
    html = "<div><p>This is a sample paragraph.</p></div>"
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("p")


@pytest.fixture
def sample_element_with_image():
    html = '<img src="chapter_one.jpg"/>'
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("img")


@pytest.fixture
def epub_text_extractor(fake_ocr_provider):
    return EpubTextExtractor(ocr_provider=fake_ocr_provider)


@pytest.fixture
def epub_converter(epub_file, metadata, epub_text_extractor):
    return EpubConverter(epub_file, metadata, epub_text_extractor)


@pytest.fixture
def epub_converter_with_image(
    epub_file_with_image, metadata, epub_text_extractor
):
    return EpubConverter(epub_file_with_image, metadata, epub_text_extractor)


class TestEpubConverter:
    def test_parse_file_returns_valid_chapters(self, epub_converter):
        chapters = list(epub_converter.parse_file())
        assert len(chapters)
        assert all(isinstance(chapter, str) for chapter in chapters)
        assert all(len(chapter.strip()) > 0 for chapter in chapters)

    def test_process_chapter_text_extracts_content(
        self, epub_converter, epub_file
    ):
        page_4 = list(epub_converter._get_items())[4]
        text = epub_converter._process_chapter_text(page_4)
        assert isinstance(text, str)
        assert text == "First chapter paragraph text."

    def test_return_string_with_separators(self, epub_converter):
        chapters = list(epub_converter.parse_file())
        result_string = epub_converter.return_string(chapters)
        assert isinstance(result_string, str)
        assert (
            result_string.count(epub_converter.chapter_separator)
            == len(chapters) - 1
        )
        assert all(chapter in result_string for chapter in chapters)

    def test_write_text_with_chapter_separators(
        self, epub_converter, tmp_path
    ):
        content = "This is a test chapter."
        file_path = tmp_path / "output.txt"
        file_path.touch()

        epub_converter.write_text(content, file_path)
        with file_path.open("r", encoding="utf-8") as f:
            written_content = f.read()
        expected_content = f"\n***\n{content}"
        assert written_content == expected_content


class TestEpubTextExtractor:
    def test_extract_text_from_regular_element(
        self, epub_text_extractor, sample_element_with_text
    ):
        result = epub_text_extractor.extract_text(sample_element_with_text)
        assert result == "This is a sample paragraph."

    def test_extract_text_from_image_element(
        self,
        epub_converter_with_image,
        epub_text_extractor,
        sample_element_with_image,
    ):
        epub_book = epub_converter_with_image.epub_book
        element = sample_element_with_image
        print(element.get("src"))
        print(element.name)
        for key, value in element.attrs.items():
            print(key, value)
        result = epub_text_extractor.extract_text(
            sample_element_with_image, epub_book
        )
        assert isinstance(result, str)
        assert result == "Chapter One"

    def test_extract_text_from_empty_element(self, epub_text_extractor):
        html = "<div></div>"
        soup = BeautifulSoup(html, "html.parser")
        empty_element = soup.find("div")
        result = epub_text_extractor.extract_text(empty_element)
        assert result == ""

    def test_extract_text_from_whitespace_element(self, epub_text_extractor):
        html = "<p>    </p>"
        soup = BeautifulSoup(html, "html.parser")
        whitespace_element = soup.find("p")
        result = epub_text_extractor.extract_text(whitespace_element)
        assert result == ""

    def test_extract_text_from_element_with_nested_elements(
        self, epub_text_extractor
    ):
        html = "<div><p>This is a <strong>sample</strong> paragraph with <em>nested</em> elements.</p></div>"
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("p")
        result = epub_text_extractor.extract_text(element)
        assert result == "This is a sample paragraph with nested elements."
