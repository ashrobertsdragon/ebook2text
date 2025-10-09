import base64
import itertools
from io import BytesIO
from pathlib import Path

from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import resolve1
from pdfminer.pdfparser import PDFParser
from pdfminer.pdftypes import PDFStream
from pdfminer.psparser import PSLiteral
from PIL import Image

from ebook2text import logger
from ebook2text._exceptions import ImageTooLargeError, ImageTooSmallError


def _expand_bits(data: bytes, bit_depth: int) -> bytes:
    """Convert 2 or 4 bit data to 8 bit"""
    if bit_depth in {8, 1}:
        return data
    elif bit_depth not in {2, 4}:
        raise ValueError(f"Unsupported bit depth: {bit_depth}")

    pixels_per_byte: int = 8 // bit_depth
    mask: int = (1 << bit_depth) - 1

    result = bytearray()
    for byte, i in itertools.product(data, range(pixels_per_byte - 1, -1, -1)):
        pixel = (byte >> (i * bit_depth)) & mask
        pixel = (pixel * 255) // ((1 << bit_depth) - 1)
        result.append(pixel)

    return bytes(result)


def _convert_psliteral_to_str(attr: PSLiteral) -> str:
    """Convert a PSLiteral attribute to string."""
    return str(attr).lstrip("/'").rstrip("'")


def _get_pillow_mode(color_space: str) -> str:
    """
    Get the Pillow mode based on bit depth and color space.

    Args:
        color_space (str): Color space of the image.

    Returns:
        str: Pillow mode.
    """
    match color_space:
        case "DeviceRGB":
            return "RGB"
        case "DeviceCMYK":
            return "CMYK"
        case _:
            return "RGB"  # Default mode for unknown color spaces


