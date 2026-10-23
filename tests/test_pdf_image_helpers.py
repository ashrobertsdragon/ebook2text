import pytest
from pdfminer.pdftypes import PDFStream
from pdfminer.psparser import LIT

from ebook2text.pdf_conversion.pdf_image_extractor import (
    PDFImageExtractor,
    _expand_bits,
    _get_pillow_mode,
)


class TestExpandBits:
    # Convert 2-bit data to 8-bit with correct pixel values
    def test_2bit_to_8bit_conversion(self):
        input_data = bytes([0b11001100])  # 2-bit values: 3,0,3,0
        expected = bytes([255, 0, 255, 0])
        result = _expand_bits(input_data, 2)
        assert result == expected

    # Convert 4-bit data to 8-bit with correct pixel values
    def test_4bit_to_8bit_conversion(self):
        input_data = bytes([0xF0])  # 4-bit values: 15,0
        expected = bytes([255, 0])
        result = _expand_bits(input_data, 4)
        assert result == expected

    # Return original data unchanged for 8-bit input
    def test_8bit_passthrough(self):
        input_data = bytes([0, 128, 255])
        result = _expand_bits(input_data, 8)
        assert result == input_data

    # Return original data unchanged for 1-bit input
    def test_1bit_passthrough(self):
        input_data = bytes([0b10101010])
        result = _expand_bits(input_data, 1)
        assert result == input_data

    # Verify pixel values are properly scaled between 0-255
    def test_pixel_value_scaling(self):
        input_data = bytes([0b01101001])  # 2-bit values: 1,2,2,1
        expected = bytes([85, 170, 170, 85])  # Scaled to 8-bit
        result = _expand_bits(input_data, 2)
        assert result == expected

    # Handle empty byte array input
    def test_empty_input(self):
        input_data = bytes([])
        result = _expand_bits(input_data, 2)
        assert result == bytes([])

    # Process single byte input
    def test_single_byte_input(self):
        input_data = bytes([0b00000011])  # 2-bit values: 0,0,0,3
        expected = bytes([0, 0, 0, 255])
        result = _expand_bits(input_data, 2)
        assert result == expected

    # Process large byte arrays
    def test_large_input(self):
        input_data = bytes([0xFF] * 1000)
        result = _expand_bits(input_data, 4)
        assert len(result) == 2000  # Each input byte produces 2 output bytes
        assert all(b == 255 for b in result)

    # Handle bit depth of 0
    def test_zero_bit_depth(self):
        with pytest.raises(ValueError) as exc_info:
            _expand_bits(bytes([0xFF]), 0)
        assert "Unsupported bit depth: 0" in str(exc_info.value)

    # Handle negative bit depth
    def test_negative_bit_depth(self):
        with pytest.raises(ValueError) as exc_info:
            _expand_bits(bytes([0xFF]), -2)
        assert "Unsupported bit depth: -2" in str(exc_info.value)


class TestGetPillowMode:
    # Handle empty color space string
    def test_empty_color_space_returns_rgb(self):
        result = _get_pillow_mode(color_space="")
        assert result == "RGB"

    # Returns 'RGB' for DeviceRGB color space
    def test_device_rgb_returns_rgb(self):
        result = _get_pillow_mode(color_space="DeviceRGB")
        assert result == "RGB"

    # Returns 'CMYK' for DeviceCMYK color space
    def test_devicecmyk_returns_cmyk(self):
        result = _get_pillow_mode(color_space="DeviceCMYK")
        assert result == "CMYK"

    # Returns 'RGB' as default for unknown color spaces
    def test_unknown_color_space_returns_rgb(self):
        result = _get_pillow_mode(color_space="UnknownColorSpace")
        assert result == "RGB"


@pytest.mark.parametrize("wrapped", [False, True], ids=["literal", "list"])
@pytest.mark.parametrize(
    ("color_space_name", "bit_depth", "expected_mode", "data_size"),
    [
        ("DeviceRGB", 8, "RGB", 192),
        ("DeviceCMYK", 8, "CMYK", 256),
        ("DeviceGray", 1, "1", 8),
        ("UnknownColorSpace", 8, "RGB", 192),
    ],
)
def test_parse_image_data_normalizes_pdf_color_space(
    test_files_dir,
    wrapped,
    color_space_name,
    bit_depth,
    expected_mode,
    data_size,
):
    extractor = PDFImageExtractor(test_files_dir / "test_pdf.pdf")
    color_space = LIT(color_space_name)
    data = bytes(data_size)
    stream = PDFStream(
        {
            "Width": 8,
            "Height": 8,
            "BitsPerComponent": bit_depth,
            "ColorSpace": [color_space] if wrapped else color_space,
        },
        data,
    )

    assert extractor._parse_image_data(stream) == (8, 8, expected_mode, data)
