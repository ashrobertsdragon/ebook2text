import pytest
from pdfminer.high_level import extract_pages

from ebook2text._exceptions import PDFConversionError
from ebook2text.pdf_conversion import (
    PDFConverter,
    PDFImageExtractor,
    PDFTextExtractor,
)


@pytest.fixture
def test_pdf_path(test_files_dir):
    """Fixture for retrieving test PDF without images."""
    return test_files_dir / "test_pdf.pdf"


@pytest.fixture
def test_pdf_with_images_path(test_files_dir):
    """Fixture for retrieving test PDF with images."""
    return test_files_dir / "test_pdf_with_image.pdf"


@pytest.fixture
def pdf_image_extractor(test_pdf_with_images_path):
    """Fixture for initializing a PDFImageExtractor instance."""
    return PDFImageExtractor(file_path=test_pdf_with_images_path)


@pytest.fixture
def fake_image_extractor(test_pdf_with_images_path):
    """Fixture for initializing a fake PDFImageExtractor class for TextExtractor."""

    class FakeImageExtraction(PDFImageExtractor):
        def extract_images(self, return_list: list) -> list:
            return return_list

    return FakeImageExtraction(file_path=test_pdf_with_images_path)


@pytest.fixture
def pdf_text_extractor(fake_image_extractor):
    """Fixture for initializing a PDFTextExtractor instance."""
    return PDFTextExtractor(image_extractor=fake_image_extractor)


@pytest.fixture
def pdf_converter(test_pdf_path, metadata, pdf_text_extractor):
    """Fixture for initializing a PDFConverter instance."""
    return PDFConverter(
        file_path=str(test_pdf_path),
        metadata=metadata,
        text_extractor=pdf_text_extractor,
    )


@pytest.fixture
def pdf_converter_with_images(
    test_pdf_with_images_path, metadata, pdf_text_extractor
):
    """Fixture for initializing a PDFConverter instance with images."""
    return PDFConverter(
        file_path=str(test_pdf_with_images_path),
        metadata=metadata,
        text_extractor=pdf_text_extractor,
    )


class TestPDFConverter:
    def test_pdf_converter_read_file(self, pdf_converter):
        """Test the _read_file method to ensure pages are correctly read."""
        assert len(list(pdf_converter.pages)) == 7

    def test_pdf_converter_catches_pdf_syntax_error(
        self, pdf_text_extractor, metadata, tmp_path
    ):
        """Test the _read_file method to catch PDFSyntaxError."""
        file_content = b"Not a real PDF"
        file_name = "test.pdf"
        file_path = tmp_path / file_name
        file_path.write_bytes(file_content)
        pdf_converter = PDFConverter(file_path, metadata, pdf_text_extractor)
        with pytest.raises(PDFConversionError):
            list(pdf_converter.pages)

    def test_pdf_converter_ends_with_punctuation(self, pdf_converter):
        """Test ends_with_punctuation to confirm sentence end detection."""
        assert pdf_converter._ends_with_punctuation("Hello world!")
        assert not pdf_converter._ends_with_punctuation("Hello world")

    def test_parse_file_text_extraction(self, pdf_converter):
        """Test that parse_file extracts only the main content and excludes unwanted sections."""
        parsed_text = "".join(pdf_converter.parse_file())
        assert "Sample Title" not in parsed_text, (
            "Title text should be removed from output"
        )
        assert "Introduction" not in parsed_text, (
            "Introduction section should be removed from output"
        )
        assert "Chapter 1" not in parsed_text, (
            "Chapter 1 header should be removed from output"
        )
        assert "Chapter 2" not in parsed_text, (
            "Chapter 2 header should be removed from output"
        )
        assert "First chapter paragraph text." in parsed_text, (
            "Text after Chapter 1 should be included"
        )
        assert (
            "Lorem ipsum odor amet, consectetuer adipiscing elit."
            in parsed_text
        ), "Text after Chapter 2 should be included"

    def test_chapter_separator_insertion(self, pdf_converter):
        parsed_text = "".join(pdf_converter.parse_file())
        assert pdf_converter._chapter_separator in parsed_text, (
            "Chapter separator should be inserted between chapters"
        )

    def test_page_combining(self, pdf_converter):
        page_lines = [
            "This is a sentence.",
            "This is part of a sentence ",
            "that continues on the next line.",
        ]
        processed_text = pdf_converter._process_page_text(
            page_lines, pdf_converter.metadata
        )
        assert processed_text.endswith(
            "This is part of a sentence that continues on the next line.\n"
        )

    def test_remove_extra_whitespace(self, pdf_converter):
        text_with_whitespace = "Line 1\n\n\nLine 2  Line 3"
        cleaned_text = pdf_converter.remove_extra_whitespace(
            text_with_whitespace
        )
        assert cleaned_text == "Line 1\nLine 2 Line 3", (
            "Extra whitespace should be removed"
        )

    def test_image_processing(self, pdf_converter_with_images):
        """Test parsing with an image-based PDF containing 'Chapter 1' as an image."""
        parsed_text = "".join(pdf_converter_with_images.parse_file())

        assert "Sample Title" not in parsed_text, (
            "Title text should be removed from output"
        )
        assert "Introduction" not in parsed_text, (
            "Introduction section should be removed from output"
        )
        assert "Chapter 1" not in parsed_text, (
            "Chapter 1 header should be removed from output"
        )
        assert "Chapter 2" not in parsed_text, (
            "Chapter 2 header should be removed from output"
        )
        assert "First chapter paragraph text." in parsed_text, (
            "Text after Chapter 1 should be included"
        )
        assert (
            "Lorem ipsum odor amet, consectetuer adipiscing elit."
            in parsed_text
        ), "Text after Chapter 2 should be included"

    def test_write_text(self, pdf_converter, tmp_path):
        """Test that write_text correctly writes parsed content to a file."""
        output_file = tmp_path / "output.txt"
        if output_file.exists():
            output_file.unlink()
        for parsed_text in pdf_converter.parse_file():
            pdf_converter.write_text(parsed_text, output_file)

        assert output_file.exists(), "Output file should be created"
        written_content = output_file.read_text(encoding="utf-8")
        assert written_content.startswith(
            "First chapter paragraph text.\n***\nLorem ipsum odor amet, consectetuer adipiscing elit."
        )

    def test_return_string(self, pdf_converter):
        """Test that return_string correctly combines parsed text into a single string."""
        parsed_text_generator = pdf_converter.parse_file()
        result_string = pdf_converter.return_string(parsed_text_generator)

        assert isinstance(result_string, str), "Result should be a string"
        assert result_string.startswith(
            "First chapter paragraph text.\n***\nLorem ipsum odor amet, consectetuer adipiscing elit."
        )


