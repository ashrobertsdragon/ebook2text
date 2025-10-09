from ebook2text._types import EpubBook, Tag
from ebook2text.ocr import encode_image_bytes, run_ocr


class EpubTextExtractor:
    """
    Extracts text from EPUB elements, handling image OCR.
    """

    def extract_text(self, element: Tag, book: EpubBook | None = None) -> str:
        """
        Extracts text from an element, using OCR for images.

        Args:
            element: The element from which text needs to be extracted.
            book (EpubBook): The EpubBook object for accessing image data.

        Returns:
            str: The extracted text from the element.
        """
        if element.name != "img":
            return self._extract_text(element)
        if not book:
            raise ValueError("Book is not provided")
        return self._extract_image_text(element, book)

    def _get_image_file(self, element: Tag, book: EpubBook) -> list:
        """
        Extracts images from the EPUB file.

        Args:
            element: The element containing the image data.

        Returns:
            list: A list of encoded image data.
        """
        if element.name != "img":
            raise ValueError("Element is not an image")
        image = book.get_item_with_id(element.get("src"))
        return [encode_image_bytes(image.get_content())]

    def _extract_image_text(self, element: Tag, book: EpubBook) -> str:
        """
        Extracts text from an image element.

        Args:
            element (Tag): The element containing the image data.
            book (EpubBook): The EpubBook object for accessing image data.

        Returns:
            str: The extracted text from the image.
        """
        base64_images: list = self._get_image_file(element, book)
        return run_ocr(base64_images)

    def _extract_text(self, element: Tag) -> str:
        return element.get_text().strip()
