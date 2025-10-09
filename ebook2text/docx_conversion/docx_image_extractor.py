from ebook2text import logger
from ebook2text._types import Paragraph
from ebook2text.docx_conversion._namespaces import docx_ns_map
from ebook2text.ocr import encode_image_bytes


class DocxImageExtractor:
    """
    A class dedicated to extracting images from docx Paragraph objects.
    """

    def extract_images(self, paragraph: Paragraph) -> list[str]:
        """
        Extracts and converts images found in the paragraph into
        base64-encoded strings.

        Returns:
            list: A list of base64-encoded strings, each representing an image
                extracted from the paragraph.
        """
        image_blobs: list = self._extract_image_blobs(paragraph)
        return self._build_base64_images_list(image_blobs)

    def _build_base64_images_list(self, image_streams: list) -> list:
        """
        Converts image blobs to base64-encoded strings.

        Args:
            image_blobs (list): A list of extracted image streams.

        Returns:
            list: A list of base64-encoded strings representing the images.
        """
        return [encode_image_bytes(image) for image in image_streams]

    def _extract_image_blobs(self, paragraph: Paragraph) -> list:
        """
        Extracts image blobs from the paragraph.

        Returns:
            list: A list of image blobs extracted from the paragraph.
        """
        namespace: dict = docx_ns_map
        image_blobs: list = []

        blips = paragraph._p.findall(".//a:blip", namespaces=namespace)
        for blip in blips:
            try:
                r_id = blip.attrib[f"{{{namespace['r']}}}embed"]
                image_part = paragraph.part.related_parts[r_id]
                blob = image_part.blob
                image_blobs.append(blob)
            except (KeyError, ValueError, AttributeError) as e:
                logger.exception(f"Corrupted image data: {str(e)}")
                continue
        return image_blobs
