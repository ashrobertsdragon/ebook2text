import pytest

from ebook2text.convert_file import convert_file


@pytest.mark.parametrize(
    "file_name",
    [
        "test_pdf_with_image.pdf",
        "test_epub_with_image.epub",
        "test_docx_with_image.docx",
    ],
)
def test_convert_file_with_injected_ocr_provider(
    test_files_dir, metadata, file_name, fake_ocr_provider_class
):
    provider = fake_ocr_provider_class(response="Injected OCR text")
    result = convert_file(
        test_files_dir / file_name,
        metadata,
        save_file=False,
        ocr_provider=provider,
    )
    assert isinstance(result, str)
    assert provider.calls
