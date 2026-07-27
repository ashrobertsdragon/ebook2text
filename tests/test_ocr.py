from pathlib import Path

import pytest
from PIL import Image

from ebook2text.ocr import encode_image_bytes, encode_image_file, run_ocr


@pytest.fixture
def saved_image(tmp_path):
    img_file = tmp_path / "test.png"
    stream = b"\x00\xff\x00\xff\x00\xff\x00\xff\x00"
    image = Image.frombytes("L", (3, 3), stream)
    image.save(img_file, format="PNG")
    return str(img_file)


def test_encode_image_bytes(expected_base64_image):
    test_file_path = Path(__file__).parent / "test_files" / "chapter_one.jpg"
    with open(test_file_path, "rb") as image_file:
        image_bytes = image_file.read()
    encoded_image = encode_image_bytes(image_bytes)
    assert encoded_image == expected_base64_image


def test_encode_image_file(saved_image):
    encoded_str = encode_image_file(saved_image)
    assert isinstance(encoded_str, str)
    assert (
        encoded_str
        == "iVBORw0KGgoAAAANSUhEUgAAAAMAAAADCAAAAABzQ+pjAAAAEElEQVR4nGNg+M/A8B9CAAAX9AP9aK8TcAAAAABJRU5ErkJggg=="
    )


def test_run_ocr_delegates_to_provider_and_warns(mocker):
    provider = mocker.MagicMock()
    provider.perform_ocr.return_value = "Detected text"
    factory = mocker.patch(
        "ebook2text.ocr.get_ocr_provider", return_value=provider
    )
    with pytest.deprecated_call():
        result = run_ocr(["base64data"])
    assert result == "Detected text"
    factory.assert_called_once_with()
    provider.perform_ocr.assert_called_once_with(["base64data"])


def test_importing_ocr_requires_no_env_vars(monkeypatch):
    import importlib

    import ebook2text.ocr

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    importlib.reload(ebook2text.ocr)
