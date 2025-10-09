from pdfminer.pdfdocument import PDFSyntaxError

from ebook2text import logger
from ebook2text._exceptions import PDFConversionError
from ebook2text._types import LTChar, LTContainer, LTItem, LTPage, LTText
from ebook2text.ocr import run_ocr
from ebook2text.pdf_conversion.pdf_image_extractor import PDFImageExtractor


class PDFTextExtractor:
    """
    The PDFTextExtractor class implements the functionality to extract text
    from a PDF page, including OCR text from images.

    Methods:
        extract_text: Extracts text from a PDF page, including OCR text from
            images.
    """

    def __init__(self, image_extractor: PDFImageExtractor) -> None:
        self.image_extractor = image_extractor
        self._image_obj_nums: list[int] = []
        self._pdf_text_list: list[str] = []

    def _match_objects(self, obj_type: str, obj_data: int | str) -> None:
        """
        Matches objects to their respective types.

        Args:
            obj_type (str): The type of the object.
            obj_data (Union[int, str]): The data of the object.
        """
        match obj_type:
            case "image":
                self._image_obj_nums.append(int(obj_data))
            case "text":
                self._pdf_text_list.append(str(obj_data))
            case _:
                pass

    def _extract_element_data(
        self, page: LTPage
    ) -> tuple[list[int], list[str]]:
        """
        Extracts text and image data from a PDF page.

        This function receives an LTPage object extracted by PDFMiner and
        returns a tuple containing a list of image object numbers and a list
        of strings containing the text from the page.

        Args:pdf
            page (LTPage): The page to extract text and image data from.

        Returns:
            tuple[list[int], list[str]]: A tuple containing a list of image
                object numbers and a list of strings containing the text from
                the page.
        """

        for element in page:
            obj_type, obj_data = self._process_element(element)
            self._match_objects(obj_type, obj_data)
        return self._image_obj_nums, self._pdf_text_list

    def extract_text(self, page: LTPage) -> list[str]:
        """
        Extracts text from a PDF page, including OCR text from images.

        This method processes a given PDF page represented by the LTPage
        object. It iterates through the elements on the page, categorizes them
        as images or text using the '_process_element' method, and collects
        the object numbers of images and text content. For text elements, it
        appends the extracted text to a list after checking for the presence
        of actual text. If the element is an image, it adds the object number
        to a separate list. After processing all elements, it calls the
        '_extract_text_from_image' method to extract text from images using
        OCR. Finally, it combines the OCR text with the extracted text content
        from the page and returns the concatenated result as a single string.

        Args:
            page (LTPage): The PDF page represented as an LTPage object.

        Returns:
            List[str]: The extracted text content from the PDF page, including
                OCR text from images.
        """
        image_obj_nums, pdf_text_list = self._extract_element_data(page)
        self._image_obj_nums = []
        self._pdf_text_list = []

        if not image_obj_nums:
            return pdf_text_list

        try:
            ocr_text = self._extract_image_text(image_obj_nums)
        except PDFSyntaxError as e:
            logger.error(f"PDFMiner error parsing page: {e}")
            raise PDFConversionError from e
        return [ocr_text] + pdf_text_list

    def _process_element(self, element: LTItem) -> tuple[str, int | str]:
        """
        Processes a PDF layout element to identify its type and extract
        relevant data.

        This function categorizes a given PDF layout element into types such
        as image, text, or other. For image elements, it returns the object
        ID. For text elements, it returns the extracted text. The function
        handles container elements by recursively processing their children.
        If an element does not match any specific type, it is categorized as
        "other".

        Args:
            element (LTItem): A PDF layout element from pdfminer.

        Returns:
            Tuple[str, Union[int, str]]: A tuple containing the element
                type and its relevant data (object ID for images or text
                content for text elements), or None for other types.
        """
        if hasattr(element, "stream"):
            return "image", element.stream.objid
        elif isinstance(element, LTText) and not isinstance(element, LTChar):
            return "text", element.get_text()
        elif isinstance(element, LTContainer):
            for child in element:
                return self._process_element(child)
        return "other", ""

    def _extract_image_text(self, image_obj_nums: list[int]) -> str:
        """
        Collect list of Base64 encoded images and extract text with LLM.
        Args:
            image_obj_nums (List[int]): List of image object numbers.

        Returns:
            str: Extracted text from images.
        """
        base64_images: list[str] = self.image_extractor.extract_images(
            image_obj_nums
        )
        return run_ocr(base64_images)
