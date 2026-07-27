from ebook2text._types import Paragraph
from ebook2text.ai_providers import OCRProvider, get_ocr_provider
from ebook2text.docx_conversion.docx_image_extractor import DocxImageExtractor


class DocxTextExtractor:
    """
    Class dedicated to extracting and processing text from docx Paragraphs.
    """

    def __init__(
        self,
        image_extractor: DocxImageExtractor,
        ocr_provider: OCRProvider | None = None,
    ):
        self.image_extractor = image_extractor
        self._ocr_provider = ocr_provider

    @property
    def ocr_provider(self) -> OCRProvider:
        """Return the injected provider or build the default one."""
        if self._ocr_provider is None:
            self._ocr_provider = get_ocr_provider()
        return self._ocr_provider

    def extract_text(self, paragraph: Paragraph) -> str:
        """
        Extracts the text content from the paragraph, performs OCR on any
        images present, and returns whichever is not empty.

        Args:
            paragraph: The Paragraph object containing the text and formatting.

        Returns:
            str: The extracted and processed text.
        """
        ocr_text = self._extract_image_text(paragraph)
        paragraph_text = paragraph.text.strip()
        return ocr_text or paragraph_text

    def _extract_image_text(self, paragraph: Paragraph) -> str:
        """
        Extracts text from images within the paragraph using OCR.
        """
        if base64_images := self.image_extractor.extract_images(paragraph):
            return self.ocr_provider.perform_ocr(base64_images)
        return ""