class TestPDFTextExtractor:
    def test_extract_element_data(
        self, test_pdf_with_images_path, pdf_text_extractor
    ):
        """Test _extract_element_data method using the test PDF."""
        pages = list(extract_pages(test_pdf_with_images_path, maxpages=1))
        first_page = pages[0]
        image_nums, text_list = pdf_text_extractor._extract_element_data(
            first_page
        )

        assert image_nums == []
        assert "Sample Title" in text_list[0]

    def test_extract_image_object_number(
        self, test_pdf_with_images_path, pdf_text_extractor
    ):
        pages = list(extract_pages(test_pdf_with_images_path, maxpages=5))
        page_with_image = pages[4]
        image_nums, _ = pdf_text_extractor._extract_element_data(
            page_with_image
        )
        assert image_nums == [24]

    def test_process_element_data_text(
        self, test_pdf_with_images_path, pdf_text_extractor
    ):
        page = next(extract_pages(test_pdf_with_images_path, maxpages=1))
        text_element = list(page)[0]
        expected_result = ("text", "Sample Title \n")

        result = pdf_text_extractor._process_element(text_element)

        assert result == expected_result

    def test_process_element_data_image(
        self, test_pdf_with_images_path, pdf_text_extractor
    ):
        pages = list(extract_pages(test_pdf_with_images_path, maxpages=5))
        page_with_image = pages[4]
        image_element = list(page_with_image)[1]
        expected_result = ("image", 24)

        result = pdf_text_extractor._process_element(image_element)

        assert result == expected_result

    def test_extract_text_no_images(
        self, test_pdf_with_images_path, pdf_text_extractor, monkeypatch
    ):
        """Test extract_text method for pages without images."""

        pages = list(extract_pages(test_pdf_with_images_path, maxpages=4))
        expected_result = [
            "Introduction \n",
            "Sample introduction text paragraph. \n",
            " \n",
            " \n",
        ]

        text_result = pdf_text_extractor.extract_text(pages[3])

        assert isinstance(text_result, list)
        assert text_result == expected_result

    def test_extract_text_with_images(
        self, test_pdf_with_images_path, pdf_text_extractor, monkeypatch
    ):
        """Test extract_text method for pages with images."""

        def mock_run_ocr(images):
            return "Chapter One"

        monkeypatch.setattr(
            "ebook2text.pdf_conversion.pdf_text_extractor.run_ocr",
            mock_run_ocr,
        )

        pages = list(extract_pages(test_pdf_with_images_path, maxpages=5))
        page_with_image = pages[4]
        expected_result = [
            "Chapter One",
            "First chapter paragraph text. \n",
            " \n",
            " \n",
            " \n",
        ]

        text_result = pdf_text_extractor.extract_text(page_with_image)

        assert text_result == expected_result


class TestPDFImageExtractor:
    def test_pdf_image_extractor_extract_images(self, pdf_image_extractor):
        """Test extract_images to ensure images are properly processed and extracted."""
        images = pdf_image_extractor.extract_images([24])
        assert len(images) > 0
        assert isinstance(images[0], str)

    def test_pdf_image_extractor_create_image_from_binary(
        self, pdf_image_extractor
    ):
        """Test _create_image_from_binary to ensure valid base64 image encoding."""
        test_stream = b"\x00\xff\x00\xff\x00\xff\x00\xff\x00"
        encoded_image = pdf_image_extractor._create_image_from_binary(
            stream=test_stream, width=3, height=3, mode="L"
        )
        assert isinstance(encoded_image, str)
        assert (
            encoded_image
            == "iVBORw0KGgoAAAANSUhEUgAAAAMAAAADCAAAAABzQ+pjAAAAEElEQVR4nGNg+M/A8B9CAAAX9AP9aK8TcAAAAABJRU5ErkJggg=="
        )