class PDFImageExtractor:
    """
    PDFImageExtractor class for extracting images from PDF objects.

    This class inherits from ImageExtraction and provides methods to process
    and extract images from PDF files based on the provided object numbers. It
    includes functionality to read the PDF file, retrieve image data, convert
    binary image data into base64-encoded PNG strings, and handle exceptions
    related to image size.

    Methods:
        extract_images: Processes and extracts images from PDF objects based
            on the provided object numbers.

    Raises:
        ImageTooSmallError: If the image dimensions are too small.
        ImageTooLargeError: If the image dimensions are too large.
        TypeError: If an invalid object type is encountered during image
            retrieval.
        Exception: If there is an error in processing the image data.
    """

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path

    def extract_images(self, obj_nums: list[int]) -> list[str]:
        """
        Processes and extracts images from PDF objects based on the provided
        object numbers.

        This method reads the PDF file, initializes a PDF parser, and iterates
        through the list of object numbers. For each object number, it
        attempts to retrieve the image data using the '_get_image' method. If
        successful, the binary image data is converted into a base64-encoded
        JPEG format string and added to the list. The final output is a list
        of base64-encoded strings representing the images extracted from the
        PDF.

        Args:
            obj_nums (List[int]): A list of object numbers corresponding to
            images in the PDF.

        Returns:
            List[str]: A list of base64-encoded strings representing the
                extracted images.
        """
        with self.file_path.open("rb") as f:
            parser = PDFParser(f)
            self.document = PDFDocument(parser)
            base64_images: list = [
                self._get_image(obj_num, attempt=0) for obj_num in obj_nums
            ]
        return [image for image in base64_images if image]

    def _create_image_from_binary(
        self, stream: bytes, width: int, height: int, mode: str
    ) -> str:
        """
        Convert binary image data into a base64-encoded JPEG string.

        Args:
            stream (bytes): The binary data of the image.
            width (int): The width of the image in pixels.
            height (int): The height of the image in pixels.

        Returns:
            str: A base64-encoded string representing the PNG image.

        Raises:
            Exception: If there is an error in processing the image data.
        """

        try:
            image = Image.frombytes(mode, (width, height), stream)
            image = (
                image.convert("L")
                if mode == "1"
                else image.convert("RGB")
                if mode == "CMYK"
                else image
            )
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except ValueError as e:
            logger.exception(
                f"Failed to create base64 encoded image due to {e}"
            )
            return ""

    def _transcode_to_png(self, jpeg_data: bytes) -> str:
        """
        Converts a JPEG byte stream to a PNG-based base64-encoded string
        without decoding.

        Args:
            jpeg_data (bytes): Byte stream of the JPEG image.

        Returns:
            bytes: PNG byte stream.
        """
        try:
            with BytesIO(jpeg_data) as jpeg, BytesIO() as png:
                image = Image.open(jpeg)
                image.save(png, format="PNG")
                return base64.b64encode(png.getvalue()).decode("utf-8")
        except Exception as e:
            logger.exception(f"Failed to transcode JPEG to PNG: {e}")
            raise

    def _get_image(self, obj_num: int, attempt: int = 0) -> str:
        """
        Processes and retrieves images from a PDF object.

        Args:
            obj_num (int): The object number of the PDF image to retrieve.
            attempt (Optional[int]): The number of attempts made to retrieve
                the image (default is 0).

        Returns:
            str: A base64-encoded string representing the JPEG image if
                successful, otherwise an empty string.

        Raises:
            Exception: If there is an error in processing the image data or if
                the image does not meet the required criteria.
        """
        if attempt > 1:
            logger.warning(
                f"Unable to extract image from object: {obj_num} "
                f"or {obj_num - 1}"
            )
            return ""
        try:
            obj = resolve1(self.document.getobj(obj_num))
            if not isinstance(obj, PDFStream):
                raise TypeError(
                    "Invalid object. "
                    f"Received {type(obj)} instead of PDFStream"
                )
            if _convert_psliteral_to_str(obj.get("Filter")) == "DCTDecode":
                return self._transcode_to_png(obj.get_data())
            width, height, mode, stream = self._parse_image_data(obj)
            return self._create_image_from_binary(stream, width, height, mode)
        except (ValueError, AttributeError, TypeError) as e:
            logger.exception(f"ValueError: {e}")
            return ""
        except ImageTooSmallError:
            # Small amounts of text with an embedded font are stored as a
            # soft mask to a 2x2 pixel image. This is not a real image, and
            # the soft mask translates to a bitmap.
            new_num, next_attempt = self._find_next_image(obj_num, attempt)
            return self._get_image(new_num, next_attempt)
        except ImageTooLargeError:
            logger.info(f"Image too large. Skipping object: {obj_num}")
            return ""
        except Exception as e:
            logger.exception(f"Exception: {e}")
            return ""

    def _find_next_image(self, obj_num: int, attempt: int) -> tuple[int, int]:
        """
        Finds the next image object in the PDF document.

        Args:
            obj_num (int): The object number of the current image.

        Returns:
            int: The object number of the next image in the PDF document.
        """
        next_obj = obj_num + 1
        new_attempt = attempt + 1
        if obj := resolve1(self.document.getobj(next_obj)):
            if isinstance(obj, PDFStream):
                return next_obj, new_attempt
        return (
            obj_num,
            100,
        )  # ensure attempt limit is exceeded to stop further attempts

    def _parse_image_data(
        self, stream: PDFStream
    ) -> tuple[int, int, str, bytes]:
        """
        Parses image data from a PDF object.

        Args:
            stream (PDFStream): The PDF object to parse.

        Returns:
            Tuple[int, int, str, bytes]: A tuple containing the width, height,
                color mode, and binary data of the image.
        """
        width: int = stream.get("Width", 0)
        height: int = stream.get("Height", 0)
        if width < 5 or height < 5:
            raise ImageTooSmallError(
                "Image too small. Get soft mask from next object"
            )
        if width > 1000 and height > 1000:
            raise ImageTooLargeError("probably full page image")
        mode, bit_depth = self._extract_color_data(stream)
        stream = _expand_bits(stream.get_data(), bit_depth)
        return width, height, mode, stream

    def _extract_color_data(self, stream: PDFStream) -> tuple[str, int]:
        """
        Extracts color data from a PDF object.

        Args:
            stream (PDFStream): The PDF object to extract color data from.

        Returns:
            Tuple[str, int]: A tuple containing the color mode and bit depth
                of the image.
        """
        bit_depth: int = stream.get("BitsPerComponent")
        color_space: PSLiteral = stream.get("ColorSpace")
        if isinstance(color_space, list):
            color_space = color_space[0]
        mode: str = "1" if bit_depth == 1 else _get_pillow_mode(color_space)
        return mode, bit_depth
